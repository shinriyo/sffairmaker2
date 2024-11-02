# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from sffairmaker import const
from sffairmaker.model_null import NullSpr

from sffairmaker.edit_mixin import (
    EditMixin,
    EditSpinBox,
    EditCheckBox,
    ImageLabel,
)

import sffairmaker.sff_jump_dialog as sff_jump_dialog
from sffairmaker.spr_image_label import SprImageLabel

class SprEditMixin(EditMixin):
    def setup(self):
        EditMixin.setup(self)
        self.xmodel().sff().updated.connect(self._updateValue)
    exec def_alias("setSpr", "setTarget")
    exec def_alias("spr", "target")

class SprEditSpinBox(EditSpinBox, SprEditMixin):
    def setup(self):
        SprEditMixin.setup(self)

class SprEditCheckBox(EditCheckBox, SprEditMixin):
    def setup(self):
        SprEditMixin.setup(self)

class SprGroupEdit(SprEditSpinBox):
    _field = "group"
    _range = const.SprGroupRange
    
class SprIndexEdit(SprEditSpinBox):
    _field = "index"
    _range = const.SprIndexRange
    
class SprXEdit(SprEditSpinBox):
    _field = "x"
    _range = const.SprXRange
class SprYEdit(SprEditSpinBox):
    _field = "y"
    _range = const.SprYRange

class SprUseActEdit(SprEditCheckBox):
    _field = "useAct"
    _label = u"Act�K�p"
    def _updateValue(self):
        SprEditCheckBox._updateValue(self)
        self.setEnabled(not self.target().isUseActFixed())



class CharSffEdit(ValueCheckBox):
    def __init__(self, parent=None):
        ValueCheckBox.__init__(self, parent)
        
        self.setText(u"�L�����p")
        self.setValue(self.xmodel().sff().isCharSff())
        self.valueChanged.connect(self.xmodel().sff().setIsCharSff)
        self.xmodel().sff().updated.connect(self._updateValue)
    
    def _updateValue(self):
        with blockSignals(self):
            self.setValue(self.xmodel().sff().isCharSff())
    
    exec def_xmodel()
    
    


def main():
    pass
    
if __name__ == "__main__":
    main()