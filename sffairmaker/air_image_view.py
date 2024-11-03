# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type

from collections import OrderedDict
from enum import Enum
from collections import namedtuple

from sffairmaker.model_null import NullElm
from sffairmaker import const
from sffairmaker.qutil import *
from sffairmaker.play_button import PlayButton

from sffairmaker.image_view import (
    AbstractImageViewCore,
    createImageViewClass,
    DraggingType,
    DraggingView,
    drawRect,
)

from sffairmaker.clsn_image_view_mixin import (
    ClsnImageViewMixin,
    ClsnData,
    RectIndex,
    DraggingClsnBase,
    DraggingClsn,
    DraggingClsnGroup,
    DraggingAppendingClsn,
)


class ClsnDragMode(Enum):
    Normal = "Normal"
    Group = "Group"
    All = "All"
    AllPos = "AllPos"

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
                if self.clsnDragMode() != ClsnDragMode.Normal:
                    self.setCursor(Qt.SizeAllCursor)
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


class DraggingClsn(DraggingClsn):
    def clsnDragMode(self):
        return ClsnDragMode.Normal

class DraggingClsnGroup(DraggingClsnGroup):
    def clsnDragMode(self):
        return ClsnDragMode.Group
    
class DraggingClsnAll(DraggingClsnBase):
    def dragType(self):
        return "move"
    
    def clsnDragMode(self):
        return ClsnDragMode.All
    
    def mouseRelease(self, event):
        if not self.elm().isValid():
            return
        self.elm().moveAllClsn(self._moveDelta())
        
class DraggingClsnAllPos(DraggingClsnBase):
    def dragType(self):
        return "move"
    
    def clsnDragMode(self):
        return ClsnDragMode.AllPos
    
    def mouseRelease(self, event):
        if not self.elm().isValid():
            return
        self.elm().moveAllClsnPos(self._moveDelta())

class DraggingPos(DraggingType):
    def type(self):
        return "pos"
    
    def mousePress(self, event):
        self.setCursor(Qt.SizeAllCursor)

    def mouseMove(self, event):
        self.update()
    
    def mouseRelease(self, event):
        if not self.elm().isValid():
            return
        
        pos = self.elm().pos() + self._moveDelta()
        self.elm().change(x=pos.x(), y=pos.y())



