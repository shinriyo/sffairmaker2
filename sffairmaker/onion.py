# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from enum import Enum
from collections import namedtuple

from sffairmaker import model
from sffairmaker.sff_jump_dialog import SffJumpButton
from sffairmaker.spr_selector import SffGroupIndexSelector


OnionType = Enum("Relative", "Fixed")

class NeMixin:
    def __nq__(self, other):
        return not (self==other)


class Onion(NeMixin):
    def __init__(self, count):
        self._count = count
    
    exec def_qgetter("count")
    
    def __repr__(self):
        return "{0.__class__.__name__}({0._count})".format(self)
        
    @classmethod
    def type(cls):
        return OnionType.Relative
    
    def __eq__(self, other):
        return isinstance(other, Onion) and \
               self.count() == other.count()
    
    __hash__ = None
    
class FixedOnion(NeMixin):
    def __init__(self, group_index):
        self._group_index = group_index
    
    exec def_qgetter("group_index")
    
    def __repr__(self):
        return "{0.__class__.__name__}({0._group_index})".format(self)
    
    @classmethod
    def type(cls):
        return OnionType.Fixed
    
    def __eq__(self, other):
        return isinstance(other, FixedOnion) and \
               self.group_index() == other.group_index()
    
    __hash__ = None

class GroupIndexWidget(QWidget):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._selector = SffGroupIndexSelector(parent=self)
        self._jump = SffJumpButton(u"�Q��", parent=self)
        
        @self._jump.sprChanged.connect
        def onJump(spr):
            if spr.isValid():
                self._selector.setValue(spr.group_index())
            else:
                self._selector.setValue(None)
        
        @self._selector.valueChanged.connect
        def onValueChanged(value):
            if value is None:
                self._jump.setSpr(model.Spr.Null())
            else:
                self._jump.setSpr(self.xmodel().sff().sprByIndex(*value))
        
        relaySignal(self, self._selector, "valueChanged")
        
        self.setLayout(vBoxLayout(
            self._selector,
            self._jump,
        ))
    
    def xmodel(self):
        return model.Model()
        
    exec def_delegate("_selector", "setValue", "value")


class OnionSlider(QWidget):
    valueChanged = pyqtSignal(int)
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._slider = QSlider(Qt.Vertical, parent=self)
        self._slider.setRange(0, 3)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        self._slider.setTracking(True)
        
        @self._slider.valueChanged.connect
        def displaySliderValue(x):
            pos = self._slider.mapToGlobal(self._slider.rect().topRight())
            QToolTip.showText(pos, str(x), self._slider)
        
        relaySignal(self, self._slider, "valueChanged")
        
        L = QGridLayout()
        L.addWidget(self._slider, 0, 0, 2, 1)
        L.addWidget(QLabel(u"3"), 0, 1, Qt.AlignTop)
        L.addWidget(QLabel(u"0"), 1, 1, Qt.AlignBottom)
        self.setLayout(L)
    
    exec def_delegate("_slider", "value", "setValue")


class OnionWidget(QWidget):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._value = Onion(0)
        
        self._relative = QRadioButton(u"����")
        self._fixed = QRadioButton(u"�Œ�")
        
        self._group_index = GroupIndexWidget(self)
        self._slider = OnionSlider(self)
        
        self._relative.setChecked(self._value.type() == OnionType.Relative)
        self._setItemEnabled(self._value.type() == OnionType.Relative)
        
        for f in [self._relative.toggled,
                  self._group_index.valueChanged,
                  self._slider.valueChanged]:
            f.connect(lambda _:self._onWidgetChanged())
        
        self.setLayout(vBoxLayout(
            self._relative,
            self._slider,
            self._fixed,
            self._group_index,
        ))
    
    def _setItemEnabled(self, v):
        self._group_index.setEnabled(not v)
        self._slider.setEnabled(v)
    
    def _onWidgetChanged(self):
        self.setValue(self._getValue())
        
    def _getValue(self):
        if self._relative.isChecked():
            return Onion(self._slider.value())
        else:
            return FixedOnion(self._group_index.value())
    
    exec def_qgetter("value")
    
    @emitSetter
    def setValue(self):
        with blockSignals(self._slider, self._group_index, 
                          self._relative, self._fixed):
            
            self._relative.setChecked(self.value().type() == OnionType.Relative)
            self._setItemEnabled(self.value().type() == OnionType.Relative)
            if self.value().type() == OnionType.Relative:
                self._slider.setValue(self.value().count())
            else:
                self._group_index.setValue(self.value().group_index())


def main():
    app = QApplication([])
    w = QWidget()
    
    o = OnionWidget()
    o.valueChanged.connect(print)
    
    w.setLayout(
        vBoxLayout(
            hBoxLayout(
                groupBoxV("onion", o),
                ("stretch", 1),
            ),
            ("stretch", 1),
        ),
    )
    
    w.show()
    
    app.exec_()

if "__main__" == __name__:
    main()