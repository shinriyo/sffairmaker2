# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

from sffairmaker.clsn import Clsn
from sffairmaker.model_null import NullSpr

from sffairmaker.image_view import (
    DraggingType,
    AbstractImageViewCore,
    createImageViewClass,
    DraggingView,
)
from sffairmaker.clsn_image_view_mixin import (
    ClsnData,
    RectIndex,
    DraggingClsn,
    DraggingAppendingClsn,
    ClsnImageViewMixin,
)

from collections import OrderedDict


class NoDragging(DraggingType):
    def mousePress(self, event):
        pass
    
    def mouseMove(self, event):
        ##M    : 表示位置移動
        ##S-C-L: 表示位置移動
        ##S-L  : 画像の移動（Pos変更）
        ##C-L  : CLSNの移動・リサイズ
        ##L    : CLSN追加 or 画像の移動
        ctrl  = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        
        if shift and ctrl:
            self.setCursor(Qt.ArrowCursor)
        elif shift:
            self.setCursor(Qt.SizeAllCursor)
        elif ctrl:
            c = self._rectUnderCursor(self._dragCurrentPos)
            if not c:
                self.setCursor(Qt.ArrowCursor)
            else:
                dragType, target = c
                self.setRectFocus(target)
                self._setClsnDragCursor(dragType)
        else:
            if self.appendingClsn() is not None:
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

from enum import Enum
# ClsnKeys = Enum("_0")
ClsnKeys = Enum('ClsnKeys', ['_0'])  # リストで囲む必要がある

class ClsnImageViewCore(AbstractImageViewCore, ClsnImageViewMixin):
    clsnChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, parent=None):
        AbstractImageViewCore.__init__(self, parent=None)
        ClsnImageViewMixin.__init__(self)
        
        self.setAppendingClsn(ClsnKeys._0)
        
        self._clsn = Clsn()
        self._spr = NullSpr()
        
        self.setupShortcut()
        
    exec(def_qgetter("clsn", "spr"))

    def setupShortcut(self):
        focusNextRect = QAction(self)
        focusNextRect.setShortcut("TAB")
        focusNextRect.triggered.connect(self._focusNextRect)
        
        deleteRect = QAction(self)
        deleteRect.setShortcut("Delete")
        deleteRect.triggered.connect(self._deleteRect)
        
        self.addActions([focusNextRect, deleteRect])
        
    @mySetter(emit=True)
    def setClsn(self):
        self.update()
    
    @mySetter(emit=False, signal=("updated", "update"))
    def setSpr(self):
        self.update()
    
    def _drawSpr(self, painter, event):
        if not self.spr().isValid(): return
        delta = QPoint(0, 0)
        self._drawASpr(painter, self.spr(), delta, 255)
    
    #ここからvirtualメソッド
    def _clsns(self):
        o = OrderedDict()
        o[ClsnKeys._0] = ClsnData(
            self._clsn,
            self.setClsn,
            QColor("#666"),
        )
        return o
    
    def _noDragging(self):
        return NoDragging(self)

    def _isRectBeingDragged(self, rectIndex):
        if self._dragging.type() != "clsn":
            return False
        return rectIndex == self._dragging.dragTarget()

    def _draggingType(self, event, pos):
        ##M    : 表示位置移動
        ##S-C-L: 表示位置移動
        ##C-L  : CLSNの移動・リサイズ
        ##L    : CLSN追加
        
        left  = event.buttons() & Qt.LeftButton
        mid   = event.buttons() & Qt.MidButton
        ctrl  = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        if mid:
            return DraggingView(self)
        elif shift and ctrl and left:
            return DraggingView(self)
        elif ctrl and left:
            c = self._rectUnderCursor(pos)
            if c:
                return DraggingClsn(self, *c)
            else:
                return self._noDragging()
        elif left:
            return DraggingAppendingClsn(self)
        else:
            return self._noDragging()
    
    
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setBackground(self.bgColor())
        painter.eraseRect(event.rect())
        
        if self._gridOption.grid:
            self._drawGrid(painter, event)
        
        self._drawSpr(painter, event)
        
        if self._gridOption.axis:
            self._drawAxis(painter, event)
        
        if self._dragging.type() == "appendingClsn":
            self._drawDraggingRect(painter, event)
        
        self._drawClsnRect(painter, event)
    
    def setDrawingAllClsn(self, v=True):
        if v:
            self.setDrawingClsn(frozenset(ClsnKeys._values))
        else:
            self.setDrawingClsn(frozenset())
    

ClsnImageView = createImageViewClass(ClsnImageViewCore)

def main():
    from sffairmaker.model import Model
    app = QApplication([])
    Model().sff().open(debugDataDir() + "\\kfm.sff")
    
    sprs = Model().sff().sprs()
    from operator import methodcaller
    sprs.sort(key=methodcaller("group_index"))
    
    v = ClsnImageView()
    v.setSpr(sprs[0])
    v.show()
    
    from pprint import pprint
    v.clsnChanged.connect(lambda clsn:pprint(map(rcvtx, clsn)))
    
    app.exec_()
    

if "__main__" == __name__:
    main()