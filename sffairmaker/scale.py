#encoding:shift-jis
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from fractions import Fraction
import numbers

class ScaleObject(QObject):
    valueChanged = pyqtSignal(Fraction)
    indexChanged = pyqtSignal(int)
    maximumChanged = pyqtSignal(int)
    minimumChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._index = 1
        self._maximum = 8
        self._minimum = -2
    
    exec def_qgetter("index", "maximum", "minimum")
    exec def_alias("scale", "value")
    exec def_alias("setScale", "setValue")
    exec def_alias("scaleChanged", "valueChanged")
    
    def setMaximum(self, v):
        v = int(v)
        if v < self._minimum:
            v = self._minimum
        if self._maximum == v:
            return
        self._maximum = v
        self.maximumChanged.emit(self._maximum)
        if self._index > self._maximum:
            self.setIndex(self._maximum)
    
    def setMinimum(self, v):
        v = int(v)
        if self._maximum < v:
            v = self._maximum
        if self._minimum == v:
            return
        self._minimum = v
        self.minimumChanged.emit(self._minimum)
        if self._index < self._minimum:
            self.setIndex(self._minimum)
    
    def zoomIn(self):
        self.setIndex(self.index() + 1)
    
    def zoomOut(self):
        self.setIndex(self.index() - 1)
    
    def zoomReset(self):
        self.setIndex(1)
    
    def value(self):
        if self._index <= 0:
            return Fraction(1, 2 - self._index)
        else:
            return Fraction(self._index)
    
    def setIndex(self, v):
        v = min(self._maximum, max(self._minimum, int(v)))
        if v == self._index:return
        
        self._index = v
        self.valueChanged.emit(self.value())
        self.indexChanged.emit(self.index())
        
    
class ScaleWidget(QAbstractSpinBox):
    valueChanged = pyqtSignal(Fraction)
    indexChanged = pyqtSignal(int)
    maximumChanged = pyqtSignal(int)
    minimumChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        QAbstractSpinBox.__init__(self, parent)
        self._scaleObject = ScaleObject()
        
        self.lineEdit().setReadOnly(True)
        self._setText(self.value())
        self._scaleObject.valueChanged.connect(self._setText)
        
        relaySignal(self, self._scaleObject, 
            "valueChanged", "indexChanged",
            "maximumChanged", "minimumChanged")
    
    def __getattr__(self, name):
        return getattr(self._scaleObject, name)
        
    def _setText(self, value):
        self.lineEdit().setText(unicode(value))
    
    def stepBy(self, steps):
        self.setIndex(self.index() + steps)
    
    def stepEnabled(self):
        e = QAbstractSpinBox.StepNone
        if self.index() < self._maximum:
            e |= QAbstractSpinBox.StepUpEnabled
        if self._minimum < self.index():
            e |= QAbstractSpinBox.StepDownEnabled
        return e
    
def main():
    pass
    
if __name__ == "__main__":
    main()