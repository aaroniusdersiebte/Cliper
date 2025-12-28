from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor

from data.models import Clip, ClipStatus, ClipRating
from config import COLORS


class ClipListItem(QFrame):
    """Custom Widget für einen Clip in der Liste"""

    def __init__(self, clip: Clip, index: int, user_avg_score: float = 0.0):
        super().__init__()
        self.clip = clip
        self.index = index
        self._user_avg_score = user_avg_score

        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setMinimumHeight(60)  # Mindesthöhe für bessere Lesbarkeit
        self._setup_ui(user_avg_score)

    def _setup_ui(self, user_avg_score: float):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)

        # Status-Indikator (größer und auffälliger)
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(12, 12)
        self._update_status_dot()
        layout.addWidget(self.status_dot)

        # User + Timestamp + Duration
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Username (größer und klarer)
        self.user_label = QLabel(self.clip.user)
        self.user_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 14px;
            color: {COLORS['text_primary']};
        """)
        self.user_label.setMinimumWidth(100)

        # Timestamp + Duration in einer Zeile
        time_str = self._format_time(self.clip.timestamp)
        duration_str = f"({self._format_duration(self.clip.duration)})"
        self.time_label = QLabel(f"{time_str}  {duration_str}")
        self.time_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
        """)

        info_layout.addWidget(self.user_label)
        info_layout.addWidget(self.time_label)
        layout.addLayout(info_layout, 1)

        # Right side: Score + Rating
        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)

        # User-Score Badge
        if user_avg_score > 0:
            score_badge = QLabel(f"{user_avg_score:.1f}")
            score_badge.setStyleSheet(f"""
                background-color: {self._score_color(user_avg_score)};
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 10px;
                min-width: 28px;
            """)
            score_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right_layout.addWidget(score_badge)

        # Rating-Anzeige (größere Sterne)
        self.rating_label = QLabel()
        self._update_rating_display()
        right_layout.addWidget(self.rating_label)

        layout.addLayout(right_layout)

    def _update_rating_display(self):
        """Aktualisiert die Rating-Anzeige"""
        if self.clip.rating != ClipRating.UNRATED:
            stars = "★" * self.clip.rating.value + "☆" * (5 - self.clip.rating.value)
            self.rating_label.setText(stars)
            self.rating_label.setStyleSheet(f"""
                color: {COLORS['warning']};
                font-size: 14px;
                letter-spacing: 2px;
            """)
        else:
            self.rating_label.setText("☆☆☆☆☆")
            self.rating_label.setStyleSheet(f"""
                color: {COLORS['text_secondary']};
                font-size: 14px;
                letter-spacing: 2px;
            """)

    def _format_duration(self, seconds: float) -> str:
        """Formatiert die Dauer"""
        if seconds < 60:
            return f"{int(seconds)}s"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _score_color(self, score: float) -> str:
        if score >= 4.0:
            return COLORS["success"]
        elif score >= 3.0:
            return COLORS["accent"]
        elif score >= 2.0:
            return COLORS["warning"]
        else:
            return COLORS["error"]

    def _update_status_dot(self):
        if self.clip.status == ClipStatus.ACCEPTED:
            color = COLORS["success"]
        elif self.clip.status == ClipStatus.SKIPPED:
            color = COLORS["text_secondary"]
        else:
            color = COLORS["accent"]

        self.status_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 6px;
        """)

    def update_display(self):
        """Aktualisiert die Anzeige nach Änderungen"""
        self._update_status_dot()
        self._update_rating_display()


class ClipListWidget(QListWidget):
    """Liste aller Clips"""

    clip_selected = pyqtSignal(int)  # Emittiert Index des ausgewählten Clips

    def __init__(self):
        super().__init__()
        self._clips = []
        self._user_scores = {}
        self._setup_style()

    def _setup_style(self):
        self.setSpacing(4)  # Mehr Abstand zwischen Items
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Größere Items mit mehr Padding
        self.setStyleSheet(f"""
            QListWidget::item {{
                padding: 4px;
                border-radius: 8px;
                margin: 2px 4px;
                min-height: 56px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {COLORS['bg_light']};
            }}
        """)

    def set_clips(self, clips: list, user_scores: dict = None):
        """Setzt die Clip-Liste"""
        self._clips = clips
        self._user_scores = user_scores or {}
        self._populate()

    def _populate(self):
        self.clear()
        for i, clip in enumerate(self._clips):
            user_score = 0.0
            if clip.user in self._user_scores:
                user_score = self._user_scores[clip.user].average_score

            item_widget = ClipListItem(clip, i, user_score)
            item = QListWidgetItem(self)
            # Mindesthöhe für bessere Lesbarkeit
            item.setSizeHint(QSize(item_widget.sizeHint().width(), max(64, item_widget.sizeHint().height())))
            self.addItem(item)
            self.setItemWidget(item, item_widget)

    def update_clip(self, index: int):
        """Aktualisiert die Anzeige eines einzelnen Clips"""
        if 0 <= index < self.count():
            item = self.item(index)
            widget = self.itemWidget(item)
            if isinstance(widget, ClipListItem):
                widget.clip = self._clips[index]
                widget.update_display()

    def select_clip(self, index: int):
        """Wählt einen Clip aus"""
        if 0 <= index < self.count():
            self.setCurrentRow(index)
            self.clip_selected.emit(index)

    def get_accepted_count(self) -> int:
        """Gibt die Anzahl akzeptierter Clips zurück"""
        return sum(1 for c in self._clips if c.status == ClipStatus.ACCEPTED)

    def get_skipped_count(self) -> int:
        """Gibt die Anzahl übersprungener Clips zurück"""
        return sum(1 for c in self._clips if c.status == ClipStatus.SKIPPED)
