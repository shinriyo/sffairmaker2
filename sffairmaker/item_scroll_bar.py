# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from bisect import bisect_left
from iterutils import unique_everseen


class Items(list):
    def __init__(self, alist):
        list.__init__(self, unique_everseen(alist))
        self._indexDict = dict((x, i) for i, x in enumerate(alist))
    
    def safe_index(self, x):
        return self._indexDict.get(x)


class ItemScrollBar(QScrollBar):
    currentItemChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, *a, **kw):
        QScrollBar.__init__(self, *a, **kw)
        
        self.setMinimum(0)
        self.setValue(0)
        self._currentItem = self._default()
        self._items = None
        self.setItems([])
        self.valueChanged.connect(self._onScrollChanged)
    
    exec(def_qgetter("currentItem", "items"))
    
    def setCurrentItem(self, item):
        if self._currentItem == item:
            return
        
        i = self._items.safe_index(item)
        if i is None:
            return
        
        self._currentItem = item
        self.setValue(i)
        self.currentItemChanged.emit(self._currentItem)
    
##    def setItems(self, items):
##        items = Items(items)
##        if self._items == items:
##            return
        
##        olditems = self._items
##        self._items = items
##        if not self._items:
##            self.setMaximum(0)
##            self.setEnabled(False)
##            if self._currentItem != self._default():
##                self._currentItem = self._default()
##                self.currentItemChanged.emit(self._currentItem)
##            return
        
##        self.setMaximum(len(self._items) - 1)
##        self.setEnabled(True)
        
##        newindex = self._items.safe_index(self._currentItem)
##        if newindex is not None:
##            self.setValue(newindex)
##            return
        
##        oldindex = olditems.safe_index(self._currentItem)
##        if oldindex is None:
##            self._currentItem = self._items[0]
##            self.setValue(0)
##            self.currentItemChanged.emit(self._currentItem)
##            return
        
##        leftItems = olditems[:oldindex]
##        leftItems.reverse()
##        rightItems = olditems[oldindex + 1:]
##        remainItems = [i for i in leftItems + rightItems if i in self._items]
        
##        if remainItems:
##            self._currentItem = remainItems[0]
##            self.setValue(self._items.index(self._currentItem))
##            self.currentItemChanged.emit(self._currentItem)
##        else:
##            self._currentItem = self._items[0]
##            self.setValue(0)
##            self.currentItemChanged.emit(self._currentItem)
    

    def setItems(self, items):
        items = Items(items)
        if self._items == items:
            return
        
        olditems = self._items
        self._items = items
        if not self._items:
            self.setMaximum(0)
            self.setEnabled(False)
            if self._currentItem != self._default():
                self._currentItem = self._default()
                self.currentItemChanged.emit(self._currentItem)
            return
        
        self.setMaximum(len(self._items) - 1)
        self.setEnabled(True)
        
        newindex = self._items.safe_index(self._currentItem)
        if newindex is not None:
            self.setValue(newindex)
            return
        
        oldindex = olditems.safe_index(self._currentItem)
        if oldindex is None:
            self._currentItem = self._items[0]
            self.setValue(0)
            self.currentItemChanged.emit(self._currentItem)
            return
        
        leftItems = olditems[:oldindex]
        leftItems.reverse()
        rightItems = olditems[oldindex + 1:]
        
        try:
            newItemsSet = set(self._items)
        except TypeError:
            newItemsSet = self._items
        
        import itertools
        for item in itertools.chain(leftItems, rightItems):
            if item in newItemsSet:
                self._currentItem = item
                self.setValue(self._items.index(self._currentItem))
                self.currentItemChanged.emit(self._currentItem)
                break
        else:
            self._currentItem = self._items[0]
            self.setValue(0)
            self.currentItemChanged.emit(self._currentItem)

        
    def _default(self):
        """when self._items() is empty, self._default() is used for currentItem.
           this method can be(/ should be) overrided in subclass."""
        return None
    
    def _onScrollChanged(self, index):
        self.setCurrentItem(self._items[index])
    
def main():
    app = QApplication([])
    import string
    
    v = ItemScrollBar(Qt.Horizontal)
    v.currentItemChanged.connect(print)
    
    txt = QLineEdit()
    btn = QPushButton("setItems")
    @btn.clicked.connect
    def callback(_):
        v.setItems(txt.text())
    
    w = QWidget()
    w.setLayout(
        vBoxLayout(
            v,
            hBoxLayout(
                (txt, 1),
                btn
            )
        )
    )
    w.show()
    app.exec_()
        
if __name__ == "__main__":
    main()