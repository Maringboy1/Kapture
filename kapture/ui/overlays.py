import time

from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QApplication, QLabel

from kapture.core import windows
from kapture.core.geometry import even


def _freeze_screen():
    from kapture.core.capture import capture_full, virtual_geometry
    vg = virtual_geometry()
    vx, vy, vw, vh = vg
    data, _ = capture_full(0, cursor=False, delay=0)
    # capture full virtual instead
    import subprocess
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
           "-video_size", f"{vw}x{vh}", "-i", f":0.0+{vx},{vy}",
           "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"]
    r = subprocess.run(cmd, capture_output=True)
    from PyQt6.QtGui import QImage
    img = QImage()
    img.loadFromData(r.stdout)
    pm = QPixmap.fromImage(img)
    return pm, vg


class RegionOverlay(QWidget):
    selected = pyqtSignal(int, int, int, int)
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.pm, self.vg = _freeze_screen()
        vx, vy, vw, vh = self.vg
        self.setGeometry(vx, vy, vw, vh)
        self.origin = None
        self.current = None
        self.dragging = False
        self.handle = None
        self.rect_sel = None
        self.magnifier = True

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.pm)
        # dim
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))
        r = self._sel_rect()
        if r:
            # clear selection area
            p.drawPixmap(r, self.pm, r)
            pen = QPen(QColor("#3b82f6"), 2)
            p.setPen(pen)
            p.drawRect(r.adjusted(0, 0, -1, -1))
            # size label
            p.setPen(QColor("#ffffff"))
            p.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            p.drawText(r.bottomRight() + QPoint(6, 16), f"{r.width()} x {r.height()}")
        # magnifier
        if self.magnifier and self.current is not None:
            self._draw_magnifier(p)
        p.end()

    def _sel_rect(self):
        if self.rect_sel is not None:
            return self.rect_sel
        if self.origin is None or self.current is None:
            return None
        return QRect(self.origin, self.current).normalized()

    def _draw_magnifier(self, p):
        pos = self.mapFromGlobal(QApplication.instance().primaryScreen().cursor().pos() if False else self.cursor().pos())
        # use global cursor
        from PyQt6.QtGui import QCursor
        gpos = QCursor.pos()
        lx = gpos.x() - self.vg[0]
        ly = gpos.y() - self.vg[1]
        zoom = 6
        src = QRect(lx - 8, ly - 8, 16, 16)
        dst = QRect(lx + 20, ly + 20, 96, 96)
        if dst.right() > self.width():
            dst.moveLeft(lx - 116)
        if dst.bottom() > self.height():
            dst.moveTop(ly - 116)
        p.drawPixmap(dst, self.pm, src)
        p.setPen(QPen(QColor("#3b82f6"), 2))
        p.drawRect(dst)
        # crosshair
        cx = dst.left() + dst.width() // 2
        cy = dst.top() + dst.height() // 2
        p.drawLine(cx, dst.top(), cx, dst.bottom())
        p.drawLine(dst.left(), cy, dst.right(), cy)
        # color under cursor
        c = self.pm.toImage().pixelColor(lx, ly) if 0 <= lx < self.pm.width() and 0 <= ly < self.pm.height() else QColor(0, 0, 0)
        p.setBrush(QBrush(c))
        p.setPen(QPen(QColor("#ffffff"), 1))
        p.drawRect(dst.right() + 6, dst.top(), 24, 24)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Inter", 9))
        p.drawText(dst.right() + 6, dst.top() + 40, f"{c.name()}")
        p.drawText(dst.right() + 6, dst.top() + 56, f"{gpos.x()},{gpos.y()}")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.origin = e.pos()
            self.current = e.pos()
            self.dragging = True
            self.rect_sel = None
            self.update()

    def mouseMoveEvent(self, e):
        if self.dragging:
            self.current = e.pos()
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.rect_sel = QRect(self.origin, e.pos()).normalized()
            self.origin = None
            self.current = None
            self.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()
        elif e.key() == Qt.Key.Key_Return and self.rect_sel:
            self._emit()

    def _emit(self):
        if self.rect_sel and self.rect_sel.width() > 4 and self.rect_sel.height() > 4:
            r = self.rect_sel
            vx, vy, _, _ = self.vg
            self.selected.emit(vx + r.x(), vy + r.y(), r.width(), r.height())
            self.close()

    def mouseDoubleClickEvent(self, e):
        if self.rect_sel:
            self._emit()


class WindowOverlay(QWidget):
    selected = pyqtSignal(int)  # window id
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pm, self.vg = _freeze_screen()
        vx, vy, vw, vh = self.vg
        self.setGeometry(vx, vy, vw, vh)
        self.hovered = None
        self.timer = QTimer(self)
        self.timer.setInterval(60)
        self.timer.timeout.connect(self._update_hover)
        self.timer.start()

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.pm)
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))
        if self.hovered:
            w = self.hovered
            vx, vy, _, _ = self.vg
            r = QRect(w["x"] - vx, w["y"] - vy, w["w"], w["h"])
            # clear
            p.drawPixmap(r, self.pm, r)
            pen = QPen(QColor("#3b82f6"), 3)
            p.setPen(pen)
            p.drawRect(r.adjusted(0, 0, -1, -1))
            # label
            label = f"{w['class']} - {w['name']}"
            p.setPen(QColor("#ffffff"))
            p.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            lx = r.x()
            ly = r.y() - 22 if r.y() > 30 else r.y() + r.height() + 6
            p.fillRect(lx, ly - 16, min(400, len(label) * 8 + 12), 20, QColor(0, 0, 0, 180))
            p.drawText(lx + 6, ly, label)
        p.end()

    def _update_hover(self):
        from PyQt6.QtGui import QCursor
        gpos = QCursor.pos()
        vx, vy, _, _ = self.vg
        w = windows.top_window_at(gpos.x(), gpos.y())
        if w != self.hovered:
            self.hovered = w
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.hovered:
            self.selected.emit(self.hovered["id"])
            self._stop()
            self.close()
        elif e.button() == Qt.MouseButton.RightButton:
            self.cancelled.emit()
            self._stop()
            self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self._stop()
            self.close()

    def _stop(self):
        self.timer.stop()


class CountdownOverlay(QWidget):
    cancelled = pyqtSignal()

    def __init__(self, seconds):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen().geometry()
        self.setGeometry(scr)
        self.remaining = seconds
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.close()
        else:
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Inter", 120, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.remaining))
        p.setFont(QFont("Inter", 14))
        p.drawText(self.rect().adjusted(0, 120, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Press Esc to cancel")
        p.end()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.timer.stop()
            self.close()
