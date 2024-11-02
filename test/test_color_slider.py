#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.color_slider import *

def test():
    app = QApplication([])
    s = ColorSlider()
    
    assert s.value() == QColor(0, 0, 0)
    log = []
    s.valueChanged.connect(log.append)
    
    for i in range(3):
        s.setValue(QColor(0, 0, 0))
        log[:] = []
        s._scrs[i].setValue(255)
        
        assert crgb(s.value()) == tuple(255 if k==i else 0 for k in [0,1,2]), crgb(s.value())
        assert len(log) == 1, log
        assert crgb(log[0]) == tuple(255 if k==i else 0 for k in [0,1,2]), crgb(log[0])
    
    s.setValue(QColor(0, 0, 0))
    rgb = [0, 0, 0]
    for i in range(3):
        assert s._scrs[i].value() == 0
        rgb[i] = 255
        s.setValue(QColor(*rgb))
        assert s._scrs[i].value() == 255
    

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
