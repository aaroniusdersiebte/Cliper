import json
import re
from pathlib import Path
from typing import List, Optional, Tuple
from data.models import Clip, ClipRating, ClipStatus


def load_chapters(file_path: str) -> Tuple[List[Clip], Optional[str]]:
    """
    Lädt Clips aus einer Chapter-Datei vom OBS streamup-chapter-manager Plugin.

    Format:
        Chapter Markers for 2025-12-27 00-30-53
        00:00:00 - Start
        00:00:04 - (Annotation) username (source)
        00:00:11 - End

    Returns:
        Tuple[List[Clip], Optional[str]]: (Liste der Clips, Recording-Dateiname)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Chapter-Datei nicht gefunden: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.strip().split("\n")
    clips = []
    recording_name = None

    # Erste Zeile: "Chapter Markers for 2025-12-27 00-30-53"
    if lines and lines[0].startswith("Chapter Markers for "):
        recording_name = lines[0].replace("Chapter Markers for ", "").strip()

    # Annotation-Pattern: "00:00:04 - (Annotation) username (source)"
    annotation_pattern = re.compile(
        r"^(\d{2}:\d{2}:\d{2})\s*-\s*\(Annotation\)\s*(.+?)(?:\s*\([^)]*\))?\s*$"
    )

    for line in lines:
        match = annotation_pattern.match(line.strip())
        if match:
            timecode = match.group(1)
            username = match.group(2).strip()

            timestamp = _parse_timestamp(timecode)
            if timestamp is not None:
                clip = Clip(
                    user=username,
                    timestamp=timestamp
                )
                clips.append(clip)

    clips.sort(key=lambda c: c.timestamp)
    return clips, recording_name


def find_matching_video(chapter_file: str, video_extensions: List[str] = None) -> Optional[str]:
    """
    Findet die passende Video-Datei zur Chapter-Datei.

    Sucht nach Videos mit gleichem Basis-Namen im selben Verzeichnis.
    z.B.: "2025-12-27 00-30-53_chapters.txt" -> "2025-12-27 00-30-53.mkv"
    """
    if video_extensions is None:
        video_extensions = [".mkv", ".mp4", ".mov", ".avi", ".flv"]

    path = Path(chapter_file)
    base_name = path.stem.replace("_chapters", "")
    parent_dir = path.parent

    for ext in video_extensions:
        video_path = parent_dir / f"{base_name}{ext}"
        if video_path.exists():
            return str(video_path)

    return None


def load_clips(file_path: str) -> List[Clip]:
    """Lädt Clips aus einer JSON-Datei von Streamerbot"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Clip-Datei nicht gefunden: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    clips = []

    # Unterstützt verschiedene JSON-Formate
    if isinstance(data, list):
        # Array von Clips
        for item in data:
            clip = _parse_clip(item)
            if clip:
                clips.append(clip)
    elif isinstance(data, dict):
        # Mögliche Wrapper-Struktur
        clip_list = data.get("clips", data.get("data", []))
        for item in clip_list:
            clip = _parse_clip(item)
            if clip:
                clips.append(clip)

    # Nach Timestamp sortieren
    clips.sort(key=lambda c: c.timestamp)
    return clips


def _parse_clip(item: dict) -> Optional[Clip]:
    """Parst ein einzelnes Clip-Objekt"""
    if not isinstance(item, dict):
        return None

    user = item.get("user", item.get("username", item.get("viewer", "Unknown")))
    timestamp = item.get("timestamp", item.get("time", item.get("seconds", 0)))

    # Timestamp kann verschiedene Formate haben
    if isinstance(timestamp, str):
        timestamp = _parse_timestamp(timestamp)

    if timestamp is None or timestamp < 0:
        return None

    return Clip(
        user=str(user),
        timestamp=float(timestamp)
    )


def _parse_timestamp(ts: str) -> Optional[float]:
    """Parst verschiedene Timestamp-Formate"""
    # Versuche als Float
    try:
        return float(ts)
    except ValueError:
        pass

    # Versuche Timecode-Format HH:MM:SS oder HH:MM:SS:FF
    try:
        parts = ts.replace(";", ":").split(":")
        if len(parts) >= 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            frames = int(parts[3]) if len(parts) > 3 else 0
            # Annahme: 30 fps für Frame-Konvertierung
            return hours * 3600 + minutes * 60 + seconds + frames / 30.0
    except (ValueError, IndexError):
        pass

    return None


def save_session(clips: List[Clip], file_path: str):
    """Speichert den aktuellen Session-Stand"""
    data = []
    for clip in clips:
        data.append({
            "user": clip.user,
            "timestamp": clip.timestamp,
            "rating": clip.rating.value,
            "status": clip.status.value,
            "in_point": clip.in_point,
            "out_point": clip.out_point,
            "note": clip.note,
        })

    path = Path(file_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_session(file_path: str) -> List[Clip]:
    """Lädt eine gespeicherte Session"""
    path = Path(file_path)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    clips = []
    for item in data:
        clip = Clip(
            user=item["user"],
            timestamp=item["timestamp"],
            rating=ClipRating(item.get("rating", 0)),
            status=ClipStatus(item.get("status", 0)),
            in_point=item.get("in_point"),
            out_point=item.get("out_point"),
            note=item.get("note", ""),
        )
        clips.append(clip)

    return clips
