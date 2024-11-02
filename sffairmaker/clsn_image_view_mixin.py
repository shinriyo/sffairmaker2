# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from sffairmaker.image_view import (
    DraggingType,
    drawRect,
)
from sffairmaker import const
from collections import namedtuple
from operator import methodcaller

RectIndex = namedtuple("RectIndex", "clsn index")
ClsnData = namedtuple("ClsnData", "clsn change color")



class DraggingClsnBase(DraggingType):
    def __init__(self, p, dragType, dragTarget):
        self._dragType = dragType
        self._dragTarget = dragTarget
        DraggingType.__init__(self, p)
    
    exec(def_qgetter("dragType", "dragTarget"))
    def type(self):
        return "clsn"
    
    def mousePress(self, event):
        self._setClsnDragCursor(self.dragType())
    
    def mouseMove(self, event):
        self.update()

class DraggingClsn(DraggingClsnBase):
    def mouseRelease(self, event):
        k, i = self.dragTarget()
        c = self._clsns()[k]
        rect = self._draggedRect(c.clsn[i], self.dragType(), self._dragDelta())
        c.change(c.clsn.replace_at(i, rect))
    
class DraggingClsnGroup(DraggingClsnBase):
    def dragType(self):
        return "move"
    
    def mouseRelease(self, event):
        delta = self._moveDelta()
        k, i = self.dragTarget()
        c = self._clsns()[k]
        c.change(c.clsn.move_all(delta))


class DraggingAppendingClsn(DraggingType):
    def type(self):
        return "appendingClsn"
    
    def mousePress(self, event):
        self.setCursor(Qt.ArrowCursor)
    
    def mouseMove(self, event):
        self.update()

    def mouseRelease(self, event):
        rc = self._dataRect(self._dragRect())
        c = self._clsns()[self.appendingClsn()]
        clsn1 = c.clsn.append(rc)
        c.change(clsn1)
        
        self.setRectFocus(RectIndex(self.appendingClsn(), len(clsn1) - 1))


