# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type
import os.path

from sffairmaker.qutil import *
from sffairmaker import (
    model,
    const,
)

from sffairmaker.anim_scroll_bar import AnimScrollBar
from sffairmaker.air_image_view import AirImageView, ClsnDragMode
from sffairmaker.alpha import AlphaBlend
from sffairmaker.air_jump_dialog import AirJumpDialog
from sffairmaker.slider_position_widget import SliderPositionWidget
from sffairmaker.elm_scroll_bar import ElmScrollBar
from sffairmaker.elm_insert_pos_dialog import ElmInsertPosDialog
from sffairmaker.radio_group import RadioGroup
from sffairmaker.line import HLine, VLine
from sffairmaker import spr_display

from sffairmaker.air_edit import (
    AnimLoopEdit,
    AnimIndexSpinBox,
    AnimClsn1Edit,
    AnimClsn2Edit,
    
    ElmAlphaEdit,
    ElmHCheckBox,
    ElmVCheckBox,
    ElmGroupSpinBox,
    ElmIndexSpinBox,
    ElmXSpinBox,
    ElmYSpinBox,
    ElmTimeSpinBox,

    ElmClsn1Edit,
    ElmClsn2Edit,
)


class DrawingAllClsnButton(ValueButton):
    def __init__(self, imageView, parent=None):
        ValueButton.__init__(self, u"CLSN全表示", parent=parent)
        self._imageView = imageView
        
        self.valueChanged.connect(self.onValueChanged)
        self._imageView.drawingClsnChanged.connect(self.setDrawingClsn)
        
    def onValueChanged(self):
        if self.value():
            self._imageView.setDrawingClsn(set(const.ClsnKeys))
        else:
            self._imageView.setDrawingClsn(set())
        
    def setDrawingClsn(self, clsns):
        if clsns == set(const.ClsnKeys):
            self.setValue(True)
        else:
            with blockSignals(self):
                self.setValue(False)


class AppendingClsnButton(ValueButton):
    def __init__(self, key, imageView, parent=None):
        ValueButton.__init__(self, u"追加", parent=parent)
        self.setCheckable(True)
        self._key = key
        self._imageView = imageView
        
        self.valueChanged.connect(self.onValueChanged)
        self._imageView.appendingClsnChanged.connect(self.setAppendingClsn)
        self.setAppendingClsn(imageView.appendingClsn())
        
    def onValueChanged(self, t):
        if t:
            self._imageView.setAppendingClsn(self._key)
        else:
            if self._key == self._imageView.appendingClsn():
                self._imageView.setAppendingClsn(None)
    
    def setAppendingClsn(self, appending):
        self.setValue(self._key==appending)
    

class ClsnDragModeGroup(RadioGroup):
    def __init__(self, imageView, parent=None):
        items = [
            (ClsnDragMode.Normal, u"個別"),
            (ClsnDragMode.Group, u"グループ"),
            (ClsnDragMode.All, u"すべて同時に"),
            (ClsnDragMode.AllPos, u"画像位置も同時に")
        ]
        RadioGroup.__init__(self, u"CLSNの移動方法", items, parent=parent)
        
        self.valueChanged.connect(imageView.setClsnDragMode)
        imageView.clsnDragModeChanged.connect(self.setValue)
        self.setValue(imageView.clsnDragMode())
        

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


