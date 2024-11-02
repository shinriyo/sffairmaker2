# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

class LineEditWithBrowse(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._lineEdit = QLineEdit(self)
        @commandButton(u"�Q��")
        def browseButton():
            t = self.browse()
            if not t:
                return
            self._lineEdit.setText(t)
        
        self.setLayout(hBoxLayout(
            (self._lineEdit, 1),
            browseButton,
        ))
    
    def browse(self):
        raise NotImplimentedError
    
    def __getattr__(self, name):
        return getattr(self._lineEdit, name)
    

def main():
    pass

if "__main__" == __name__:
    main()