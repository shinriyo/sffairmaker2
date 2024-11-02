# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type

from collections import OrderedDict
from sffairmaker.qutil import *
from iterutils import nth

class RadioGroup(QGroupBox):
    valueChanged = pyqtSignal(object)
    def __init__(self, title, items, orientation=Qt.Horizontal, parent=None):
        QGroupBox.__init__(self, title, parent)
        
        self._buttons = OrderedDict()
        
        for k, t in items:
            b = QRadioButton(t, self)
            @b.toggled.connect
            def onToggled(v, k=k):
                if v:
                    self.setValue(k)
            self._buttons[k] = b
        
        k, b = nth(self._buttons.items(), 0)
        self._value = k
        b.setChecked(True)
        
        direction = {
            Qt.Horizontal:QBoxLayout.LeftToRight,
            Qt.Vertical:QBoxLayout.TopToBottom,
        }[orientation]
        layout = QBoxLayout(direction)
        layout.setContentsMargins(1, 1, 1, 1)  # マージンを1ピクセルに設定
        for b in self._buttons.values():
            layout.addWidget(b)
        
        layout.addStretch(1)
        self.setLayout(layout)
    
    exec(def_qgetter("value"))
    
    @emitSetter
    def setValue(self):
        self._buttons[self._value].setChecked(True)
    
def main():
    pass
    
if "__main__" == __name__:
    main()