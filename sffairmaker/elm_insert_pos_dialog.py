#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker import model

class InsertPosWidget(QWidget):
    _spacingSize = 10
    clicked = pyqtSignal()
    
    def __init__(self, items, parent=None):
        QWidget.__init__(self, parent)
        self._items = list(items)
        
        self._insertPos = 0
        L = QHBoxLayout()
        L.setMargin(0)
        L.setSpacing(0)
        
        L.addSpacing(self._spacingSize)
        for item in self._items:
            L.addWidget(item)
            L.addSpacing(self._spacingSize)
        self.setLayout(L)
        
        for item in self._items:
            item.setMouseTracking(True)
            for child in item.children():
                if hasattr(child, "setMouseTracking"):
                    child.setMouseTracking(True)
        self.setMouseTracking(True)
    
    exec def_qgetter("insertPos")
    
    def setInsertPos(self, v):
        v = max(min(v, len(self._items)), 0)
        if self.insertPos() == v:return
        self._insertPos = v
        self.update()
    
    def _itemRects(self):
        for item in self._items:
            yield item.rect().translated(item.pos())
    
    def _itemCenters(self):
        for item in self._items:
            yield item.rect().translated(item.pos()).center().x()
    
    def _setInsertPosFromMousePos(self, x):
        centers = list(self._itemCenters())
        for i, (left, right) in enumerate(zip([0] + centers, centers)):
            if left <= x < right:
                self.setInsertPos(i)
                return
        else:
            self.setInsertPos(len(self._items))
        
    def mouseMoveEvent(self, evt):
        self._setInsertPosFromMousePos(evt.pos().x())
    
    def mousePressEvent(self, evt):
        self._setInsertPosFromMousePos(evt.pos().x())
        if evt.button() == Qt.LeftButton:
            self.clicked.emit()
    
    def cursorRect(self):
        rects = list(self._itemRects())
        
        if 0 < self.insertPos():
            x = rects[self.insertPos() - 1].right() + 1
        elif self.insertPos() == 0:
            x = 0
        
        h = max(r.height() for r in rects)
        return QRect(x, 0, self._spacingSize, h)
    
    def paintEvent(self, evt):
        painter = QStylePainter(self)
        color = self.palette().color(QPalette.Highlight)
        painter.fillRect(self.cursorRect(), color)
    
class InsertPosDialog(QDialog):
    def __init__(self, items, caption=None, parent=None):
        QDialog.__init__(self, parent)
        if caption is not None:
            self.setWindowTitle(caption)
        
        w = InsertPosWidget(items, self)
        self.setInsertPos = w.setInsertPos
        self.insertPos = w.insertPos
        w.clicked.connect(self.accept)
        
        buttons = dialogButtons(self)
        
        area = QScrollArea(self)
        area.setWidget(w)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        def event(evt):
            if evt.type() == QEvent.KeyPress and evt.key() in [Qt.Key_Up, Qt.Key_Down]:
                if evt.key() == Qt.Key_Up:
                    w.setInsertPos(w.insertPos() - 1)
                else:
                    w.setInsertPos(w.insertPos() + 1)
                r = w.cursorRect()
                area.ensureVisible(r.left(), r.top())
                area.ensureVisible(r.right(), r.bottom())
                return True
            return QScrollArea.event(area, evt)
        area.event = event
        
        L = QVBoxLayout()
        L.setMargin(0)
        L.setSpacing(0)
        L.addWidget(area, 1)
        L.addWidget(buttons)
        self.setLayout(L)
    
    @classmethod
    def get(cls, *a, **kw):
        self = cls(*a, **kw)
        if self.exec_():
            return self.insertPos()
        else:
            return None

from sffairmaker.air_edit import ElmImageLabel
class Thumb(QFrame):
    def __init__(self, elm, parent=None):
        QFrame.__init__(self, parent)
        
        self.setAutoFillBackground(True)
        self.setStyleSheet("Thumb{border:1px solid black;}")
        
        L = QGridLayout()
        L.setMargin(0)
        L.setSpacing(0)
        
        label = ElmImageLabel(self)
        label.setElm(elm)
        L.addWidget(label, 0, 0, 2, 3, Qt.AlignCenter)
        
        def textLabel(x):
            label = QLabel()
            label.setText(unicode(x))
            label.setAutoFillBackground(True)
            return label
        
        if elm.loopStart():
            L.addWidget(textLabel("LoopStart"), 0, 0)
        
        t = "{0} - {1}".format(elm.group(), elm.index())
        L.addWidget(textLabel(t), 1, 1, Qt.AlignBottom | Qt.AlignHCenter)
        self.setLayout(L)

class ElmInsertPosDialog(InsertPosDialog):
    def __init__(self, anim, *a, **kw):
        items = [Thumb(e) for e in anim.elms()]
        InsertPosDialog.__init__(self, items, *a, **kw)
        self.setWindowTitle(u"コマの挿入先")
        
def main():
    pass
    
    
if "__main__" == __name__:
    main()