class AirTab(QWidget):
    labelChanged = pyqtSignal(str)
    titleChanged = pyqtSignal(str)
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.air().updated.connect(lambda :self.labelChanged.emit(self.label()))
        self.air().updated.connect(lambda :self.titleChanged.emit(self.title()))
        
        self._scroll = AnimScrollBar(Qt.Horizontal, self)
        
        @commandButton(u"追加")
        def animNew():
            if not self.anim().isValid():return
            self.setAnim(self.air().newAnim())
        
        @commandButton(u"複製")
        def animClone():
            if not self.anim().isValid():return
            self.anim().clone()
            
        @commandButton(u"削除")
        def animDelete():
            if not self.anim().isValid():return
            anim = self.anim().remove()
        
        @commandButton(u"テキスト編集")
        def animEdit():
            if not self.anim().isValid():return
            self.anim().textEdit()
        
        self._elmScroll = ElmScrollBar(Qt.Horizontal)
        self._elmScrollPos = SliderPositionWidget()
        self._elmScrollPos.setSlider(self._elmScroll)
        
        @commandButton(u"複製")
        def elmClone():
            if not self.elm().isValid():return
            self.elm().clone()
            
        @commandButton(u"移動")
        def elmMove():
            if not self.elm().isValid():return
            self.elm().move()
        
        @commandButton(u"削除")
        def elmDelete():
            if not self.elm().isValid():return
            self.elm().remove()
        
        @commandButton(u"追加")
        def elmAdd():
            if not self.elm().isValid():return
            self.elm().anim().newElm()
            
        self.elm = self._elmScroll.elm
        self.anim = self._elmScroll.anim
        self.setElm = self._elmScroll.setElm
        self.setAnim = self._elmScroll.setAnim
        self.animChanged = self._elmScroll.animChanged
        self.elmChanged = self._elmScroll.elmChanged
        
        self._scroll.animChanged.connect(self._elmScroll.setAnim)
        self._elmScroll.animChanged.connect(self._scroll.setAnim)
        self._elmScroll.setAnim(self._scroll.anim())
        
        jump = commandButton("jump")(self.jump)
        
        scrollPos = SliderPositionWidget(self)
        scrollPos.setSlider(self._scroll)
        
        self._animIndex = AnimIndexSpinBox(self)
        self._animLoop = AnimLoopEdit(self)
        self._animClsn1 = AnimClsn1Edit()
        self._animClsn2 = AnimClsn2Edit()
        for s in "animIndex animLoop animClsn1 animClsn2".split():
            w = getattr(self, "_"+s)
            self.animChanged.connect(w.setAnim)
            w.setAnim(self.anim())
            
        for s in "time x y group index".split():
            spn = eval("Elm" + s.title() + "SpinBox")()
            setattr(self, "_"+s, spn)
        
        self._h = ElmHCheckBox(self)
        self._v = ElmVCheckBox(self)
        self._alpha = ElmAlphaEdit(self)
        
        self._clsn1 = ElmClsn1Edit()
        self._clsn2 = ElmClsn2Edit()
        
        for s in "time x y group index h v alpha clsn1 clsn2".split():
            w = getattr(self, "_" + s)
            self.elmChanged.connect(w.setElm)
            w.setElm(self.elm())

        imageView = AirImageView()
        self.elmChanged.connect(imageView.setElm)
        imageView.setElm(self.elm())
        
        syncAttrTo(imageView, self.xview(),
            "gridOption", "onion", "scale", "colors", "transparent")
        
        syncAttr(imageView, self.xview(), "axisDelta")
        
        self._appendingClsn = dict(
            (k, AppendingClsnButton(k, imageView, self))
                for k in const.ClsnKeys)
        
        self._drawingAllClsn = DrawingAllClsnButton(imageView, self)
        self.animChanged.connect(lambda _:imageView.setAppendingClsn(None))
        
        self._clsnDragMode = ClsnDragModeGroup(imageView, parent=self)
        
        def wheelEvent(event):
            # if event.orientation() != Qt.Vertical:
            #     return
            # if event.delta() < 0:
            #     self.xview().scaleZoomOut()
            # elif event.delta() > 0:
            #     self.xview().scaleZoomIn()
            # 縦方向のスクロールかどうかを確認
            if event.angleDelta().y() == 0:
                return  # 縦方向のスクロールでなければ終了
            
            # スクロール量に応じてズームイン/ズームアウトを実行
            if event.angleDelta().y() < 0:
                self.xview().scaleZoomOut()  # ズームアウト
            elif event.angleDelta().y() > 0:
                self.xview().scaleZoomIn()   # ズームイン
        imageView.wheelEvent = wheelEvent
        
        self._sprDisplayMode = SprDisplayModeWidget(parent=self)
        #レイアウトここから
        items = [
            ("Clsn1", self._clsn1, const.ClsnKeys._1),
            ("Clsn2", self._clsn2, const.ClsnKeys._2),
            ("ClsnDefault1", self._animClsn1, const.ClsnKeys._1d),
            ("ClsnDefault2", self._animClsn2, const.ClsnKeys._2d),
        ]
        
        boxes = {}
        for (caption, c, key) in items:
            groupBox = QGroupBox(caption, self)
            layout = QGridLayout()
            layout.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを設定
            layout.setSpacing(0)
            
            layout.addWidget(c, 0, 0, 1, 2)
