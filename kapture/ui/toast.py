from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame

from kapture.ui.icons import icon as I


class Toast(QWidget):
    def __init__(self, title, body, thumb=None, actions=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(360)
        self._build(title, body, thumb, actions or [])
        self._position()
        self.show()
        QTimer.singleShot(6000, self.close)

    def _build(self, title, body, thumb, actions):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        card = QFrame()
        card.setStyleSheet("QFrame { background: rgba(18,20,28,0.95); border:1px solid rgba(255,255,255,0.1); border-radius:14px; }")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        if thumb is not None:
            lbl = QLabel()
            lbl.setPixmap(thumb.scaled(56, 56))
            cl.addWidget(lbl)
        txt = QVBoxLayout()
        t = QLabel(title)
        t.setStyleSheet("color:#f5f7fa; font-weight:700;")
        txt.addWidget(t)
        b = QLabel(body)
        b.setStyleSheet("color:#9aa4b2; font-size:9pt;")
        b.setWordWrap(True)
        txt.addWidget(b)
        cl.addLayout(txt, 1)
        btns = QHBoxLayout()
        for name, cb in actions:
            btn = QPushButton(name)
            btn.setFixedHeight(26)
            btn.clicked.connect(cb)
            btn.clicked.connect(self.close)
            btns.addWidget(btn)
        if btns.count():
            txt.addLayout(btns)
        lay.addWidget(card)

    def _position(self):
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen().geometry()
        self.move(scr.right() - self.width() - 20, scr.bottom() - self.height() - 20)

    def paintEvent(self, e):
        pass
