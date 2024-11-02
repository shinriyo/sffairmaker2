# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 

from operator import methodcaller

from sffairmaker.qutil import *
from sffairmaker.item_scroll_bar import ItemScrollBar
from sffairmaker.model_null import NullSpr

class SprScrollBar(ItemScrollBar):
    def __init__(self, *a, **kw):
        ItemScrollBar.__init__(self, *a, **kw)
        self.sff().updated.connect(self._updateItems)
        self._updateItems()
    
    exec(def_sff())
    def _default(self):
        return NullSpr()
    
    def _updateItems(self):
        items = sorted(self.xmodel().sff().sprs(), key=methodcaller("group_index"))
        self.setItems(items)
    
    exec(def_alias("sprChanged", "currentItemChanged"))
    exec(def_alias("spr", "currentItem"))
    exec(def_alias("setSpr", "setCurrentItem"))

    
def main():
    pass
    
if "__main__" == __name__:
    main()