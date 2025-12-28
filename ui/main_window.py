from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QFileDialog, QComboBox, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut

from config import STYLESHEET, COLORS
from data.models import Clip, ClipStatus, ClipRating
from data.clip_loader import load_clips, load_chapters, find_matching_video, save_session
from data.user_scores import UserScoreManager
from resolve import get_resolve, get_playback, get_timeline_controller
from ui.clip_list import ClipListWidget
from ui.controls import (
    RatingButtons, TrimControls, PlaybackControls,
    ActionButtons, NoteInput
)
from ui.mini_controller import MiniController
from global_hotkeys import get_global_hotkeys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clip Workflow Tool")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        # Data
        self._clips = []  # Alle geladenen Clips
        self._filtered_clips = []  # Aktuell angezeigte (gefilterte) Clips
        self._current_index = -1  # Index in self._clips (nicht in filtered!)
        self._user_scores = UserScoreManager()

        # Resolve
        self._resolve = get_resolve()
        self._playback = get_playback()
        self._timeline = get_timeline_controller()

        # Global Hotkeys
        self._global_hotkeys = get_global_hotkeys()

        # Mini Controller
        self._mini_controller = None

        # UI Setup
        self.setStyleSheet(STYLESHEET)
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_global_hotkeys()

        # Connection check
        self._check_resolve_connection()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Main Content (Splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Left: Clip List
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right: Current Clip Details
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([350, 650])
        main_layout.addWidget(splitter, 1)

        # Footer
        footer = self._create_footer()
        main_layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 8)

        # Load Button
        self.load_btn = QPushButton("Clips laden")
        self.load_btn.setObjectName("primary")
        self.load_btn.clicked.connect(self._on_load_clips)
        layout.addWidget(self.load_btn)

        layout.addSpacing(16)

        # Filter
        filter_label = QLabel("Filter:")
        filter_label.setObjectName("secondary")
        layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Alle", "Excellent", "Good", "Average", "Poor", "Unbewertet"])
        self.filter_combo.setMinimumWidth(120)
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_combo)

        layout.addStretch()

        # Mini Controller Button
        self.mini_ctrl_btn = QPushButton("Mini Controller")
        self.mini_ctrl_btn.setToolTip("Öffnet kompaktes Always-on-Top Fenster")
        self.mini_ctrl_btn.clicked.connect(self._open_mini_controller)
        layout.addWidget(self.mini_ctrl_btn)

        layout.addSpacing(8)

        # Global Hotkeys Toggle
        self.global_hotkey_btn = QPushButton("Global Hotkeys: AUS")
        self.global_hotkey_btn.setCheckable(True)
        self.global_hotkey_btn.setToolTip("Ctrl+Alt+<Key> funktioniert auch in anderen Programmen")
        self.global_hotkey_btn.clicked.connect(self._toggle_global_hotkeys)
        layout.addWidget(self.global_hotkey_btn)

        layout.addSpacing(8)

        # Resolve Status
        self.resolve_status = QLabel("● Resolve")
        self.resolve_status.setStyleSheet(f"color: {COLORS['error']};")
        layout.addWidget(self.resolve_status)

        return header

    def _create_left_panel(self) -> QWidget:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)

        # Title
        title = QLabel("Clips")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Clip List
        self.clip_list = ClipListWidget()
        self.clip_list.itemClicked.connect(self._on_clip_clicked)
        layout.addWidget(self.clip_list, 1)

        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(16)

        # Current Clip Info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)

        self.clip_title = QLabel("Kein Clip ausgewählt")
        self.clip_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addWidget(self.clip_title)

        self.clip_time = QLabel("--:--:--")
        self.clip_time.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        info_layout.addWidget(self.clip_time)

        self.clip_user_score = QLabel("")
        self.clip_user_score.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        info_layout.addWidget(self.clip_user_score)

        layout.addWidget(info_frame)

        # Trim Controls
        trim_section = QFrame()
        trim_layout = QVBoxLayout(trim_section)
        trim_layout.setContentsMargins(0, 0, 0, 0)

        trim_title = QLabel("Trimmen")
        trim_title.setStyleSheet(f"font-weight: bold; color: {COLORS['text_secondary']};")
        trim_layout.addWidget(trim_title)

        self.trim_controls = TrimControls()
        self.trim_controls.in_btn.clicked.connect(self._on_set_in_point)
        self.trim_controls.out_btn.clicked.connect(self._on_set_out_point)
        trim_layout.addWidget(self.trim_controls)

        layout.addWidget(trim_section)

        # Rating
        rating_section = QFrame()
        rating_layout = QVBoxLayout(rating_section)
        rating_layout.setContentsMargins(0, 0, 0, 0)

        rating_title = QLabel("Bewertung")
        rating_title.setStyleSheet(f"font-weight: bold; color: {COLORS['text_secondary']};")
        rating_layout.addWidget(rating_title)

        self.rating_buttons = RatingButtons()
        self.rating_buttons.rating_changed.connect(self._on_rating_changed)
        rating_layout.addWidget(self.rating_buttons)

        layout.addWidget(rating_section)

        # Note
        self.note_input = NoteInput()
        self.note_input.note_changed.connect(self._on_note_changed)
        layout.addWidget(self.note_input)

        # Playback Controls
        self.playback_controls = PlaybackControls()
        self.playback_controls.play_clicked.connect(self._on_play_pause)
        self.playback_controls.prev_clicked.connect(self._on_prev_clip)
        self.playback_controls.next_clicked.connect(self._on_next_clip)
        self.playback_controls.frame_back_clicked.connect(self._on_frame_back)
        self.playback_controls.frame_forward_clicked.connect(self._on_frame_forward)
        layout.addWidget(self.playback_controls)

        # Action Buttons
        self.action_buttons = ActionButtons()
        self.action_buttons.accept_clicked.connect(self._on_accept_clip)
        self.action_buttons.skip_clicked.connect(self._on_skip_clip)
        layout.addWidget(self.action_buttons)

        layout.addStretch()

        return panel

    def _create_footer(self) -> QWidget:
        footer = QFrame()
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        # Hotkey Hilfe
        hotkey_frame = QFrame()
        hotkey_layout = QHBoxLayout(hotkey_frame)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)

        hotkey_text = (
            "Hotkeys: [Space] Play/Pause | [1-5] Rating | [I/O] In/Out | "
            "[N/P] Nächster/Vorher | [T] Timestamp | [Enter] Accept | [S] Skip"
        )
        hotkey_label = QLabel(hotkey_text)
        hotkey_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
            padding: 4px 8px;
            background-color: {COLORS['bg_medium']};
            border-radius: 4px;
        """)
        hotkey_layout.addWidget(hotkey_label)
        layout.addWidget(hotkey_frame)

        # Stats + Export Row
        stats_row = QFrame()
        stats_layout = QHBoxLayout(stats_row)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        # Stats
        self.stats_label = QLabel("Akzeptiert: 0 | Übersprungen: 0 | Gesamt: 0")
        self.stats_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        # Export Button
        self.export_btn = QPushButton("Export Timeline")
        self.export_btn.setObjectName("success")
        self.export_btn.clicked.connect(self._on_export)
        self.export_btn.setEnabled(False)
        stats_layout.addWidget(self.export_btn)

        layout.addWidget(stats_row)

        return footer

    def _setup_shortcuts(self):
        # Play/Pause
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_play_pause)

        # Ratings
        for i in range(1, 6):
            QShortcut(QKeySequence(str(i)), self, lambda r=i: self._on_rating_changed(r))

        # Trim
        QShortcut(QKeySequence(Qt.Key.Key_I), self, self._on_set_in_point)
        QShortcut(QKeySequence(Qt.Key.Key_O), self, self._on_set_out_point)

        # Navigation
        QShortcut(QKeySequence(Qt.Key.Key_N), self, self._on_next_clip)
        QShortcut(QKeySequence(Qt.Key.Key_P), self, self._on_prev_clip)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._on_frame_back)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._on_frame_forward)

        # Actions
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self._on_accept_clip)
        QShortcut(QKeySequence(Qt.Key.Key_S), self, self._on_skip_clip)

        # Jump to timestamp
        QShortcut(QKeySequence(Qt.Key.Key_T), self, self._on_goto_timestamp)

    def _setup_global_hotkeys(self):
        """Verbindet die globalen Hotkey-Signale mit den Methoden"""
        # Verbinde mit den Manager-Signalen (nicht direkt mit dem Listener)
        # Der Manager leitet die Signale vom Listener weiter
        self._global_hotkeys.set_in_point.connect(self._on_set_in_point)
        self._global_hotkeys.set_out_point.connect(self._on_set_out_point)
        self._global_hotkeys.accept_clip.connect(self._on_accept_clip)
        self._global_hotkeys.skip_clip.connect(self._on_skip_clip)
        self._global_hotkeys.next_clip.connect(self._on_next_clip)
        self._global_hotkeys.prev_clip.connect(self._on_prev_clip)
        self._global_hotkeys.rate_1.connect(lambda: self._on_rating_changed(1))
        self._global_hotkeys.rate_2.connect(lambda: self._on_rating_changed(2))
        self._global_hotkeys.rate_3.connect(lambda: self._on_rating_changed(3))
        self._global_hotkeys.rate_4.connect(lambda: self._on_rating_changed(4))
        self._global_hotkeys.rate_5.connect(lambda: self._on_rating_changed(5))
        self._global_hotkeys.play_pause.connect(self._on_play_pause)

    def _toggle_global_hotkeys(self, checked: bool):
        """Schaltet globale Hotkeys ein/aus"""
        if checked:
            self._global_hotkeys.start()
            # Signal-Verbindungen sind bereits im __init__ gemacht worden
            self.global_hotkey_btn.setText("Global Hotkeys: AN")
            self.global_hotkey_btn.setStyleSheet(f"background-color: {COLORS['success']};")
        else:
            self._global_hotkeys.stop()
            self.global_hotkey_btn.setText("Global Hotkeys: AUS")
            self.global_hotkey_btn.setStyleSheet("")

    def _open_mini_controller(self):
        """Öffnet den Mini-Controller"""
        if self._mini_controller is None:
            self._mini_controller = MiniController()
            # Verbinde Signals
            self._mini_controller.set_in_point.connect(self._on_set_in_point)
            self._mini_controller.set_out_point.connect(self._on_set_out_point)
            self._mini_controller.rating_changed.connect(self._on_rating_changed)
            self._mini_controller.accept_clip.connect(self._on_accept_clip)
            self._mini_controller.skip_clip.connect(self._on_skip_clip)
            self._mini_controller.next_clip.connect(self._on_next_clip)
            self._mini_controller.prev_clip.connect(self._on_prev_clip)
            self._mini_controller.closed.connect(self._on_mini_controller_closed)

        # Position: rechts neben dem Hauptfenster
        main_geo = self.geometry()
        self._mini_controller.move(main_geo.right() + 10, main_geo.top())

        self._mini_controller.show()
        self._update_mini_controller()
        self.mini_ctrl_btn.setText("Mini Controller ✓")

    def _on_mini_controller_closed(self):
        """Wird aufgerufen wenn Mini-Controller geschlossen wird"""
        self.mini_ctrl_btn.setText("Mini Controller")

    def _update_mini_controller(self):
        """Aktualisiert den Mini-Controller mit aktuellem Clip"""
        if self._mini_controller is None or not self._mini_controller.isVisible():
            return
        if self._current_index < 0 or self._current_index >= len(self._clips):
            return

        clip = self._clips[self._current_index]
        self._mini_controller.update_clip_info(
            clip.user,
            clip.in_point,
            clip.out_point,
            clip.rating.value
        )

    def _check_resolve_connection(self):
        if self._resolve.connect():
            self.resolve_status.setText("● Resolve verbunden")
            self.resolve_status.setStyleSheet(f"color: {COLORS['success']};")
        else:
            self.resolve_status.setText("● Resolve nicht verbunden")
            self.resolve_status.setStyleSheet(f"color: {COLORS['error']};")

    # Event Handlers

    def _on_load_clips(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Clip-Datei laden",
            "",
            "Chapter Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                # Detect file type and load accordingly
                if file_path.endswith('.txt'):
                    self._clips, recording_name = load_chapters(file_path)

                    # Try to find matching video
                    video_path = find_matching_video(file_path)
                    if video_path:
                        # Import video to Resolve media pool
                        if self._resolve.is_connected:
                            success = self._timeline.import_media(video_path)
                            if success:
                                self.setWindowTitle(f"Clip Workflow Tool - {recording_name}")
                            else:
                                QMessageBox.warning(
                                    self, "Video Import",
                                    f"Video gefunden aber Import fehlgeschlagen:\n{video_path}"
                                )
                        else:
                            QMessageBox.information(
                                self, "Video gefunden",
                                f"Video: {video_path}\n\nResolve nicht verbunden - bitte manuell importieren."
                            )
                    else:
                        QMessageBox.warning(
                            self, "Video nicht gefunden",
                            f"Kein passendes Video für '{recording_name}' gefunden.\n"
                            "Bitte Video manuell in Resolve importieren."
                        )
                else:
                    self._clips = load_clips(file_path)

                self._user_scores.load()
                self._filtered_clips = self._clips.copy()  # Initial: alle Clips
                self.clip_list.set_clips(self._filtered_clips, self._user_scores.get_all_users())
                self._update_stats()

                if self._clips:
                    self._select_clip_obj(self._clips[0])

                    # Show clip count
                    QMessageBox.information(
                        self, "Geladen",
                        f"{len(self._clips)} Clips geladen."
                    )

            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Laden: {e}")

    def _on_filter_changed(self, filter_text: str):
        """Filtert die Clip-Liste nach Status/Rating"""
        if not self._clips:
            return

        # Erstelle gefilterte Liste
        if filter_text == "Alle":
            self._filtered_clips = self._clips.copy()
        elif filter_text == "Excellent":
            self._filtered_clips = [c for c in self._clips if c.rating.value >= 4]
        elif filter_text == "Good":
            self._filtered_clips = [c for c in self._clips if c.rating.value == 3]
        elif filter_text == "Average":
            self._filtered_clips = [c for c in self._clips if c.rating.value == 2]
        elif filter_text == "Poor":
            self._filtered_clips = [c for c in self._clips if c.rating.value == 1]
        elif filter_text == "Unbewertet":
            self._filtered_clips = [c for c in self._clips if c.rating.value == 0]
        else:
            self._filtered_clips = self._clips.copy()

        # Aktualisiere die Anzeige
        self.clip_list.set_clips(self._filtered_clips, self._user_scores.get_all_users())

        # Ersten Clip auswählen wenn möglich
        if self._filtered_clips:
            self._select_clip_obj(self._filtered_clips[0])

    def _on_clip_clicked(self, item):
        """Wird aufgerufen wenn ein Clip in der Liste angeklickt wird"""
        filtered_index = self.clip_list.currentRow()
        if 0 <= filtered_index < len(self._filtered_clips):
            # Hole den echten Clip aus der gefilterten Liste
            clip = self._filtered_clips[filtered_index]
            self._select_clip_obj(clip)

    def _get_clip_index(self, clip: Clip) -> int:
        """Findet den Index eines Clips in self._clips"""
        try:
            return self._clips.index(clip)
        except ValueError:
            return -1

    def _get_filtered_index(self, clip: Clip) -> int:
        """Findet den Index eines Clips in self._filtered_clips"""
        try:
            return self._filtered_clips.index(clip)
        except ValueError:
            return -1

    def _select_clip_obj(self, clip: Clip):
        """Wählt einen Clip direkt über das Objekt aus (nicht über Index)"""
        real_index = self._get_clip_index(clip)
        if real_index < 0:
            print(f"[UI] Clip nicht in _clips gefunden: {clip.user}")
            return

        self._current_index = real_index

        # Update UI
        self.clip_title.setText(f"Clip von {clip.user}")
        self.clip_time.setText(f"Zeit: {clip.timestamp_timecode}")

        user_score = self._user_scores.get_average(clip.user)
        if user_score > 0:
            tier = self._user_scores.get_tier(clip.user)
            self.clip_user_score.setText(f"User-Score: {user_score:.1f} ({tier})")
        else:
            self.clip_user_score.setText("User-Score: Keine Daten")

        self.trim_controls.set_points(clip.in_point, clip.out_point)
        self.rating_buttons.set_rating(clip.rating.value)
        self.note_input.set_note(clip.note)

        # Jump to review position (10 seconds before timestamp for context)
        review_position = max(0, clip.timestamp - 10)
        self._playback.goto_seconds(review_position)

        # Select in filtered list
        filtered_index = self._get_filtered_index(clip)
        if filtered_index >= 0:
            self.clip_list.select_clip(filtered_index)

        # Update Mini Controller
        self._update_mini_controller()

    def _on_rating_changed(self, rating: int):
        if self._current_index < 0:
            return

        clip = self._clips[self._current_index]
        old_rating = clip.rating.value
        clip.rating = ClipRating(rating)

        # Update user score only if rating changed
        if old_rating != rating and rating > 0:
            self._user_scores.add_rating(clip.user, rating)

        self.rating_buttons.set_rating(rating)
        # Update in der gefilterten Liste
        clip = self._clips[self._current_index]
        filtered_index = self._get_filtered_index(clip)
        if filtered_index >= 0:
            self.clip_list.update_clip(filtered_index)

    def _on_set_in_point(self):
        if self._current_index < 0:
            print("[UI] Kein Clip ausgewählt für In-Point")
            return

        current_pos = self._playback.get_current_seconds()
        if current_pos is not None:
            clip = self._clips[self._current_index]
            clip.in_point = current_pos
            self.trim_controls.set_in_point(current_pos)
            print(f"[UI] In-Point gesetzt: {current_pos:.2f}s für Clip von {clip.user}")

            # Marker in Resolve setzen (grün für In-Point, ersetzt alten IN-Marker)
            self._timeline.add_marker_at_position(
                current_pos,
                clip.user,
                f"IN @ {current_pos:.1f}s",
                "Green",
                marker_type="IN"
            )

            # Update Mini Controller
            if self._mini_controller and self._mini_controller.isVisible():
                self._mini_controller.update_in_point(current_pos)
        else:
            print("[UI] Konnte aktuelle Position nicht lesen")

    def _on_set_out_point(self):
        if self._current_index < 0:
            print("[UI] Kein Clip ausgewählt für Out-Point")
            return

        current_pos = self._playback.get_current_seconds()
        if current_pos is not None:
            clip = self._clips[self._current_index]
            clip.out_point = current_pos
            self.trim_controls.set_out_point(current_pos)
            print(f"[UI] Out-Point gesetzt: {current_pos:.2f}s für Clip von {clip.user}")

            # Marker in Resolve setzen (rot für Out-Point, ersetzt alten OUT-Marker)
            self._timeline.add_marker_at_position(
                current_pos,
                clip.user,
                f"OUT @ {current_pos:.1f}s",
                "Red",
                marker_type="OUT"
            )

            # Update Mini Controller
            if self._mini_controller and self._mini_controller.isVisible():
                self._mini_controller.update_out_point(current_pos)
        else:
            print("[UI] Konnte aktuelle Position nicht lesen")

    def _on_note_changed(self, text: str):
        if self._current_index >= 0:
            self._clips[self._current_index].note = text

    def _on_play_pause(self):
        self._playback.toggle_play()

    def _on_prev_clip(self):
        """Wechselt zum vorherigen Clip in der gefilterten Liste"""
        if self._current_index < 0 or not self._filtered_clips:
            return
        current_clip = self._clips[self._current_index]
        filtered_index = self._get_filtered_index(current_clip)
        if filtered_index > 0:
            prev_clip = self._filtered_clips[filtered_index - 1]
            self._select_clip_obj(prev_clip)

    def _on_next_clip(self):
        """Wechselt zum nächsten Clip in der gefilterten Liste"""
        if self._current_index < 0 or not self._filtered_clips:
            return
        current_clip = self._clips[self._current_index]
        filtered_index = self._get_filtered_index(current_clip)
        if filtered_index < len(self._filtered_clips) - 1:
            next_clip = self._filtered_clips[filtered_index + 1]
            self._select_clip_obj(next_clip)

    def _on_frame_back(self):
        self._playback.frame_backward()

    def _on_frame_forward(self):
        self._playback.frame_forward()

    def _on_goto_timestamp(self):
        """Springt zum ursprünglichen Clip-Timestamp"""
        if self._current_index < 0:
            return
        clip = self._clips[self._current_index]
        self._playback.goto_seconds(clip.timestamp)

    def _on_accept_clip(self):
        if self._current_index < 0:
            return

        clip = self._clips[self._current_index]
        clip.status = ClipStatus.ACCEPTED

        # Update in der gefilterten Liste
        filtered_index = self._get_filtered_index(clip)
        if filtered_index >= 0:
            self.clip_list.update_clip(filtered_index)

        self._update_stats()
        self._on_next_clip()

    def _on_skip_clip(self):
        if self._current_index < 0:
            return

        clip = self._clips[self._current_index]
        clip.status = ClipStatus.SKIPPED

        # Update in der gefilterten Liste
        filtered_index = self._get_filtered_index(clip)
        if filtered_index >= 0:
            self.clip_list.update_clip(filtered_index)

        self._update_stats()
        self._on_next_clip()

    def _update_stats(self):
        accepted = sum(1 for c in self._clips if c.status == ClipStatus.ACCEPTED)
        skipped = sum(1 for c in self._clips if c.status == ClipStatus.SKIPPED)
        total = len(self._clips)

        self.stats_label.setText(f"Akzeptiert: {accepted} | Übersprungen: {skipped} | Gesamt: {total}")
        self.export_btn.setEnabled(accepted > 0)

    def _on_export(self):
        accepted_clips = [c for c in self._clips if c.status == ClipStatus.ACCEPTED]
        if not accepted_clips:
            QMessageBox.information(self, "Export", "Keine Clips zum Exportieren ausgewählt.")
            return

        # Export to new timeline
        success = self._timeline.create_timeline_from_clips(accepted_clips, "Exported Clips")

        if success:
            QMessageBox.information(
                self,
                "Export",
                f"{len(accepted_clips)} Clips wurden in eine neue Timeline exportiert!"
            )
        else:
            QMessageBox.warning(
                self,
                "Export",
                "Export fehlgeschlagen. Stelle sicher, dass Resolve verbunden ist."
            )

    def closeEvent(self, event):
        # Stop global hotkeys
        if self._global_hotkeys.is_enabled:
            self._global_hotkeys.stop()

        # Save session on close
        if self._clips:
            try:
                save_session(self._clips, "last_session.json")
            except Exception:
                pass
        event.accept()
