from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

from kapture.ui.icons import pixmap


class Tray:
    def __init__(self, app, popup, cfg):
        self.app = app
        self.popup = popup
        self.cfg = cfg
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(pixmap("camera", "#3b82f6", 24)))
        self.tray.setToolTip("Kapture")
        self.menu = QMenu()
        show_act = QAction("Show Kapture", app)
        show_act.triggered.connect(self.show_popup)
        self.menu.addAction(show_act)
        self.menu.addSeparator()
        shot_menu = self.menu.addMenu("Screenshot")
        for label, mode in (("Full screen", "full"), ("Window", "window"), ("Region", "region")):
            a = QAction(label, app)
            a.triggered.connect(lambda checked=False, m=mode: self._shot(m))
            shot_menu.addAction(a)
        rec_menu = self.menu.addMenu("Record")
        for label, mode in (("Full screen", "full"), ("Window", "window"), ("Region", "region")):
            a = QAction(label, app)
            a.triggered.connect(lambda checked=False, m=mode: self._record(m))
            rec_menu.addAction(a)
        self.menu.addSeparator()
        settings_act = QAction("Settings", app)
        settings_act.triggered.connect(lambda: self.settings_requested())
        self.menu.addAction(settings_act)
        quit_act = QAction("Quit", app)
        quit_act.triggered.connect(app.quit)
        self.menu.addAction(quit_act)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._activated)
        self.tray.show()
        self._shot_cb = None
        self._record_cb = None
        self._settings_cb = None

    def on_shot(self, cb):
        self._shot_cb = cb

    def on_record(self, cb):
        self._record_cb = cb

    def on_settings(self, cb):
        self._settings_cb = cb

    def settings_requested(self):
        if self._settings_cb:
            self._settings_cb()

    def show_popup(self):
        self.popup.show_animated()

    def _shot(self, mode):
        if self._shot_cb:
            self._shot_cb(mode)

    def _record(self, mode):
        if self._record_cb:
            self._record_cb(mode)

    def _activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_popup()

    def set_tooltip(self, text):
        self.tray.setToolTip(text)

    def show_message(self, title, body):
        self.tray.showMessage(title, body, QSystemTrayIcon.MessageIcon.Information, 4000)
