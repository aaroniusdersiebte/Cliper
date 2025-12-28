from typing import Optional
from resolve.connection import get_resolve


class PlaybackController:
    def __init__(self):
        self._resolve_conn = get_resolve()
        self._is_playing = False

    def _seconds_to_frames(self, seconds: float) -> int:
        """Konvertiert Sekunden zu Frames"""
        fps = self._resolve_conn.get_fps()
        return int(seconds * fps)

    def _frames_to_timecode(self, frames: int, include_timeline_start: bool = False) -> str:
        """Konvertiert Frames zu Timecode string"""
        fps = int(self._resolve_conn.get_fps())

        # Optional: Timeline-Start-Frame addieren
        if include_timeline_start:
            timeline = self._resolve_conn.timeline
            if timeline:
                start_frame = timeline.GetStartFrame()
                frames = frames + start_frame

        total_seconds = frames // fps
        frame_remainder = frames % fps
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame_remainder:02d}"

    def _seconds_to_timecode(self, seconds: float, include_timeline_start: bool = False) -> str:
        """Konvertiert Sekunden zu Timecode string"""
        frames = self._seconds_to_frames(seconds)
        return self._frames_to_timecode(frames, include_timeline_start)

    def goto_seconds(self, seconds: float) -> bool:
        """Springt zu einer bestimmten Position in Sekunden (relativ zum Timeline-Start)"""
        resolve = self._resolve_conn.resolve
        timeline = self._resolve_conn.timeline

        if resolve is None:
            print("[Playback] Fehler: Keine Resolve-Verbindung")
            return False

        if timeline is None:
            print("[Playback] Fehler: Keine Timeline gefunden")
            return False

        # Sicherstellen dass wir auf der Edit-Page sind
        current_page = resolve.GetCurrentPage()
        if current_page not in ["edit", "cut", "color", "fairlight", "deliver"]:
            print(f"[Playback] Wechsle von {current_page} zu Edit-Page")
            resolve.OpenPage("edit")

        fps = self._resolve_conn.get_fps()
        start_frame = timeline.GetStartFrame()
        end_frame = timeline.GetEndFrame()
        timeline_duration = (end_frame - start_frame) / fps

        # Relative Sekunden -> Absolute Frames (mit Timeline-Start-Offset)
        target_frame = start_frame + int(seconds * fps)

        # Bounds-Check
        if seconds > timeline_duration:
            print(f"[Playback] WARNUNG: {seconds:.1f}s > Timeline-Dauer ({timeline_duration:.1f}s), springe ans Ende")
            target_frame = end_frame - 10
        if seconds < 0:
            print(f"[Playback] Position < 0, korrigiere auf Start")
            target_frame = start_frame

        # Frame zu Timecode konvertieren (absolut, inklusive Timeline-Start)
        timecode = self._frames_to_timecode(target_frame, include_timeline_start=False)
        print(f"[Playback] Springe zu {seconds:.2f}s (relativ) -> Frame {target_frame} -> Timecode: {timecode}")

        result = timeline.SetCurrentTimecode(timecode)
        if not result:
            start_tc = timeline.GetStartTimecode()
            print(f"[Playback] SetCurrentTimecode fehlgeschlagen. Timeline-Start: {start_tc}")
        return result

    def get_current_seconds(self) -> Optional[float]:
        """Gibt die aktuelle Playhead-Position in Sekunden zurück (relativ zum Timeline-Start)"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return None

        timecode = timeline.GetCurrentTimecode()
        if not timecode:
            return None

        fps = self._resolve_conn.get_fps()

        # Parse timecode HH:MM:SS:FF
        try:
            parts = timecode.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            frames = int(parts[3])

            # Absolute Position in Sekunden
            absolute_seconds = hours * 3600 + minutes * 60 + seconds + frames / fps

            # Timeline-Start-Offset abziehen (DaVinci startet oft bei 01:00:00:00)
            start_frame = timeline.GetStartFrame()
            start_seconds = start_frame / fps

            # Relative Position (ab Timeline-Start)
            relative_seconds = absolute_seconds - start_seconds

            print(f"[Playback] Position: Timecode={timecode}, Absolut={absolute_seconds:.2f}s, Start-Offset={start_seconds:.2f}s, Relativ={relative_seconds:.2f}s")

            return relative_seconds
        except (IndexError, ValueError) as e:
            print(f"[Playback] Fehler beim Parsen von Timecode '{timecode}': {e}")
            return None

    def play(self) -> bool:
        """Startet die Wiedergabe"""
        resolve = self._resolve_conn.resolve
        if resolve is None:
            return False

        # Resolve API: Play über Fusion/DaVinci UI Automation
        # Alternativ: Keyboard-Event senden (Space)
        self._is_playing = True
        return True

    def pause(self) -> bool:
        """Pausiert die Wiedergabe"""
        self._is_playing = False
        return True

    def toggle_play(self) -> bool:
        """Wechselt zwischen Play und Pause"""
        if self._is_playing:
            return self.pause()
        else:
            return self.play()

    def frame_forward(self, frames: int = 1) -> bool:
        """Geht n Frames vorwärts"""
        current = self.get_current_seconds()
        if current is None:
            return False

        fps = self._resolve_conn.get_fps()
        new_pos = current + (frames / fps)
        return self.goto_seconds(new_pos)

    def frame_backward(self, frames: int = 1) -> bool:
        """Geht n Frames rückwärts"""
        current = self.get_current_seconds()
        if current is None:
            return False

        fps = self._resolve_conn.get_fps()
        new_pos = max(0, current - (frames / fps))
        return self.goto_seconds(new_pos)

    @property
    def is_connected(self) -> bool:
        return self._resolve_conn.is_connected


# Singleton
_controller: Optional[PlaybackController] = None


def get_playback() -> PlaybackController:
    global _controller
    if _controller is None:
        _controller = PlaybackController()
    return _controller
