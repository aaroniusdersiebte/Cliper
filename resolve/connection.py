import sys
from pathlib import Path
from typing import Optional
import os

# DaVinci Resolve Scripting API Pfade
RESOLVE_SCRIPT_PATHS = [
    # Windows - verschiedene mögliche Pfade
    os.path.join(os.environ.get("PROGRAMDATA", "C:/ProgramData"),
                 "Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Modules"),
    "C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Modules",
    os.path.join(os.environ.get("APPDATA", ""),
                 "../Local/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Modules"),
    # macOS
    "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
    # Linux
    "/opt/resolve/Developer/Scripting/Modules",
    "/home/resolve/Developer/Scripting/Modules",
]

# Windows: DaVinci Resolve Installationspfade (für DLLs)
RESOLVE_INSTALL_PATHS = [
    "C:/Prog/Blackmagic Design/DaVinci Resolve",  # Dein Pfad
    "C:/Program Files/Blackmagic Design/DaVinci Resolve",
    os.path.join(os.environ.get("PROGRAMFILES", "C:/Program Files"),
                 "Blackmagic Design/DaVinci Resolve"),
]

# Environment Variable checken
RESOLVE_SCRIPT_API = os.environ.get("RESOLVE_SCRIPT_API", "")
if RESOLVE_SCRIPT_API:
    RESOLVE_SCRIPT_PATHS.insert(0, RESOLVE_SCRIPT_API)


class ResolveConnection:
    def __init__(self):
        self._resolve = None
        self._project = None
        self._timeline = None
        self._setup_script_path()

    def _setup_script_path(self):
        """Fügt den Resolve Scripting Pfad zu sys.path hinzu"""
        # Zuerst: DLL-Pfad zum PATH hinzufügen (Windows)
        if sys.platform == "win32":
            for install_path in RESOLVE_INSTALL_PATHS:
                path = Path(install_path)
                if path.exists():
                    # Füge zum Windows PATH hinzu
                    current_path = os.environ.get("PATH", "")
                    if str(path) not in current_path:
                        os.environ["PATH"] = str(path) + os.pathsep + current_path
                    print(f"[Resolve] DLL-Pfad hinzugefügt: {path}")
                    break

        # Dann: Python Scripting Module
        found_path = None
        for script_path in RESOLVE_SCRIPT_PATHS:
            path = Path(script_path)
            if path.exists():
                if str(path) not in sys.path:
                    sys.path.append(str(path))
                found_path = path
                print(f"[Resolve] Script-Pfad gefunden: {path}")
                break

        if not found_path:
            print("[Resolve] WARNUNG: Kein Scripting-Modul gefunden!")
            print("[Resolve] Geprüfte Pfade:")
            for p in RESOLVE_SCRIPT_PATHS:
                print(f"  - {p}")

    def connect(self) -> bool:
        """Verbindet mit DaVinci Resolve"""
        try:
            import DaVinciResolveScript as dvr
            print("[Resolve] DaVinciResolveScript Modul geladen")

            self._resolve = dvr.scriptapp("Resolve")
            if self._resolve is None:
                print("[Resolve] FEHLER: scriptapp('Resolve') returned None")
                print("[Resolve] Ist DaVinci Resolve geöffnet?")
                return False

            print("[Resolve] Verbindung hergestellt!")

            # Test: Projekt holen
            pm = self._resolve.GetProjectManager()
            if pm:
                proj = pm.GetCurrentProject()
                if proj:
                    print(f"[Resolve] Aktuelles Projekt: {proj.GetName()}")

            return True
        except ImportError as e:
            print(f"[Resolve] FEHLER: DaVinciResolveScript nicht gefunden: {e}")
            print("[Resolve] Stelle sicher, dass:")
            print("  1. DaVinci Resolve installiert ist")
            print("  2. 'External scripting using: Local' in Preferences aktiviert ist")
            print("  3. DaVinci Resolve VORHER gestartet wurde")
            return False
        except Exception as e:
            print(f"[Resolve] Fehler beim Verbinden: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._resolve is not None

    @property
    def resolve(self):
        return self._resolve

    @property
    def project(self):
        if self._project is None and self._resolve:
            pm = self._resolve.GetProjectManager()
            if pm:
                self._project = pm.GetCurrentProject()
        return self._project

    @property
    def timeline(self):
        # Immer die aktuelle Timeline holen, nicht cachen
        # Das verhindert Probleme wenn der User in Resolve die Timeline wechselt
        if self.project:
            return self.project.GetCurrentTimeline()
        return None

    def refresh_timeline(self):
        """Aktualisiert die Timeline-Referenz (legacy, nicht mehr nötig)"""
        return self.timeline

    @property
    def media_pool(self):
        if self.project:
            return self.project.GetMediaPool()
        return None

    def get_fps(self) -> float:
        """Gibt die Timeline-Framerate zurück"""
        if self.timeline:
            fps_str = self.timeline.GetSetting("timelineFrameRate")
            try:
                return float(fps_str)
            except (ValueError, TypeError):
                pass
        return 30.0  # Fallback


# Singleton-Instanz
_connection: Optional[ResolveConnection] = None


def get_resolve() -> ResolveConnection:
    global _connection
    if _connection is None:
        _connection = ResolveConnection()
    return _connection
