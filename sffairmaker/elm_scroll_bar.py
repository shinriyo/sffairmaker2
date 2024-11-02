# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 

from sffairmaker.qutil import *
from sffairmaker import  model
from sffairmaker.item_scroll_bar import ItemScrollBar
from operator import methodcaller

class ElmScrollBar(ItemScrollBar):
    animChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, *a, **kw):
        ItemScrollBar.__init__(self, *a, **kw)
        self._anim = model.Anim.Null()
        self.xmodel().air().updated.connect(self._updateItems)
        self._updateItems()
        
    def _updateItems(self):
        if self.anim().isValid():
            items = self.anim().elms()
        else:
            items = []
        self.setItems(items)
    
    exec(def_qgetter("anim"))
    
    def xmodel(self):
        return model.Model()
        
    def _default(self):
        return model.Elm.Null()
    
    @emitSetter
    def setAnim(self):
        self._updateItems()
    
    exec(def_alias("elmChanged", "currentItemChanged"))
    exec(def_alias("elm", "currentItem"))
    exec(def_alias("setElm", "setCurrentItem"))
    

def main():
    pass

if "__main__" == __name__:
    main()
