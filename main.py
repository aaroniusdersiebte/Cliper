#!/usr/bin/env python3
"""
Clip Workflow Tool für DaVinci Resolve

Ein Tool zum effizienten Durchgehen und Schneiden von Stream-Clips.
Integriert sich mit DaVinci Resolve über die Scripting API.

Hotkeys:
    Space   - Play/Pause
    1-5     - Bewertung
    I       - In-Point setzen
    O       - Out-Point setzen
    Enter   - Clip akzeptieren
    S       - Clip überspringen
    N       - Nächster Clip
    P       - Vorheriger Clip
    ←/→     - Frame vor/zurück
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from ui.main_window import MainWindow

    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Clip Workflow Tool")
    app.setOrganizationName("ClipTool")

    # Dark theme system preference
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