class ClsnImageViewMixin:
    ClsnDragErrorMargin = 5


    def __init__(self, parent=None):
        self._rectFocus = None
        self._appendingClsn = None
        self._drawingClsn = frozenset()
    
    exec(def_qgetter("drawingClsn", "appendingClsn", "clsnDragMode"))
    exec(def_update_accessor("rectFocus"))
    
    def _draggedRect(self, rect, dragType, delta):
        delta /= self.scale()
        rect = QRect(rect)
        if dragType == "move":
            rect.translate(delta.x(), delta.y())
        else:
            if "top" in dragType:
                rect.setTop(rect.top() + delta.y())
            if "bottom" in dragType:
                rect.setBottom(rect.bottom() + delta.y())
            if "left" in dragType:
                rect.setLeft(rect.left() + delta.x())
            if "right" in dragType:
                rect.setRight(rect.right() + delta.x())
        return rect
    
    def _deleteRect(self):
        if self._rectFocus is None:return
        index = self._rectsCanBeFocused().index(self._rectFocus)
        
        c = self._clsns()[self._rectFocus.clsn]
        c.change(c.clsn.remove_at(self._rectFocus.index))
        
        rects = self._rectsCanBeFocused()
        if not rects:
            self._rectFocus = None
        else:
            self._rectFocus = rects[index % len(rects)]
        self.update()
    
    def dragTypeToCursor(self, dragType):
        cursor = {
            ("top", "left"):Qt.SizeFDiagCursor,
            ("bottom", "right"):Qt.SizeFDiagCursor,
            ("bottom", "left"):Qt.SizeBDiagCursor,
            ("top", "right"):Qt.SizeBDiagCursor,
            "move":Qt.SizeAllCursor,
        }[dragType]
        return cursor
    
    def _setClsnDragCursor(self, dragType):
        self.setCursor(self.dragTypeToCursor(dragType))
    
    def _rectUnderCursor(self, pos):
        dragClsns = []
        for rectIndex in self._rectsCanBeFocused():
            k, i = rectIndex
            c = self._clsns()[k]
            rect = c.clsn[i]
            drc = self._screenRect(rect) #�\�����Rect
            
            #���Ɋ܂߂邩�ǂ����́A�덷���邢�͋��e�͈�
            #Rect�̊O���ւ̌덷
            errorMargin = self.ClsnDragErrorMargin * self.scale()
            
            #Rect�̓����ւ̌덷�i�c�Ӂj
            vErrorMargin = min(errorMargin, abs(drc.height()) // 3)
            
            #Rect�̓����ւ̌덷�i���Ӂj
            hErrorMargin = min(errorMargin, abs(drc.width()) // 3)
            
            on = {} #�㉺���E�̊e�ӂ̉�������ɂ��邩�H
            on["left"]   = -errorMargin <= pos.x()-drc.left()  <= hErrorMargin
            on["right"]  = -hErrorMargin<= pos.x()-drc.right() <= errorMargin
            on["top"]    = -errorMargin <= pos.y()-drc.top()   <= vErrorMargin
            on["bottom"] = -vErrorMargin<= pos.y()-drc.bottom()<= errorMargin
            
            import itertools
            for v, h in itertools.product(["top", "bottom"], ["left", "right"]):
                if on[v] and on[h]:
                    diff = abs(pos.x() - methodcaller(h)(drc)) + \
                           abs(pos.y() - methodcaller(v)(drc))
                    dragType = (v, h)
                    dragClsns.append((diff, dragType, rectIndex))
            
            #Rect�̏�ɂ��邩
            onRect = drc.left() - errorMargin <= pos.x() <= drc.right() + errorMargin and \
                     drc.top() - errorMargin <= pos.y() <= drc.bottom() + errorMargin
            
            if onRect and len([v for v in on.values() if v]) == 1:
                diffs = [
                    drc.left() - pos.x(),
                    drc.right() - pos.x(),
                    drc.top() - pos.y(),
                    drc.bottom() - pos.y(),
                ]
                diff = min(abs(d) for d in diffs)
                dragClsns.append((diff, "move", rectIndex))
        
        if not dragClsns:
            return None
        
        def sortKey(item):
            diff, dragType, _ = item
            i = [("top",    "left"), 
                 ("bottom", "right"),
                 ("top",    "right"),
                 ("bottom", "left"), 
                 "move"
            ].index(dragType)
            return diff, i
        
        dragClsns.sort(key=sortKey)
        _, dragType, rectIndex = dragClsns[0]
        return dragType, rectIndex
    
    def _rectsCanBeFocused(self):
        rects = []
        for k, c in self._clsns().items():
            if k not in self._drawingClsn:continue
            for i in xrange(len(c.clsn)):
                rects.append(RectIndex(k, i))
        return rects
    
    def _focusNextRect(self):
        rects = self._rectsCanBeFocused()
        try:
            i = rects.index(self._rectFocus)
        except ValueError:
            self.setRectFocus(rects[0] if rects else None)
        else:
            self.setRectFocus(rects[(i + 1) % len(rects)])
    
    @mySetter()
    def setAppendingClsn(self):
        self._killDragging()
        if self._appendingClsn is not None:
            self.setDrawingAllClsn()
        self.update()
    
    @mySetter()
    def setDrawingClsn(self):
        self.update()
    
    def setDrawingAClsn(self, key, value):
        if value:
            self.setDrawingClsn(self.drawingClsn() | set([key]))
        else:
            self.setDrawingClsn(self.drawingClsn() - set([key]))
    
    def _drawClsnRect(self, painter, event):
        def drawClsn(key, clsn, color):
            if key not in self.drawingClsn():
                return
            
            if self.appendingClsn():
                if key == self.appendingClsn():
                    color.setAlpha(255)
                else:
                    color.setAlpha(64)
            else:
                color.setAlpha(192)
            
            with savePainter(painter):
                painter.translate(self.axis())
                
                rects = []
                for i, rc in enumerate(clsn):
                    rectIndex = RectIndex(key, i)
                    if self._isRectBeingDragged(rectIndex):
                        rects.append((0, i, rc))
                    elif self._rectFocus == rectIndex:
                        rects.append((1, i, rc))
                    else:
                        rects.append((2, i, rc))
                rects.sort(reverse=True)
                for t, _, rc in rects:
                    if t == 0:
                        rc = self._draggedRect(rc, self._dragging.dragType(), self._dragDelta())
                        drawRect(painter, rc, color, self.scale())
                    elif t == 1:
                        drawRect(painter, rc, color, self.scale())
                    else:
                        drawRect(painter, rc, color.light(), self.scale())
        
        for key, c in self._displayClsns().items():
            if key != self.appendingClsn():
                drawClsn(key, c.clsn, c.color)
        if self.appendingClsn() is not None:
            c = self._displayClsns()[self.appendingClsn()]
            drawClsn(self.appendingClsn(), c.clsn, c.color)
        

    #��������virtual���\�b�h
    def _clsns(self):
        raise NotImplementedError
    
    def _isRectBeingDragged(self, rectIndex):
        raise NotImplementedError
    
    def _displayClsns(self):
        return self._clsns()
    
    def setDrawingAllClsn(self, v=True):
        raise NotImplementedError
        
