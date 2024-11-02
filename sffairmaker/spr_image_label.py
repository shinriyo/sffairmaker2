# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.model_null import NullSpr

from sffairmaker import spr_display

class SprImageLabel(QWidget):
    Size = 100
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._spr = NullSpr()
        self._spr.updated.connect(self.update)
        
        self._sprDisplayMode = None
        self._actColorTable = None
        syncAttrTo(self, self.xview(), 
            "actColorTable",
            "sprDisplayMode",
        )
        self.setFixedSize(self.Size, self.Size)
    
    exec(def_sff())
    exec(def_xview())
    
    exec(def_update_accessor(
        "sprDisplayMode",
        "actColorTable",
    ))
    def setSpr(self, spr):
        if self._spr == spr:
            return
        self._spr.updated.disconnect(self.update)
        self._spr = spr
        self._spr.updated.connect(self.update)
        self.update()
    
    def paintEvent(self, event):
        if not self._spr.isValid():
            return
        
        image = spr_display.image(
            self._spr,
            self.actColorTable(),
            self.sprDisplayMode()
        )
        if image.isNull():
            return
        
        image = image.scaled(self.size(), Qt.KeepAspectRatio)
        
        x = (self.width() - image.width()) / 2
        y = (self.height() - image.height()) / 2
        
        painter = QPainter(self)
        painter.drawImage(QPointF(x, y), image)


def main():
    pass

if "__main__" == __name__:
    main()