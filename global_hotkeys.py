"""
Global Hotkeys - Ermöglicht Hotkeys auch außerhalb des Programms (z.B. in DaVinci Resolve)
"""
from typing import Callable, Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import threading


class GlobalHotkeyListener(QThread):
    """Thread für globale Hotkey-Erkennung mit pynput"""

    # Signale für die verschiedenen Aktionen
    set_in_point = pyqtSignal()
    set_out_point = pyqtSignal()
    accept_clip = pyqtSignal()
    skip_clip = pyqtSignal()
    next_clip = pyqtSignal()
    prev_clip = pyqtSignal()
    rate_1 = pyqtSignal()
    rate_2 = pyqtSignal()
    rate_3 = pyqtSignal()
    rate_4 = pyqtSignal()
    rate_5 = pyqtSignal()
    play_pause = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._listener = None
        self._ctrl_pressed = False
        self._alt_pressed = False

    def run(self):
        """Thread-Main: Startet den pynput Listener"""
        try:
            from pynput import keyboard

            self._running = True
            print("[GlobalHotkeys] pynput Listener gestartet")

            def on_press(key):
                if not self._running:
                    return False

                try:
                    # Modifier-Tasten tracken
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self._ctrl_pressed = True
                        return True
                    if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                        self._alt_pressed = True
                        return True

                    # Globale Hotkeys: Ctrl+Alt+<Key>
                    if self._ctrl_pressed and self._alt_pressed:
                        if hasattr(key, 'char') and key.char:
                            char = key.char.lower()
                            print(f"[GlobalHotkeys] Ctrl+Alt+{char} erkannt")

                            # In/Out Points
                            if char == 'i':
                                self.set_in_point.emit()
                            elif char == 'o':
                                self.set_out_point.emit()

                            # Navigation
                            elif char == 'n':
                                self.next_clip.emit()
                            elif char == 'p':
                                self.prev_clip.emit()

                            # Accept/Skip
                            elif char == 'a':
                                self.accept_clip.emit()
                            elif char == 's':
                                self.skip_clip.emit()

                            # Ratings
                            elif char == '1':
                                self.rate_1.emit()
                            elif char == '2':
                                self.rate_2.emit()
                            elif char == '3':
                                self.rate_3.emit()
                            elif char == '4':
                                self.rate_4.emit()
                            elif char == '5':
                                self.rate_5.emit()

                        # Space für Play/Pause
                        elif key == keyboard.Key.space:
                            print("[GlobalHotkeys] Ctrl+Alt+Space erkannt")
                            self.play_pause.emit()

                except AttributeError as e:
                    print(f"[GlobalHotkeys] AttributeError: {e}")

                return True

            def on_release(key):
                if not self._running:
                    return False

                try:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self._ctrl_pressed = False
                    if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                        self._alt_pressed = False
                except Exception:
                    pass

                return True

            # Listener starten
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                self._listener = listener
                listener.join()

        except ImportError as e:
            print(f"[GlobalHotkeys] pynput nicht installiert - globale Hotkeys deaktiviert: {e}")
        except Exception as e:
            import traceback
            print(f"[GlobalHotkeys] Fehler: {e}")
            traceback.print_exc()

    def stop(self):
        """Stoppt den Listener"""
        print("[GlobalHotkeys] Stoppe Listener...")
        self._running = False
        if self._listener:
            self._listener.stop()


class GlobalHotkeyManager(QObject):
    """Manager für globale Hotkeys - leitet Signale vom Listener weiter"""

    # Eigene Signale die von außen verbunden werden können
    set_in_point = pyqtSignal()
    set_out_point = pyqtSignal()
    accept_clip = pyqtSignal()
    skip_clip = pyqtSignal()
    next_clip = pyqtSignal()
    prev_clip = pyqtSignal()
    rate_1 = pyqtSignal()
    rate_2 = pyqtSignal()
    rate_3 = pyqtSignal()
    rate_4 = pyqtSignal()
    rate_5 = pyqtSignal()
    play_pause = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None
        self._enabled = False

    def start(self):
        """Startet die globale Hotkey-Erkennung"""
        if self._listener is not None and self._listener.isRunning():
            print("[GlobalHotkeys] Listener läuft bereits")
            return

        self._listener = GlobalHotkeyListener(self)

        # Verbinde Listener-Signale mit Manager-Signalen
        self._listener.set_in_point.connect(self.set_in_point.emit)
        self._listener.set_out_point.connect(self.set_out_point.emit)
        self._listener.accept_clip.connect(self.accept_clip.emit)
        self._listener.skip_clip.connect(self.skip_clip.emit)
        self._listener.next_clip.connect(self.next_clip.emit)
        self._listener.prev_clip.connect(self.prev_clip.emit)
        self._listener.rate_1.connect(self.rate_1.emit)
        self._listener.rate_2.connect(self.rate_2.emit)
        self._listener.rate_3.connect(self.rate_3.emit)
        self._listener.rate_4.connect(self.rate_4.emit)
        self._listener.rate_5.connect(self.rate_5.emit)
        self._listener.play_pause.connect(self.play_pause.emit)

        self._enabled = True
        self._listener.start()
        print("[GlobalHotkeys] Globale Hotkeys aktiviert (Ctrl+Alt+<Key>)")

    def stop(self):
        """Stoppt die globale Hotkey-Erkennung"""
        if self._listener:
            self._listener.stop()
            self._listener.wait(2000)  # Max 2 Sekunden warten
            self._listener = None
        self._enabled = False
        print("[GlobalHotkeys] Globale Hotkeys deaktiviert")

    @property
    def listener(self) -> Optional[GlobalHotkeyListener]:
        return self._listener

    @property
    def is_enabled(self) -> bool:
        return self._enabled


# Singleton
_manager: Optional[GlobalHotkeyManager] = None


def get_global_hotkeys() -> GlobalHotkeyManager:
    global _manager
    if _manager is None:
        _manager = GlobalHotkeyManager()
    return _manager
