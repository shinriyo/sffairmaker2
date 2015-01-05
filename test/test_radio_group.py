#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.radio_group import *

def test():
    app = QApplication([])
    t = RadioGroup("test", [(i, str(i)) for i in xrange(4)])
    assert t.value() == 0
    assert t._buttons[0].isChecked()
    
    values = []
    t.valueChanged.connect(values.append)
    
    t.setValue(3)
    assert t.value() == 3
    assert len(values) == 1 and values[0] == 3
    assert not t._buttons[0].isChecked()
    assert t._buttons[3].isChecked()
    
    t.setValue(2)
    assert t.value() == 2
    assert len(values) == 2 and values[-1] == 2


def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