##            layout.addWidget(self._drawingClsn[key], 1, 0)
            layout.addWidget(self._appendingClsn[key], 1, 1)
            groupBox.setLayout(layout)
            boxes[key] = groupBox
        
        clsnLayout = QGridLayout()
        clsnLayout.addWidget(boxes[const.ClsnKeys._1], 0, 0)
        clsnLayout.addWidget(boxes[const.ClsnKeys._2], 0, 1)
        clsnLayout.addWidget(boxes[const.ClsnKeys._1d], 1, 0)
        clsnLayout.addWidget(boxes[const.ClsnKeys._2d], 1, 1)
        
        leftLayout = vBoxLayout(
            hBoxLayout(
               jump,
               scrollPos,
               (self._scroll, 1)
            ),
            hBoxLayout(
               animNew,
               animDelete,
               animClone,
               animEdit,
               ("stretch", 1),
            ),
            hBoxLayout(
               hGroupBox(u"アニメ番号", self._animIndex),
               hGroupBox(u"Loop", self._animLoop),
               ("stretch", 1),
            ),
            ("spacing", 10),
            self._sprDisplayMode,
            ("spacing", 10),
            
            hBoxLayout(
                self._elmScrollPos,
                (self._elmScroll, 1),
            ),
            hBoxLayout(
               elmAdd,
               elmDelete,
               elmMove,
               elmClone,
               ("stretch", 1),
            ),
            hBoxLayout(
                hGroupBox(u"画像番号", self._group, self._index),
                hGroupBox(u"位置", self._x, self._y),
                ("stretch", 1),
            ),
            hBoxLayout(
                hGroupBox(u"表示時間", self._time),
                hGroupBox(u"反転", self._h, self._v),
               ("stretch", 1),
            ),
            hBoxLayout(
                hGroupBox(u"透過", self._alpha),
               ("stretch", 1),
            ),
            self._drawingAllClsn,
            clsnLayout,
            ("stretch", 1),
        )
        
        self._clsnDragMode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        rightLayout = vBoxLayout(
            self._clsnDragMode,
            (imageView, 1),
        )
        
        mainLayout = hBoxLayout(
            leftLayout,
            (rightLayout, 1),
        )
        
        self.setLayout(mainLayout)
    
    def label(self):
        air = self.air()
        if air.filename() is None:
            path = u"新規"
        else:
            path = os.path.basename(air.filename())
        
        size = len(air.anims())
        t = u"air/{0}/({1})".format(path, size)
        if air.hasChanged():
            return t + u"(更新)"
        else:
            return t
    
    def title(self):
        air = self.air()
        return const.TitleFormat("air", air.filename(), air.hasChanged())

    def jump(self):
        anim = AirJumpDialog.get(self.anim())
        if anim.isValid():
            self.setAnim(anim)
    
    def nextItem(self):
        self._scroll.setValue(self._scroll.value() + 1)
    
    def prevItem(self):
        self._scroll.setValue(self._scroll.value() - 1)
    
    def xview(self):
        import sffairmaker.view
        return sffairmaker.view.View()
    
    exec(def_air())
    
        
def main():
    pass
    
if __name__ == "__main__":
    main()