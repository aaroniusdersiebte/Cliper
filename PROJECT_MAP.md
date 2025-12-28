# Project Map - Clip Workflow Tool

## Hauptdateien
- `main.py` - Einstiegspunkt, startet PyQt6 App
- `config.py` - Farben und Stylesheet-Konfiguration
- `start.bat` - Windows Starter mit DaVinci Resolve Pfaden

## /ui - User Interface
- `main_window.py` - Hauptfenster, Hotkeys, Event-Handler
- `controls.py` - Rating, Trim, Playback UI-Komponenten
- `clip_list.py` - Clip-Liste Widget

## /resolve - DaVinci Resolve Integration
- `connection.py` - Verbindung zu Resolve, Singleton
- `timeline.py` - Timeline-Operationen, Export, Marker
- `playback.py` - Playhead-Navigation, Timecode-Konvertierung

## /data - Datenmodelle
- `models.py` - Clip, ClipRating, ClipStatus Dataclasses
- `clip_loader.py` - JSON Laden/Speichern
- `user_scores.py` - User-Bewertungs-Management

## Sonstiges
- `global_hotkeys.py` - Globale Hotkeys via pynput (Ctrl+Alt+Key)
- `requirements.txt` - Python Dependencies
