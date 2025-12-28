"""
Mini Controller - Kompaktes Always-on-Top Fenster für schnellen Workflow
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QKeySequence, QShortcut, QMouseEvent

from config import COLORS


class MiniController(QWidget):
    """Kompaktes Floating-Fenster für Clip-Bearbeitung"""

    # Signals
    set_in_point = pyqtSignal()
    set_out_point = pyqtSignal()
    rating_changed = pyqtSignal(int)
    accept_clip = pyqtSignal()
    skip_clip = pyqtSignal()
    next_clip = pyqtSignal()
    prev_clip = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self._in_point = 0.0
        self._out_point = 0.0
        self._current_rating = 0

        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_window(self):
        """Konfiguriert Fenster-Eigenschaften"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setFixedWidth(280)
        self.setStyleSheet(self._get_stylesheet())

    def _get_stylesheet(self) -> str:
        return f"""
            MiniController {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 12px;
            }}
            QLabel#title {{
                font-weight: bold;
                font-size: 13px;
            }}
            QLabel#secondary {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
                border-color: {COLORS['accent']};
            }}
            QPushButton#action {{
                padding: 6px 12px;
            }}
            QPushButton#accept {{
                background-color: {COLORS['success']};
                border: none;
            }}
            QPushButton#rating {{
                min-width: 28px;
                min-height: 28px;
                padding: 0;
                font-weight: bold;
            }}
            QPushButton#rating_active {{
                background-color: {COLORS['warning']};
                border: none;
                min-width: 28px;
                min-height: 28px;
                padding: 0;
                font-weight: bold;
            }}
            QPushButton#nav {{
                min-width: 24px;
                padding: 2px 6px;
            }}
            QPushButton#close {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_secondary']};
                font-size: 14px;
                padding: 2px 6px;
            }}
            QPushButton#close:hover {{
                color: {COLORS['error']};
            }}
        """

    def _setup_ui(self):
        """Erstellt das UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)

        # Title Bar (draggable)
        title_bar = self._create_title_bar()
        layout.addWidget(title_bar)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Trim Section
        trim_section = self._create_trim_section()
        layout.addWidget(trim_section)

        # Rating Section
        rating_section = self._create_rating_section()
        layout.addWidget(rating_section)

        # Action Buttons
        action_section = self._create_action_section()
        layout.addWidget(action_section)

    def _create_title_bar(self) -> QWidget:
        """Erstellt die Titel-Leiste"""
        bar = QFrame()
        bar.setCursor(Qt.CursorShape.SizeAllCursor)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Drag Handle
        handle = QLabel("≡")
        handle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        layout.addWidget(handle)

        # Clip Name
        self.clip_label = QLabel("Kein Clip")
        self.clip_label.setObjectName("title")
        layout.addWidget(self.clip_label, 1)

        # Navigation
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setObjectName("nav")
        self.prev_btn.setToolTip("Vorheriger Clip (P)")
        self.prev_btn.clicked.connect(self.prev_clip.emit)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▶")
        self.next_btn.setObjectName("nav")
        self.next_btn.setToolTip("Nächster Clip (N)")
        self.next_btn.clicked.connect(self.next_clip.emit)
        layout.addWidget(self.next_btn)

        # Close
        close_btn = QPushButton("×")
        close_btn.setObjectName("close")
        close_btn.setToolTip("Schließen")
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        return bar

    def _create_trim_section(self) -> QWidget:
        """Erstellt den Trim-Bereich"""
        section = QFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Zeit-Anzeige
        time_row = QHBoxLayout()
        time_row.setSpacing(8)

        in_label = QLabel("In:")
        in_label.setObjectName("secondary")
        time_row.addWidget(in_label)

        self.in_value = QLabel("--:--:--")
        self.in_value.setStyleSheet("font-family: monospace;")
        time_row.addWidget(self.in_value)

        time_row.addStretch()

        out_label = QLabel("Out:")
        out_label.setObjectName("secondary")
        time_row.addWidget(out_label)

        self.out_value = QLabel("--:--:--")
        self.out_value.setStyleSheet("font-family: monospace;")
        time_row.addWidget(self.out_value)

        layout.addLayout(time_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.in_btn = QPushButton("[I] Set In")
        self.in_btn.setToolTip("In-Point setzen (I)")
        self.in_btn.clicked.connect(self.set_in_point.emit)
        btn_row.addWidget(self.in_btn)

        self.out_btn = QPushButton("[O] Set Out")
        self.out_btn.setToolTip("Out-Point setzen (O)")
        self.out_btn.clicked.connect(self.set_out_point.emit)
        btn_row.addWidget(self.out_btn)

        layout.addLayout(btn_row)

        return section

    def _create_rating_section(self) -> QWidget:
        """Erstellt den Rating-Bereich"""
        section = QFrame()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        layout.addStretch()

        self.rating_buttons = []
        for i in range(1, 6):
            btn = QPushButton(str(i))
            btn.setObjectName("rating")
            btn.setToolTip(f"Bewertung {i}")
            btn.clicked.connect(lambda checked, r=i: self._on_rating_click(r))
            self.rating_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        return section

    def _create_action_section(self) -> QWidget:
        """Erstellt die Action-Buttons"""
        section = QFrame()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        self.accept_btn = QPushButton("✓ Accept")
        self.accept_btn.setObjectName("accept")
        self.accept_btn.setToolTip("Clip akzeptieren (Enter)")
        self.accept_btn.clicked.connect(self.accept_clip.emit)
        layout.addWidget(self.accept_btn)

        self.skip_btn = QPushButton("✗ Skip")
        self.skip_btn.setObjectName("action")
        self.skip_btn.setToolTip("Clip überspringen (S)")
        self.skip_btn.clicked.connect(self.skip_clip.emit)
        layout.addWidget(self.skip_btn)

        return section

    def _setup_shortcuts(self):
        """Richtet Hotkeys ein"""
        # Trim
        QShortcut(QKeySequence(Qt.Key.Key_I), self, self.set_in_point.emit)
        QShortcut(QKeySequence(Qt.Key.Key_O), self, self.set_out_point.emit)

        # Rating
        for i in range(1, 6):
            QShortcut(QKeySequence(str(i)), self, lambda r=i: self._on_rating_click(r))

        # Navigation
        QShortcut(QKeySequence(Qt.Key.Key_N), self, self.next_clip.emit)
        QShortcut(QKeySequence(Qt.Key.Key_P), self, self.prev_clip.emit)

        # Actions
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self.accept_clip.emit)
        QShortcut(QKeySequence(Qt.Key.Key_S), self, self.skip_clip.emit)

    def _on_rating_click(self, rating: int):
        """Handler für Rating-Klick"""
        self._current_rating = rating
        self._update_rating_buttons()
        self.rating_changed.emit(rating)

    def _update_rating_buttons(self):
        """Aktualisiert das visuelle Rating"""
        for i, btn in enumerate(self.rating_buttons, 1):
            if i <= self._current_rating:
                btn.setObjectName("rating_active")
            else:
                btn.setObjectName("rating")
            btn.setStyle(btn.style())  # Force style refresh

    def _on_close(self):
        """Schließt das Fenster"""
        self.closed.emit()
        self.hide()

    # Public Methods

    def update_clip_info(self, name: str, in_point: float, out_point: float, rating: int):
        """Aktualisiert die Clip-Informationen"""
        self.clip_label.setText(name)
        self._in_point = in_point
        self._out_point = out_point
        self._current_rating = rating

        self.in_value.setText(self._format_time(in_point))
        self.out_value.setText(self._format_time(out_point))
        self._update_rating_buttons()

    def update_in_point(self, value: float):
        """Aktualisiert nur den In-Point"""
        self._in_point = value
        self.in_value.setText(self._format_time(value))

    def update_out_point(self, value: float):
        """Aktualisiert nur den Out-Point"""
        self._out_point = value
        self.out_value.setText(self._format_time(value))

    def _format_time(self, seconds: float) -> str:
        """Formatiert Sekunden als HH:MM:SS"""
        if seconds <= 0:
            return "--:--:--"
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    # Focus on Hover

    def enterEvent(self, event):
        """Automatischer Fokus wenn Maus über Fenster"""
        self.activateWindow()
        self.setFocus()
        super().enterEvent(event)

    # Dragging

    def mousePressEvent(self, event: QMouseEvent):
        """Startet Drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Bewegt Fenster"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Beendet Drag"""
        self._drag_pos = QPoint()
        event.accept()
