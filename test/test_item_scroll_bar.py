# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.elm_scroll_bar import *

def test():
    app = QApplication([])
    
    m = model._Model()
    scr = ElmScrollBar(Qt.Horizontal)
    scr.xmodel =lambda :m
    
    a = sorted(m.air().anims(), key=lambda a:a.index())[0]
    scr.setAnim(a)
    
    a.changeFromString(a.toString())

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()