class AirImageViewCore(AbstractImageViewCore, ClsnImageViewMixin):
    elmChanged = pyqtSignal("PyQt_PyObject")
    clsnDragModeChanged = pyqtSignal("PyQt_PyObject")
    appendingClsnChanged = pyqtSignal("PyQt_PyObject")
    drawingClsnChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, parent=None, model=None):
        AbstractImageViewCore.__init__(self, parent)
        ClsnImageViewMixin.__init__(self)
        
        self._xmodel = model
        self._elm = NullElm()
        self._playAnim = PlayAnim(self)
        self.playAnimChanged = self._playAnim.playAnimChanged
        self._playAnim.repaint.connect(self.update)
        
        self._clsnDragMode = ClsnDragMode.Normal
        
        self.xmodel().sff().updated.connect(self.update)
        self._elm.updated.connect(self.update)
        
        syncAttrTo(self, self.xview(),
            "sprDisplayMode",
            "actColorTable",
            "bgImage",
            "bgImageDelta",
            "bgImageTile",
        )
        
        self.update()
    
    def setupShortcut(self):
        endAppendingClsn = QAction(self)
        endAppendingClsn.setShortcut("ESCAPE")
        endAppendingClsn.triggered.connect(self.setAppendingClsn, None)
        endAppendingClsn.triggered.connect(self.update)
        
        focusNextRect = QAction(self)
        focusNextRect.setShortcut("TAB")
        focusNextRect.triggered.connect(self._focusNextRect)
        
        deleteRect = QAction(self)
        deleteRect.setShortcut("Delete")
        deleteRect.triggered.connect(self._deleteRect)
        
        self.addActions([endAppendingClsn, focusNextRect, deleteRect])
    
    exec(def_xview())
    exec(def_xmodel())

    exec(def_qgetter("clsnDragMode"))
    exec(def_qgetter("elm"))

    
    def setAppendingClsn(self, *a, **kw):
        if ClsnImageViewMixin.setAppendingClsn(self, *a, **kw): 
            self.appendingClsnChanged.emit(self.appendingClsn())
    
    def setDrawingClsn(self, *a, **kw):
        if ClsnImageViewMixin.setDrawingClsn(self, *a, **kw): 
            self.drawingClsnChanged.emit(self.drawingClsn())

    @mySetter(emit=True, signal=("updated", "update"))
    def setElm(self):
        self.stopAnim()
        self.update()
    
    @emitSetter
    def setClsnDragMode(self):
        pass
    
    def event(self, event):
        if event.type()==QEvent.KeyPress and event.key()==Qt.Key_Tab:
            self.keyPressEvent(event)
            return True
        return QWidget.event(self, event)
    
    def toggleAnim(self, v):
        if v:
            self.startAnim()
        else:
            self.stopAnim()
       
    def startAnim(self):
        self._playAnim.start(self.elm().anim())
    
    def stopAnim(self):
        self._playAnim.stop()
        self.update()

    def _currentElm(self):
        if self._playAnim.playing():
            return self._playAnim.elm()
        else:
            return self.elm()
    
    def _drawRelativeOnion(self, painter):
        elm = self._currentElm()
        if not elm.isValid(): return
        
        elms = elm.anim().elms()
        indexInAnim = elms.index(elm)
        for k in range(indexInAnim - self.onion().count(), indexInAnim):
            if k < 0: continue
            self._drawAElm(painter, elms[k], QPoint(0, 0), 128, frame=False)
        
    def _drawAElm(self, painter, elm, delta, density, frame=True):
        if not elm.isValid(): return
        
        spr = elm.spr()
        if not spr.isValid(): return
        
        self._drawASpr(painter, spr, delta + elm.pos(), density, frame=False, hv=elm.hv())
    
    def _drawElm(self, painter, event=None):
        elm = self._currentElm()
        if not elm.isValid(): return
        
        elms = elm.anim().elms()
        if self._dragging.type() == "pos" or \
           (self._dragging.type() == "clsn" and self._dragging.clsnDragMode() == ClsnDragMode.AllPos):
            delta = QPoint(self._dragDelta() / self.scale())
        else:
            delta = QPoint(0, 0)
        self._drawAElm(painter, elm, delta, 255)
    
    # ここからvirtualメソッド
    def _clsns(self, elm=None):
        if elm is None:
            elm = self.elm()
        
        o = OrderedDict()
        for k, color in zip(const.ClsnKeys._values, "#F00 #00F #880 #088".split()):
            color = QColor(color)
            
            def change(clsn, k=k):
                if not elm.isValid():
                    return
                self.elm().change(**{k.name:clsn})
            if not elm.isValid():
                continue
            
            o[k] = ClsnData(
                clsn=getattr(elm, k.name)(),
                change=change,
                color=color,
            )
        return o
    
    def _displayClsns(self):
        return self._clsns(self._currentElm())
    
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setBackground(self.bgColor())
        painter.eraseRect(event.rect())
        
        self._drawBg(painter, event)
        self._drawOnion(painter, event)
        
        if self._gridOption.grid:
            self._drawGrid(painter, event)
        
        self._drawElm(painter, event)
        
        if self._gridOption.axis:
            self._drawAxis(painter, event)
        
        self._drawClsnRect(painter, event)
        
        if self._dragging.type() == "appendingClsn":
            self._drawDraggingRect(painter, event)
    
    def _noDragging(self):
        return NoDragging(self)
    
    def _draggingType(self, event, pos):
        ##M    : �\���ʒu�ړ�
        ##S-C-L: �\���ʒu�ړ�
        ##S-L  : �摜�̈ړ��iPos�ύX�j
        ##C-L  : CLSN�̈ړ��E���T�C�Y
        ##L    : CLSN�ǉ� or �摜�̈ړ�
        
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
                draggingClsnTypes = {
                    ClsnDragMode.Normal: DraggingClsn,
                    ClsnDragMode.Group: DraggingClsnGroup,
                    ClsnDragMode.All: DraggingClsnAll,
                    ClsnDragMode.AllPos:DraggingClsnAllPos,
                }
                t = draggingClsnTypes[self.clsnDragMode()]
                return t(self, *c)
            else:
                return self._noDragging()
        elif shift and left:
            return DraggingPos(self)
        elif left:
            if self.appendingClsn():
                return DraggingAppendingClsn(self)
            else:
                return DraggingPos(self)
        else:
            return self._noDragging()

    def _isRectBeingDragged(self, rectIndex):
        if self._dragging.type() != "clsn":
            return False
        elif self._dragging.clsnDragMode() == ClsnDragMode.Normal:
            return rectIndex == self._dragging.dragTarget()
        elif self._dragging.clsnDragMode() == ClsnDragMode.Group:
            return rectIndex.clsn == self._dragging.dragTarget().clsn
        else:
            return True
    
    def setDrawingAllClsn(self, v=True):
        if v:
            self.setDrawingClsn(frozenset(const.ClsnKeys._values))
        else:
            self.setDrawingClsn(frozenset())
            
