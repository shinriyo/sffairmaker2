# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker import null

class ActList(QListWidget):
    def __init__(self, parent=None):
        QListWidget.__init__(self, parent)
        self.xmodel().act().listUpdated.connect(self.updateItems)
        self.updateItems()
        
    def xmodel(self):
        import model
        return model.Model()
    
    def updateItems(self):
        pals = [self.xmodel().sff().palette()]
        pals.extend(self.xmodel().act().acts())
        
        self.clear()
        for p in pals:
            self.addItem(p.title())
            item = self.item(self.count() - 1)
            if p == self.xmodel().palette():
                item.setBackgroundColor(QColor(255, 128, 128))
            
        
class ActTab(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self.setLayout(
            vBoxLayout(
                ActList(),
                ("stretch", 1)
            )
        )
    
    def label(self):
        return "act"
    
    def __getattr__(self, name):
        return null.Null()
    
def main():
    pass

if "__main__" == __name__:
    main()