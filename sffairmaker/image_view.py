#encoding:shift-jis
from __future__ import division, with_statement, print_function
__metaclass__ = type

from sffairmaker.qutil import *
from sffairmaker import const
from sffairmaker.onion import Onion, OnionType
from sffairmaker import spr_display
from sffairmaker import image_op

import re
import math
from abc import ABCMeta, abstractmethod
from enum import Enum
import math
from itertools import count, product



def minmax(x, y):
    if x < y:
        return x, y
    else:
        return y, x

def dataPos(p, scale):
    return QPoint(p.x()//scale, p.y()//scale)

def screenPos(p, scale):
    return p*scale

def dataRect(rc, scale):
    """
    screen上のRect -> SFFやAIRなどのdata内でのRect
    
    dataのピクセル(0, 0)は、screen上でQRect(0, 0, scale, scale)として描画される。
    
    この関数では、screen上でrcが少しでも被るようなdataのピクセルは、
    dataRectに含まれるとする。
    
    >>> dataRect(QRect(QPoint(0, 0), QPoint(0, 0)), 1)
    PyQt4.QtCore.QRect(0, 0, 1, 1)
    >>> dataRect(QRect(QPoint(1, 1), QPoint(1, 1)), 5)
    PyQt4.QtCore.QRect(0, 0, 1, 1)
    >>> dataRect(QRect(QPoint(-1, -1), QPoint(-1, -1)), 5)
    PyQt4.QtCore.QRect(-1, -1, 1, 1)
    >>> dataRect(QRect(QPoint(-1, -1), QPoint(11, 12)), 5)
    PyQt4.QtCore.QRect(-1, -1, 4, 4)
    """
    rc = rc.normalized()
    return QRect(dataPos(rc.topLeft(), scale), dataPos(rc.bottomRight(), scale))
    
def screenRect(rc, scale):
    """
    SFFやAIRなどのdata内でのRect -> screen上のRect
    >>> rc = QRect(0, 0, 1, 1)
    >>> s = 5
    >>> dataRect(screenRect(rc, s), s)
    PyQt4.QtCore.QRect(0, 0, 1, 1)
    """
    rc = rc.normalized()
    return QRect(rc.topLeft()*scale, rc.size()*scale)



def drawRect(painter, rc, color, scale=1):
    scale = float(scale)
    rc = rc.normalized()
    if rc.size() == QSize(0, 0):
        return
    with savePainter(painter):
        if scale > 1:
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            
            if rc.size() == QSize(1, 1):
                painter.drawRect(rc.left()*scale, rc.top()*scale, scale, scale)
            elif rc.width() > 1 and rc.height() == 1:
                painter.drawRect(rc.left()*scale, rc.top()*scale, scale*rc.width(), scale)
            elif rc.width() == 1 and rc.height() > 1:
                painter.drawRect(rc.left()*scale, rc.top()*scale, scale, scale*rc.height())
            else:
                painter.drawRect(rc.left()*scale, rc.top()*scale, scale, scale*rc.height())
                painter.drawRect(rc.right()*scale, rc.top()*scale, scale, scale*rc.height())
                
                painter.drawRect((rc.left()+1)*scale, rc.top()*scale, (rc.width()-2)*scale, scale)
                painter.drawRect((rc.left()+1)*scale, rc.bottom()*scale, (rc.width()-2)*scale, scale)
        else:
            painter.setPen(color)
            painter.setBrush(Qt.NoBrush)
            r = QRect(rc.topLeft()*scale, rc.size()*scale)
            painter.drawRect(r)
    


class DraggingType:
    __metaclass__ = ABCMeta
    def __init__(self, p):
        self.p = p
    
    def __getattr__(self, name):
        return getattr(self.p, name)
    
    @abstractmethod
    def mousePress(self, event):
        pass
    @abstractmethod
    def mouseMove(self, event):
        pass
    @abstractmethod
    def mouseRelease(self, event):
        pass


class NoDragging(DraggingType):
    def mousePress(self, event):
        self.setCursor(Qt.ArrowCursor)
    
    def mouseMove(self, event):
        self.setCursor(Qt.ArrowCursor)
    
    def mouseRelease(self, event):
        pass
    
    def type(self):
        return "no"
    
    def __nonzero__(self):
        return False
        

class DraggingView(DraggingType):
    def type(self):
        return "view"
    
    def mousePress(self, event):
        self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMove(self, event):
        if self._prevMovePos is not None:
            delta = event.pos() - self._prevMovePos
            self.moveAxis(delta)
    
    def mouseRelease(self, event):
        pass

def tilling(left, right, size, leftOverflow=False):
    if size == 0: return
    
    if not leftOverflow:
        ileft = math.ceil(left / size)
    else:
        ileft = math.floor(left / size)
    
    iright = math.ceil(right / size)
    for i in xrange(int(ileft), int(iright)):
        yield i, i * size
    

def gridLines(rect, size):
    for i, x in tilling(rect.left(), rect.right(), size):
        yield i, QPointF(x, rect.top()), QPointF(x, rect.bottom())
    for i, y in tilling(rect.top(), rect.bottom(), size):
        yield i, QPointF(rect.left(), y), QPointF(rect.right(), y)


class AbstractImageViewCore(QWidget):
##    ImageViewの文字通り核。
##    AbstractImageViewCoreのサブクラスをcreateImageViewClassに渡し、
##    ImageViewのサブクラスを作る。
    
##    Drag&Drop を追加したいときは、
##    mousePressEventなどをオーバーライドするのではなく、
##    _draggingTypeをオーバーライドする。
##    _draggingTypeはマウスの（axisに基づいた内部的な）位置とmouseEventを元に、
##    DraggingTypeのサブクラスを返す。
    
##    DraggingTypeはmousePress mouseMove mouseRelease時にしたい何かを実装したクラスである。
    
    
    axisDeltaChanged = pyqtSignal(QPoint)
    AxisOrigin = Enum("Center", "TopLeft")
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._bgColor = QColor("#FFF")
        self._axisColor = QColor("#000")
        self._grid1Color= QColor("#880")
        self._grid2Color= QColor("#080")
        self._grid1Size = 10
        self._grid2Size = 10
        self._drawGrid1 = True
        self._drawGrid2 = True
        self._gridXor = True
        self._minimumGridSize = 10
        self._transparent = True
        self._actColorTable = None
        self._onion = Onion(0)
        self._sprDisplayMode = spr_display.Mode.Act
        self._actColorTable = None
        
        self._bgImage = None
        self._bgImageDelta = QPoint(0, 0)
        self._bgImageTile = False
        
        self._scale = 1
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        
        self._axisDelta = QPoint(0, 0)
        self._axisOrigin = self.AxisOrigin.Center
        
        self._prevMovePos = None
        self._dragStartPos = self._dragCurrentPos = None
        self._dragging = self._noDragging()
        
        self._gridOption = const.GridOption(const.ImageZOrder.Middle, True, True)
        
        self._gridLinesMemo = {}

    exec def_update_accessor(*"""
        axisOrigin
        gridOption
        sprDisplayMode
        actColorTable
        bgImage
        bgImageDelta
        bgImageTile
    """.split())
    
    exec def_qgetter("axisDelta")

    def axis(self):
        origin = {
            self.AxisOrigin.Center: self.rect().center(),
            self.AxisOrigin.TopLeft: self.rect().topLeft(),
        }[self.axisOrigin()]
        
        return origin - self.axisDelta()
    
    @emitSetter
    def setAxisDelta(self):
        self.update()
    
    def resetAxisDelta(self):
        self.setAxisDelta(QPoint(0, 0))
    
    def moveAxis(self, delta):
        self.setAxisDelta(self.axisDelta() - delta)
    
    def setAxisDeltaX(self, x):
        self.setAxisDelta(QPoint(x, self.axisDelta().y()))
    
    def setAxisDeltaY(self, y):
        self.setAxisDelta(QPoint(self.axisDelta().x(), y))
    
    exec def_update_accessor(*"""
        bgColor
        axisColor
        grid1Color
        grid2Color
        grid1Size
        grid2Size
        drawGrid1
        drawGrid2
        gridXor
        minimumGridSize
        scale
        transparent
        colorTable
        onion
    """.split())
    
    def setColors(self, colors):
        self.setBgColor(colors.bg)
        self.setAxisColor(colors.axis)
        self.setGrid1Color(colors.grid1)
        self.setGrid2Color(colors.grid2)
    
    def colors(self):
        return dict(
            bg=self.bgColor(),
            axis=self.axisColor(),
            grid1=self.grid1Color(),
            grid2=self.grid2Color(),
        )
    
    exec def_sff()
    
    def _noDragging(self):
        return NoDragging(self)
    
    def _killDragging(self):
        self._dragging = self._noDragging()
        self.update()
        
    def mousePressEvent(self, event):
        if self._dragging:
            return
        pos = event.pos() - self.axis()
        self._dragging = self._draggingType(event, pos)
        
        self._dragStartPos = self._dragCurrentPos = pos
        self._dragging.mousePress(event)
    
    def mouseMoveEvent(self, event):
        self._dragging.mouseMove(event)
        self._prevMovePos = event.pos()
        self._dragCurrentPos = event.pos() - self.axis()
        
    def mouseReleaseEvent(self, event):
        self._prevMovePos = event.pos()
        self._dragCurrentPos = event.pos() - self.axis()
        if (event.button() in [Qt.LeftButton, Qt.MidButton] and \
            not event.buttons() & Qt.LeftButton and 
            not event.buttons() & Qt.MidButton
        ): 
            self._dragging.mouseRelease(event)
            self._killDragging()
            self.setCursor(Qt.ArrowCursor)
            self.update()
    
    def _gridLines(self, rect, size):
        key = (rect.left(), rect.top(), rect.right(), rect.bottom(), size)
        if key not in self._gridLinesMemo:
            self._gridLinesMemo[key] = list(gridLines(rect, size))
        return self._gridLinesMemo[key]
        
    def _drawGrid(self, painter, event):
        with savePainter(painter):
            painter.translate(self.axis())
            rect = event.rect().translated(QPoint(-self.axis()))
            
            c1 = colorXor(self.grid1Color(), self.bgColor())
            c2 = colorXor(self.grid2Color(), self.bgColor())

            size1 = self._grid1Size*self.scale()
            size2 = self._grid1Size*self._grid2Size*self.scale()
            
            lines1 = []
            lines2 = []
            lines1_append = lines1.append
            lines2_append = lines2.append
            if size2 < self.minimumGridSize():
                return
            elif size1 < self.minimumGridSize():
                painter.setPen(c2)
                for _, from_ ,to in self._gridLines(rect, size2):
                    lines1_append(QLineF(from_, to))
            else:
                for i, from_ ,to in self._gridLines(rect, size1):
                    if i % self.grid2Size() == 0:
                        lines1_append(QLineF(from_, to))
                    else:
                        lines2_append(QLineF(from_, to))
            painter.setPen(c2)
            painter.drawLines(lines2)
            
            painter.setPen(c1)
            painter.drawLines(lines1)

    def _drawAxis(self, painter, event):
        with savePainter(painter):
            painter.setPen(self.axisColor())
            painter.drawLine(self.rect().left(), self.axis().y(),
                             self.rect().right(), self.axis().y())
            painter.drawLine(self.axis().x(), self.rect().top(),
                             self.axis().x(), self.rect().bottom())

    def _drawBg(self, painter, event, delta=QPoint(0, 0)):
        if self.bgImage() is None or self.bgImage().isNull(): return
        
        delta = QPoint(delta)
        delta += self.bgImageDelta()
        im = self.bgImage()
        start = self.axis() - delta
        if not self.bgImageTile():
            painter.drawImage(start, im)
        else:
            rc = event.rect().translated(-start)
            
            xpos = [x for i, x in tilling(rc.left(), rc.right(), im.width(), True)]
            ypos = [y for i, y in tilling(rc.top(), rc.bottom(), im.height(), True)]
            for x, y in product(xpos, ypos):
                p = QPoint(x, y)
                painter.drawImage(p + start, im)
    
    def _drawImage(self, painter, image, pos, density=255, frame=True):
        if image is None or image.isNull():
            return QRect()
        
        with savePainter(painter):
            painter.translate(self.axis())
            pos *= float(self.scale())
            if self.scale() != 1:
                image = image.scaled(image.size()*self.scale())
            
            colorTable = image.colorTable()
            if self.transparent():
                colorTable[0] = colorTable[0] & 0x00FFFFFF
            
            if density < 255:
                for i, v in enumerate(colorTable):
                    if i == 0:
                        continue
                    colorTable[i] = qRgba(qRed(v), qGreen(v), qBlue(v), density)
            
            image = QImage(image)
            image.setColorTable(colorTable)
            
            if frame:
                painter.setPen(QColor(0x80, 0x80, 0x80))
                painter.drawRect(image.rect().translated(QPoint(pos)))
            painter.drawImage(pos, image)
    
    def _drawASpr(self, painter, spr, delta, density, frame=True, hv=(False, False)):
        if not spr.isValid(): return
        
        image = spr_display.image(
            spr,
            self.actColorTable(),
            self.sprDisplayMode()
        )
        if image.isNull():
            return
        
        pos = -spr.pos() + delta
        image, pos = image_op.mirrored(image, pos, spr.pos(), *hv)
        
        self._drawImage(painter, image, pos, density, frame=frame)
    
    def _drawFixedOnion(self, painter):
        self._drawASpr(painter,
            self.sff().sprByIndex(*self.onion().group_index()),
            QPoint(0, 0),
            128,
            frame=False,
        )
    
    def _drawOnion(self, painter, event):
        if self.onion().type() == OnionType.Fixed:
            self._drawFixedOnion(painter)
        else:
            self._drawRelativeOnion(painter)

    def _drawDraggingRect(self, painter, event):
        with savePainter(painter):
            painter.translate(self.axis())
            painter.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
            drawRect(painter, self._dataRect(self._dragRect()), QColor("#FFF"), self.scale())
    
    def _screenRect(self, rc):
        return screenRect(rc, self.scale())
    
    def _dataRect(self, rc):
        return dataRect(rc, self.scale())
    
    def _dragRect(self):
        rc = QRect(self._dragStartPos, self._dragCurrentPos)
        return rc.normalized()
    
    def _dragDelta(self):
        if self._dragging.type() != "no":
            return self._dragCurrentPos - self._dragStartPos
        else:
            return QPoint()
            
    def _moveDelta(self):
        return QPoint(self._dragDelta() / self.scale())
    
    # ここからvirtualメソッド
    def _draggingType(self, event, pos):
        raise NotImplementedError
    
    def _drawRelativeOnion(self, painter):
        raise NotImplementedError
    
    def paintEvent(self):
        raise NotImplementedError
    
    

class ImageView(QWidget):
    """
    描画関係を拡張したいとき、このクラスは直接継承するべきではない。
    AbstractImageViewを継承し、createImageViewClassでサブクラスを作るべし。
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._core = self._createCoreWidget(self)
        
        self._x1 = QScrollBar(Qt.Horizontal, self)
        self._x2 = QScrollBar(Qt.Horizontal, self)
        self._x1.setMinimum(-200)
        self._x1.setMaximum(200)
        self._x2.setMinimum(-200)
        self._x2.setMaximum(200)
        
        self._y1 = QScrollBar(Qt.Vertical, self)
        self._y2 = QScrollBar(Qt.Vertical, self)
        self._y1.setMinimum(-200)
        self._y1.setMaximum(200)
        self._y2.setMinimum(-200)
        self._y2.setMaximum(200)
        
        syncAttr(self._x1, self._x2, "value")
        syncAttr(self._y1, self._y2, "value")
        
        self._y1.valueChanged.connect(self.setAxisDeltaY)
        self.axisDeltaChanged.connect(lambda c:self._y1.setValue(c.y()))
        self._x1.valueChanged.connect(self.setAxisDeltaX)
        self.axisDeltaChanged.connect(lambda c:self._x1.setValue(c.x()))
        
        self._y1.setValue(0)
        self._x1.setValue(0)
        
        self._x1.setCursor(Qt.ArrowCursor)
        self._x2.setCursor(Qt.ArrowCursor)
        self._y1.setCursor(Qt.ArrowCursor)
        self._y2.setCursor(Qt.ArrowCursor)
        
        layout = QGridLayout()
        layout.addWidget(self._x1, 0, 0, 1, 3)
        layout.addWidget(self._x2, 2, 0, 1, 3)
        layout.addWidget(self._y1, 1, 0)
        layout.addWidget(self._y2, 1, 2)
        layout.addWidget(self._core, 1, 1)
        
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)
        
        self.setLayout(layout)
        
    def _createCoreWidget(self, parent=None):
        raise NotImplementedError
    
    def __getattr__(self, name):
        return getattr(self._core, name)


def createImageViewClass(coreClass):
    class ImageViewSubClass(ImageView):
        def _createCoreWidget(self, parent):
            return coreClass(parent)
    m = re.match("(.*)Core", coreClass.__name__)
    if m:
        ImageViewSubClass.__name__ = m.group(1)
    return ImageViewSubClass




def main():
    pass
    
if __name__ == "__main__":
    main()