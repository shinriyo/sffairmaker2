# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from sffairmaker import const
from sffairmaker import model
from sffairmaker.alpha import AlphaBlend
from sffairmaker.edit_mixin import (
    EditMixin,
    EditSpinBox,
    EditCheckBox,
    ImageLabel,
)
from sffairmaker.clsn_text_edit import ClsnTextEdit
from sffairmaker import spr_display


class AirEditMixin(EditMixin):
    def setup(self):
        EditMixin.setup(self)
        self.xmodel().air().updated.connect(self._updateValue)

class AlphaEdit(QWidget):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        # layout.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを設定
        layout.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを設定
        
        self.src = QSpinBox(self)
        self.src.setRange(*const.AlphaSourceRange)
        self.src.setValue(0)
        self.dst = QSpinBox(self)
        self.dst.setRange(*const.AlphaDestRange)
        self.dst.setValue(0)
        
        self.sub = ValueCheckBox(self)
        self.sub.setText("S")
        self.sub.setValue(True)
        
        layout.addWidget(QLabel("AS"))
        layout.addWidget(self.src)
        layout.addSpacing(7)
        layout.addWidget(QLabel("D"))
        layout.addWidget(self.dst)
        layout.addSpacing(7)
        layout.addWidget(self.sub)
        
        for k in "N A A1".split():
            v = getattr(AlphaBlend, k)()
            b = SquareButton(k)
            b.clicked.connect(partial(self.setValue, v))
            layout.addWidget(b)
        
        for w in [self.src, self.dst, self.sub]:
            w.valueChanged.connect(self._onWidgetsChanged)
    
    def _onWidgetsChanged(self):
        self.valueChanged.emit(self.value())
    
    def value(self):
        return AlphaBlend(
            self.src.value(),
            self.dst.value(),
            self.sub.value()
        )
    
    def setValue(self, value):
        if self.value() == value:
            return
        with blockSignals(self.src, self.dst, self.sub):
            self.src.setValue(value.source)
            self.dst.setValue(value.dest)
            self.sub.setValue(value.sub)
        self.valueChanged.emit(value)


class LoopEdit(QWidget):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを設定
        self.setLayout(layout)
        
        self._hasLoop = QCheckBox(self)
        self._pos = QSpinBox(self)
        self._pos.setEnabled(self._hasLoop.isChecked())
        
        layout.addWidget(self._hasLoop)
        layout.addWidget(self._pos)
        self._hasLoop.toggled.connect(self._onWidgetsChanged)
        self._pos.valueChanged.connect(self._onWidgetsChanged)
     
    def value(self):
        return self._pos.value() if self._hasLoop.isChecked() else None
    
    def _onWidgetsChanged(self):
        self._pos.setEnabled(self._hasLoop.isChecked())
        self.valueChanged.emit(self.value())
    
    def setValue(self, v):
        if self.value() == v:return
        
        with blockSignals(self._hasLoop, self._pos):
            if v is not None:
                self._hasLoop.setChecked(True)
                self._pos.setValue(v)
            else:
                self._hasLoop.setChecked(False)
        
        self._pos.setEnabled(self._hasLoop.isChecked())
        
        self.valueChanged.emit(self.value())
    
    def setElmCount(self, count):
        self._pos.setMaximum(count - 1)

class AnimLoopEdit(LoopEdit, AirEditMixin):
    _field = "loop"
    def __init__(self, parent=None):
        LoopEdit.__init__(self, parent)
        self.setup()
    
    exec(def_alias("anim", "target"))
    exec(def_alias("setAnim", "setTarget"))
    
    def _updateValue(self):
        if not self.anim().isValid():return
        with blockSignals(self):
            self.setValue(self.anim().loop())
            self.setElmCount(len(self.anim().elms()))


class AnimIndexSpinBox(EditSpinBox, AirEditMixin):
    _field = "index"
    _range = const.AnimIndexRange
    def __init__(self, *a, **kw):
        EditSpinBox.__init__(self, *a, **kw)
        self.setup()

    exec(def_alias("anim", "target"))
    exec(def_alias("setAnim", "setTarget"))


