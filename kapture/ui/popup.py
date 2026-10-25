import time

from PyQt6.QtCore import Qt, QPoint, QRect, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QTabWidget,
    QComboBox, QSpinBox, QCheckBox, QButtonGroup, QRadioButton, QSizePolicy,
)

from kapture.ui import icons, theme
from kapture.ui.icons import icon as I
from kapture.core import windows, audio
from kapture.core.geometry import clamp


def _bottom_anchor(cfg):
    # find bottom dock
    try:
        wins = windows.list_windows()
    except Exception:
        wins = []
    docks = [w for w in wins if "dock" in (t.lower() for t in (w.get("type") or []))]
    # fallback: any window with y+height near screen bottom and width > 500
    from PyQt6.QtWidgets import QApplication
    scr = QApplication.primaryScreen().geometry()
    bottom = scr.bottom()
    dock_top = None
    for w in docks:
        if w["y"] + w["h"] > scr.height() - 120:
            if dock_top is None or w["y"] < dock_top:
                dock_top = w["y"]
    if dock_top is None:
        # panel autohide: use known from earlier? default margin
        dock_top = scr.height() - 24
    margin = 16
    return dock_top - margin


class Popup(QWidget):
    shot_requested = pyqtSignal(str)   # full/region/window
    record_requested = pyqtSignal(str)
    settings_requested = pyqtSignal()
    hide_requested = pyqtSignal()

    def __init__(self, cfg, app):
        super().__init__()
        self.cfg = cfg
        self.app = app
        self.pinned = bool(cfg.get("ui", "popup_pinned", default=False))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)
        self._drag_pos = None
        self._build_ui()
        self._position()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(theme.qss(self.cfg))
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(10)

        # header
        hdr = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(I("camera", self.cfg.get("ui", "accent", default="#3b82f6"), 22).pixmap(22, 22))
        hdr.addWidget(logo)
        title = QLabel("Kapture")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        self.pin_btn = QPushButton()
        self.pin_btn.setIcon(I("pin", "#9aa4b2", 16))
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setObjectName("ghost")
        self.pin_btn.clicked.connect(self._toggle_pin)
        hdr.addWidget(self.pin_btn)
        settings_btn = QPushButton()
        settings_btn.setIcon(I("settings", "#9aa4b2", 16))
        settings_btn.setFixedSize(28, 28)
        settings_btn.setObjectName("ghost")
        settings_btn.clicked.connect(lambda: self.settings_requested.emit())
        hdr.addWidget(settings_btn)
        close_btn = QPushButton()
        close_btn.setIcon(I("close", "#9aa4b2", 16))
        close_btn.setFixedSize(28, 28)
        close_btn.setObjectName("ghost")
        close_btn.clicked.connect(self.hide_animated)
        hdr.addWidget(close_btn)
        cl.addLayout(hdr)

        sub = QLabel("Screenshot and screen recording")
        sub.setObjectName("subtitle")
        cl.addWidget(sub)

        # tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        shot_tab = self._shot_tab()
        rec_tab = self._rec_tab()
        self.tabs.addTab(shot_tab, "Screenshot")
        self.tabs.addTab(rec_tab, "Record")
        cl.addWidget(self.tabs)

        # action button
        self.action_btn = QPushButton("Capture")
        self.action_btn.setObjectName("primary")
        self.action_btn.setFixedHeight(40)
        self.action_btn.clicked.connect(self._on_action)
        cl.addWidget(self.action_btn)
        self.tabs.currentChanged.connect(self._update_action_label)

        root.addWidget(card)

    def _shot_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)
        # target
        row = QHBoxLayout()
        row.addWidget(QLabel("Target"))
        self.shot_target = QComboBox()
        self.shot_target.addItems(["Full screen", "Window", "Region"])
        row.addWidget(self.shot_target, 1)
        v.addLayout(row)
        # delay
        row = QHBoxLayout()
        row.addWidget(QLabel("Delay"))
        self.shot_delay = QSpinBox()
        self.shot_delay.setRange(0, 30)
        self.shot_delay.setValue(self.cfg.get("capture", "delay", default=0))
        self.shot_delay.setSuffix(" s")
        row.addWidget(self.shot_delay)
        row.addStretch()
        v.addLayout(row)
        # cursor
        self.shot_cursor = QCheckBox("Include cursor")
        self.shot_cursor.setChecked(self.cfg.get("capture", "cursor", default=True))
        v.addWidget(self.shot_cursor)
        v.addStretch()
        return w

    def _rec_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)
        row = QHBoxLayout()
        row.addWidget(QLabel("Target"))
        self.rec_target = QComboBox()
        self.rec_target.addItems(["Full screen", "Window", "Region"])
        row.addWidget(self.rec_target, 1)
        v.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("FPS"))
        self.rec_fps = QSpinBox()
        self.rec_fps.setRange(10, 60)
        self.rec_fps.setValue(self.cfg.get("recording", "fps", default=30))
        row.addWidget(self.rec_fps)
        row.addWidget(QLabel("CRF"))
        self.rec_crf = QSpinBox()
        self.rec_crf.setRange(10, 40)
        self.rec_crf.setValue(self.cfg.get("recording", "crf", default=20))
        row.addWidget(self.rec_crf)
        v.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Audio"))
        self.rec_audio = QComboBox()
        self.rec_audio.addItems(["none", "desktop", "mic", "both"])
        self.rec_audio.setCurrentText(self.cfg.get("recording", "audio", default="desktop"))
        row.addWidget(self.rec_audio, 1)
        v.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Format"))
        self.rec_format = QComboBox()
        self.rec_format.addItems(["mp4", "mkv", "webm", "gif"])
        self.rec_format.setCurrentText(self.cfg.get("recording", "format", default="mp4") if False else "mp4")
        row.addWidget(self.rec_format, 1)
        v.addLayout(row)

        self.rec_cursor = QCheckBox("Include cursor")
        self.rec_cursor.setChecked(self.cfg.get("capture", "cursor", default=True))
        v.addWidget(self.rec_cursor)

        v.addStretch()
        return w

    def _update_action_label(self):
        if self.tabs.currentIndex() == 0:
            self.action_btn.setText("Capture")
        else:
            self.action_btn.setText("Record")

    def _on_action(self):
        if self.tabs.currentIndex() == 0:
            t = self.shot_target.currentText().lower().replace(" ", "")
            if t == "fullscreen":
                t = "full"
            self.shot_requested.emit(t)
        else:
            t = self.rec_target.currentText().lower().replace(" ", "")
            if t == "fullscreen":
                t = "full"
            self.record_requested.emit(t)

    def _toggle_pin(self):
        self.pinned = not self.pinned
        self.cfg.set("ui", "popup_pinned", value=self.pinned)
        self.pin_btn.setIcon(I("pin", "#3b82f6" if self.pinned else "#9aa4b2", 16))

    def _position(self):
        x = self.cfg.get("ui", "popup_x", default=None)
        y = self.cfg.get("ui", "popup_y", default=None)
        if x is not None and y is not None:
            self.move(int(x), int(y))
            return
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen().geometry()
        ax = scr.x() + (scr.width() - self.width()) // 2
        ay = _bottom_anchor(self.cfg) - self.height()
        self.move(ax, ay)

    def show_animated(self):
        self._position()
        if self.cfg.get("ui", "reduced_motion", default=False):
            self.show()
            self.raise_()
            self.activateWindow()
            return
        self.setWindowOpacity(0.0)
        geo = self.geometry()
        start = QRect(geo.x(), geo.y() + 40, geo.width(), geo.height())
        self.setGeometry(start)
        self.show()
        self.raise_()
        self.activateWindow()
        anim_g = QPropertyAnimation(self, b"geometry")
        anim_g.setDuration(220)
        anim_g.setStartValue(start)
        anim_g.setEndValue(geo)
        anim_g.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_o = QPropertyAnimation(self, b"windowOpacity")
        anim_o.setDuration(220)
        anim_o.setStartValue(0.0)
        anim_o.setEndValue(1.0)
        anim_o.setEasingCurve(QEasingCurve.Type.OutCubic)
        grp = QParallelAnimationGroup(self)
        grp.addAnimation(anim_g)
        grp.addAnimation(anim_o)
        grp.start()

    def hide_animated(self):
        if self.cfg.get("ui", "reduced_motion", default=False):
            self.hide()
            self.hide_requested.emit()
            return
        geo = self.geometry()
        end = QRect(geo.x(), geo.y() + 40, geo.width(), geo.height())
        anim_g = QPropertyAnimation(self, b"geometry")
        anim_g.setDuration(180)
        anim_g.setStartValue(geo)
        anim_g.setEndValue(end)
        anim_g.setEasingCurve(QEasingCurve.Type.InCubic)
        anim_o = QPropertyAnimation(self, b"windowOpacity")
        anim_o.setDuration(180)
        anim_o.setStartValue(self.windowOpacity())
        anim_o.setEndValue(0.0)
        anim_o.setEasingCurve(QEasingCurve.Type.InCubic)
        grp = QParallelAnimationGroup(self)
        grp.addAnimation(anim_g)
        grp.addAnimation(anim_o)
        grp.finished.connect(self._after_hide)
        grp.start()

    def _after_hide(self):
        self.hide()
        self.hide_requested.emit()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        self.cfg.set("ui", "popup_x", value=self.x())
        self.cfg.set("ui", "popup_y", value=self.y())

    def apply_config(self, cfg):
        self.cfg = cfg
        self.setStyleSheet(theme.qss(cfg))
