#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

class ChoiceMenu(QMenu):
    def __init__(self, values, *a, **kw):
        QMenu.__init__(self, *a, **kw)
        
        self._value = None
        i = 0
        for v in values:
            if v == "-":
                self.addSeparator()
            else:
                a = self.addAction(v)
                a.triggered.connect(lambda _, i=i:self.setValue(i))
                i += 1
        self.addSeparator()
        self.addAction(u"キャンセル")
    exec def_qaccessor("value")
    
def choiceMenu(values, pos, *a, **kw):
    m = ChoiceMenu(values, *a, **kw)
    m.exec_(pos)
    return m.value()
    
def main():
    app = QApplication([])
    
    class Test(QWidget):
        def mousePressEvent(self, evt):
            v = choiceMenu(u"spam egg - ham".split(), evt.globalPos(), u"選択", self)
            QMessageBox.information(self, u"結果", str(v))
    
    t = Test()
    t.resize(200, 200)
    t.show()
    
    app.exec_()
    
    
if "__main__" == __name__:
    main()