#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

class TextDialog(QDialog):
    def __init__(self, text="", parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"テキスト編集")
        
        self._textEdit = QTextEdit(self)
        self._textEdit.setText(text)
        self._textEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._textEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self._textEdit.setLineWrapMode(QTextEdit.NoWrap)
        self._textEdit.setAutoFormatting(QTextEdit.AutoNone)
        self.setLayout(vBoxLayout(
            self._textEdit,
            dialogButtons(self)
        ))
    
    def __getattr__(self, name):
        return getattr(self._textEdit, name)
    
    def text(self):
        return self.toPlainText()
    
    @classmethod
    def get(cls, *a, **kw):
        dlg = cls(*a, **kw)
        if dlg.exec_():
            return dlg.text()
        else:
            return QString()
    
def main():
    app = QApplication([])
    s = u"""\
くぁｗせｄｒｆｔｇｙふじこｌｐ
ｐぉきじゅｈｙｇｔｆｒですぁｑ"""
    print(TextDialog.get(s))
    
    
    
    
if "__main__" == __name__:
    main()