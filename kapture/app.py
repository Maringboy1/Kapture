import os
import sys
import time

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox

from kapture import __version__
from kapture.core.config import Config
from kapture.core.paths import ensure_dirs
from kapture.core.logging import get_logger
from kapture.core import capture, windows, audio
from kapture.core.recorder import RecordingSession
from kapture.core.hotkeys import HotkeyManager
from kapture.single_instance import SingleInstance
from kapture.ui.theme import apply_app_style, qss
from kapture.ui.popup import Popup
from kapture.ui.overlays import RegionOverlay, WindowOverlay, CountdownOverlay
from kapture.ui.hud import HUD
from kapture.ui.toast import Toast
from kapture.ui.tray import Tray
from kapture.ui.settings import SettingsDialog
from kapture.ui.annotator import AnnotatorDialog

log = get_logger("app")


class KaptureApp:
    def __init__(self, argv):
        ensure_dirs()
        self.cfg = Config()
        self.app = QApplication(argv)
        self.app.setApplicationName("Kapture")
        self.app.setApplicationDisplayName("Kapture")
        self.app.setOrganizationName("Kapture")
        apply_app_style(self.app, self.cfg)
        self.app.setStyleSheet(qss(self.cfg))
        self.si = SingleInstance()
        self.primary = self.si.start_primary()
        self.si.message_received.connect(self._on_ipc)
        self.popup = Popup(self.cfg, self.app)
        self.popup.shot_requested.connect(self.handle_shot_request)
        self.popup.record_requested.connect(self.handle_record_request)
        self.popup.settings_requested.connect(self.open_settings)
        self.tray = Tray(self.app, self.popup, self.cfg)
        self.tray.on_shot(self.handle_shot_request)
        self.tray.on_record(self.handle_record_request)
        self.tray.on_settings(self.open_settings)
        self.recorder = RecordingSession(self.cfg)
        self.recorder.tick.connect(self._on_rec_tick)
        self.recorder.state_changed.connect(self._on_rec_state)
        self.recorder.finished.connect(self._on_rec_finished)
        self.recorder.error.connect(self._on_rec_error)
        self.hud = None
        self._active_overlay = None
        self._pending_shot = None
        self._pending_rec = None
        self._hotkeys = None
        self._start_hotkeys()
        self._recovery_check()

    def _start_hotkeys(self):
        if not self.cfg.get("hotkeys", "enabled", default=True):
            return
        shortcuts = {
            "full_shot": self.cfg.get("hotkeys", "full", default="Super+Print"),
            "region_shot": self.cfg.get("hotkeys", "region", default="Ctrl+Alt+S"),
            "window_shot": self.cfg.get("hotkeys", "window", default="Ctrl+Alt+W"),
            "toggle_record": self.cfg.get("hotkeys", "record", default="Ctrl+Alt+R"),
        }
        self._hotkeys = HotkeyManager(shortcuts)
        self._hotkeys.triggered.connect(self._on_hotkey)
        self._hotkeys.start()
        # report conflicts
        for name, ok in self._hotkeys.status.items():
            if not ok:
                from kapture.core.notify import notify
                notify("Kapture", f"Hotkey conflict: {name}. Open Settings to change it.")

    def _on_hotkey(self, name):
        if name == "full_shot":
            self.handle_shot_request("full")
        elif name == "region_shot":
            self.handle_shot_request("region")
        elif name == "window_shot":
            self.handle_shot_request("window")
        elif name == "toggle_record":
            if self.recorder.state in ("recording", "paused"):
                self.recorder.stop()
            else:
                self.handle_record_request("full")

    def _recovery_check(self):
        from kapture.core.paths import TMP_DIR
        leftover = [p for p in TMP_DIR.iterdir() if p.is_dir() and p.name.startswith("session_")]
        if leftover:
            from PyQt6.QtWidgets import QMessageBox
            r = QMessageBox.question(None, "Kapture", "Unfinished recording found. Recover now?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r == QMessageBox.StandardButton.Yes:
                # finalize each
                for d in leftover:
                    try:
                        self._recover_session(d)
                    except Exception:
                        pass

    def _recover_session(self, d):
        # build a temp session object manually
        from kapture.core.recorder import RecordingSession
        rs = RecordingSession(self.cfg)
        rs.session_dir = d
        rs.segments = []
        for p in sorted(d.glob("segment_*.mkv")):
            from kapture.core.recorder import Segment
            rs.segments.append(Segment(p))
        out = rs._finalize()
        if out:
            Toast("Kapture", f"Recovered recording: {out}")
        # cleanup
        import shutil
        shutil.rmtree(d, ignore_errors=True)

    def _on_ipc(self, msg):
        cmd = msg.get("cmd")
        if cmd == "shot":
            self.handle_shot_request(msg.get("mode", "full"))
        elif cmd == "record":
            self.handle_record_request(msg.get("mode", "full"))
        elif cmd == "stop":
            self.recorder.stop()
        elif cmd == "pause":
            self.recorder.pause()
        elif cmd == "resume":
            self.recorder.resume()
        elif cmd == "show":
            self.popup.show_animated()
        elif cmd == "settings":
            self.open_settings()

    # ---------- shots ----------
    def handle_shot_request(self, mode):
        self.popup.hide()
        QTimer.singleShot(150, lambda: self._start_shot(mode))

    def _start_shot(self, mode):
        if mode == "region":
            self._region_pick("shot")
            return
        if mode == "window":
            self._window_pick("shot")
            return
        delay = self.cfg.get("capture", "delay", default=0)
        cursor = self.cfg.get("capture", "cursor", default=True)
        if delay and delay > 0:
            self._run_countdown(delay, lambda: self._do_shot_full(cursor))
        else:
            self._do_shot_full(cursor)

    def _do_shot_full(self, cursor):
        data, err = capture.capture_full(self.cfg.get("capture", "screen_index", default=0), cursor, 0)
        self._finish_shot_data(data, err)

    def _region_pick(self, purpose):
        ov = RegionOverlay()
        self._active_overlay = ov
        if purpose == "shot":
            ov.selected.connect(self._region_shot_done)
        else:
            ov.selected.connect(self._region_record_done)
        ov.cancelled.connect(self._overlay_cancelled)
        ov.show()

    def _window_pick(self, purpose):
        ov = WindowOverlay()
        self._active_overlay = ov
        if purpose == "shot":
            ov.selected.connect(self._window_shot_done)
        else:
            ov.selected.connect(self._window_record_done)
        ov.cancelled.connect(self._overlay_cancelled)
        ov.show()

    def _region_shot_done(self, x, y, w, h):
        self._close_overlay()
        delay = self.cfg.get("capture", "delay", default=0)
        cursor = self.cfg.get("capture", "cursor", default=True)
        if delay and delay > 0:
            self._run_countdown(delay, lambda: self._do_region_shot(x, y, w, h, cursor))
        else:
            self._do_region_shot(x, y, w, h, cursor)

    def _do_region_shot(self, x, y, w, h, cursor):
        data, err = capture.capture_region(x, y, w, h, cursor, 0)
        self._finish_shot_data(data, err)

    def _window_shot_done(self, wid):
        self._close_overlay()
        delay = self.cfg.get("capture", "delay", default=0)
        cursor = self.cfg.get("capture", "cursor", default=True)
        if delay and delay > 0:
            self._run_countdown(delay, lambda: self._do_window_shot(wid, cursor))
        else:
            self._do_window_shot(wid, cursor)

    def _do_window_shot(self, wid, cursor):
        data, err = capture.capture_window(wid, cursor, 0, self.cfg.get("recording", "include_titlebar", default=False))
        self._finish_shot_data(data, err)

    def _finish_shot_data(self, data, err):
        if err or data is None:
            from kapture.core.notify import notify
            notify("Kapture", f"Screenshot failed: {err}")
            return
        img = capture.bytes_to_qimage(data)
        from kapture.core.paths import SCREENSHOTS_DIR
        directory = self.cfg.get("capture", "screenshots_dir") or str(SCREENSHOTS_DIR)
        fmt = self.cfg.get("capture", "format", default="png")
        path = capture.save_bytes(data, directory, "photo", fmt, fmt=fmt)
        # clipboard
        from kapture.core import clipboard
        clipboard.set_image(img)
        # toast
        thumb = QPixmap.fromImage(img.scaled(64, 64))
        Toast("Kapture", f"Saved {path.name}", thumb=thumb, actions=[
            ("Edit", lambda p=path, i=img: self._open_annotator(i)),
            ("Copy", lambda i=img: clipboard.set_image(i)),
            ("Folder", lambda d=directory: clipboard.open_path(d)),
        ])
        # open annotator? no, on demand via Edit

    def _open_annotator(self, img):
        dlg = AnnotatorDialog(img, None)
        dlg.exec()

    def _run_countdown(self, seconds, cb):
        ov = CountdownOverlay(seconds)
        self._active_overlay = ov
        cancelled = {"v": False}

        def on_cancel():
            cancelled["v"] = True
            self._close_overlay()

        ov.cancelled.connect(on_cancel)
        ov.show()
        # wait
        QTimer.singleShot(seconds * 1000 + 100, lambda: self._after_countdown(cancelled, cb))

    def _after_countdown(self, cancelled, cb):
        self._close_overlay()
        if not cancelled["v"]:
            cb()

    def _close_overlay(self):
        if self._active_overlay is not None:
            try:
                self._active_overlay.close()
            except Exception:
                pass
            self._active_overlay = None

    def _overlay_cancelled(self):
        self._close_overlay()

    # ---------- recording ----------
    def handle_record_request(self, mode):
        self.popup.hide()
        if mode == "region":
            self._region_pick("record")
            return
        if mode == "window":
            self._window_pick("record")
            return
        delay = self.cfg.get("capture", "delay", default=0)
        cursor = self.cfg.get("capture", "cursor", default=True)
        target = {"mode": "full", "cursor": cursor}
        if delay and delay > 0:
            self._run_countdown(delay, lambda: self._do_start_record("full", {}, cursor))
        else:
            self._do_start_record("full", {}, cursor)

    def _region_record_done(self, x, y, w, h):
        self._close_overlay()
        cursor = self.cfg.get("capture", "cursor", default=True)
        delay = self.cfg.get("capture", "delay", default=0)
        if delay and delay > 0:
            self._run_countdown(delay, lambda: self._do_start_record("region", {"x": x, "y": y, "w": w, "h": h}, cursor))
        else:
            self._do_start_record("region", {"x": x, "y": y, "w": w, "h": h}, cursor)

    def _window_record_done(self, wid):
        self._close_overlay()
        cursor = self.cfg.get("capture", "cursor", default=True)
        delay = self.cfg.get("capture", "delay", default=0)
        if delay and delay > 0:
            self._run_countdown(delay, lambda: self._do_start_record("window", {"wid": wid}, cursor))
        else:
            self._do_start_record("window", {"wid": wid}, cursor)

    def _do_start_record(self, mode, target, cursor):
        target = dict(target)
        target["cursor"] = cursor
        # hud visibility
        hide_full = self.cfg.get("recording", "hide_hud_fullscreen", default=True)
        show_hud = self.cfg.get("recording", "show_hud", default=True)
        self.recorder.start(mode, target)
        if show_hud:
            if not (mode == "full" and hide_full):
                self._show_hud(mode, target)

    def _show_hud(self, mode="full", target=None):
        if self.hud is None:
            self.hud = HUD()
            self.hud.pause_clicked.connect(self.recorder.pause)
            self.hud.resume_clicked.connect(self.recorder.resume)
            self.hud.stop_clicked.connect(self.recorder.stop)
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen().geometry()
        x = scr.x() + (scr.width() - self.hud.width()) // 2
        y = scr.bottom() - self.hud.height() - 80
        if mode == "region" and target:
            rx, ry, rw, rh = target.get("x", 0), target.get("y", 0), target.get("w", 0), target.get("h", 0)
            # try above
            if ry - self.hud.height() - 16 >= scr.top():
                x = rx + rw // 2 - self.hud.width() // 2
                y = ry - self.hud.height() - 16
            elif ry + rh + self.hud.height() + 16 <= scr.bottom():
                x = rx + rw // 2 - self.hud.width() // 2
                y = ry + rh + 16
            elif rx - self.hud.width() - 16 >= scr.left():
                x = rx - self.hud.width() - 16
                y = ry + rh // 2 - self.hud.height() // 2
            elif rx + rw + self.hud.width() + 16 <= scr.right():
                x = rx + rw + 16
                y = ry + rh // 2 - self.hud.height() // 2
            else:
                # no room: hide HUD
                self.hud.hide()
                return
        x = max(scr.left() + 8, min(x, scr.right() - self.hud.width() - 8))
        y = max(scr.top() + 8, min(y, scr.bottom() - self.hud.height() - 8))
        self.hud.move(x, y)
        self.hud.show()

    def _on_rec_tick(self, ms):
        if self.hud is not None:
            self.hud.set_time(ms)
        s = ms // 1000
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        txt = f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
        self.tray.set_tooltip(f"Kapture - recording {txt}")
        # max duration
        maxd = self.cfg.get("recording", "max_duration", default=0)
        if maxd and ms >= maxd * 1000:
            self.recorder.stop()

    def _on_rec_state(self, state):
        if state == "paused":
            if self.hud:
                self.hud.paused = True
        elif state == "recording":
            if self.hud:
                self.hud.paused = False
        elif state in ("stopped", "finalizing"):
            pass

    def _on_rec_finished(self, path):
        if self.hud:
            self.hud.hide()
        from kapture.core.paths import VIDEOS_DIR
        directory = self.cfg.get("capture", "videos_dir") or str(VIDEOS_DIR)
        Toast("Kapture", f"Recording saved: {path}", actions=[
            ("Play", lambda p=path: self._open_path(p)),
            ("Folder", lambda d=directory: self._open_path(d)),
        ])
        self.tray.set_tooltip("Kapture")

    def _on_rec_error(self, err):
        if self.hud:
            self.hud.hide()
        from kapture.core.notify import notify
        notify("Kapture", f"Recording failed: {err}")

    def _open_path(self, p):
        from kapture.core.clipboard import open_path
        open_path(p)

    # ---------- settings ----------
    def open_settings(self):
        dlg = SettingsDialog(self.cfg, None)
        if dlg.exec():
            self.app.setStyleSheet(qss(self.cfg))
            self.popup.apply_config(self.cfg)
            # restart hotkeys
            if self._hotkeys:
                self._hotkeys.stop()
            self._start_hotkeys()

    def run(self):
        if not self.primary:
            # another instance running; forward nothing, just exit
            return 0
        # hidden mode?
        hidden = "--hidden" in sys.argv or "-hidden" in sys.argv
        if not hidden:
            QTimer.singleShot(200, self.popup.show_animated)
        return self.app.exec()
