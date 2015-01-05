#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 

from sffairmaker.qutil import *
from sffairmaker.clsn import Clsn

def int0(x):
    try:
        return int(x)
    except ValueError:
        return 0

class ClsnTextEdit(QPlainTextEdit):
    valueChanged = pyqtSignal(Clsn)
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        self._value = Clsn()
        self.textChanged.connect(self._onTextChanged)
    
    exec def_qgetter("value")
    
    @emitSetter
    def setValue(self):
        with blockSignals(self):
            self.setText(self.clsnToText(self._value))

    @classmethod
    def clsnToText(cls, clsn):
        lines = []
        for rc in clsn:
            line = "{0:3}, {1:3}, {2:3}, {3:3}".format(
                rc.left(), rc.top(), rc.right(), rc.bottom())
            lines.append(line)
        return "\n".join(lines)
    
    @classmethod
    def textToClsn(cls, text):
        text = unicode(text)
        lines = []
        for line in text.splitlines():
            line = line.split(";")[0]
            if line:
                lines.append(line)
        
        rects = []
        for line in lines:
            items = line.split(",")
            left, top, right, bottom = [int0(list_get(items, i, 0)) for i in xrange(4)]
            rects.append(QRect(QPoint(left, top), QPoint(right, bottom)))
        
        return Clsn(rects)
    
    def _onTextChanged(self):
        clsn = self.textToClsn(self.text())
        if self._value == clsn:
            return
        self._value = clsn
        self.valueChanged.emit(clsn)
    
    def sizeHint(self):
        t = "-9999, -9999, -9999, -9999"
        w = self.fontMetrics().width(t)
        h = self.fontMetrics().height()
        return QSize(w, h)
    
    exec def_alias("text", "toPlainText")
    exec def_alias("setText", "setPlainText")


def main():
    pass
    

if "__main__" == __name__:
    main()