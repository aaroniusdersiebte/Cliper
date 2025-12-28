

# Clip Workflow Tool

## Project Overview
This project is a Python-based desktop application designed to streamline the workflow of reviewing and editing video clips for streamers. It integrates directly with **DaVinci Resolve** via its scripting API to semi-automate the process of cutting clips.

**Key Features:**
*   **Clip Review:** Iterate through a list of logged clips (e.g., from Streamer.bot).
*   **Rating System:** Rate clips on a scale (1-5) to filter by quality.
*   **Editing:** Intuitively set In/Out points for each clip.
*   **DaVinci Resolve Integration:** Automatically places accepted clips into a designated timeline in DaVinci Resolve.
*   **Workflow:** Designed for speed and minimal context switching, keeping the user in the tool as much as possible.

## Tech Stack
*   **Language:** Python 3
*   **GUI Framework:** PyQt6
*   **Integration:** DaVinci Resolve Scripting API (Py3)

## Setup & Usage

### Prerequisites
1.  **DaVinci Resolve Studio:** The scripting API requires the Studio version (or a compatible free version configuration).
2.  **Configuration:** Ensure DaVinci Resolve is configured to accept external scripting (`Preferences` -> `System` -> `General` -> `External scripting using: Local`).
3.  **Python Environment:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Tool
1.  Start **DaVinci Resolve** and open your project.
2.  Run the application:
    ```bash
    python main.py
    ```
    *(Note: `start.bat` is also available for Windows users)*

### Hotkeys
*   `Space`: Play/Pause
*   `1-5`: Rate Clip
*   `I`: Set In-Point
*   `O`: Set Out-Point
*   `Enter`: Accept Clip
*   `S`: Skip Clip
*   `N`: Next Clip
*   `P`: Previous Clip

## Project Structure

*   **`main.py`**: The entry point of the application. Initializes the PyQt6 application and main window.
*   **`konzept.txt`**: Original project concept and requirements (in German).
*   **`ui/`**: User Interface logic.
    *   `main_window.py`: The primary application window.
    *   `controls.py`: Player controls.
    *   `clip_list.py`: The list view of clips.
*   **`resolve/`**: DaVinci Resolve integration.
    *   `connection.py`: Handles connection to the running Resolve instance.
    *   `timeline.py`: Timeline manipulation logic.
    *   `playback.py`: Playback control.
*   **`data/`**: Data handling.
    *   `clip_loader.py`: Loads clip data (e.g., from JSON/Logs).
    *   `models.py`: Data models for Clips.
    *   `user_scores.py`: Logic for user scoring/ranking.
