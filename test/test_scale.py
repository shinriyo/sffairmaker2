#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.scale import *

def test():
    F = Fraction
    app = QApplication([])
    
    scaleWidget = ScaleWidget()
    scaleObject = ScaleObject()
    
    for sp in [scaleWidget, scaleObject]:
        sp.setMaximum(4)
        sp.setMinimum(-2)
        sp.setIndex(1)
        
        assert sp.value() == 1
        
        vlog = []
        ilog = []
        sp.valueChanged.connect(vlog.append)
        sp.indexChanged.connect(ilog.append)
        
        sp.zoomIn()
        sp.zoomIn()
        sp.zoomIn()
        assert vlog == [2, 3, 4]
        assert ilog == [2, 3, 4]
        
        sp.zoomIn()
        assert vlog == [2, 3, 4]
        assert ilog == [2, 3, 4]
        
        for i in range(6):
            sp.zoomOut()
        
        assert vlog == [2, 3, 4, 3, 2, 1, F(1,2), F(1,3), F(1, 4)], vlog
        assert ilog == [2, 3, 4, 3, 2, 1, 0, -1, -2], ilog
        
        sp.zoomOut()
        assert vlog == [2, 3, 4, 3, 2, 1, F(1,2), F(1,3), F(1, 4)], vlog
        assert ilog == [2, 3, 4, 3, 2, 1, 0, -1, -2], ilog
    
    scaleWidget.setIndex(4)
    assert scaleWidget.lineEdit().text() == "4"
    
    scaleWidget.setIndex(-2)
    assert scaleWidget.lineEdit().text() == "1/4"
    

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
