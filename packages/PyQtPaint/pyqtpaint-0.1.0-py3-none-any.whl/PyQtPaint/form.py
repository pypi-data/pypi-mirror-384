
from typing import Sequence
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPainter, QBrush
from PyQt5.QtCore import Qt, pyqtSignal
from PyQtPaint.objects import PainterObject

class PainterWindow(QMainWindow):
    update_signal = pyqtSignal()

    default_position = (0, 0)
    default_size = (600, 600)

    def __init__(self, **kwargs):
        super().__init__()
        self.setMouseTracking(kwargs.pop('mouse_tracking', False))
        self.init_qwindow(**kwargs)
        self.painter_objects = []
        self.update_signal.connect(self.update)

    # --- QMainWindow Setup ---
    def init_qwindow(self, **kwargs):
        self.setWindowTitle(kwargs.pop('title', 'Painter Window'))
        if kwargs.pop('fullscreen', False):
            self.showFullScreen()
        else:
            if 'size' in kwargs:
                width, height = kwargs.pop('size')
            else:
                width = kwargs.pop('width', self.default_size[0])
                height = kwargs.pop('height', self.default_size[1])
            x, y = kwargs.pop('position', self.default_position)
            self.setGeometry(x, y, width, height)
        self.render_hint = kwargs.pop('render_hint', QPainter.Antialiasing)
        self.background = kwargs.pop('background', QBrush(Qt.black))

    # --- Painter Object Management ---
    def add_painter_object(self, obj: PainterObject):
        self.painter_objects.append(obj)

    def add_painter_objects(self, objs: Sequence[PainterObject]):
        [self.add_painter_object(obj) for obj in objs]

    def remove_painter_object(self, obj: PainterObject):
        try: self.painter_objects.remove(obj)
        except ValueError: pass
    
    def remove_painter_objects(self, objs: Sequence[PainterObject]):
        [self.remove_painter_object(obj) for obj in objs]

    # --- Paint Handling ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(self.render_hint)
        painter.setBrush(self.background)
        painter.drawRect(self.rect())
        for obj in self.painter_objects:
            obj.paint(painter)
        painter.end()

    # --- Key Handling ---
    def keyPress(self, event): pass
    def keyRelease(self, event): pass

    def keyPressEvent(self, event): self.keyPress(event)
    def keyReleaseEvent(self, event): self.keyRelease(event)

    # --- Mouse Event Handling ---
    def mousePress(self, event): pass
    def mouseRelease(self, event): pass
    def mouseDouble(self, event): pass
    def mouseMove(self, event): pass
    def mouseEnter(self, event): pass
    def mouseLeave(self, event): pass
    def mouseWheel(self, event): pass

    def mousePressEvent(self, event): self.mousePress(event)
    def mouseReleaseEvent(self, event): self.mouseRelease(event)
    def mouseDoubleClickEvent(self, event): self.mouseDouble(event)
    def mouseMoveEvent(self, event): self.mouseMove(event)
    def enterEvent(self, event): self.mouseEnter(event)
    def leaveEvent(self, event): self.mouseLeave(event)
    def wheelEvent(self, event): self.mouseWheel(event)
