# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type

import os.path

from sffairmaker.qutil import *
from sffairmaker.sff_image_view import SffImageView, ImageOpMode
from sffairmaker import spr_display
from sffairmaker.spr_scroll_bar import SprScrollBar
from sffairmaker.slider_position_widget import SliderPositionWidget
from sffairmaker.image_size_view import ImageSizeView
from sffairmaker.radio_group import RadioGroup

from sffairmaker import const

from sffairmaker.sff_edit import (
    SprGroupEdit,
    SprIndexEdit,
    SprXEdit,
    SprYEdit,
    SprUseActEdit,
    CharSffEdit,
)

from sffairmaker.sff_jump_dialog import SffJumpButton

from sffairmaker.color_table_edit import (
    SprColorTableEdit,
    CommonColorTableEdit,
    ColorSlider,
    ColorTableDragModeRadio,
)

class ImageOpRadioGroup(RadioGroup):
    def __init__(self, imageView, parent=None):
        items = [
            (ImageOpMode.Pos, u"�ړ�"),
            (ImageOpMode.EraseRects, u"����"),
            (ImageOpMode.EraseRectsColors, u"�F�̏���"),
        ]
        RadioGroup.__init__(self, u"�h���b�O���̑���", items, parent=parent)
        
        imageView.setImageOpMode(self.value())
        self.valueChanged.connect(imageView.setImageOpMode)
        
        
class SprDisplayModeWidget(RadioGroup):
    def __init__(self, parent=None):
        items = [
            (spr_display.Mode.Act, u"Act"),
            (spr_display.Mode.Sff, u"Sff"),
            (spr_display.Mode.Spr, u"�摜�ŗL"),
        ]
        RadioGroup.__init__(self, u"�\������p���b�g", items, parent=parent)
        
        syncAttr(self, self.xview(), 
            ("value", "sprDisplayMode"))
    exec def_xview()



class SffTab(QWidget):
    labelChanged = pyqtSignal(unicode)
    titleChanged = pyqtSignal(unicode)
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.xmodel().sff().updated.connect(lambda :self.labelChanged.emit(self.label()))
        self.xmodel().sff().updated.connect(lambda :self.titleChanged.emit(self.title()))
        
        self._scroll = SprScrollBar(Qt.Horizontal, self)
        self.spr = self._scroll.spr
        self.setSpr = self._scroll.setSpr
        self.sprChanged = self._scroll.sprChanged
        
        self._jump = SffJumpButton(parent=self)
        syncAttr(self._jump, self, "spr")
        
        scrollPos = SliderPositionWidget(self)
        scrollPos.setSlider(self._scroll)
        
        @commandButton(u"����")
        def sprClone():
            if not self.spr().isValid():return
            self.spr().clone()
        
        @commandButton(u"�폜")
        def sprDelete():
            if not self.spr().isValid():return
            self.spr().remove()
        
        @commandButton(u"�ǉ�")
        def sprAdd():
            if not self.spr().isValid():return
            self.xmodel().sff().addSprs()
        
        @commandButton(u"����")
        def sprSwap():
            if not self.spr().isValid():return
            self.spr().swap()
            
        @commandButton(u"�ۑ�")
        def sprSave():
            if not self.spr().isValid():return
            self.spr().save()
        
        for s in "x y group index useAct".split():
            w = eval("Spr" + s[0].upper() + s[1:] + "Edit")(self)
            self.sprChanged.connect(w.setSpr)
            w.setSpr(self.spr())
            setattr(self, "_"+s, w)
        
        charSff = CharSffEdit(self)
        
        self._imageView = SffImageView(self)
        self._imageView.setSpr(self.spr())
        
        self.sprChanged.connect(self._imageView.setSpr)
        self._imageView.sprChanged.connect(self.setSpr)
        
        syncAttr(self._imageView, self.xview(), "axisDelta")
        syncAttrTo(self._imageView, self.xview(), "gridOption", "onion", "scale", "colors", "transparent")
        
        imageOp = ImageOpRadioGroup(self._imageView, parent=self)
        sprDisplayMode = SprDisplayModeWidget(parent=self)
        
        size = ImageSizeView()
        size.setSpr(self.spr())
        self.sprChanged.connect(size.setSpr)
        
        def wheelEvent(event):
            if event.orientation() != Qt.Vertical:
                return
            if event.delta() < 0:
                self.xview().scaleZoomOut()
            elif event.delta() > 0:
                self.xview().scaleZoomIn()
        self._imageView.wheelEvent = wheelEvent
        
        self._sprColorTable = SprColorTableEdit(self)
        self._sprColorTable.setSpr(self.spr())
        self.sprChanged.connect(self._sprColorTable.setSpr)
        self._sprColorSlider = ColorSlider(self._sprColorTable, self)
        
        self._commonColorTable = CommonColorTableEdit(self)
        self._commonColorSlider = ColorSlider(self._commonColorTable, self)
        
        colorTableDragMode = ColorTableDragModeRadio()
        colorTableDragMode.connectEdits(self._sprColorTable, self._commonColorTable)
        
        self._imageView.colorNumberSelected.connect(self._sprColorTable.setCurrentNumber)
        self._imageView.colorNumberSelected.connect(self._commonColorTable.setCurrentNumber)
                
        
        #���C�A�E�g��������
        leftLayout = vBoxLayout(
            hBoxLayout(
                self._jump,
                scrollPos,
                (self._scroll, 1),
            ),
            charSff,
            hBoxLayout(
                sprClone,
                sprDelete,
                ("stretch", 1),
            ),
            hBoxLayout(
                sprAdd,
                sprSwap,
                sprSave,
                ("stretch", 1),
            ),
            hBoxLayout(
                hGroupBox(u"�ԍ�", self._group, self._index),
                hGroupBox(u"�ʒu", self._x, self._y),
                self._useAct,
                size,
            ),
            
            sprDisplayMode,
            colorTableDragMode,
            hBoxLayout(
                groupBoxV(u"SFF�S�̂̃p���b�g", 
                    self._commonColorTable,
                    self._commonColorSlider,
                ),
                groupBoxV(u"�摜�ŗL�̃p���b�g", 
                    self._sprColorTable,
                    self._sprColorSlider,
                ),
                ("stretch", 1),
            ),
            ("stretch", 1),
        )
        
        imageOp.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        rightLayout = vBoxLayout(
            imageOp,
            (self._imageView, 1)
        )
        
        mainLayout = hBoxLayout(
            leftLayout,
            (rightLayout, 1),
        )
        self.setLayout(mainLayout)
    
    def label(self):
        #tab�̃��x��
        sff = self.xmodel().sff()
        if sff.filename() is None:
            path = u"�V�K"
        else:
            path = os.path.basename(sff.filename())
        
        size = len(sff.sprs())
        t = u"sff/{0}/({1})".format(path, size)
        if sff.hasChanged():
            return t + u"(�X�V)"
        else:
            return t
    
    def title(self):
        sff = self.xmodel().sff()
        return const.TitleFormat("sff", sff.filename(), sff.hasChanged())
        
    def jump(self):
        self._jump.jump()
    
    def nextItem(self):
        self._scroll.setValue(self._scroll.value() + 1)
    
    def prevItem(self):
        self._scroll.setValue(self._scroll.value() - 1)
        
    def xview(self):
        import sffairmaker.view
        return sffairmaker.view.View()
    
    def xmodel(self):
        import sffairmaker.model
        return sffairmaker.model.Model()
    
def main():
    pass
    
if __name__ == "__main__":
    main()