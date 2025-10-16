
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF
from abc import ABC, abstractmethod

class PainterObject(ABC):
    def __init__(self, **kwargs):
        brushColor = kwargs.get("brushColor", Qt.white)
        penColor = kwargs.get("penColor", Qt.white)
        self._isPen = True
        self._isBrush = True
        self.set_color(brushColor, penColor)

    def isInside(self, x, y):
        return False

    def set_isPen(self, isPen): self._isPen = isPen
    def set_isBrush(self, isBrush): self._isBrush = isBrush

    def set_color(self, brushColor, penColor):
        self.brushColor = brushColor
        self.penColor = penColor
        if not hasattr(self, "_brush"): self._brush = QBrush(brushColor) 
        else: self._brush.setColor(brushColor)
        if not hasattr(self, "_pen"): self._pen = QPen(penColor) 
        else: self._pen.setColor(penColor)

    def set_line_width(self, width: float):
        self._pen.setWidthF(width)

    def set_line_cap(self, capStyle):
        self._pen.setCapStyle(capStyle)

    def painter_brush_and_pen(self, painter: QPainter):
        if self._isBrush: painter.setBrush(self._brush)
        else: painter.setBrush(QBrush())
        if self._isPen: painter.setPen(self._pen)
        else: painter.setPen(Qt.NoPen)

    @abstractmethod
    def paint(self, painter: QPainter):
        self.painter_brush_and_pen(painter)


class PRectangle(PainterObject):
    def __init__(self, x, y, width, height, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def isInside(self, x, y):
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )
    
    def paint(self, painter: QPainter):
        super().paint(painter)

        x = int(self.x)
        y = int(self.y)
        w = int(self.width)
        h = int(self.height)
        
        painter.drawRect(x, y, w, h)


class PLine(PainterObject):
    def __init__(self, x1, y1, x2, y2, **kwargs):
        super().__init__(**kwargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.set_line_width(1)
    
    def paint(self, painter: QPainter):
        super().paint(painter)

        x1 = int(self.x1)
        y1 = int(self.y1)
        x2 = int(self.x2)
        y2 = int(self.y2)
        
        painter.drawLine(x1, y1, x2, y2)

class PPolygon(PainterObject):
    def __init__(self, xs, ys, **kwargs):
        super().__init__(**kwargs)
        if len(xs) != len(ys):
            raise ValueError("xs and ys must have the same length")
        
        self.points = []
        for i in range(len(xs)):
            self.points.append(QPointF(xs[i], ys[i]))

    def paint(self, painter: QPainter):
        super().paint(painter)
        painter.drawPolygon(QPolygonF(self.points))


class PCircle(PainterObject):
    def __init__(self, x, y, r, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.r = r

    def isInside(self, x, y):
        if (
            self.x + self.r <= x <= self.x - self.r or 
            self.y + self.r <= y <= self.y - self.r 
        ): return False
        dx = self.x - x
        dy = self.y - y
        dist = (dx**2 + dy**2) ** 0.5
        return dist <= self.r

    def paint(self, painter: QPainter):
        super().paint(painter)

        x = int(self.x - self.r)
        y = int(self.y - self.r)
        s = int(self.r*2)
        painter.drawEllipse(x, y, s, s)

class PText(PainterObject):
    def __init__(self, x, y, text, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.text = text

        font = kwargs.pop('font', None)
        if font != None:
            self.font = font
        else:
            fontFamily = kwargs.pop('font_family', 'Arial')
            fontSize = kwargs.pop('font_size', 12)
            self.font = QFont(fontFamily, fontSize)

    def paint(self, painter):
        super().paint(painter)

        x = int(self.x)
        y = int(self.y)

        painter.setFont(self.font)

        painter.drawText(x, y, self.text)