class ElmAlphaEdit(AlphaEdit, AirEditMixin):
    _field = "alpha"
    def __init__(self, parent=None):
        AlphaEdit.__init__(self, parent)
        self.setup()

    exec(def_alias("elm", "target"))
    exec(def_alias("setElm", "setTarget"))
    

class ElmCheckBox(EditCheckBox, AirEditMixin):
    def __init__(self, *a, **kw):
        EditCheckBox.__init__(self, *a, **kw)
        self.setup()

    exec(def_alias("elm", "target"))
    exec(def_alias("setElm", "setTarget"))
    
class ElmHCheckBox(ElmCheckBox):
    _field = "h"
class ElmVCheckBox(ElmCheckBox):
    _field = "v"

class ElmLoopStartCheckBox(ElmCheckBox):
    _field = "loopStart"

class ElmEditSpinBox(EditSpinBox, AirEditMixin):
    def __init__(self, *a, **kw):
        self._range = eval("const.Elm{0}Range".format(self._field.title()))
        EditSpinBox.__init__(self,*a, **kw)
        self.setup()
    exec(def_alias("elm", "target"))
    exec(def_alias("setElm", "setTarget"))
    
class ElmGroupSpinBox(ElmEditSpinBox):
    _field = "group"
class ElmIndexSpinBox(ElmEditSpinBox):
    _field = "index"
class ElmXSpinBox(ElmEditSpinBox):
    _field = "x"
class ElmYSpinBox(ElmEditSpinBox):
    _field = "y"
class ElmTimeSpinBox(ElmEditSpinBox):
    _field = "time"


class ElmImageLabel(QWidget):
    Size = 100
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._elm = model.Elm.Null()
        
        self._actColorTable = None
        syncAttrTo(self, self.xview(),
            "actColorTable"
        )
        
        self.sff().updated.connect(self.update)
        self.air().updated.connect(self.update)
        self.setFixedSize(self.Size, self.Size)
    
    exec(def_sff())
    exec(def_air())
    exec(def_xview())
    exec(def_update_accessor("actColorTable"))
    
    def setElm(self, elm):
        if self._elm == elm:return
        self._elm = elm
        self.update()
    
    def paintEvent(self, event):
        if not self._elm.isValid():return
        spr = self._elm.spr()
        if not spr.isValid():return
        
        image = spr_display.image(
            spr,
            self.actColorTable(),
        )
        if image.isNull():return
        
        image = image.scaled(self.size(), Qt.KeepAspectRatio)
        if self._elm.h() or self._elm.v():
            image = image.mirrored(self._elm.h(), self._elm.v())
        
        painter = QPainter(self)
        x = (self.width() - image.width()) / 2
        y = (self.height() - image.height()) / 2
        painter.drawImage(QPointF(x, y), image)
        

class ElmClsnEditBase(ClsnTextEdit, AirEditMixin):
    def __init__(self, parent=None):
        ClsnTextEdit.__init__(self, parent)
        self.setup()
    exec(def_alias("elm", "target"))
    exec(def_alias("setElm", "setTarget"))

class ElmClsn1Edit(ElmClsnEditBase):
    _field = "clsn1"
class ElmClsn2Edit(ElmClsnEditBase):
    _field = "clsn2"


class AnimClsnEditBase(ClsnTextEdit, AirEditMixin):
    def __init__(self, parent=None):
        ClsnTextEdit.__init__(self, parent)
        self.setup()
    exec(def_alias("anim", "target"))
    exec(def_alias("setAnim", "setTarget"))

class AnimClsn1Edit(AnimClsnEditBase):
    _field = "clsn1"
class AnimClsn2Edit(AnimClsnEditBase):
    _field = "clsn2"

def main():
    app = QApplication([])
    from sffairmaker.model import Model
    Model().air()._open("kfm.air")
    
    x = Clsn1Edit()
    y = Clsn1Edit()
    
    x.setElm(Model().air().anims()[0].elms()[0])
    y.setElm(Model().air().anims()[0].elms()[0])
    
    x.show()
    y.show()
    
    app.exec_()
    
if __name__ == "__main__":
    main()