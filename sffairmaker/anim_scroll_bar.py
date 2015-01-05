#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker import model
from sffairmaker.item_scroll_bar import ItemScrollBar
from operator import methodcaller

class AnimScrollBar(ItemScrollBar):
    def __init__(self, *a, **kw):
        ItemScrollBar.__init__(self, *a, **kw)
        self.xmodel().air().updated.connect(self._updateItems)
        self._updateItems()

    def _updateItems(self):
        items = self.xmodel().air().anims()
        items.sort(key=methodcaller("index")) 
        self.setItems(items)
    
    def xmodel(self):
        return model.Model()
    
    def _default(self):
        return model.Anim.Null()
    
    exec def_alias("animChanged", "currentItemChanged")
    exec def_alias("anim", "currentItem")
    exec def_alias("setAnim", "setCurrentItem")
    
    
def main():
    pass
    
if "__main__" == __name__:
    main()