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
            (ImageOpMode.Pos, u"移動"),
            (ImageOpMode.EraseRects, u"消去"),
            (ImageOpMode.EraseRectsColors, u"色の除去"),
        ]
        RadioGroup.__init__(self, u"ドラッグ時の操作", items, parent=parent)
        
        imageView.setImageOpMode(self.value())
        self.valueChanged.connect(imageView.setImageOpMode)
        
        
class SprDisplayModeWidget(RadioGroup):
    def __init__(self, parent=None):
        items = [
            (spr_display.Mode.Act, u"Act"),
            (spr_display.Mode.Sff, u"Sff"),
            (spr_display.Mode.Spr, u"画像固有"),
        ]
        RadioGroup.__init__(self, u"表示するパレット", items, parent=parent)
        
        syncAttr(self, self.xview(), 
            ("value", "sprDisplayMode"))
    exec(def_xview())



class SffTab(QWidget):
    labelChanged = pyqtSignal(str)
    titleChanged = pyqtSignal(str)
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
        
        @commandButton(u"複製")
        def sprClone():
            if not self.spr().isValid():return
            self.spr().clone()
        
        @commandButton(u"削除")
        def sprDelete():
            if not self.spr().isValid():return
            self.spr().remove()
        
        @commandButton(u"追加")
        def sprAdd():
            if not self.spr().isValid():return
            self.xmodel().sff().addSprs()
        
        @commandButton(u"入替")
        def sprSwap():
            if not self.spr().isValid():return
            self.spr().swap()
            
        @commandButton(u"保存")
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
            # if event.orientation() != Qt.Vertical:
            #     return
            # if event.delta() < 0:
            #     self.xview().scaleZoomOut()
            # elif event.delta() > 0:
            #     self.xview().scaleZoomIn()
            if event.angleDelta().y() == 0:
                return  # 縦方向のスクロールでなければ終了
            
            # スクロール量に応じてズームイン/ズームアウトを実行
            if event.angleDelta().y() < 0:
                self.xview().scaleZoomOut()  # ズームアウト
            elif event.angleDelta().y() > 0:
                self.xview().scaleZoomIn()   # ズームイン
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
                
        
        #レイアウトここから
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
                hGroupBox(u"番号", self._group, self._index),
                hGroupBox(u"位置", self._x, self._y),
                self._useAct,
                size,
            ),
            
            sprDisplayMode,
            colorTableDragMode,
            hBoxLayout(
                groupBoxV(u"SFF全体のパレット", 
                    self._commonColorTable,
                    self._commonColorSlider,
                ),
                groupBoxV(u"画像固有のパレット", 
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
        #tabのラベル
        sff = self.xmodel().sff()
        if sff.filename() is None:
            path = u"新規"
        else:
            path = os.path.basename(sff.filename())
        
        size = len(sff.sprs())
        t = u"sff/{0}/({1})".format(path, size)
        if sff.hasChanged():
            return t + u"(更新)"
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