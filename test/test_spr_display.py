#encoding:shift-jis
from __future__ import division, print_function, unicode_literals
__metaclass__ = type 

import nose
from nose.tools import *
from sffairmaker.qutil import *
from sffairmaker.spr_display import *


def test():
    app = QApplication([])
    actColorTable = [qRgb(0, 0, 0)] * 256
    sffColorTable = [qRgb(1, 1, 1)] * 256
    sprColorTable = [qRgb(2, 2, 2)] * 256
    
    class Spr:
        def __init__(self, useAct):
            self._useAct = useAct
        
        def image(self):
            im = QImage(1, 1, QImage.Format_Indexed8)
            im.setColorTable(sprColorTable)
            im.setPixel(0, 0, 0)
            return im
        
        def commonColorTable(self):
            return sffColorTable
        
        def useAct(self):
            return self._useAct
    
    def name(c):
        if c == actColorTable:
            return "act"
        elif c == sffColorTable:
            return "sff"
        elif c == sprColorTable:
            return "spr"
        else:
            return "other"
        
    for useAct, mode, value in [(True, Mode.Act, "act"),
                                (False, Mode.Act, "spr"),
                                (True, Mode.Sff, "sff"),
                                (False, Mode.Sff, "spr"),
                                (True, Mode.Spr, "spr"),
                                (False, Mode.Spr, "spr")]:
        
        spr = Spr(useAct)
        c = colorTable(spr, actColorTable, mode)
        assert_equals(name(c), value)
        
        im = image(spr, actColorTable, mode)
        c = im.colorTable()
        assert_equals(name(c), value)
    
    

def main():
##    nose.runmodule()
    test()
    

if "__main__" == __name__:
    main()