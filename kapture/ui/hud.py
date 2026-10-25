from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from kapture.ui.icons import icon as I


class HUD(QWidget):
    pause_clicked = pyqtSignal()
    resume_clicked = pyqtSignal()
    mute_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 52)
        self._drag = None
        self.paused = False
        self.muted = False
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)
        self.dot = QLabel("●")
        self.dot.setStyleSheet("color:#ef4444; font-size:16px;")
        lay.addWidget(self.dot)
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setStyleSheet("color:#f5f7fa; font-weight:700; font-size:14px;")
        lay.addWidget(self.timer_lbl)
        lay.addStretch()
        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(I("pause", "#f5f7fa", 16))
        self.pause_btn.setFixedSize(28, 28)
        self.pause_btn.clicked.connect(self._pause)
        lay.addWidget(self.pause_btn)
        self.mute_btn = QPushButton()
        self.mute_btn.setIcon(I("mute", "#f5f7fa", 16))
        self.mute_btn.setFixedSize(28, 28)
        self.mute_btn.clicked.connect(self.mute_clicked.emit)
        lay.addWidget(self.mute_btn)
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(I("stop", "#f5f7fa", 16))
        self.stop_btn.setFixedSize(28, 28)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        lay.addWidget(self.stop_btn)

    def _pause(self):
        if self.paused:
            self.paused = False
            self.pause_btn.setIcon(I("pause", "#f5f7fa", 16))
            self.resume_clicked.emit()
        else:
            self.paused = True
            self.pause_btn.setIcon(I("play", "#f5f7fa", 16))
            self.pause_clicked.emit()

    def set_time(self, ms):
        s = ms // 1000
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        if h:
            self.timer_lbl.setText(f"{h:02d}:{m:02d}:{sec:02d}")
        else:
            self.timer_lbl.setText(f"{m:02d}:{sec:02d}")

    def pulse(self):
        # toggle dot opacity
        pass

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(18, 20, 28, 220))
        p.setPen(QColor(255, 255, 255, 30))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None
