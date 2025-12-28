from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QTextEdit, QFrame, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

from config import COLORS
from data.models import Clip, ClipRating


class RatingButtons(QWidget):
    """Bewertungs-Buttons"""

    rating_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._current_rating = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.buttons = []
        labels = ["1", "2", "3", "4", "5"]
        tooltips = ["Sehr schlecht", "Schlecht", "Meh", "Gut", "Sehr gut"]

        for i, (label, tooltip) in enumerate(zip(labels, tooltips), 1):
            btn = QPushButton(label)
            btn.setFixedSize(40, 40)
            btn.setToolTip(f"{tooltip} ({i})")
            btn.clicked.connect(lambda checked, r=i: self._on_rating_click(r))
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

    def _on_rating_click(self, rating: int):
        self.set_rating(rating)
        self.rating_changed.emit(rating)

    def set_rating(self, rating: int):
        self._current_rating = rating
        for i, btn in enumerate(self.buttons, 1):
            if i <= rating:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['warning']};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['bg_medium']};
                        color: {COLORS['text_secondary']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['bg_light']};
                    }}
                """)

    def get_rating(self) -> int:
        return self._current_rating


class TrimControls(QWidget):
    """In/Out-Point Controls"""

    in_point_changed = pyqtSignal(float)
    out_point_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._in_point = 0.0
        self._out_point = 0.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # In-Point
        in_layout = QHBoxLayout()
        in_label = QLabel("In:")
        in_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 30px;")
        self.in_value = QLabel("00:00:00")
        self.in_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-family: monospace;")
        self.in_btn = QPushButton("[I]")
        self.in_btn.setFixedWidth(50)
        self.in_btn.setToolTip("In-Point setzen (I)")

        in_layout.addWidget(in_label)
        in_layout.addWidget(self.in_value, 1)
        in_layout.addWidget(self.in_btn)
        layout.addLayout(in_layout)

        # Out-Point
        out_layout = QHBoxLayout()
        out_label = QLabel("Out:")
        out_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 30px;")
        self.out_value = QLabel("00:00:00")
        self.out_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-family: monospace;")
        self.out_btn = QPushButton("[O]")
        self.out_btn.setFixedWidth(50)
        self.out_btn.setToolTip("Out-Point setzen (O)")

        out_layout.addWidget(out_label)
        out_layout.addWidget(self.out_value, 1)
        out_layout.addWidget(self.out_btn)
        layout.addLayout(out_layout)

        # Duration
        dur_layout = QHBoxLayout()
        dur_label = QLabel("Dauer:")
        dur_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 30px;")
        self.duration_value = QLabel("00:00")
        self.duration_value.setStyleSheet(f"color: {COLORS['accent']}; font-family: monospace;")

        dur_layout.addWidget(dur_label)
        dur_layout.addWidget(self.duration_value, 1)
        layout.addLayout(dur_layout)

    def set_points(self, in_point: float, out_point: float):
        self._in_point = in_point
        self._out_point = out_point
        self._update_display()

    def set_in_point(self, value: float):
        self._in_point = value
        self._update_display()
        self.in_point_changed.emit(value)

    def set_out_point(self, value: float):
        self._out_point = value
        self._update_display()
        self.out_point_changed.emit(value)

    def _update_display(self):
        self.in_value.setText(self._format_time(self._in_point))
        self.out_value.setText(self._format_time(self._out_point))

        duration = max(0, self._out_point - self._in_point)
        self.duration_value.setText(self._format_duration(duration))

    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def _format_duration(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_in_point(self) -> float:
        return self._in_point

    def get_out_point(self) -> float:
        return self._out_point


class PlaybackControls(QWidget):
    """Playback-Buttons"""

    play_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    frame_back_clicked = pyqtSignal()
    frame_forward_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Frame zurück
        self.frame_back_btn = QPushButton("◀")
        self.frame_back_btn.setFixedSize(36, 36)
        self.frame_back_btn.setToolTip("Frame zurück (←)")
        self.frame_back_btn.clicked.connect(self.frame_back_clicked)

        # Prev Clip
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setToolTip("Vorheriger Clip (P)")
        self.prev_btn.clicked.connect(self.prev_clicked)

        # Play/Pause
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setToolTip("Play/Pause (Space)")
        self.play_btn.setObjectName("primary")
        self.play_btn.clicked.connect(self.play_clicked)

        # Next Clip
        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setToolTip("Nächster Clip (N)")
        self.next_btn.clicked.connect(self.next_clicked)

        # Frame vorwärts
        self.frame_forward_btn = QPushButton("▶")
        self.frame_forward_btn.setFixedSize(36, 36)
        self.frame_forward_btn.setToolTip("Frame vorwärts (→)")
        self.frame_forward_btn.clicked.connect(self.frame_forward_clicked)

        layout.addStretch()
        layout.addWidget(self.frame_back_btn)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.frame_forward_btn)
        layout.addStretch()

    def set_playing(self, is_playing: bool):
        self.play_btn.setText("⏸" if is_playing else "▶")


class ActionButtons(QWidget):
    """Accept/Skip Buttons"""

    accept_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Skip
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.setToolTip("Clip überspringen (S)")
        self.skip_btn.clicked.connect(self.skip_clicked)

        # Accept
        self.accept_btn = QPushButton("Akzeptieren")
        self.accept_btn.setObjectName("success")
        self.accept_btn.setToolTip("Clip akzeptieren (Enter)")
        self.accept_btn.clicked.connect(self.accept_clicked)

        layout.addWidget(self.skip_btn, 1)
        layout.addWidget(self.accept_btn, 1)


class NoteInput(QWidget):
    """Notiz-Eingabefeld"""

    note_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("Notiz:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Notiz zum Clip (wird als Marker gespeichert)...")
        self.text_edit.setMaximumHeight(80)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)

    def _on_text_changed(self):
        self.note_changed.emit(self.text_edit.toPlainText())

    def set_note(self, text: str):
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(text)
        self.text_edit.blockSignals(False)

    def get_note(self) -> str:
        return self.text_edit.toPlainText()

    def clear(self):
        self.text_edit.clear()
