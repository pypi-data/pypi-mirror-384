# yolo_analyzer.py
import cv2
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import logging
import torch
from typing import Optional, List, Dict
import json, typing

try:
    from ultralytics import YOLO
except ImportError:
    logging.error("Ultralytics (YOLO) not installed. Cannot run object detection.")
    YOLO = None


# --- FUNZIONI DI ANALISI YOLO ---

def _get_yolo_device():
    """Determines the optimal device for YOLO inference (CUDA, MPS, or CPU)."""
    if torch.cuda.is_available():
        logging.info("CUDA GPU detected. Using 'cuda' for YOLO.")
        return 'cuda'
    elif torch.backends.mps.is_available():
        logging.info("Apple MPS detected. Using 'mps' for YOLO.")
        return 'mps'
    else:
        logging.info("No compatible GPU detected. Using 'cpu' for YOLO.")
        return 'cpu'

def _load_and_sync_data(data_dir: Path):
    """Loads and synchronizes fixation, pupil, and world timestamps."""
    try:
        world_ts = pd.read_csv(data_dir / 'world_timestamps.csv')
        world_ts['frame'] = world_ts.index
        world_ts.sort_values('timestamp [ns]', inplace=True)
        fixations = pd.read_csv(data_dir / 'fixations.csv').sort_values('start timestamp [ns]')
        pupil = pd.read_csv(data_dir / '3d_eye_states.csv').sort_values('timestamp [ns]')
        gaze = pd.read_csv(data_dir / 'gaze.csv').sort_values('timestamp [ns]')
        # --- NUOVO: Carica anche gli eventi ---
        events = pd.read_csv(data_dir / 'events.csv').sort_values('timestamp [ns]')
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Missing required file for YOLO analysis: {e}")

    merged_fix = pd.merge_asof(world_ts, fixations, left_on='timestamp [ns]', right_on='start timestamp [ns]', direction='backward', suffixes=('', '_fix'))
    merged_fix['duration_s'] = merged_fix['duration [ms]'] / 1000.0
    duration_ns = (merged_fix['duration_s'] * 1e9).round()
    merged_fix['end_ts_ns'] = merged_fix['start timestamp [ns]'] + duration_ns.astype('Int64')
    synced_data_fixations_base = merged_fix[merged_fix['timestamp [ns]'] <= merged_fix['end_ts_ns']].copy()
    synced_data_fixations_pupil = pd.merge_asof(synced_data_fixations_base, pupil[['timestamp [ns]', 'pupil diameter left [mm]']], left_on='timestamp [ns]', right_on='timestamp [ns]', direction='nearest', suffixes=('', '_pupil'))
    
    # --- NUOVO: Aggiungi le informazioni sull'evento corrente a ogni fissazione ---
    synced_data_fixations = pd.merge_asof(synced_data_fixations_pupil.sort_values('timestamp [ns]'), 
                                          events[['timestamp [ns]', 'name']].rename(columns={'name': 'event_name'}), 
                                          on='timestamp [ns]', direction='backward')

    synced_data_gaze = pd.merge_asof(world_ts, gaze[['timestamp [ns]', 'gaze x [px]', 'gaze y [px]']], on='timestamp [ns]', direction='nearest')

    return synced_data_fixations, synced_data_gaze


def _is_inside(px, py, x1, y1, x2, y2):
    """Checks if a point (px, py) is inside a bounding box (x1, y1, x2, y2)."""
    return x1 <= px <= x2 and y1 <= py <= y2

