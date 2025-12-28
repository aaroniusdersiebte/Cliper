# Project Map

## Core Structure
- Brain/
  - PROJECT_MAP.md     # Projektstruktur
  - PROGRESS.md        # Tasks & Status
  - INFO.md            # Temp Buffer
  - decisions/         # Architektur-Entscheidungen

## Application Files
- main.py              # Entry point, PyQt6 App
- ui/
  - main_window.py     # Hauptfenster
  - controls.py        # Player Controls
  - clip_list.py       # Clip-Listenansicht
- data/
  - models.py          # Clip, ClipRating, UserScore
  - clip_loader.py     # JSON + Chapter-Parser
  - user_scores.py     # User-Bewertungslogik
- resolve/
  - connection.py      # DaVinci Resolve API
  - timeline.py        # Timeline-Manipulation
  - playback.py        # Playback-Control

## Key Functions
- `load_chapters()`: Parst OBS Chapter-Manager Dateien
- `find_matching_video()`: Findet Video zu Chapter-Datei
- `import_media()`: Video in Resolve importieren + Timeline erstellen
- `load_clips()`: Legacy JSON-Import