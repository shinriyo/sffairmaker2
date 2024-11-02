# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type
from sffairmaker.qutil import *

class SliderPositionWidget(QLabel):
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        
        self._slider = None
        self._value = 0
        self._range = (0, 0)
    
    def _setRange(self, minimum, maximum):
        v = (minimum, maximum)
        if self._range == v:return
        self._range = v
        self._updateText()
    
    def _setValue(self, v):
        if self._value == v:return
        self._value = v
        self._updateText()
    
    def setSlider(self, v):
        if self._slider is not None:
            self._slider.rangeChanged.disconnect(self._setRange)
            self._slider.valueChanged.disconnect(self._setValue)
        self._slider = v
        self._slider.rangeChanged.connect(self._setRange)
        self._slider.valueChanged.connect(self._setValue)
        
        self._setValue(v.value())
        self._setRange(v.minimum(), v.maximum())
        self._updateText()
    
    def _updateText(self):
        mini, maxi = self._range
        length = maxi - mini + 1
        pos = self._value - mini + 1
        self.setText("{0:0{2}}/{1}".format(pos, length, len(str(length))))
        
def main():
    app = QApplication([])
    
    scr = QScrollBar(Qt.Horizontal)
    scr.setMinimum(-5)
    scr.setMaximum(5)
    
    p = SliderPositionWidget()
    p.setSlider(scr)
    
    mini = QSpinBox()
    mini.setRange(-10, 0)
    mini.setValue(scr.minimum())
    mini.valueChanged.connect(scr.setMinimum)
    
    maxi = QSpinBox()
    maxi.setRange(0, 10)
    maxi.setValue(scr.maximum())
    maxi.valueChanged.connect(scr.setMaximum)

    
    w = QWidget()
    L = QGridLayout()
    
    L.addWidget(scr, 0, 0)
    L.addWidget(p, 0, 1)
    L.addWidget(mini, 1, 0)
    L.addWidget(maxi, 1, 1)
    
    w.setLayout(L)
    w.show()
    
    app.exec_()
    
    
if "__main__" == __name__:
    main()