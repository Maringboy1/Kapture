import io

from PyQt6.QtCore import Qt, QRectF, QPointF, QEvent
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QFont, QBrush, QPolygonF,
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QSpinBox,
    QColorDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsPathItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QFileDialog, QSizePolicy, QComboBox,
)

from kapture.ui.icons import icon as I
from kapture.core.clipboard import set_image, qimage_to_png_bytes
from kapture.core.logging import get_logger

log = get_logger("annotator")


def _pixelate(img, rect, block=12):
    x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
    x = max(0, x); y = max(0, y)
    w = min(w, img.width() - x); h = min(h, img.height() - y)
    if w <= 0 or h <= 0:
        return img
    sub = img.copy(x, y, w, h)
    small = sub.scaled(max(1, w // block), max(1, h // block), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
    big = small.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
    p = QPainter(img)
    p.drawImage(x, y, big)
    p.end()
    return img


def _blur(img, rect, radius=8):
    x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
    x = max(0, x); y = max(0, y)
    w = min(w, img.width() - x); h = min(h, img.height() - y)
    if w <= 0 or h <= 0:
        return img
    sub = img.copy(x, y, w, h)
    from PyQt6.QtGui import QImage as QI
    # simple box blur via scaled down/up
    small = sub.scaled(max(1, w // radius), max(1, h // radius), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    big = small.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    p = QPainter(img)
    p.drawImage(x, y, big)
    p.end()
    return img



class CanvasView(QGraphicsView):
    def __init__(self, scene, annotator):
        super().__init__(scene)
        self.annotator = annotator
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            if self.annotator._press_scene(pos):
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        if self.annotator._move_scene(pos):
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            if self.annotator._release_scene(pos):
                event.accept()
                return
        super().mouseReleaseEvent(event)

class AnnotatorDialog(QDialog):
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Annotate")
        self.resize(900, 640)
        self.image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.tool = "pen"
        self.color = QColor("#ff3b30")
        self.width = 3
        self.font_size = 18
        self._drawing = False
        self._start = None
        self._current_item = None
        self._undo = []
        self._redo = []
        self._build()
        self._set_base(self.image)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        # toolbar
        tb = QHBoxLayout()
        tools = [("pen", "Pen"), ("highlighter", "Highlight"), ("arrow", "Arrow"),
                 ("rect", "Rect"), ("ellipse", "Ellipse"), ("text", "Text"),
                 ("pixelate", "Pixelate"), ("blur", "Blur"), ("crop", "Crop")]
        self.tool_buttons = {}
        for key, label in tools:
            b = QPushButton(label)
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False, k=key: self._set_tool(k))
            tb.addWidget(b)
            self.tool_buttons[key] = b
        tb.addStretch()
        # color
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(28, 28)
        self.color_btn.clicked.connect(self._pick_color)
        self._update_color_btn()
        tb.addWidget(self.color_btn)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 40)
        self.width_spin.setValue(self.width)
        self.width_spin.valueChanged.connect(lambda v: setattr(self, "width", v))
        tb.addWidget(self.width_spin)
        root.addLayout(tb)

        # canvas
        self.scene = QGraphicsScene(self)
        self.view = CanvasView(self.scene, self)
        self.scene.focusItemChanged.connect(self._on_focus_changed)
        root.addWidget(self.view, 1)

        # bottom bar
        bb = QHBoxLayout()
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self._undo_act)
        bb.addWidget(self.undo_btn)
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self._redo_act)
        bb.addWidget(self.redo_btn)
        bb.addStretch()
        zoom_in = QPushButton("Zoom +")
        zoom_in.clicked.connect(lambda: self.view.scale(1.2, 1.2))
        bb.addWidget(zoom_in)
        zoom_out = QPushButton("Zoom -")
        zoom_out.clicked.connect(lambda: self.view.scale(1 / 1.2, 1 / 1.2))
        bb.addWidget(zoom_out)
        fit_btn = QPushButton("Fit")
        fit_btn.clicked.connect(self._fit)
        bb.addWidget(fit_btn)
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self._copy)
        bb.addWidget(copy_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        bb.addWidget(save_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bb.addWidget(close_btn)
        root.addLayout(bb)

        self.view.setMouseTracking(True)
        self._set_tool("pen")

    def _set_base(self, img):
        self.base_img = img.convertToFormat(QImage.Format.Format_ARGB32)
        self.base_item = QGraphicsPixmapItem(QPixmap.fromImage(self.base_img))
        self.scene.clear()
        self.scene.addItem(self.base_item)
        self.scene.setSceneRect(QRectF(self.base_item.boundingRect()))
        self._fit()

    def _on_focus_changed(self, new, old):
        from PyQt6.QtWidgets import QGraphicsTextItem
        if isinstance(old, QGraphicsTextItem):
            self._bake()

    def _fit(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _set_tool(self, tool):
        self.tool = tool
        for k, b in self.tool_buttons.items():
            b.setChecked(k == tool)

    def _pick_color(self):
        c = QColorDialog.getColor(self.color, self, "Color")
        if c.isValid():
            self.color = c
            self._update_color_btn()

    def _update_color_btn(self):
        self.color_btn.setStyleSheet(f"background:{self.color.name()}; border:1px solid #888; border-radius:6px;")

    def _render_current(self):
        rect = self.scene.sceneRect()
        img = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        self.scene.render(painter, QRectF(img.rect()), rect)
        painter.end()
        return img

    def _push_undo(self):
        self._undo.append(self.base_img.copy())
        if len(self._undo) > 50:
            self._undo.pop(0)
        self._redo.clear()

    def _bake(self):
        img = self._render_current()
        self._set_base(img)

    def _undo_act(self):
        if not self._undo:
            return
        self._redo.append(self.base_img.copy())
        prev = self._undo.pop()
        self._set_base(prev)

    def _redo_act(self):
        if not self._redo:
            return
        self._undo.append(self.base_img.copy())
        nxt = self._redo.pop()
        self._set_base(nxt)

    def _copy(self):
        set_image(self.base_img.copy())

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG (*.png);;JPEG (*.jpg);;WebP (*.webp)")
        if path:
            self.base_img.save(path)

    def _scene_pos(self, event):
        return event.scenePos()

    def _press_scene(self, pos):
        if self.tool == "text":
            self._push_undo()
            item = QGraphicsTextItem("Text")
            item.setPos(pos)
            item.setFont(QFont("Inter", self.font_size))
            item.setDefaultTextColor(self.color)
            item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.scene.addItem(item)
            item.setFocus()
            return True
        self._drawing = True
        self._start = pos
        self._push_undo()
        if self.tool == "pen":
            item = QGraphicsPathItem()
            item.setPen(QPen(self.color, self.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            path = QPainterPath() if False else None
            from PyQt6.QtGui import QPainterPath
            pp = QPainterPath()
            pp.moveTo(pos)
            item.setPath(pp)
            self.scene.addItem(item)
            self._current_item = item
            self._path = pp
        elif self.tool == "highlighter":
            from PyQt6.QtGui import QPainterPath
            item = QGraphicsPathItem()
            c = QColor(self.color)
            c.setAlpha(90)
            item.setPen(QPen(c, self.width * 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            pp = QPainterPath()
            pp.moveTo(pos)
            item.setPath(pp)
            self.scene.addItem(item)
            self._current_item = item
            self._path = pp
        elif self.tool in ("arrow", "line"):
            item = QGraphicsLineItem(pos.x(), pos.y(), pos.x(), pos.y())
            item.setPen(QPen(self.color, self.width))
            self.scene.addItem(item)
            self._current_item = item
        elif self.tool in ("rect", "crop"):
            item = QGraphicsRectItem(QRectF(pos, pos))
            item.setPen(QPen(self.color, self.width))
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.scene.addItem(item)
            self._current_item = item
        elif self.tool == "ellipse":
            item = QGraphicsEllipseItem(QRectF(pos, pos))
            item.setPen(QPen(self.color, self.width))
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.scene.addItem(item)
            self._current_item = item
        elif self.tool in ("pixelate", "blur"):
            item = QGraphicsRectItem(QRectF(pos, pos))
            item.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine))
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.scene.addItem(item)
            self._current_item = item
        return True

    def _move_scene(self, pos):
        if not self._drawing or self._current_item is None:
            return False
        if self.tool in ("pen", "highlighter"):
            self._path.lineTo(pos)
            self._current_item.setPath(self._path)
        elif self.tool in ("arrow", "line"):
            self._current_item.setLine(self._start.x(), self._start.y(), pos.x(), pos.y())
        elif self.tool in ("rect", "ellipse", "crop", "pixelate", "blur"):
            self._current_item.setRect(QRectF(self._start, pos).normalized())
        return True

    def _release_scene(self, pos):
        if not self._drawing:
            return False
        self._drawing = False
        if self.tool == "arrow":
            # add arrowhead
            line = self._current_item.line()
            import math
            angle = math.atan2(line.y2() - line.y1(), line.x2() - line.x1())
            size = 10 + self.width
            p1 = QPointF(line.x2(), line.y2())
            p2 = QPointF(line.x2() - size * math.cos(angle - 0.4), line.y2() - size * math.sin(angle - 0.4))
            p3 = QPointF(line.x2() - size * math.cos(angle + 0.4), line.y2() - size * math.sin(angle + 0.4))
            poly = QGraphicsPolygonItem(QPolygonF([p1, p2, p3]))
            poly.setBrush(QBrush(self.color))
            poly.setPen(QPen(self.color))
            self.scene.addItem(poly)
        if self.tool == "crop":
            rect = self._current_item.rect()
            self.scene.removeItem(self._current_item)
            self._current_item = None
            # apply crop
            x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
            x = max(0, x); y = max(0, y)
            w = min(w, self.base_img.width() - x)
            h = min(h, self.base_img.height() - y)
            if w > 4 and h > 4:
                cropped = self.base_img.copy(x, y, w, h)
                self._set_base(cropped)
            return True
        if self.tool in ("pixelate", "blur"):
            rect = self._current_item.rect()
            self.scene.removeItem(self._current_item)
            self._current_item = None
            if self.tool == "pixelate":
                self.base_img = _pixelate(self.base_img, rect)
            else:
                self.base_img = _blur(self.base_img, rect)
            self._set_base(self.base_img)
            return True
        # bake other drawings
        self._bake()
        self._current_item = None
        return True
