# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

from collections import namedtuple, defaultdict
import copy
import cPickle as pickle

import sip

Colors = namedtuple("Colors", "bg axis grid1 grid2")
ColorIndexes = namedtuple("ColorIndexes", "bg axis grid1 grid2")

class ColorIndexes(ColorIndexes):
    def toVariant(self):
        return QVariant(pickle.dumps(self))
    
    @classmethod
    def fromVariant(cls, v):
        s = str(v.toString())
        try:
            return cls(*pickle.loads(s))
        except Exception:
            raise ValueError
        
class ColorsHolder(QObject):
    colorsChanged = pyqtSignal(Colors)
    colorIndexesChanged = pyqtSignal(ColorIndexes)
    colorListChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._colorList = [QColor(s) for s in "#fff #000 #3C3 #33C #C33 #883 #838 #388".split()]
        self._colorIndexes = ColorIndexes(bg=0, axis=1, grid1=2, grid2=3)
    
    exec def_qgetter("colorList", "colorIndexes")
    
    def colorList(self):
        return copy.deepcopy(self._colorList)
    
    def setColorList(self, v):
        if self._colorList == v:
            return
        
        oldColors = self.colors()
        oldIndexes = indexes = self._colorIndexes
        self._colorList = copy.deepcopy(v)
        
        for k, v in self._colorIndexes._asdict().items():
            if v < 0:
                indexes = indexes._replace(**{k:0})
            elif len(self._colorList) <= v:
                indexes = indexes._replace(**{k:len(self._colorList) - 1})
        
        self.colorListChanged.emit(copy.deepcopy(self._colorList))
        
        self._colorIndexes = indexes
        if oldIndexes != indexes:
            self.colorIndexesChanged.emit(indexes)
        
        if oldColors != self.colors():
            self.colorsChanged.emit(self.colors())
    
    def setColorIndexes(self, v):
        if self._colorIndexes == v:
            return
        
        oldColors = self.colors()
        self._colorIndexes = v
        self.colorIndexesChanged.emit(self._colorIndexes)
        if oldColors != self.colors():
            self.colorsChanged.emit(self.colors())
    
    def addColorIndexes(self, f, i):
        self.setColorIndexes(self.colorIndexes()._replace(**{f:i}))
    
    def colors(self):
        return Colors._make(list_get(self._colorList, index, QColor())
                     for index in self._colorIndexes)
    
class Rect(QWidget):
    selected = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._color = QColor()
        self._selection = frozenset()
        self.setFixedSize(30, 30)
    
    exec def_update_accessor("color", "selection")
    
    def mousePressEvent(self, event):
        left= event.button() == Qt.LeftButton
        mid = event.button() == Qt.MidButton
        right=event.button() == Qt.RightButton
        ctrl  = bool(event.modifiers() & Qt.ControlModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        
        if ctrl and left:
            self.selected.emit("grid1")
        elif shift and left:
            self.selected.emit("grid2")
        elif left:
            self.selected.emit("bg")
        elif right:
            self.selected.emit("axis")
    
    def sizeHint(self):
        return QSize(30, 30)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color())
        
        textColor = colorXor(self.color(), QColor(0xD0, 0x80, 0x80))
        painter.setPen(QPen(textColor))
        
        r = self.rect()
        c = r.center()
        d = {
            "bg":   ("B",  r.x(), c.y()),
            "axis" :("A",  c.x(), c.y()),
            "grid1" :("G",  r.x(), r.bottom()),
            "grid2":("G2", c.x(), r.bottom()),
        }
        for t, (text, x, y) in d.iteritems():
            if t in self._selection:
                painter.drawText(QPoint(x+1, y-2), text)


class RectGroup(QObject):
    selected = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._colorList = []
        self._rects = []
    
    exec def_qgetter("rects")
    
    def setColorList(self, colorList):
        self._colorList = list(colorList)
        for i in xrange(len(colorList), len(self._rects)):
            r = self._rects.pop(-1)
            sip.delete(r)
        
        for i in xrange(len(self._rects), len(colorList)):
            r = Rect(self.parent())
            r.selected.connect(lambda f,i=i:self.selected.emit((f, i)))
            self._rects.append(r)
        
        for i, c in enumerate(colorList):
            self._rects[i].setColor(c)
        
    def setColorIndexes(self, indexes):
        sel = defaultdict(set)
        for k, v in indexes._asdict().items():
            sel[v].add(k)
        for i, r in enumerate(self._rects):
            r.setSelection(sel[i])


class ColorsSelector(QWidget):
    colorsChanged = pyqtSignal(Colors)
    colorIndexesChanged = pyqtSignal(ColorIndexes)
    colorListChanged = pyqtSignal(list)
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._colors = ColorsHolder()
        self._rectGroup = RectGroup(self)
        
        relaySignal(self, self._colors,
            "colorIndexesChanged",
            "colorListChanged",
            "colorsChanged"
        )
        
        def setColorList(colorList):
            self._rectGroup.setColorList(colorList)
            
            if not self.layout():
                self.setLayout(QGridLayout())
            
            for i, rc in enumerate(self._rectGroup.rects()):
                rc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                self.layout().addWidget(rc, i // 2, i % 2)
        self._colors.colorListChanged.connect(setColorList)
        
        self._colors.colorIndexesChanged.connect(
            self._rectGroup.setColorIndexes)
        
        @self._rectGroup.selected.connect
        def addColorIndexes(x):
            f, i = x
            self._colors.addColorIndexes(f, i)
        
        setColorList(self._colors.colorList())
        self._rectGroup.setColorIndexes(self._colors.colorIndexes())
        

    exec def_delegate("_colors", *"""
        colorList
        colorIndexes
        setColorList
        setColorIndexes
        colors
        """.split())


def main1():
    from random import randrange
    app = QApplication([])
    w = QWidget()
    c = ColorSelector()
    
    @commandButton(u"�ǉ�")
    def add():
        colorList = list(c.colorList())
        colorList.append(QColor(randrange(256), randrange(256), randrange(256)))
        c.setColorList(colorList)
    
    @commandButton(u"�폜")
    def remove():
        colorList = c.colorList()
        if colorList:
            colorList.pop(-1)
        c.setColorList(colorList)
    
    w.setLayout(hBoxLayout(
        c,
        add,
        remove,
    ))
    
    w.show()
    app.exec_()
    

def main():
    pass

if "__main__" == __name__:
    main()