#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class HLine(QFrame):
    def __init__(self, margin=5, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.setFixedHeight(margin*2)

class VLine(QFrame):
    def __init__(self, margin=5, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameStyle(QFrame.VLine | QFrame.Sunken)
        self.setFixedWidth(margin*2)

def main():
    app = QApplication([])
    
    w = QWidget()
    L = QVBoxLayout()
    L.setSpacing(0)
    
    L.addWidget(QTextEdit())
    L.addWidget(HLine())
    L.addWidget(QTextEdit())
    
    w.setLayout(L)
    w.show()
    
    app.exec_()
    
if "__main__" == __name__:
    main()