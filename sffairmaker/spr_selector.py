#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.model_null import NullSpr

    
def safe_int(s):
    try:
        return int(s)
    except StandardError:
        return None

class IntComboBox(QComboBox):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        
        self.setEditable(True)
        self.lineEdit().setValidator(QIntValidator())
        self._value = None
        self.editTextChanged.connect(self._onTextChanged)
        
        sh = self.sizeHint()
        self.setMinimumSize(sh.width(), sh.height())
        
    exec def_qgetter("value")
    
    def _onTextChanged(self, t):
        v = safe_int(t)
        if v == self._value:
            return
        self._value = v
        self.valueChanged.emit(self._value)
    
    @emitSetter
    def setValue(self):
        if self.value() is None:
            self.setEditText("")
        else:
            self.setEditText(str(self.value()))
    
    def setItems(self, items):
        items = [int(i) for i in items]
        
        with blockSignals(self):
            self.clear()
            for i in items:
                self.addItem(unicode(i))
        if items:
            self.setValue(items[0])
        else:
            self.setValue(None)
    
    def sizeHint(self):
        fm = self.fontMetrics()
        
        w = max(fm.width(str(i)*4) for i in xrange(10))
        h = max(fm.height(), 14) + 2
        
        sh = QSize(w, h)
##        // add style and strut values
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        return QSize(self.style().sizeFromContents(QStyle.CT_ComboBox, opt, sh, self))
        
    
class GroupIndexSelector(QWidget):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None, sprs=[]):
        QWidget.__init__(self, parent)
        
        if isinstance(sprs, (list, tuple)):
            self._sprs = []
            self.setSprs = self._setSelfSprs
            self.sprs = self._selfSprs
        else:
            self._xmodel = sprs
            self.sprs = self._xmodelSprs
            def updateItems():
                self._groupbox.setItems(self.groups())
                self._indexbox.setItems(self.indexes(self._groupbox.value()))
            self._xmodel.sff().updated.connect(updateItems)
        
        self._groupbox = IntComboBox()
        self._indexbox = IntComboBox()
        
        self._groupbox.setItems(self.groups())
        self._indexbox.setItems(self.indexes(self._groupbox.value()))
        
        self._groupbox.valueChanged.connect(self.setGroup)
        self._indexbox.valueChanged.connect(self.setIndex)
        
        self._group = self._groupbox.value()
        self._index = self._indexbox.value()
        
        #レイアウトここから
        self.setLayout(hBoxLayout(
            (self._groupbox, 1),
            (self._indexbox, 1),
        ))
    
    exec def_qgetter("group", "index")
    
    exec def_sff()
    
    def _xmodelSprs(self):
        return self.sff().sprs()
    
    def _selfSprs(self):
        return self._sprs
    
    def _setSelfSprs(self, sprs):
        self._sprs = sprs
        self._groupbox.setItems(self.groups())
        self._indexbox.setItems(self.indexes(self._groupbox.value()))
    
    def groups(self):
        sprs = self.sprs()
        return sorted(set(spr.group() for spr in sprs))
    
    def indexes(self, group):
        sprs = (spr for spr in self.sprs() if group == spr.group())
        return sorted(set(spr.index() for spr in sprs))
    
    def _getValue(self, group, index):
        if group is None or index is None:
            return None
        return (group, index)
    
    def setGroup(self, group):
        if self._group == group:
            return
        
        old = self._getValue(self._group, self._index)
        
        self._group = group
        self._groupbox.setValue(group)
        
        with blockSignals(self._indexbox):
            self._indexbox.setItems(self.indexes(group))
        self._index = self._indexbox.value()
        
        new = self._getValue(self._group, self._index)
        if old != new:
            self.valueChanged.emit(new)
        
    def setIndex(self, index):
        if self._index == index:
            return
        
        old = self._getValue(self._group, self._index)
        
        self._index = index
        self._indexbox.setValue(index)
        
        new = self._getValue(self._group, self._index)
        if old != new:
            self.valueChanged.emit(new)
    
    def value(self):
        return self._getValue(self._group, self._index)
    
    def setValue(self, v):
        if self.value() == v:
            return
        
        if v is None:
            group = index = None
        else:
            group, index = v
        
        with blockSignals(self):
            # blockSignals(self)というのは、# self.valueChanged.emitのみ抑制したいから
            # self._indexboxのitemsは更新されて欲しい
            self._groupbox.setValue(group)
            self._indexbox.setValue(index)
        
        self.valueChanged.emit(v)


class SprSelector(GroupIndexSelector):
    sprChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, *a, **kw):
        GroupIndexSelector.__init__(self, *a, **kw)
        self._spr = self.sprByValue(self.value())
        self.valueChanged.connect(lambda v:self.setSpr(self.sprByValue(v)))
    
    exec def_qgetter("spr")
    exec def_sff()
    
    def sprByValue(self, v):
        if v is not None:
            return self.sff().sprByIndex(*v)
        else:
            return NullSpr()
    
    def setSpr(self, spr):
        if self.spr() == spr:
            return False
        
        self._spr = spr
        if not self._spr.isValid():
            if self.sprByValue(self.value()).isValid():
                self.setValue(None)
        else:
            self.setValue(self.spr().group_index())
        
        self.sprChanged.emit(spr)

class SffGroupIndexSelector(GroupIndexSelector):
    def __init__(self, parent=None, xmodel=None):
        if xmodel is None:
            import sffairmaker.model
            xmodel = sffairmaker.model.Model()
        GroupIndexSelector.__init__(self, parent, sprs=xmodel)

class SffSprSelector(SprSelector):
    def __init__(self, parent=None, xmodel=None):
        if xmodel is None:
            import sffairmaker.model
            xmodel = sffairmaker.model.Model()
        SprSelector.__init__(self, parent, sprs=xmodel)


def main():
    pass

if "__main__" == __name__:
    main()