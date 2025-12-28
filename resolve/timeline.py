from typing import List, Optional
from resolve.connection import get_resolve
from data.models import Clip


class TimelineController:
    def __init__(self):
        self._resolve_conn = get_resolve()
        self._source_timeline = None  # Referenz zur Quell-Timeline

    def _seconds_to_frames(self, seconds: float) -> int:
        """Konvertiert Sekunden zu Frames"""
        fps = self._resolve_conn.get_fps()
        return int(seconds * fps)

    def _frames_to_timecode(self, frames: int) -> str:
        """Konvertiert Frames zu Timecode string"""
        fps = int(self._resolve_conn.get_fps())
        total_seconds = frames // fps
        frame_remainder = frames % fps
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame_remainder:02d}"

    def _seconds_to_timecode(self, seconds: float) -> str:
        """Konvertiert Sekunden zu Timecode string"""
        frames = self._seconds_to_frames(seconds)
        return self._frames_to_timecode(frames)

    def add_marker(self, seconds: float, name: str, note: str = "", color: str = "Blue") -> bool:
        """Fügt einen Marker zur Timeline hinzu"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return False

        frame = self._seconds_to_frames(seconds)
        # AddMarker(frameId, color, name, note, duration, customData)
        return timeline.AddMarker(frame, color, name, note, 1, "")

    def add_marker_at_position(self, seconds: float, name: str, note: str = "",
                                color: str = "Blue", duration_frames: int = 1,
                                marker_type: str = "") -> bool:
        """
        Fügt einen Marker auf dem TimelineItem (Clip) hinzu.

        Args:
            marker_type: "IN" oder "OUT" - wenn gesetzt, wird der alte Marker
                         dieses Typs für diesen User gelöscht (nur 1 In/Out pro Clip)
        """
        timeline = self._resolve_conn.timeline
        if timeline is None:
            print("[Timeline] Fehler: Keine Timeline für Marker")
            return False

        # Timeline-FPS für Frame-Berechnung
        timeline_fps = self._resolve_conn.get_fps()
        start_frame = timeline.GetStartFrame()

        # Berechne absoluten Timeline-Frame
        timeline_frame = start_frame + int(seconds * timeline_fps)

        # CustomData für eindeutige Identifikation (z.B. "IN:username" oder "OUT:username")
        custom_data = f"{marker_type}:{name}" if marker_type else ""

        try:
            # Finde das TimelineItem an dieser Position
            timeline_item = self._get_timeline_item_at_frame(timeline_frame)

            if timeline_item:
                # Berechne Frame-Position relativ zum Clip-Start
                clip_start = timeline_item.GetStart()
                clip_frame = timeline_frame - clip_start

                # Lösche alten Marker mit gleichem customData (falls marker_type gesetzt)
                if custom_data:
                    timeline_item.DeleteMarkerByCustomData(custom_data)
                    print(f"[Timeline] Alte {marker_type}-Marker für '{name}' gelöscht")

                # Setze neuen Marker auf dem Clip
                result = timeline_item.AddMarker(clip_frame, color, name, note, duration_frames, custom_data)
                if result:
                    print(f"[Timeline] {marker_type}-Marker gesetzt: '{name}' bei Clip-Frame {clip_frame} ({seconds:.2f}s)")
                else:
                    print(f"[Timeline] Clip-Marker konnte nicht gesetzt werden")
                return result
            else:
                # Fallback: Marker auf Timeline setzen wenn kein Clip gefunden
                print(f"[Timeline] Kein Clip bei Frame {timeline_frame} gefunden, setze Timeline-Marker")
                if custom_data:
                    timeline.DeleteMarkerByCustomData(custom_data)
                result = timeline.AddMarker(timeline_frame, color, name, note, duration_frames, custom_data)
                if result:
                    print(f"[Timeline] Timeline-Marker gesetzt: '{name}' bei Frame {timeline_frame}")
                return result

        except Exception as e:
            print(f"[Timeline] Fehler beim Setzen des Markers: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_timeline_item_at_frame(self, frame: int):
        """Findet das TimelineItem an einer bestimmten Frame-Position"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return None

        # Durchsuche alle Video-Tracks
        track_count = timeline.GetTrackCount("video")
        for track_idx in range(1, track_count + 1):
            items = timeline.GetItemListInTrack("video", track_idx)
            if items:
                for item in items:
                    item_start = item.GetStart()
                    item_end = item.GetEnd()
                    if item_start <= frame < item_end:
                        return item
        return None

    def delete_marker_at(self, seconds: float) -> bool:
        """Löscht Marker an einer bestimmten Position"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return False

        frame = self._seconds_to_frames(seconds)
        return timeline.DeleteMarkerAtFrame(frame)

    def get_markers(self) -> dict:
        """Gibt alle Marker der Timeline zurück"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return {}
        return timeline.GetMarkers() or {}

    def store_source_timeline(self):
        """Speichert die aktuelle Timeline als Quell-Timeline"""
        self._source_timeline = self._resolve_conn.timeline

    def get_source_media_pool_item(self):
        """Holt das erste Media Pool Item der aktuellen Timeline"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return None

        # Versuche das Video aus der aktuellen Timeline zu finden
        track_count = timeline.GetTrackCount("video")
        if track_count > 0:
            items = timeline.GetItemListInTrack("video", 1)
            if items and len(items) > 0:
                return items[0].GetMediaPoolItem()
        return None

    def create_timeline_from_clips(self, clips: List[Clip], name: str = "Exported Clips") -> bool:
        """Erstellt eine neue Timeline mit den akzeptierten Clips"""
        media_pool = self._resolve_conn.media_pool
        project = self._resolve_conn.project
        timeline = self._resolve_conn.timeline

        if not all([media_pool, project, timeline]):
            print("[Timeline] Fehler: media_pool, project oder timeline nicht verfügbar")
            return False

        # Quell-Media Pool Item holen (das Video aus der aktuellen Timeline)
        source_item = self.get_source_media_pool_item()
        if source_item is None:
            print("[Timeline] Fehler: Kein Quell-Video in der Timeline gefunden")
            return False

        print(f"[Timeline] Quell-Video gefunden: {source_item.GetName()}")

        # Debug: Zeige Clip-Properties und berechne Grenzen
        source_start_frame = 0
        source_end_frame = 0
        source_fps = 30.0  # Default
        try:
            props = source_item.GetClipProperty()
            source_start_frame = int(props.get('Start', 0))
            source_end_frame = int(props.get('End', 0))
            source_fps = float(props.get('FPS', 30.0))
            source_duration_sec = (source_end_frame - source_start_frame) / source_fps
            print(f"[Timeline] Source-Clip: Frame {source_start_frame} - {source_end_frame}")
            print(f"[Timeline] Source-Clip FPS: {source_fps}")
            print(f"[Timeline] Source-Clip Dauer: {source_duration_sec:.1f} Sekunden ({source_duration_sec/60:.1f} Minuten)")
        except Exception as e:
            print(f"[Timeline] Konnte Eigenschaften nicht lesen: {e}")

        # Akzeptierte Clips filtern und nach In-Point sortieren
        accepted_clips = [c for c in clips if c.status.value == 1]  # ACCEPTED
        if not accepted_clips:
            print("[Timeline] Keine akzeptierten Clips zum Exportieren")
            return False

        accepted_clips.sort(key=lambda c: c.in_point)
        print(f"[Timeline] {len(accepted_clips)} akzeptierte Clips werden exportiert")

        # Neue Timeline erstellen
        new_timeline = media_pool.CreateEmptyTimeline(name)
        if new_timeline is None:
            print("[Timeline] Fehler: Konnte Timeline nicht erstellen")
            return False

        # Zur neuen Timeline wechseln
        project.SetCurrentTimeline(new_timeline)

        # WICHTIG: Source-FPS verwenden für Frame-Berechnung, nicht Timeline-FPS!
        timeline_fps = self._resolve_conn.get_fps()
        print(f"[Timeline] Timeline-FPS: {timeline_fps}, Source-FPS: {source_fps}")

        # Verwende Source-FPS für die Frame-Berechnung
        fps = source_fps
        print(f"[Timeline] Verwendete FPS für Frame-Berechnung: {fps}")
        success_count = 0

        # Lücke zwischen Clips: 60 Sekunden (in Timeline-Frames!)
        gap_seconds = 60.0
        gap_frames = int(gap_seconds * timeline_fps)
        print(f"[Timeline] Lücke zwischen Clips: {gap_seconds}s ({gap_frames} Frames)")

        # Track current position on new timeline (in timeline frames)
        current_timeline_position = new_timeline.GetStartFrame()

        # Clips zur neuen Timeline hinzufügen
        for i, clip in enumerate(accepted_clips):
            try:
                # In/Out Points in Frames berechnen (Source-Frames mit Source-FPS!)
                in_frame = int(clip.in_point * fps)
                out_frame = int(clip.out_point * fps)

                # Debug: Zeige ob Custom oder Default-Werte verwendet werden
                is_default_in = (clip.in_point == max(0, clip.timestamp - 30))
                is_default_out = (clip.out_point == clip.timestamp)
                custom_info = ""
                if is_default_in and is_default_out:
                    custom_info = " [DEFAULT-Werte, keine Custom In/Out gesetzt!]"
                elif is_default_in:
                    custom_info = " [Default In-Point]"
                elif is_default_out:
                    custom_info = " [Default Out-Point]"
                else:
                    custom_info = " [Custom In/Out]"

                print(f"[Timeline] Clip {i+1}: in_point={clip.in_point:.2f}s -> Frame {in_frame}, out_point={clip.out_point:.2f}s -> Frame {out_frame}{custom_info}")

                # WICHTIG: Prüfen ob Frames innerhalb des Source-Materials liegen
                if source_end_frame > 0:
                    if in_frame > source_end_frame or out_frame > source_end_frame:
                        print(f"[Timeline] WARNUNG: Frames liegen außerhalb des Source-Materials!")
                        print(f"[Timeline]   Source-Ende: Frame {source_end_frame} ({source_end_frame/fps:.1f}s)")
                        print(f"[Timeline]   Gewünschte Frames: {in_frame} - {out_frame}")
                        print(f"[Timeline]   -> Clip wird übersprungen!")
                        continue

                    if in_frame < source_start_frame:
                        print(f"[Timeline] WARNUNG: In-Point vor Source-Start, korrigiere auf {source_start_frame}")
                        in_frame = source_start_frame

                # Clip-Infos für AppendToTimeline mit recordFrame für Position
                clip_info = {
                    "mediaPoolItem": source_item,
                    "startFrame": in_frame,
                    "endFrame": out_frame,
                    "recordFrame": current_timeline_position,  # Position auf der neuen Timeline
                }

                # Clip zur Timeline hinzufügen
                result = media_pool.AppendToTimeline([clip_info])

                if result and len(result) > 0:
                    success_count += 1
                    print(f"[Timeline] Clip {i+1}/{len(accepted_clips)} hinzugefügt: {clip.user} ({clip.in_point:.1f}s - {clip.out_point:.1f}s) bei Timeline-Position {current_timeline_position}")

                    # Berechne Clip-Dauer in Timeline-Frames
                    clip_duration_sec = clip.out_point - clip.in_point
                    clip_duration_frames = int(clip_duration_sec * timeline_fps)

                    # Hole das gerade hinzugefügte Timeline-Item
                    current_items = new_timeline.GetItemListInTrack("video", 1)
                    if current_items:
                        last_item = current_items[-1]
                        marker_start = last_item.GetStart()

                        # Clip umbenennen auf Username
                        try:
                            last_item.SetClipColor("Orange")  # Visuelle Hervorhebung
                            # SetName funktioniert auf Timeline-Items
                            last_item.SetName(clip.user)
                            print(f"[Timeline] Clip umbenannt zu: '{clip.user}'")
                        except Exception as e:
                            print(f"[Timeline] Konnte Clip nicht umbenennen: {e}")

                        # Marker mit Username auf der Export-Timeline setzen
                        marker_name = clip.user
                        marker_note = f"Rating: {clip.rating.value}" if clip.rating.value > 0 else ""
                        if clip.note:
                            marker_note = f"{marker_note} | {clip.note}" if marker_note else clip.note

                        marker_result = new_timeline.AddMarker(
                            marker_start,
                            self._rating_to_color(clip.rating.value),
                            marker_name,
                            marker_note,
                            1, ""
                        )
                        if marker_result:
                            print(f"[Timeline] Marker '{marker_name}' auf Export-Timeline bei Frame {marker_start} gesetzt")
                        else:
                            print(f"[Timeline] Marker konnte nicht gesetzt werden bei Frame {marker_start}")

                    # Position für nächsten Clip: aktuelle Position + Clip-Dauer + Lücke
                    current_timeline_position += clip_duration_frames + gap_frames
                else:
                    print(f"[Timeline] Fehler beim Hinzufügen von Clip: {clip.user} - AppendToTimeline returned: {result}")

            except Exception as e:
                import traceback
                print(f"[Timeline] Fehler bei Clip {clip.user}: {e}")
                traceback.print_exc()

        print(f"[Timeline] Export abgeschlossen: {success_count}/{len(accepted_clips)} Clips erfolgreich")
        return success_count > 0

    def _rating_to_color(self, rating: int) -> str:
        """Konvertiert Rating zu Marker-Farbe"""
        colors = {
            5: "Green",    # Sehr gut
            4: "Cyan",     # Gut
            3: "Blue",     # Meh
            2: "Yellow",   # Schlecht
            1: "Red",      # Sehr schlecht
            0: "Purple",   # Unbewertet
        }
        return colors.get(rating, "Blue")

    def get_timeline_duration(self) -> Optional[float]:
        """Gibt die Timeline-Dauer in Sekunden zurück"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return None

        # Timeline-Dauer in Frames
        end_frame = timeline.GetEndFrame()
        start_frame = timeline.GetStartFrame()
        duration_frames = end_frame - start_frame

        fps = self._resolve_conn.get_fps()
        return duration_frames / fps

    def get_timeline_name(self) -> Optional[str]:
        """Gibt den Timeline-Namen zurück"""
        timeline = self._resolve_conn.timeline
        if timeline is None:
            return None
        return timeline.GetName()

    def import_media(self, file_path: str) -> bool:
        """
        Importiert ein Video in den Media Pool und erstellt eine Timeline.

        Args:
            file_path: Pfad zur Videodatei

        Returns:
            True bei Erfolg, False bei Fehler
        """
        media_pool = self._resolve_conn.media_pool
        project = self._resolve_conn.project

        if not media_pool or not project:
            print("[Timeline] Fehler: Media Pool oder Projekt nicht verfügbar")
            return False

        try:
            # Video in Media Pool importieren
            media_items = media_pool.ImportMedia([file_path])
            if not media_items or len(media_items) == 0:
                print(f"[Timeline] Fehler: Konnte '{file_path}' nicht importieren")
                return False

            media_item = media_items[0]
            print(f"[Timeline] Video importiert: {media_item.GetName()}")

            # Timeline mit dem Video erstellen
            timeline_name = media_item.GetName().rsplit('.', 1)[0]  # Dateiname ohne Extension
            new_timeline = media_pool.CreateTimelineFromClips(timeline_name, [media_item])

            if new_timeline:
                project.SetCurrentTimeline(new_timeline)
                print(f"[Timeline] Timeline erstellt: {timeline_name}")
                return True
            else:
                print("[Timeline] Fehler: Konnte Timeline nicht erstellen")
                return False

        except Exception as e:
            print(f"[Timeline] Fehler beim Import: {e}")
            return False


# Singleton
_controller: Optional[TimelineController] = None


def get_timeline_controller() -> TimelineController:
    global _controller
    if _controller is None:
        _controller = TimelineController()
    return _controller
