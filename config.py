from pathlib import Path

# Pfade
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
USER_SCORES_FILE = APP_DIR / "user_scores.json"

# Clip-Einstellungen
DEFAULT_PRE_ROLL = 30.0  # Sekunden vor Clip-Zeitpunkt
DEFAULT_FPS = 30.0

# Design - Minimalist Dark Theme
COLORS = {
    "bg_dark": "#1a1a1a",
    "bg_medium": "#2d2d2d",
    "bg_light": "#3d3d3d",
    "text_primary": "#ffffff",
    "text_secondary": "#888888",
    "accent": "#6366f1",
    "accent_hover": "#818cf8",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "border": "#404040",
}

# Stylesheet für PyQt
STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {COLORS['text_primary']};
}}

QLabel#secondary {{
    color: {COLORS['text_secondary']};
}}

QPushButton {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_light']};
    border-color: {COLORS['accent']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent']};
}}

QPushButton#primary {{
    background-color: {COLORS['accent']};
    border: none;
}}

QPushButton#primary:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#success {{
    background-color: {COLORS['success']};
    border: none;
}}

QListWidget {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 4px;
    margin: 2px;
}}

QListWidget::item:selected {{
    background-color: {COLORS['accent']};
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_light']};
}}

QLineEdit, QTextEdit {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

QLineEdit:focus, QTextEdit:focus {{
    border-color: {COLORS['accent']};
}}

QComboBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_light']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {COLORS['text_secondary']};
}}
"""

# Hotkeys
HOTKEYS = {
    "play_pause": "Space",
    "rate_1": "1",
    "rate_2": "2",
    "rate_3": "3",
    "rate_4": "4",
    "rate_5": "5",
    "set_in": "I",
    "set_out": "O",
    "accept": "Return",
    "skip": "S",
    "next": "N",
    "prev": "P",
    "frame_back": "Left",
    "frame_forward": "Right",
}
