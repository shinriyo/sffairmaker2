#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

class ErrorDialog(QDialog):
    def __init__(self, message="", parent=None):
        QDialog.__init__(self, parent=parent)
        self.setWindowTitle(u"エラー")
        
        self._text = QPlainTextEdit(message, parent=self)
        self._text.setReadOnly(True)
        
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, parent=self)
        buttonBox.accepted.connect(self.accept)
        
        self.setLayout(vBoxLayout(
            self._text,
            buttonBox,
        ))
        
    def setMessage(self, message):
        self._text.setPlainText(message)
    
    @classmethod
    def showMessage(cls, message, parent=None, modal=True):
        dlg = cls(message, parent=parent)
        dlg.setModal(modal)
        dlg.show()
    
    
def main():
    app = QApplication([])
    w = QWidget()
    @commandButton("nonmodal")
    def showNonModal():
        ErrorDialog.showMessage("nonmodalerror\nerror!error!", parent=w, modal=False)
    @commandButton("modal")
    def showModal():
        ErrorDialog.showMessage("modalerror\nerror!error!", parent=w, modal=True)
    
    w.setLayout(hBoxLayout(
        showNonModal,
        showModal,
    ))
    w.show()
    
    app.exec_()

if "__main__" == __name__:
    main()