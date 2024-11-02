# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

from enum import Enum

class Mode(Enum):
    Act = "Act"
    Sff = "Sff"
    Spr = "Spr"

def colorTable(spr, actColorTable, mode=Mode.Act):
    im = spr.image()
    if mode == Mode.Act:
        if spr.useAct() and actColorTable:
            return actColorTable
        else:
            return im.colorTable()
    elif mode == Mode.Sff:
        if spr.useAct():
            return spr.commonColorTable()
        else:
            return im.colorTable()
    elif mode == Mode.Spr:
        return im.colorTable()
    else:
        raise ValueError("invalid mode {0}".format(repr(mode)))
    
def image(spr, actColorTable, mode=Mode.Act):
    im = QImage(spr.image())
    if im.isNull():
        return im
    im.setColorTable(colorTable(spr, actColorTable, mode))
    return im


    
def main():
    pass

if "__main__" == __name__:
    main()