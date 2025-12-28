from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class ClipRating(IntEnum):
    UNRATED = 0
    VERY_BAD = 1
    BAD = 2
    MEH = 3
    GOOD = 4
    VERY_GOOD = 5


class ClipStatus(IntEnum):
    PENDING = 0
    ACCEPTED = 1
    SKIPPED = 2


@dataclass
class Clip:
    user: str
    timestamp: float  # Sekunden im Video
    rating: ClipRating = ClipRating.UNRATED
    status: ClipStatus = ClipStatus.PENDING
    in_point: Optional[float] = None  # Start des Clips
    out_point: Optional[float] = None  # Ende des Clips
    note: str = ""

    def __post_init__(self):
        # Standard: 30 Sekunden vor Timestamp als In-Point
        if self.in_point is None:
            self.in_point = max(0, self.timestamp - 30)
        # Standard: Timestamp als Out-Point
        if self.out_point is None:
            self.out_point = self.timestamp

    @property
    def duration(self) -> float:
        return self.out_point - self.in_point

    def to_timecode(self, seconds: float, fps: float = 30.0) -> str:
        """Konvertiert Sekunden zu Timecode (HH:MM:SS:FF)"""
        total_frames = int(seconds * fps)
        frames = total_frames % int(fps)
        total_seconds = total_frames // int(fps)
        secs = total_seconds % 60
        mins = (total_seconds // 60) % 60
        hours = total_seconds // 3600
        return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

    @property
    def in_timecode(self) -> str:
        return self.to_timecode(self.in_point)

    @property
    def out_timecode(self) -> str:
        return self.to_timecode(self.out_point)

    @property
    def timestamp_timecode(self) -> str:
        return self.to_timecode(self.timestamp)


@dataclass
class UserScore:
    username: str
    total_clips: int = 0
    ratings: dict = field(default_factory=lambda: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0
    })

    @property
    def average_score(self) -> float:
        total = sum(rating * count for rating, count in self.ratings.items())
        count = sum(self.ratings.values())
        return total / count if count > 0 else 0.0

    @property
    def quality_tier(self) -> str:
        avg = self.average_score
        if avg >= 4.0:
            return "excellent"
        elif avg >= 3.0:
            return "good"
        elif avg >= 2.0:
            return "average"
        else:
            return "poor"

    def add_rating(self, rating: int):
        if 1 <= rating <= 5:
            self.ratings[rating] = self.ratings.get(rating, 0) + 1
            self.total_clips += 1
