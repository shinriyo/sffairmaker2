# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from sffairmaker import model

class EditMixin:
    _field = None
    def setup(self):
        self._target = model.Null()
        self.valueChanged.connect(self._change)
    
    def xmodel(self):
        return model.Model()
        
    exec(def_qgetter("target"))
    
    def setTarget(self, v):
        if self.target() == v:return
        self._target = v
        self._updateValue()
    
    def _change(self):
        if not self.target().isValid():
            return
        self.target().change(**{self._field:self.value()})
    
    def _updateValue(self):
        if not self.target().isValid():
            return
        with blockSignals(self):
            self.setValue(self._fieldValue(self.target()))
    
    def _fieldValue(self, target):
        return getattr(target, self._field)()
    
    
class EditSpinBox(QSpinBox, EditMixin):
    def __init__(self, *a, **kw):
        QSpinBox.__init__(self, *a, **kw)
        self.setRange(*self._range)
        self.setup()
    
    
class EditCheckBox(ValueCheckBox, EditMixin):
    _label = None
    def __init__(self, *a, **kw):
        ValueCheckBox.__init__(self, *a, **kw)
        if self._label is None:
            self.setText(self._field.title())
        else:
            self.setText(self._label)
        self.setup()
    

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        
        self.setFixedSize(100, 100)
        self.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを0に設定
        self.setAlignment(Qt.AlignCenter | Qt.AlignJustify)
        
        self._target = model.Null()
        self._updateValue()
    
    exec(def_qgetter("target"))
    
    def xmodel(self):
        return model.Model()
    
    def setTarget(self, v):
        if self.target() == v:return
        self._target = v
        self._updateValue()
    
    def _image(self):
        if not self.target().isValid():
            return QImage()
        return self.target().image()
    
    def _key(self):
        raise NotImplementedError
    
    def _pixmap(self):
        raise NotImplementedError
    
    def _updateValue(self):
        im = self._image()
        if im.isNull():
            self._cacheKey = None
            self.setText("no image")
            return
        
        key = self._key(im)
        if self._cacheKey == key:
            return
        
        self._cacheKey = key
        self.setPixmap(self._pixmap(key))
        
        
def main():
    pass
    
if __name__ == "__main__":
    main()