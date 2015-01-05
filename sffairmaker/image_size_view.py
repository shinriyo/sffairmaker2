#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.model_null import NullSpr

class ImageSizeView(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self._spr = NullSpr()
        self.setReadOnly(False)
        self._spr.updated.connect(self._updateText)
        self._updateText()
    
    exec def_qgetter("spr")
    def setSpr(self, spr):
        if self._spr == spr:
            return
        
        self._spr.updated.disconnect(self._updateText)
        self._spr = spr
        self._spr.updated.connect(self._updateText)
        self._updateText()
    
    def _updateText(self):
        if not self.spr().isValid():
            size = QSize(0, 0)
        else:
            size = self.spr().size()
        self.setText(self.format(size))
    
    def format(self, size):
        return "{0}x{1}".format(size.width(), size.height())
    
    def sizeHint(self):
        fm = self.fontMetrics()
        t = self.format(QSize(99999, 99999))
        return QSize(fm.width(t), fm.height())
        
    
def main():
    app = QApplication([])
    
    v = ImageSizeView()
    class TestSpr(QObject):
        updated = pyqtSignal()
        
        def isValid(self):
            return True
        def size(self):
            return QSize(1234, 4567)
    
    s = TestSpr()
    v.setSpr(s)

    w = QWidget()
    w.setLayout(
        hBoxLayout(
            vBoxLayout(
                v,
                ("stretch", 1),
            ),
            ("stretch", 1),
        )
    )
    w.show()
    
    app.exec_()
    
    
if "__main__" == __name__:
    main()