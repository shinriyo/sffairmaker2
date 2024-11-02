# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker import model
from sffairmaker.anim_scroll_bar import AnimScrollBar
from sffairmaker.air_edit import ElmImageLabel

class AnimIndexSelector(QComboBox):
    animChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        self._anim = model.Anim.Null()
        
        indexes = set()
        for a in self.xmodel().air().anims():
            indexes.add(a.index())
        for i in sorted(indexes):
            self.addItem(unicode(i))
        self._updateAnim()
        self.currentIndexChanged.connect(lambda _:self._updateAnim())
    
    def xmodel(self):
        return model.Model()
    
    def _updateAnim(self):
        try:
            index = int(self.currentText())
        except ValueError as e:
            self.setAnim(model.Anim.Null())
            return
        
        anims = {}
        for anim in self.xmodel().air().anims():
            anims[anim.index()] = anim
        self.setAnim(anims.get(index, model.Anim.Null()))
    
    exec(def_qgetter("anim"))
    
    @emitSetter
    def setAnim(self):
        if not self._anim.isValid():
            return
        with blockSignals(self):
            itemText = {}
            for i in xrange(self.count()):
                t = unicode(self.itemText(i))
                itemText[t] = i
            index = unicode(self._anim.index())
            self.setCurrentIndex(itemText[index])
    
class AirJumpDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"�ړ���")
        
        scroll = AnimScrollBar(Qt.Horizontal)
        self._selector = selector = AnimIndexSelector()
        image = ElmImageLabel()
        
        scroll.animChanged.connect(selector.setAnim)
        selector.animChanged.connect(scroll.setAnim)
        selector.animChanged.connect(lambda anim:image.setElm(anim.elms()[0]))
        selector.setAnim(scroll.anim())
        image.setElm(scroll.anim().elms()[0])
        
        buttonBox = dialogButtons(self)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(scroll)
        mainLayout.addWidget(selector)
        mainLayout.addWidget(image, 1, Qt.AlignCenter)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
    
    exec def_delegate("_selector", "anim", "setAnim")
    
    @classmethod
    def get(cls, anim, parent=None):
        dlg = cls(parent)
        if anim.isValid():
            dlg.setAnim(anim)
        if not dlg.exec_():
            return model.Anim.Null()
        else:
            return dlg.anim()
    
def main():
    pass

if "__main__" == __name__:
    main()