class PlayAnim(QObject):
    repaint = pyqtSignal()
    playAnimChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._timer = QTimer()
        self._timer.timeout.connect(self._onTimeOut)
        self._anim = None
    
    exec(def_qgetter("animTime", "elm", "anim"))
    
    def start(self, anim, interval=16):
        if not self._timer.isActive():
            self._anim = anim
            self._elmTimeLine = self._anim.timeLine()
            self._timer.setInterval(interval)
            self._timer.start()
            
            self._elm = next(self._elmTimeLine)
            self.playAnimChanged.emit(True)
            self.repaint.emit()
    
    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
            self.playAnimChanged.emit(False)
    
    def playing(self):
        return self._timer.isActive()
    
    def _onTimeOut(self):
        prevElm = self.elm()
        self._elm = next(self._elmTimeLine)
        if prevElm != self.elm():
            self.repaint.emit()


class CurElmLabel(QLabel):
    def __init__(self, parent=None):
        QLabel.__init__(self, parent=parent)
        self._elm = NullElm()
        self.setAutoFillBackground(True)
        self._updateText()
    
    def setElm(self, elm):
        if self._elm == elm:
            return
        self._elm = elm
        self._updateText()
    
    def _updateText(self):
        if not self._elm.isValid(): return
        
        curElm = 1 + self._elm.anim().elms().index(self._elm)
        allElm = len(self._elm.anim().elms())
        
        startTime = self._elm.startTime()
        allTime = self._elm.anim().allTime()
        
        t = "{0:0{2}}/{1}".format(curElm, allElm, len(str(allElm)))
        t += " {0:0{2}}/{1}".format(startTime, allTime, len(str(allTime)))
        
        if self._elm.loopStart():
            t += " LoopStart"
        
        self.setText(t)

class AirImageViewCore2(AirImageViewCore):
    def __init__(self, *a, **kw):
        AirImageViewCore.__init__(self, *a, **kw)
        
        play  = PlayButton(self)
        play.setChecked(False)
        self.playAnimChanged.connect(lambda v:play.setChecked(bool(v)))
        play.toggled.connect(self.toggleAnim)
        
        curElm = CurElmLabel()
        self.elmChanged.connect(curElm.setElm)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを設定
        
        flag = Qt.AlignLeft | Qt.AlignTop
        layout.addWidget(play, 0, flag)
        layout.addWidget(curElm, 0, flag)
        layout.addStretch(1)
        self.setLayout(layout)
        
AirImageView = createImageViewClass(AirImageViewCore2)

def main():
    pass
    
if __name__ == "__main__":
    main()