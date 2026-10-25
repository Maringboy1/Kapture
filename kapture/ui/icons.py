from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QIcon, QPixmap, QFont
from PyQt6.QtWidgets import QWidget


def _paint_icon(painter, name, color, size):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), max(1.2, size / 12))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    s = size
    if name == "camera":
        painter.drawEllipse(QRectF(s*0.2, s*0.3, s*0.6, s*0.45))
        painter.drawLine(QPointF(s*0.5, s*0.3), QPointF(s*0.5, s*0.18))
    elif name == "video":
        painter.drawRoundedRect(QRectF(s*0.15, s*0.25, s*0.55, s*0.5), s*0.08, s*0.08)
        p = [QPointF(s*0.7, s*0.35), QPointF(s*0.88, s*0.25), QPointF(s*0.88, s*0.75), QPointF(s*0.7, s*0.65)]
        painter.drawPolygon(p)
    elif name == "region":
        painter.drawRect(QRectF(s*0.2, s*0.2, s*0.6, s*0.6))
        painter.drawLine(QPointF(s*0.2, s*0.35), QPointF(s*0.8, s*0.35))
    elif name == "window":
        painter.drawRoundedRect(QRectF(s*0.18, s*0.22, s*0.64, s*0.56), s*0.06, s*0.06)
        painter.drawLine(QPointF(s*0.18, s*0.34), QPointF(s*0.82, s*0.34))
    elif name == "settings":
        painter.drawEllipse(QRectF(s*0.3, s*0.3, s*0.4, s*0.4))
        for i in range(8):
            import math
            a = i * 45
            x1 = s*0.5 + (s*0.42)*math.cos(math.radians(a))
            y1 = s*0.5 + (s*0.42)*math.sin(math.radians(a))
            x2 = s*0.5 + (s*0.48)*math.cos(math.radians(a))
            y2 = s*0.5 + (s*0.48)*math.sin(math.radians(a))
            painter.drawLine(QPointF(x1,y1), QPointF(x2,y2))
    elif name == "close":
        painter.drawLine(QPointF(s*0.25, s*0.25), QPointF(s*0.75, s*0.75))
        painter.drawLine(QPointF(s*0.75, s*0.25), QPointF(s*0.25, s*0.75))
    elif name == "minimize":
        painter.drawLine(QPointF(s*0.25, s*0.5), QPointF(s*0.75, s*0.5))
    elif name == "pin":
        painter.drawEllipse(QRectF(s*0.35, s*0.2, s*0.3, s*0.3))
        painter.drawLine(QPointF(s*0.5, s*0.5), QPointF(s*0.5, s*0.8))
    elif name == "play":
        painter.setBrush(QColor(color))
        painter.drawPolygon([QPointF(s*0.3, s*0.2), QPointF(s*0.3, s*0.8), QPointF(s*0.75, s*0.5)])
    elif name == "stop":
        painter.setBrush(QColor(color))
        painter.drawRect(QRectF(s*0.25, s*0.25, s*0.5, s*0.5))
    elif name == "pause":
        painter.setBrush(QColor(color))
        painter.drawRect(QRectF(s*0.25, s*0.2, s*0.18, s*0.6))
        painter.drawRect(QRectF(s*0.57, s*0.2, s*0.18, s*0.6))
    elif name == "copy":
        painter.drawRoundedRect(QRectF(s*0.25, s*0.2, s*0.45, s*0.55), s*0.06, s*0.06)
        painter.drawRoundedRect(QRectF(s*0.35, s*0.3, s*0.45, s*0.55), s*0.06, s*0.06)
    elif name == "folder":
        painter.drawRoundedRect(QRectF(s*0.15, s*0.3, s*0.7, s*0.45), s*0.06, s*0.06)
        painter.drawLine(QPointF(s*0.15, s*0.3), QPointF(s*0.35, s*0.2))
    elif name == "edit":
        painter.drawLine(QPointF(s*0.2, s*0.8), QPointF(s*0.35, s*0.65))
        painter.drawLine(QPointF(s*0.35, s*0.65), QPointF(s*0.75, s*0.25))
        painter.drawLine(QPointF(s*0.75, s*0.25), QPointF(s*0.8, s*0.3))
    elif name == "trash":
        painter.drawLine(QPointF(s*0.25, s*0.3), QPointF(s*0.75, s*0.3))
        painter.drawRoundedRect(QRectF(s*0.3, s*0.3, s*0.4, s*0.5), s*0.04, s*0.04)
    elif name == "mute":
        painter.drawEllipse(QRectF(s*0.25, s*0.3, s*0.5, s*0.4))
        painter.drawLine(QPointF(s*0.2, s*0.75), QPointF(s*0.8, s*0.25))
    elif name == "mic":
        painter.drawEllipse(QRectF(s*0.35, s*0.2, s*0.3, s*0.35))
        painter.drawLine(QPointF(s*0.5, s*0.55), QPointF(s*0.5, s*0.75))
        painter.drawLine(QPointF(s*0.35, s*0.75), QPointF(s*0.65, s*0.75))
    else:
        painter.drawEllipse(QRectF(s*0.35, s*0.35, s*0.3, s*0.3))


def icon(name, color="#f5f7fa", size=24):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _paint_icon(p, name, color, size)
    p.end()
    return QIcon(pm)


def pixmap(name, color="#f5f7fa", size=24):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _paint_icon(p, name, color, size)
    p.end()
    return pm
