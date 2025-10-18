 # SPEED v5.3.8.5 (Multi-User) - labScoc Software Processing and Extraction of Eye tracking Data
 
 Desktop App & Analysis Package

*An Advanced Eye-Tracking Data Analysis Software*

SPEED is a Python-based project for processing, analyzing, and visualizing eye-tracking data. Version 5.3.8.5 introduces a major restructuring, offering two distinct components. This version also adds a powerful multi-user batch analysis feature to process multiple participants in a single run.

1.  **SPEED Desktop App**: A user-friendly GUI application for running a full analysis pipeline, designed for end-users and researchers. Documentation -> [CLICK HERE](https://danielelozzi.github.io/SPEED)
2.  **`speed-analyzer`**[![PyPI version](https://img.shields.io/pypi/v/speed-analyzer.svg)](https://pypi.org/project/speed-analyzer/): A Python package for developers who want to integrate the analysis logic into their own scripts. Library documentation - [CLICK HERE](https://danielelozzi.github.io/SPEED/documentation/documentation.html)
3.  **`speedAnalyzerR`**: An experimental command-line package for the R programming language.
4.  **SPEED repository**: The repository of the whole project. Repo website -> [CLICK HERE](https://github.org/danielelozzi/speed)

 
 This version supports GPU acceleration for YOLO analysis and also offers four powerful AOI definition methods:
1.  **Static AOI**: A fixed rectangle for stationary scenes.
2.  **Dynamic AOI (Object Tracking)**: An AOI that automatically follows a selected object detected by YOLO.
3.  **Dynamic AOI (Manual Keyframes)**: A user-defined AOI path created by setting its position and size at key moments in the video.
4.  **Surface from Markers/QR Codes**: Define a dynamic, non-rectangular surface for enrichment by mapping its corners to ArUco or QR code markers.
5.  **Real-time visualization**: A real-time visualization of external and internal camera with multi-task YOLO, dynamic AOIs, and LSL streaming. It allows for live visualization of blinks, pupillometry, fragmentation, and event management.
6.  **Data Viewer**: A separate, powerful window that allows for the interactive visualization of BIDS/DICOM/Un-enriched data, with video playback, event editing, on-the-fly YOLO analysis, and data export.
7.  **Data Plotter**: An interactive tool to plot all time-series data (pupil, gaze, fixations, etc.) and calculate statistics on user-selected time ranges.
8.  **Multi-Task YOLO**: Pre-trained and custom object detection, segmentation, pose estimation, and oriented bounding box (OBB) detection using various YOLO models.
9.  **Advanced Tracking and Re-identification (Re-ID)**: Utilize robust trackers like BoT-SORT and ByteTrack to maintain object identities across frames, even through occlusions. This is crucial for accurately analyzing interactions with specific objects or people over time.
10. **Video-in-Video**: A specialized video generation mode that replaces the scene camera view with the on-screen content the user is watching, synchronized with gaze and events.
 ---
* **LSL Time Series Viewer**: An interactive window to visualize multi-channel time-series data (like gaze or EEG) from any LSL stream in real-time, with support for event markers.
* **Interactive NSI Calculator**: A post-analysis tool to calculate the Normalized Switching Index within user-defined time windows.

---

## Table of Contents


- [1. SPEED Desktop Application (For End Users)](#1-speed-desktop-application-for-end-users)
- [2. `speed-analyzer` (Python Package for Developers)](#2-speed-analyzer-python-package-for-developers)
  - [Installation from PyPI](#installation-from-pypi)
  - [How to Use the Package](#how-to-use-the-package)
  - [Choose Your AOI Strategy](#choose-your-aoi-strategy)
  - [Real-time](#real-time)
  - [Command-Line Interface (for Developers)](#command-line-interface-for-developers)
- [3. Docker Container (For Maximum Reproducibility)](#3-docker-container-for-maximum-reproducibility)
- [The Modular Workflow (GUI)](#the-modular-workflow-gui)
  - [Step 1: Run Core Analysis](#step-1-run-core-analysis)
  - [Step 2: Generate Outputs On-Demand](#step-2-generate-outputs-on-demand)
    - [Generate Plots 📊](#generate-plots-)
    - [Generate Videos 🎬](#generate-videos-)
    - [Post-Analysis Tools 🛠️](#post-analysis-tools-️)
  - [Computer Vision Analysis with YOLO 🤖](#computer-vision-analysis-with-yolo-)
- [R package](#r-package)
- [Environment Setup (For Development) ⚙️](#environment-setup-for-development-️)
- [How to Use the Application from Source 🚀](#how-to-use-the-application-from-source-)
- [🧪 Synthetic Data Generator (`generate_synthetic_data.py`)](#-synthetic-data-generator-generate_synthetic_datapy)
- [Export to BIDS Format](#export-to-bids-format)
- [DICOM Integration (Import/Export)](#dicom-integration-importexport)
- [R package (Experimental)](#r-package)
- [✍️ Authors & Citation](#-authors--citation)
- [💻 Artificial Intelligence disclosure](#-artificial-intelligence-disclosure)

 
## 1. SPEED Desktop Application (For End Users)
 
An application with a graphical user interface (GUI) for a complete, visually-driven analysis workflow.
 
### How to Use the Application
1.  **Download the latest version**: Go to the [Releases page](https://github.com/danielelozzi/SPEED/releases) and download the `.zip` file for your operating system (Windows or macOS).
2.  **Extract and Run**: Unzip the file and run the `SpeedApp` executable.
3.  **Follow the Instructions**: 
    - Use the interface to select your data folders (RAW, Un-enriched).
    - If you do not provide an "Enriched" data folder, a **"Define AOI..."** button will become active.
    - Click it to choose your preferred AOI method (Static, Dynamic Auto, or Dynamic Manual) and follow the on-screen instructions in the interactive editor.
    - Manage events, run the analysis, and generate outputs as before.
 
 
---
 
## 2. `speed-analyzer` (Python Package for Developers)
 
The core analysis engine of SPEED, now available as a reusable package. It's designed for automation and integration into custom data pipelines.
 
### Installation from PyPI
You can install the package directly from the Python Package Index (PyPI) using pip:
```bash
pip install speed-analyzer==5.3.8.5
```
### How to Use the Package
The package exposes a main function, `run_full_analysis`, that takes paths and options as arguments. See the `example_usage.py` file for a complete demonstration.

Here is a basic snippet:

```python
import pandas as pd
from speed_analyzer import run_full_analysis

 Define input and output paths
raw_path = "./data/raw"
unenriched_path = "./data/unenriched"
output_path = "./analysis_results"
subject_name = "participant_01"
```

### Choose Your AOI Strategy

The speed-analyzer package allows you to define Areas of Interest (AOIs) on-the-fly, directly in your code. This is the recommended workflow when you do not have a pre-existing enriched_data_path. The system is designed to handle a list of multiple, mixed-type AOIs in a single analysis run.
When you provide the `defined_aois` parameter, the software will automatically generate new enriched data files (`gaze_enriched.csv`, `fixations_enriched.csv`) where each gaze point and fixation is mapped to the name of the AOI it falls into.

You define AOIs by creating a list of Python dictionaries. Each dictionary must have three keys: name, type, and data.


```python
my_aois = [
    { "name": "AOI_Name_1", "type": "...", "data": ... },
    { "name": "AOI_Name_2", "type": "...", "data": ... },
]
```

#### AOI Type 1: Static AOI

Use this for a fixed rectangular region that does not move throughout the video. The data is a dictionary containing the pixel coordinates of the rectangle's corners.

```python
static_aoi = {
    "name": "Control_Panel",
    "type": "static",
    "data": {'x1': 100, 'y1': 150, 'x2': 800, 'y2': 600}
}
```

#### AOI Type 2: Dynamic AOI (Automatic Object Tracking)

Use this to have an AOI automatically follow an object detected by YOLO. This requires setting run_yolo=True. The data is the integer track_id of the object you want to follow. You would typically get the track_id from a preliminary YOLO analysis

```python
object_id_to_track = 1 

dynamic_auto_aoi = {
    "name": "Tracked_Ball",
    "type": "dynamic_auto",
    "data": object_id_to_track
}
```

#### AOI Type 3: Dynamic AOI (Manual Keyframes)

Use this to define a custom path for a moving and resizing AOI. You set the AOI's position and size at specific frames (keyframes), and the software will interpolate its position for all frames in between. The data is a dictionary where keys are frame indices and values are tuples of coordinates (x1, y1, x2, y2).

```python
manual_keyframes_aoi = {
    "name": "Animated_Focus_Area",
    "type": "dynamic_manual",
    "data": {
        0: (50, 50, 250, 250),      # Position at the start (frame 0)
        1000: (400, 300, 600, 500), # Position at frame 1000
        2000: (50, 50, 250, 250)     # Return to the start position at frame 2000
    }
}
```

#### Putting It All Together: Example with Multiple AOIs

You can combine any number of AOIs of any type into a single list and pass it to the analysis function.

```python
import pandas as pd
from speed_analyzer import run_full_analysis

# 1. Define paths
raw_path = "./data/raw"
unenriched_path = "./data/unenriched"
output_path = "./analysis_results_multi_aoi"
subject_name = "participant_02"

# 2. Define multiple, mixed-type AOIs
my_aois = [
    { "name": "Left_Monitor", "type": "static", "data": {'x1': 0, 'y1': 0, 'x2': 960, 'y2': 1080}},
    { "name": "Right_Monitor", "type": "static", "data": {'x1': 961, 'y1': 0, 'x2': 1920, 'y2': 1080}},
    { "name": "Moving_Target", "type": "dynamic_auto", "data": 3 }
]

# 3. Run the analysis
run_full_analysis(
    raw_data_path=raw_path,
    unenriched_data_path=unenriched_path,
    output_path=output_path,
    subject_name=subject_name,
    run_yolo=True, # Required for the 'dynamic_auto' AOI
    defined_aois=my_aois # Pass the complete list of AOIs
)
```

### Real-time

The real-time window provides a suite of interactive tools:

* **Live Data Overlays**: Toggle various visualizations on the fly:
    * **YOLO Detections**: See what objects the system is identifying in real-time.
    * **Gaze Point**: A circle indicating the current gaze position.
    * **Pupil & Fragmentation Plots**: Live graphs showing pupillometry and gaze speed.
    * **Blink Detector**: An on-screen indicator that appears during a blink.
    * **AOIs**: View your defined Areas of Interest overlaid on the video.
* **Recording**:
    * Start and stop recordings directly from the interface.
    * Data (gaze, events, video) is saved into a selected folder.
* **Event Management**:
    * Add timestamped events during a live recording by typing a name and clicking "Add Event".
* **On-the-fly AOI Definition**:
    * Pause the stream to draw, name, and add static rectangular AOIs directly on the video feed.
    * These AOIs are visualized instantly and used for analysis when the recording is stopped. At the end of the recording, a `gaze_in_aoi_results.csv` file is automatically generated.

* **LSL Streaming**: The real-time window can stream gaze, events, and video data over the network via Lab Streaming Layer (LSL). To record these streams, you need to install LabRecorder. You can find the installer on the official LSL:
  - (Download LabRecorder here)[https://labstreaminglayer.org/#/]
  - Download the version appropriate for your operating system, install it, and run it to record the data streams generated by SPEED.


#### Command-Line Interface (for Developers)

For more advanced use cases and automation, a command-line interface is also available.

```bash
# Example: Run real-time analysis with a specific YOLO model and define two static AOIs
python realtime_cli.py --model yolov8n.pt --record --aoi "Screen,100,100,800,600" --aoi "Panel,850,300,1200,500"
```

You can also use a simulated data stream for testing without a physical device:

```bash
# Run with a mock device for testing purposes
python realtime_cli.py --use-mock
```

---

## 3. Docker Container (For Maximum Reproducibility)

To ensure maximum scientific reproducibility and to eliminate any issues with installation or dependencies, we provide a pre-configured Docker image that contains the exact environment to run the `speed-analyzer` package.

### Prerequisites
You must have **Docker Desktop** installed on your computer. You can download it for free from the [official Docker website](https://www.docker.com/products/docker-desktop/).

### How to Use the Docker Image

1.  **Pull the Image (Download)**:
    Open a terminal and run this command to download the latest version of the image from the GitHub Container Registry (GHCR).
    ```bash
    docker pull ghcr.io/danielelozzi/speed:latest
    ```

2.  **Run the Analysis**:
    To launch an analysis, you need to use the `docker run` command. The most important part is to "mount" your local folders (containing the data and where to save the results) inside the container.

    Here is a complete example. Replace the `/path/to/...` placeholders with the actual absolute paths on your computer.
    ```bash
    docker run --rm \
      -v "/path/to/your/RAW/folder:/data/raw" \
      -v "/path/to/your/un-enriched/folder:/data/unenriched" \
      -v "/path/to/your/output/folder:/output" \
      ghcr.io/danielelozzi/speed:latest \
      python -c "from speed_analyzer import run_full_analysis; run_full_analysis(raw_data_path='/data/raw', unenriched_data_path='/data/unenriched', output_path='/output', subject_name='docker_test')"
    ```
    
    **Command Explanation:**
    * `docker run --rm`: Runs the container and automatically removes it when finished.
    * `-v "/local/path:/container/path"`: The `-v` (volume) option creates a bridge between a folder on your computer and a folder inside the container. We are mapping your data folders into `/data/` and your output folder into `/output` inside the container.
    * `ghcr.io/danielelozzi/speed:latest`: The name of the image to use.
    * `python -c "..."`: The command that is executed inside the container. In this case, we launch a Python script that imports and runs your `run_full_analysis` function, using the paths *internal* to the container (`/data/`, `/output/`).

This approach guarantees that your analysis is always executed in the same controlled environment, regardless of the host computer.

---

## The Modular Workflow (GUI)
SPEED v5.3.8.5 operates on a two-step workflow designed to save time and computational resources.

### Step 1: Run Core Analysis
This is the main data processing stage. You run this step only once per participant for a given set of events. The software will:

- Load all necessary files from the specified input folders (RAW, Un-enriched, Enriched).
- **If you don't have Enriched data**, use the **"Define AOI..."** feature to create it dynamically. This is the new, recommended workflow for analyzing specific parts of a video. You can also combine several AOI (static, dynamic, and dynamic based on YOLO.)
- Dynamically load events from `events.csv` into the GUI, allowing you to select which events to analyze.
- Segment the data based on your selection.
- Calculate all relevant statistics for each selected segment.
- Optionally run YOLO object detection on the video frames, saving the results to a cache to speed up future runs.
- Save the processed data (e.g., filtered dataframes for each event) and summary statistics into the output folder.

This step creates a `processed_data` directory containing intermediate files. Once this is complete, you do not need to run it again unless you want to analyze a different combination of events.

### Step 2: Generate Outputs On-Demand

After the core analysis is complete, you can use the dedicated tabs in the GUI to generate as many plots and videos as you need, with any combination of settings, without re-processing the raw data.

#### Generate Plots 📊

The "Generate Plots" tab allows you to create a wide range of visualizations for each event segment. All plots are saved in PDF format for high-quality figures suitable for publications. The available plot categories are:

* **Path Plots**: Visualize the sequence of gaze points and fixations directly on the scene. This is perfect for understanding the participant's visual exploration strategy. You can generate separate plots for raw gaze data and for fixations, both in pixel coordinates (un-enriched) and normalized coordinates (enriched).
* **Density Heatmaps**: Create heatmaps to reveal the areas that attracted the most visual attention. The intensity of the color corresponds to the amount of time the participant spent looking at that specific area.
* **Duration Histograms**: Analyze the distribution of event durations. You can generate histograms for the duration of fixations, saccades, and blinks to understand their statistical properties.
* **Pupillometry**: Plot the changes in pupil diameter over time for each event. This is a crucial tool for research related to cognitive load, arousal, and emotional response. The plot also visualizes periods when the gaze is on a defined surface versus off-surface.
* **Advanced Time Series**: Dive deeper with detailed time series plots, including:
    * Mean pupil diameter over time.
    * Saccade velocity and amplitude over time.
    * A binary plot showing the exact moments when blinks occurred.
* **Gaze Fragmentation Plot**: This plot displays the speed of gaze movement (in pixels per second) over time. High fragmentation can be an indicator of visual searching behavior or cognitive instability.

Simply select the desired plot types in the GUI and click "GENERATE SELECTED PLOTS". The software will use the pre-processed data to generate the figures for all selected events.

#### Generate Videos 🎬

The "Generate Videos" tab allows you to create highly customized videos with synchronized data overlays.

*   **Standard Video**: Overlay gaze points, pupillometry plots, event names, and YOLO detections on the original scene video. You can trim the video to specific event segments.
*   **Video-in-Video**: A powerful feature for analyzing screen-based interactions. This mode replaces the external camera video with a screen recording that the participant was viewing. It requires `enriched` gaze data and synchronizes different screen recording clips to specific events. Between events, a gray screen is shown. A dedicated editor allows you to map video files to events.

To generate a video:
1.  Go to the "Generate Videos" tab.
2.  Select the desired overlays (gaze, plots, YOLO boxes, etc.).
3.  Choose the output filename.
4.  Click **"GENERATE VIDEO"** for a standard video or **"GENERATE VIDEO-IN-VIDEO"** to open the specific editor for this mode.


#### Post-Analysis Tools 🛠️

New tools are available for more in-depth, interactive analysis.

*   **Data Viewer**: A powerful, standalone window for interactive data exploration. Load data from BIDS, DICOM, or un-enriched folders to:
    *   Play the video with synchronized audio.
    *   View and edit events on an interactive timeline (add, remove, drag-and-drop).
    *   Run multi-task YOLO analysis on the fly and filter results by class or ID.
    *   Toggle overlays for gaze, gaze path, AOIs, and YOLO detections.
    *   Export a new video with custom overlays and audio.
*   **Data Plotter**: An interactive tool to visualize all time-series data (pupil, gaze, fixations, saccades, blinks, events) on a single, scrollable, and zoomable chart. Select a time range to instantly calculate and display descriptive statistics for that interval.
*   **LSL Time Series Viewer**: A real-time plotting tool that discovers and displays any LSL data stream on the network. It's ideal for monitoring gaze, pupil, or other physiological data as it is being streamed.
*   **Device Converter**: A utility to convert data from other eye-tracking devices (e.g., Tobii) into the BIDS format.

*   **Normalized Switching Index (NSI) Calculator**: This tool becomes active after an analysis is run with at least two defined Areas of Interest (AOIs). It opens an interactive video player where you can:
    *   Define one or more time windows directly on the video timeline.
    *   Calculate the NSI, which measures the frequency of gaze shifts between the defined AOIs, specifically for each selected time window.
    *   Save the results to a `nsi_results.csv` file, containing the NSI value for each time window.

This feature provides a powerful, user-driven way to analyze visual attention patterns during specific moments of a recording.

## Batch Analysis for Multiple Participants

SPEED provides a powerful batch processing feature to streamline the analysis of entire studies with multiple participants. This allows you to apply a consistent set of analysis parameters (like AOIs and YOLO models) across all selected participants, while keeping the results for each one neatly organized.

### Step 1: Organize Your Data Folder Structure

Before starting, organize your data on your computer. Create a main project folder, and inside it, create one subfolder for each participant. Each participant's subfolder should contain their respective `RAW` and `un-enriched` data.

```
My_Experiment/
├── Subject_01/
│   ├── RAW/
│   └── un-enriched/
│   └── enriched_AOI_A/  (Optional)
│
└── Subject_02/
    ├── RAW/
    └── un-enriched/
```

### Step 2: Configure Common Analysis Parameters in the Main Window

Use the main SPEED window as a **template** for your batch analysis. Configure all the settings you want to apply to every participant:

*   **Define AOIs**: Use the "Add New AOI..." button to define all static, dynamic, or marker-based AOIs.
*   **Select YOLO Models**: Choose the YOLO models for detection, segmentation, etc.
*   **Load Common Events**: If you have a single `events.csv` file to apply to everyone, load it.

### Step 3: Launch and Configure the Batch Window

1.  In the "1. Project Setup" section, click the **"Start Multi-User Batch..."** button.
2.  In the new window, click **"Select Project Root..."** and choose your main project folder (e.g., `My_Experiment`).
3.  The table will automatically populate with the participants found in your project folder.
4.  **Review and Customize**: You can now customize the settings for each participant:
    *   Use the checkboxes to select which participants to include in the batch.
    *   Double-click any path cell (`RAW Path`, `Unenriched Path`, `Enriched Paths`) to manually change it for a specific participant. This is useful if your folder structure isn't perfectly consistent.
    *   For "Enriched Paths", you can associate **multiple** enriched data folders with a single participant.

### Step 4: Run the Batch Analysis

Once you are satisfied with the configuration, click **"Run Batch Analysis"**. SPEED will iterate through each selected participant and:
1.  Apply the common settings (AOIs, YOLO models) from the main window.
2.  Use the specific `RAW`, `un-enriched`, and `Enriched` paths you configured in the table.
3.  Save the results for each participant in a dedicated subfolder within your main output directory.

### Computer Vision Analysis with YOLO 🤖

SPEED integrates the powerful **YOLO (You Only Look Once)** object detection model to add a layer of semantic understanding to the eye-tracking data. When this option is enabled during the "Core Analysis" step, the software analyzes the video to detect and track objects frame by frame.

#### How It Works

1.  **Object Detection & Tracking**: SPEED processes the scene video to identify objects and assigns a unique `track_id` to each detected object throughout its appearance in the video. The results are saved in a cache file (`yolo_detections_cache.csv`) to avoid re-processing on subsequent runs.
2.  **Gaze Correlation**: The system then correlates the participant's gaze and fixation data with the bounding boxes of the detected objects. This allows you to know not just *where* the participant was looking, but also *what* they were looking at.
3.  **Quantitative Analysis**: After the analysis, you can go to the **"YOLO Results"** tab in the GUI to view detailed statistics, such as:
    * **Stats per Instance**: A table showing metrics for each individual tracked object (e.g., `person_1`, `car_3`), including the total number of fixations it received and the average pupil diameter when looking at it.
    * **Stats per Class**: An aggregated view showing the same metrics for each object category (e.g., `person`, `car`).

#### Key Outputs

* **Dynamic AOI (Object Tracking)**: The `track_id` generated by YOLO can be used to define a "Dynamic AOI", where the Area of Interest automatically follows a specific object.
* **Video Overlays**: When generating a custom video, you can choose to overlay the YOLO detection boxes and their labels directly onto the video, providing a clear and intuitive visualization of the analysis.

This feature transforms raw gaze coordinates into meaningful interactions with the environment, opening up new possibilities for analyzing human behavior in complex scenes.

#### Multi-Stage Analysis: Detection, Classification, and Advanced Tracking

SPEED now supports a powerful multi-stage analysis workflow.
 
1.  **Detection/Segmentation**: First, run object detection or segmentation to identify and track all objects in the scene.
2.  **Advanced Tracking with Re-ID**: When running the analysis, you can select a **Re-ID model** (e.g., `yolov8n.pt` from the "Re-ID Model" dropdown) and a tracker configuration. This enhances the tracking algorithm (like BoT-SORT) by using appearance features to re-identify an object that has been occluded or has left and re-entered the scene. This helps ensure that `person_1` who disappears and reappears is still identified as `person_1`, rather than being assigned a new ID like `person_5`.
3.  **Classification (Optional)**: After detection, you can run a second-level classification on the content *inside* the detected bounding boxes. This is ideal for tasks where you need to identify an object's general class (e.g., "animal") and then determine its specific species (e.g., "cat", "dog").

**How It Works in the GUI:**

1.  **Run Core Analysis**: First, run a standard analysis with a YOLO detection or segmentation model enabled. This generates the `yolo_detections_cache.csv` file.
    - To enable Re-identification, select a model from the **"Re-ID Model"** dropdown. The system will automatically use the `default_yaml.yaml` tracker configuration, which is set up for Re-ID. You can also provide your own custom tracker configuration file.
2.  **Filter Detections (Optional)**: In the "5. YOLO Results & Filtering" section, you can select or deselect specific object classes or individual track IDs to focus your analysis.
3.  **Run Classification**: Go to the "6. Classify Detections" section.
    *   Choose a classification model (`*-cls.pt`) from the dropdown.
    *   Click **"RUN CLASSIFICATION ON FILTERED DETECTIONS"**.
4.  **View Results**: The tracking results will be more robust, and if you ran classification, the results will appear in the "10. YOLO Stats" tab and be saved to `yolo_classification_results.csv`.

**Classification vs. Re-identification**

*   **Use Classification** to answer "**What is this object?**" (e.g., Is it a cat or a dog?). It assigns a label to an object.
*   **Use Re-identification** as part of the tracking process to answer "**Is this the same object I was tracking before it was occluded?**". It helps maintain a consistent `track_id` for the same object over time.

These tools can be used independently or together to build a rich, multi-layered understanding of the scene content.


---

## R package

An experimental version of speed-analyzer package is under contruction for R language, available in R folder.


---

## Environment Setup (For Development) ⚙️
To run the project from source or contribute to development, you'll need Python 3 and several libraries.

1. **Install Anaconda**: [Link](https://www.anaconda.com/)
2. *(Optional)* Install CUDA Toolkit: For GPU acceleration with NVIDIA. [Link](https://developer.nvidia.com/cuda-downloads)
3. **Create a virtual environment**:

Open Anaconda Prompt

```bash
conda create --name speed
conda activate speed
conda install pip
conda install git
git clone https://github.com/danielelozzi/SPEED.git
```
4. **Install the required libraries**:

enter in the SPEED folder

```bash
cd SPEED
```

install requirements

```bash
pip install -r requirements.txt
```
5. **(optional) Install Pytorch CUDA**:

[https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

```bash
<command>
```
---

## How to Use the Application from Source 🚀
### Launch the GUI:
```bash
# Navigate to the desktop_app folder
cd SPEED
conda activate speed
python -m desktop_app.GUI
```
### Setup and Analysis:
- Fill in the Participant Name and select the Output Folder.
- Select the required Input Folders: RAW and Un-enriched.
- Use the Advanced Event Management section to load and edit events using the table or interactive video editor.
- Click **"RUN CORE ANALYSIS"**.
- Use the other tabs to generate plots, videos, and view YOLO results.

---

## 🧪 Synthetic Data Generator (`generate_synthetic_data.py`)
Included in this project is a utility script to create a full set of dummy eye-tracking data. This is extremely useful for testing the SPEED software without needing Pupil Labs hardware or actual recordings.

### How to Use
Run the script from your terminal:
```bash
python generate_synthetic_data.py
```
The script will create a new folder named `synthetic_data_output` in the current directory.

This folder will contain all the necessary files (`gaze.csv`, `fixations.csv`, `external.mp4`, etc.), ready to be used as input for the GUI application or the `speed-analyzer` package.

It is also possible to generate a synthetic streaming for realtime with GUI using:
```bash
python generate_synthetic_stream.py
```

or for LSL testing:

```bash
python lsl_stream_simulator.py
```

---

## Export to BIDS Format

SPEED 5.3.8.5 introduces a new feature to convert processed eye-tracking data into a format compatible with the **Brain Imaging Data Structure (BIDS)**, following the [BEP020 for Eye Tracking](https://bids.neuroimaging.io/extensions/beps/bep_020.html) guidelines. This facilitates data sharing and standardization for the research community.

### Use via Desktop App

1. After setting the input folders (specifically the **Un-enriched** folder), a new section "4. Data Export" will be available.
2. Click the **"CONVERT TO BIDS FORMAT"** button.
3. A dialog box will open asking you for the metadata required for the BIDS structure:
* **Subject ID**: The participant's identifier (e.g., `01`).
* **Session ID**: The session identifier (e.g., `01`).
* **Task Name**: The task name (e.g., `reading`, `visualsearch`).
4. Select an empty output folder where the BIDS structure will be created.
5. Click "Start Conversion" to begin the process.

### Usage via the Python `speed-analyzer` package

This functionality is also available via the `convert_to_bids` function.

```python
from pathlib import Path
from speed_analyzer import convert_to_bids

# Define input and output paths
unenriched_path = Path("./data/unenriched")
bids_output_path = Path("./bids_dataset")

# Define BIDS metadata
subject = "01"
session = "01"
task = "visualsearch"

# Perform the conversion
convert_to_bids( 
unenriched_dir=unenriched_path, 
output_bids_dir=bids_output_path, 
subject_id=subject, 
session_id=session, 
task_name=task
)
```

### Loading data in BIDS format

SPEED can also load and analyze eye-tracking datasets already structured according to the BIDS standard.

#### Using the Desktop App

1. In the "2. Input Folders" section, click the new "Load from BIDS Directory..." button.
2. Select the root folder of your BIDS dataset (the one containing the `sub-...` folders).
3. Enter the `Subject`, `Session`, and `Task` identifiers you want to load.
4. SPEED will convert the BIDS files (`_eyetrack.tsv.gz`, `_events.tsv`, etc.) into a temporary folder in the "un-enriched" format that the software can analyze.
5. The path to this temporary folder will be automatically inserted into the "Un-enriched Data Folder" field.
6. At this point, you can proceed with the analysis as you would with a normal dataset.

#### Using the Python `speed-analyzer` package

The `load_from_bids` function converts a BIDS dataset and returns the path to a temporary "un-enriched" folder.

```python
from pathlib import Path
from speed_analyzer import load_from_bids, run_full_analysis


# 1. Define the BIDS dataset path and metadata

bids_input_path = Path("./bids_dataset")
subject = "01"
session = "01"
task = "visualsearch"

# 2. Run the conversion to obtain an "un-enriched" folder

temp_unenriched_path = load_from_bids(
bids_dir=bids_input_path,
subject_id=subject,
session_id=session,
task_name=task
)

print(f"BIDS data ready for analysis in: {temp_unenriched_path}")

# 3. You can now use this folder for full analysis with SPEED
# (Note: A RAW folder is not needed in this case)
run_full_analysis( 
raw_data_path=str(temp_unenriched_path), # Use the same folder for simplicity 
unenriched_data_path=str(temp_unenriched_path), 
output_path="./analysis_from_bids", 
subject_name=f"sub-{subject}_ses-{session}"
)
```

---

## DICOM Integration (Import/Export)

To enhance interoperability with medical imaging systems and workflows, SPEED now supports basic import and export of eye-tracking data using the DICOM standard.

Inspired by standards for storing time-series data, this feature encapsulates gaze coordinates, pupil diameter, and event markers into a single DICOM file using the **Waveform IOD (Information Object Definition)**. This allows eye-tracking data to be archived and managed within Picture Archiving and Communication Systems (PACS).

### Using the Desktop App

The functionality is accessible through dedicated buttons in the graphical interface.

#### Exporting to DICOM Format

1.  Ensure your project is set up and the **Un-enriched Data Folder** is selected. The **Participant Name** field must also be filled out, as this will be used for the `PatientName` tag in the DICOM file.
2.  In the **"4. Data Export"** section, click the **"CONVERT TO DICOM FORMAT"** button.
3.  A save dialog will appear. Choose a location and filename for your `.dcm` file.
4.  SPEED will package the gaze, pupil, and event data into a single DICOM file.

#### Importing from a DICOM File

1.  In the **"2. Input Folders"** section, click the **"Load from DICOM File..."** button.
2.  Select the `.dcm` file containing the eye-tracking waveform data.
3.  SPEED will parse the DICOM file and create a temporary "un-enriched" folder containing the data converted back into the `.csv` formats required for analysis.
4.  The application will automatically populate the **"Un-enriched Data Folder"** and **"Participant Name"** fields for you.
5.  You can now proceed with the Core Analysis, plot generation, and other functions as usual.

### Using the `speed-analyzer` Package

You can also access the DICOM conversion tools programmatically.

#### Converting Data to DICOM

Use the `convert_to_dicom` function to export your data.

```python
from pathlib import Path
from speed_analyzer import convert_to_dicom

# 1. Define paths and patient information
unenriched_path = Path("./data/unenriched")
output_dicom_file = Path("./dicom_exports/subject01.dcm")
output_dicom_file.parent.mkdir(exist_ok=True)

patient_info = {
    "name": "Subject 01",
    "id": "SUB01"
}

# 2. Run the conversion
convert_to_dicom(
    unenriched_dir=unenriched_path,
    output_dicom_path=output_dicom_file,
    patient_info=patient_info
)

print(f"DICOM file successfully created at: {output_dicom_file}")
```

### Loading Data from DICOM
Use the load_from_dicom function to import a DICOM file for analysis. The function returns the path to a temporary "un-enriched" folder.


```python
from pathlib import Path
from speed_analyzer import load_from_dicom, run_full_analysis

# 1. Define the path to the DICOM file
dicom_file_path = Path("./dicom_exports/subject01.dcm")

# 2. Load and convert the DICOM data
# This creates a temporary folder with the required CSV files
temp_unenriched_path = load_from_dicom(dicom_path=dicom_file_path)

print(f"DICOM data is ready for analysis in: {temp_unenriched_path}")

# 3. Use the temporary path to run a full analysis with SPEED
run_full_analysis(
    raw_data_path=str(temp_unenriched_path), # For DICOM import, raw and unenriched can be the same
    unenriched_data_path=str(temp_unenriched_path),
    output_path="./analysis_from_dicom",
    subject_name="Subject_01_from_DICOM"
)
```

## R package

An experimental version of speed-analyzer package is under contruction for R language, available in R folder.


---

## ✍️ Authors & Citation
This tool is developed by the Cognitive and Behavioral Science Lab (LabSCoC), University of L'Aquila and Dr. Daniele Lozzi.

If you use this script in your research or work, please cite the following publications:

- Lozzi, D.; Di Pompeo, I.; Marcaccio, M.; Ademaj, M.; Migliore, S.; Curcio, G. SPEED: A Graphical User Interface Software for Processing Eye Tracking Data. NeuroSci 2025, 6, 35. [10.3390/neurosci6020035](https://doi.org/10.3390/neurosci6020035)
- Lozzi, D.; Di Pompeo, I.; Marcaccio, M.; Alemanno, M.; Krüger, M.; Curcio, G.; Migliore, S. AI-Powered Analysis of Eye Tracker Data in Basketball Game. Sensors 2025, 25, 3572. [10.3390/s25113572](https://doi.org/10.3390/s25113572)

It is also requested to cite Pupil Labs publication, as requested on their website [https://docs.pupil-labs.com/neon/data-collection/publications-and-citation/](https://docs.pupil-labs.com/neon/data-collection/publications-and-citation/)

- Baumann, C., & Dierkes, K. (2023). Neon accuracy test report. Pupil Labs, 10. [10.5281/zenodo.10420388](https://doi.org/10.5281/zenodo.10420388)

If you also the Computer Vision YOLO-based feature, please cite the following publication:

- Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. In Proceedings of the IEEE conference on computer vision and pattern recognition (pp. 779-788). [10.1109/CVPR.2016.91](https://doi.org/10.1109/CVPR.2016.91)

If you use the BIDS converter, please cite the BIDS format for eyetracker:

- Szinte, Martin, et al. "Eye-Tracking-BIDS: the brain imaging data structure extended to gaze position and pupil data." Journal of Vision 25.9 (2025): 2351-2351. [10.1167/jov.25.9.2351](https://doi.org/10.1167/jov.25.9.2351)

If you use the DICOM converter, please cite the DICOM inspiration paper:

- Di Matteo, A., Lozzi, D., Mignosi, F., Polsinelli, M., & Placidi, G. (2025). A DICOM-based standard for quantitative physical rehabilitation. Computational and Structural Biotechnology Journal, 28, 40-49. [10.1016/j.csbj.2025.01.012](https://doi.org/10.1016/j.csbj.2025.01.012)

---

## 💻 Artificial Intelligence disclosure

This code is written in Vibe Coding with Google Gemini 2.5 Pro
