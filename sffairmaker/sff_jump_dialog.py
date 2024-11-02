# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.model_null import NullSpr
from sffairmaker.spr_scroll_bar import SprScrollBar
from sffairmaker.spr_image_label import SprImageLabel
from sffairmaker.spr_selector import SprSelector

class SprPreviewSelector(QWidget):
    def __init__(self, sprs, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle(u"�ړ���")
        
        self._scroll = SprScrollBar(Qt.Horizontal, parent=self)
        self._selector = SprSelector(sprs=sprs, parent=self)
        self._image = SprImageLabel(parent=self)
        self._image.setVisible(self.isEnabled())
        
        syncAttr(self._selector, self._scroll, "spr")
        syncAttrTo(self._image, self._scroll, "spr")
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self._scroll)
        mainLayout.addWidget(self._selector)
        mainLayout.addWidget(self._image, 1, Qt.AlignCenter)
        self.setLayout(mainLayout)
    
    exec(def_delegate("_scroll", "spr", "setSpr"))
    
    def setEnabled(self, *a, **kw):
        QWidget.setEnabled(self,  *a, **kw)
        self._image.setVisible(self.isEnabled())


class SffJumpDialog(QDialog):
    def __init__(self, sprs, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"�ړ���")
        
        self._selector = SprPreviewSelector(sprs=sprs, parent=self)
        buttonBox = dialogButtons(self)
        
        self.setLayout(vBoxLayout(
            (self._selector, 1),
            buttonBox,
        ))
    
    exec def_delegate("_selector", "spr", "setSpr")
    
    @classmethod
    def get(cls, spr, sprs, parent=None):
        return cls(sprs=sprs, parent=parent).ask(spr)
    
    def ask(self, spr):
        if spr.isValid():
            self.setSpr(spr)
        if not self.exec_():
            return NullSpr()
        else:
            return self.spr()
    

class SffJumpButton(QPushButton):
    sprChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, label=u"jump", parent=None):
        QPushButton.__init__(self, label, parent)
        self._spr = NullSpr()
        self.clicked.connect(self.jump)
    
    exec(def_qgetter("spr"))
    
    exec(def_sff())
    
    @emitSetter
    def setSpr(self):
        pass
    
    def jump(self):
        spr = SffJumpDialog.get(spr=self.spr(), sprs=self.sff().sprs())
        if spr.isValid():
            self._spr = spr
            self.sprChanged.emit(spr)
    
    
def main():
    app = QApplication([])
    from os.path import join
    
    model.Model().sff()._open(join(debugDataDir(), "kfm.sff"))
    spr = SffJumpDialog.get(NullSpr)
    print(spr)
    if spr.isValid():
        print(spr.group_index())
    
if "__main__" == __name__:
    main()