# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type

import copy
from enum import Enum
from sffairmaker.qutil import *
from sffairmaker import const


from sffairmaker.image_view import (
    AbstractImageViewCore,
    createImageViewClass,
    DraggingType,
    DraggingView,
    dataPos,
)

from sffairmaker import model
from sffairmaker.model_null import NullSpr

class NoDragging(DraggingType):
    def mousePress(self, event):
        self.setCursor(Qt.ArrowCursor)
    
    def mouseMove(self, event):
        ##M    : �\���ʒu�ړ�
        ##S-C-L: �\���ʒu�ړ�
        ##S-L  : �摜�̈ړ��iPos�ύX�j
        ##C-L  : �������Ȃ�
        ##L    : �摜����i�摜�̈ړ��E�����E�F�̏����j
        ctrl  = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        
        if shift and ctrl:
            self.setCursor(Qt.ArrowCursor)
        elif shift:
            self.setCursor(Qt.SizeAllCursor)
        elif ctrl:
            self.setCursor(Qt.ArrowCursor)
        else:
            if self.imageOpMode() != ImageOpMode.Pos:
                self.setCursor(Qt.ArrowCursor)
            else:
                self.setCursor(Qt.SizeAllCursor)
        self.update()

    def mouseRelease(self, event):
        pass
    
    def type(self):
        return "no"
    
    def __nonzero__(self):
        return False


ImageOpMode = Enum("Pos", "EraseRects", "EraseRectsColors", "CropRectColors")

class DraggingPos(DraggingType):
    def type(self):
        return "pos"
    
    def mousePress(self, event):
        self.setCursor(Qt.SizeAllCursor)

    def mouseMove(self, event):
        self.update()
    
    def mouseRelease(self, event):
        pos = self.spr().pos() - self._moveDelta()
        self.spr().change(x=pos.x(), y=pos.y())

class DraggingImageOpBase(DraggingType):
    def type(self):
        return "image"
    
    def mousePress(self, event):
        self.setCursor(Qt.ArrowCursor)

    def mouseMove(self, event):
        self.update()


class DraggingEraseRects(DraggingImageOpBase):
    def mouseRelease(self, event):
        if not self.spr().isValid():
            return
        self.spr().eraseRects([self._dataRect(self._dragRect())])
        
class DraggingEraseRectsColors(DraggingImageOpBase):
    def mouseRelease(self, event):
        if not self.spr().isValid():
            return
        
        self.spr().eraseRectsColors([self._dataRect(self._dragRect())])


class SffImageViewCore(AbstractImageViewCore):
    sprChanged = pyqtSignal("PyQt_PyObject")
    imageOpModeChanged = pyqtSignal("PyQt_PyObject")
    colorNumberSelected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        AbstractImageViewCore.__init__(self, parent)
        self._spr  = NullSpr()
        
        self._imageOpMode = ImageOpMode.Pos
        self.setAcceptDrops(True)
        
        syncAttrTo(self, self.xview(),
            "sprDisplayMode",
            "actColorTable",
            "bgImage",
            "bgImageDelta",
            "bgImageTile",
        )
        self.sff().updated.connect(self.update)
        
        
    exec def_qgetter("spr", "imageOpMode")
    exec def_xview()
    exec def_xmodel()
    
    @emitSetter
    def setSpr(self):
        self.update()
    
    @emitSetter
    def setImageOpMode(self):
        self.update()
    
    def _noDragging(self):
        return NoDragging(self)
    
    def _draggingType(self, event, pos):
        ##M    : �\���ʒu�ړ�
        ##S-C-L: �\���ʒu�ړ�
        ##S-L  : �摜�̈ړ��iPos�ύX�j
        ##C-L  : �������Ȃ�
        ##L    : �摜����i�摜�̈ړ��E�����E�F�̏����j
        
        left  = event.buttons() & Qt.LeftButton
        mid   = event.buttons() & Qt.MidButton
        ctrl  = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        
        if mid:
            return DraggingView(self)
        elif shift and ctrl and left:
            return DraggingView(self)
        elif shift and left:
            return DraggingPos(self)
        elif ctrl and left:
            return self._noDragging()
        elif left:
            classes = {
                ImageOpMode.Pos: DraggingPos,
                ImageOpMode.EraseRects: DraggingEraseRects,
                ImageOpMode.EraseRectsColors: DraggingEraseRectsColors,
            }
            return classes[self.imageOpMode()](self)
        else:
            return self._noDragging()
    
    def sprPos(self, pos):
        return dataPos(pos - self.axis(), self.scale())
    
    def imagePos(self, pos):
        return dataPos(pos - self.axis(), self.scale()) + self.spr().pos()
    
    def mousePressEvent(self, event):
        AbstractImageViewCore.mousePressEvent(self, event)
        
        if not self.spr().isValid():
            return
        left  = event.buttons() & Qt.LeftButton
        ctrl  = event.modifiers() & Qt.ControlModifier
        if ctrl and left:
            imgPos = self.imagePos(event.pos())
            im = self.spr().image()
            if im.rect().contains(imgPos):
                index = im.pixelIndex(imgPos)
                self.colorNumberSelected.emit(index)
    
    def mouseMoveEvent(self, event):
        AbstractImageViewCore.mouseMoveEvent(self, event)
        
        if not self.spr().isValid():
            return
        
        strs = []
        strs.append("({0[0]}, {0[1]})".format(pxy(self.sprPos(event.pos()))))
        
        imgPos = self.imagePos(event.pos())
        im = self.spr().image()
        if im.rect().contains(imgPos):
            index = im.pixelIndex(imgPos)
            t = "pixel=({0[0]}, {0[1]}):{1}".format(pxy(imgPos), index)
            strs.append(t)
        self.xview().statusBarShowMessage(", ".join(strs))
    
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setBackground(self.bgColor())
        painter.eraseRect(event.rect())
        
        self._drawBg(painter, event)
        self._drawOnion(painter, event)
        
        if self._gridOption.grid:
            self._drawGrid(painter, event)
        
        self._drawSpr(painter, event)
        
        if self._gridOption.axis:
            self._drawAxis(painter, event)
        
        if self._dragging.type() == "image":
            self._drawDraggingRect(painter, event)
        
        
    def _drawRelativeOnion(self, painter):
        if not self.spr().isValid(): return
        
        for index in xrange(self.spr().index() - self.onion().count(), self.spr().index()):
            if index < 0:continue
            self._drawASpr(painter,
                self.xmodel().sff().sprByIndex(self.spr().group(), index),
                QPoint(0, 0),
                128,
                frame=False
            )
        
    def _drawSpr(self, painter, event):
        if not self.spr().isValid(): return
        
        if self._dragging.type() == "pos":
            delta = QPoint(self._dragDelta() / self.scale())
        else:
            delta = QPoint(0, 0)
        
        self._drawASpr(painter, self.spr(), delta, 255)
        
    
SffImageView = createImageViewClass(SffImageViewCore)

def main():
    app = QApplication([])
    
    v = SffImageView()
    m = v.xmodel()
    v.setSpr(m.sff().sprs()[0])
    
    w = QMainWindow()
    v._core._statusBar = w.statusBar()
    w.setCentralWidget(v)
    w.resize(600, 400)
    w.show()
    
    app.exec_()
    
    
if __name__ == "__main__":
    main()