def run_yolo_analysis(
    data_dir: Path, 
    output_dir: Path, 
    subj_name: str,
    yolo_models: Optional[typing.Dict[str, str]] = None,
    custom_classes: Optional[List[str]] = None,
    yolo_detections_df: Optional[pd.DataFrame] = None,
    tracker_config_path: Optional[str] = None
) -> None:
    """
    Runs YOLO object detection, correlates with fixations, and saves statistics.
    MODIFIED for multi-task (detect, segment, pose) and flexible model loading.
    """
    if YOLO is None:
        logging.warning("Skipping YOLO analysis because Ultralytics is not installed.")
        return
    if not yolo_models:
        logging.warning("Skipping YOLO analysis because no models were selected.")
        return

    video_path = next(data_dir.glob('*.mp4'), None)
    if not video_path:
        logging.warning(f"Skipping YOLO analysis: no .mp4 file found in {data_dir}.")
        return

    yolo_device = _get_yolo_device()
    models = {}
    reid_model = None # Variabile per memorizzare il modello Re-ID
    try:
        for task, model_name in yolo_models.items():
            # --- MODIFICA: Gestione speciale per i modelli Re-ID ---
            if task == 'reid':
                # Carica il modello Re-ID ma non lo aggiunge al dizionario dei modelli da eseguire per frame
                reid_model = YOLO(model_name)
                logging.info(f"Loaded Re-ID model '{model_name}'. It will be used by the tracker.")
                continue
            # --- FINE MODIFICA ---

            models[task] = YOLO(model_name)
            logging.info(f"Loaded YOLO model '{model_name}' for task '{task}'.")

        # Imposta le classi custom per il modello world, se presente
        if 'detect_world' in models and custom_classes:
            logging.info(f"Setting custom classes for zero-shot detection: {custom_classes}")
            models['detect_world'].set_classes(custom_classes)

    except Exception as e:
        logging.error(f"Error loading one or more YOLO models: {e}. Skipping YOLO analysis.")
        return

    try:
        synced_et_data_fix, synced_et_data_gaze = _load_and_sync_data(data_dir)
    except Exception as e:
        logging.error(f"Error loading/syncing eye-tracking data for YOLO: {e}. Skipping YOLO analysis.")
        return

    detections_df = pd.DataFrame() # Initialize as empty

    if yolo_detections_df is not None and not yolo_detections_df.empty:
        logging.info("Using pre-filtered YOLO detections passed from the GUI.")
        detections_df = yolo_detections_df
    else:
        yolo_cache_path = output_dir / 'yolo_detections_cache.csv'
        if yolo_cache_path.exists():
            logging.info(f"YOLO cache found. Loading detections from: {yolo_cache_path}")
            try:
                temp_df = pd.read_csv(yolo_cache_path)
                required_cols = ['frame_idx', 'track_id', 'class_name', 'task']
                if all(col in temp_df.columns for col in required_cols):
                    detections_df = temp_df
                else:
                    logging.warning("YOLO cache is outdated (missing required columns). Regenerating...")
                    yolo_cache_path.unlink() # Remove the old cache file
            except Exception as e:
                logging.warning(f"Could not read YOLO cache file ({e}). Regenerating...")
                yolo_cache_path.unlink()

    # --- MODIFICA: Esegui l'analisi video solo se detections_df è ancora vuoto ---
    if detections_df.empty:
        if not yolo_cache_path.exists():
            logging.info("YOLO cache not found. Starting video tracking...")
        cap = cv2.VideoCapture(str(video_path))
        frame_idx = 0
        detections = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logged_mps_pose_warning = False
        
        effective_device = yolo_device
        pbar = tqdm(total=total_frames, desc=f"YOLO Tracking on {effective_device.upper()}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            try:
                all_results = {}
                for task, model in models.items():
                    # Logica per forzare la CPU sui modelli di posa su MPS
                    device_for_task = effective_device
                    if task == 'pose' and effective_device == 'mps':
                        if not logged_mps_pose_warning:
                            logging.warning("Pose model on Apple MPS detected. Forcing CPU to avoid known bugs.")
                            logged_mps_pose_warning = True # Logga solo una volta
                        device_for_task = 'cpu'
                    all_results[task] = model.track(frame, persist=True, verbose=False, device=device_for_task)
            except Exception as e:
                if effective_device != 'cpu':
                    logging.warning(f"Inference on '{effective_device}' failed: {e}. Falling back to CPU.")
                    effective_device = 'cpu'
                    pbar.set_description(f"YOLO Tracking on {effective_device.upper()} (Fallback)")
                    for task, model in models.items():
                        all_results[task] = model.track(frame, persist=True, verbose=False, device=effective_device)
                else:
                    raise e # Se fallisce anche sulla CPU, l'errore è più grave

            frame_detections_list = []
            for task, results in all_results.items():
                res = results[0] # Prendi il primo risultato del batch
                if res.boxes is None or res.boxes.id is None: continue

                task_base_name = task.split('_')[0]

                for i, box in enumerate(res.boxes):
                    track_id = int(box.id[0])
                    class_id = int(box.cls[0])
                    class_name = models[task].names[class_id]
                    xyxy = box.xyxy[0].cpu().numpy()

                    # --- NUOVO: Estrai i dati OBB se disponibili ---
                    obb_coords_json = None
                    if hasattr(box, 'xywhr') and box.xywhr is not None:
                        obb_coords = box.xywhr[0].cpu().numpy().tolist()
                        obb_coords_json = json.dumps(obb_coords)

                    detection_data = {
                        'frame_idx': frame_idx, 'track_id': track_id, 'task': task_base_name,
                        'class_id': class_id, 'class_name': class_name,
                        'x1': xyxy[0], 'y1': xyxy[1], 'x2': xyxy[2], 'y2': xyxy[3]
                    }
                    
                    # Aggiungi dati di segmentazione
                    if obb_coords_json:
                        detection_data['obb_coords'] = obb_coords_json

                    if task_base_name == 'segment' and res.masks and i < len(res.masks.xy):
                        detection_data['mask_contours'] = json.dumps(res.masks.xy[i].tolist())

                    # Aggiungi dati di posa
                    if task_base_name == 'pose' and res.keypoints and i < len(res.keypoints.xy):
                        kpts_xy = res.keypoints.xy[i].cpu().numpy()
                        kpts_conf_tensor = res.keypoints.conf[i] if res.keypoints.conf is not None else torch.ones(len(kpts_xy))
                        kpts_conf = kpts_conf_tensor.cpu().numpy()[:, None]
                        kpts_with_conf = np.hstack((kpts_xy, kpts_conf))
                        detection_data['keypoints'] = json.dumps(kpts_with_conf.tolist())
                    
                    frame_detections_list.append(detection_data)

            detections.extend(frame_detections_list)
            # --- FINE NUOVA LOGICA ---

            frame_idx += 1
            pbar.update(1)

        cap.release()
        pbar.close()
    
        detections_df = pd.DataFrame(detections)
        if not yolo_cache_path.exists():
            logging.info(f"Saving YOLO detections to cache at: {yolo_cache_path}")
            detections_df.to_csv(yolo_cache_path, index=False)
    # --- FINE MODIFICA ---
    # --- INIZIA LA LOGICA DI ANALISI ---
    # Crea sempre i file di output, anche se vuoti.
    stats_instance_df = pd.DataFrame()
    stats_class_df = pd.DataFrame()
    id_map_df = pd.DataFrame(columns=['track_id', 'class_id', 'class_name', 'instance_name'])

    if not detections_df.empty:
        detections_df['instance_name'] = detections_df['class_name'] + '_' + detections_df['track_id'].astype(str)

        logging.info("Correlating detections with fixations...")
        merged_df_fix = pd.merge(detections_df, synced_et_data_fix, left_on='frame_idx', right_on='frame', how='inner')
        
        # Sostituisci la vecchia list comprehension con un ciclo esplicito per gestire la segmentazione
        fixation_hits = []
        for _, row in merged_df_fix.iterrows():
            if pd.isna(row['fixation x [px]']):
                continue

            px, py = row['fixation x [px]'], row['fixation y [px]']
            is_hit = False

            # Se il task è segmentazione e la maschera esiste
            if row.get('task') == 'segment' and 'mask_contours' in row and pd.notna(row['mask_contours']):
                try:
                    # Converte la stringa JSON di contorni in un array NumPy di interi
                    contour_points = np.array(json.loads(row['mask_contours'])).astype(np.int32)
                    # Usa pointPolygonTest di OpenCV per verificare se il punto è dentro il poligono
                    if cv2.pointPolygonTest(contour_points, (px, py), False) >= 0:
                        is_hit = True
                except (json.JSONDecodeError, ValueError, IndexError):
                    # Fallback al bounding box in caso di errore di parsing
                    if _is_inside(px, py, row['x1'], row['y1'], row['x2'], row['y2']):
                        is_hit = True
            else:
                # Comportamento di default: usa il bounding box
                if _is_inside(px, py, row['x1'], row['y1'], row['x2'], row['y2']):
                    is_hit = True

            if is_hit:
                fixation_hits.append(row)

        if fixation_hits:
            hits_df = pd.DataFrame(fixation_hits)
            logging.info("Calculating statistics for fixations...")            
            
            # --- MODIFICA: Aggiungi l'aggregazione degli eventi ---
            agg_dict_instance = {
                'n_fixations': ('fixation id', 'nunique'), 
                'avg_pupil_diameter_mm': ('pupil diameter left [mm]', 'mean'),
                'events': ('event_name', lambda x: list(x.unique())) # NUOVO
            }
            if 'avg_kp_confidence' in hits_df.columns:
                agg_dict_instance['avg_kp_confidence'] = ('avg_kp_confidence', 'mean')
            stats_instance = hits_df.groupby('instance_name').agg(**agg_dict_instance).reset_index()
            # --- FINE MODIFICA ---

            # Arrotonda il risultato per una migliore leggibilità
            if 'avg_keypoint_confidence' in stats_instance.columns:
                stats_instance['avg_keypoint_confidence'] = stats_instance['avg_keypoint_confidence'].round(3)
            
            total_detections_instance = detections_df.groupby('instance_name').size().reset_index(name='total_frames_detected')
            stats_instance = pd.merge(stats_instance, total_detections_instance, on='instance_name')
            stats_instance['normalized_fixation_count'] = stats_instance['n_fixations'] / stats_instance['total_frames_detected']
            
            # Aggregazione per classe (anch'essa condizionale)
            agg_dict_class = {
                'n_fixations': ('fixation id', 'nunique'), 
                'avg_pupil_diameter_mm': ('pupil diameter left [mm]', 'mean'),
                'events': ('event_name', lambda x: list(x.unique())) # NUOVO
            }
            if 'avg_kp_confidence' in hits_df.columns:
                agg_dict_class['avg_keypoint_confidence'] = ('avg_kp_confidence', 'mean')
            stats_class = hits_df.groupby('class_name').agg(**agg_dict_class).reset_index()

            # Arrotonda il risultato per una migliore leggibilità
            if 'avg_keypoint_confidence' in stats_class.columns:
                stats_class['avg_keypoint_confidence'] = stats_class['avg_keypoint_confidence'].round(3)

            total_detections_class = detections_df.groupby('class_name').size().reset_index(name='total_frames_detected')
            stats_class = pd.merge(stats_class, total_detections_class, on='class_name')
            stats_class['normalized_fixation_count'] = stats_class['n_fixations'] / stats_class['total_frames_detected']
            
            stats_instance_df = stats_instance
            stats_class_df = stats_class
            id_map_df = hits_df[['track_id', 'class_id', 'class_name', 'instance_name']].drop_duplicates()
            logging.info("Fixation-based statistics calculated.")
        # --- FINE MODIFICA ---
        else:
            logging.warning("No fixations were found inside any detected object bounding boxes.")
    else:
        logging.warning("No objects were detected by YOLO.")

    stats_instance_df.to_csv(output_dir / 'stats_per_instance.csv', index=False)
    stats_class_df.to_csv(output_dir / 'stats_per_class.csv', index=False)
    id_map_df.to_csv(output_dir / 'class_id_map.csv', index=False)

    logging.info("YOLO analysis part completed.")