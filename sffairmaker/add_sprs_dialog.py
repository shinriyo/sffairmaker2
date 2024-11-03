# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 

from collections import namedtuple

from sffairmaker.qutil import *
from sffairmaker import const
from sffairmaker.radio_group import RadioGroup
from sffairmaker.scale import ScaleWidget
from sffairmaker.image_op import Image256


from sffairmaker.image_view import (
    AbstractImageViewCore,
    createImageViewClass,
    DraggingType,
    NoDragging,
    DraggingView,
)

class DraggingPos(DraggingType):
    def type(self):
        return "pos"
    
    def mousePress(self, evt):
        self.setCursor(Qt.SizeAllCursor)

    def mouseMove(self, evt):
        self.update()
    
    def mouseRelease(self, evt):
        self.setPos(self.pos() - self._moveDelta())


class SprPosViewCore(AbstractImageViewCore):
    posChanged = pyqtSignal(QPoint)
    def __init__(self, parent=None):
        AbstractImageViewCore.__init__(self, parent)
        self._pos = QPoint(0, 0)
        self._image = Image256()
        syncAttrTo(self, self.xview(),
            "bgImage",
            "bgImageDelta",
            "bgImageTile",
        )
        
    exec(def_xview())
    
    def setImage(self, image):
        self._image = Image256(image)
        self.update()
    
    def setPos(self, v):
        v = QPoint(v)
        if self._pos == v:
            return
        self._pos = QPoint(v)
        self.posChanged.emit(self._pos)
        self.update()
    
    def pos(self):
        return QPoint(self._pos)
    
    def _draggingType(self, event, pos):
        if not (event.buttons() & Qt.LeftButton or
                event.buttons() & Qt.MidButton):
            return self._noDragging()
        
        if event.buttons() & Qt.LeftButton:
            return DraggingPos(self)
        else:
            return DraggingView(self)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        if self._dragging.type() == "pos":
            delta = QPoint(self._dragDelta() / self.scale())
        else:
            delta = QPoint(0, 0)
        p = - self.pos() + delta
        self._drawBg(painter, event)
        self._drawImage(painter, self._image, p)
        self._drawAxis(painter, event)

SprPosView = createImageViewClass(SprPosViewCore)


class AddSprsDialog(QDialog):
    posChanged = pyqtSignal(QPoint)
    
    def __init__(self, image=None, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"画像の追加")
        
        self._x = QSpinBox()
        self._y = QSpinBox()
        self._group = QSpinBox()
        self._index = QSpinBox()
        
        self._x.setRange(*const.Sprrange)
        self._y.setRange(*const.SprYRange)
        self._group.setRange(*const.SprGroupRange)
        self._index.setRange(*const.SprIndexRange)
        
        self._useAct = ValueCheckBox(u"Act適用")
        self._withBgColor = ValueCheckBox(u"背景色指定済み")
        self._withBgColor.setValue(True)
        
        items = [
            (const.CropType.NoCrop, u"Cropしない"),
            (const.CropType.CropPosAfter,  u"Cropする（Crop後を基準に位置指定）"),
            (const.CropType.CropPosBefore, u"Cropする（Crop前を基準に位置指定）")
        ]
        
        self._cropType = RadioGroup(u"Crop", items, Qt.Vertical)
        
        self._sequential = ValueCheckBox(u"以降は連番")
        
        for name in """x y group index useAct cropType sequential withBgColor""".split():
            setattr(self, name,
                eval("self._{0}.value".format(name)))
            setattr(self, "set" + name.title(),
                eval("self._{0}.setValue".format(name)))
        
        self._x.valueChanged.connect(lambda _:self.posChanged.emit(self.pos()))
        self._y.valueChanged.connect(lambda _:self.posChanged.emit(self.pos()))
        
        self._imageView = SprPosView()
        self.setColors = self._imageView.setColors
        self.setImage = self._imageView.setImage
        if image is not None:
            self._imageView.setImage(image)
        
        self._scale = ScaleWidget(self)
        self._scale.valueChanged.connect(self._imageView.setScale)
        self._scale.setIndex(1)
        
        self._imageView.setPos(self.pos())
        self._imageView.posChanged.connect(self.setPos)
        self.posChanged.connect(self._imageView.setPos)
        
        @createAction(self._imageView, "Ctrl+9")
        def resetAxisDelta():
            self._imageView.resetAxisDelta()

        @createAction(self._imageView, "Ctrl+0")
        def resetAxisDelta():
            self._scale.zoomReset()
        
        @createAction(self._imageView, "Ctrl+;")
        def zoomIn():
            self._scale.zoomIn()
        
        @createAction(self._imageView, "Ctrl+-")
        def zoomOut():
            self._scale.zoomOut()
        
        def wheelEvent(event):
            if event.orientation() != Qt.Vertical:
                return
            if event.delta() < 0:
                self._scale.zoomOut()
            elif event.delta() > 0:
                self._scale.zoomIn()
        self._imageView.wheelEvent = wheelEvent
        
        def sizeHint():
            return QSize(400, 400)
        self._imageView.sizeHint = sizeHint
        
        buttonBox = dialogButtons(self)
        
        #レイアウトここから
        leftLayout = vBoxLayout(
            hGroupBox(u"登録先", self._group, self._index),
            hGroupBox(u"位置", self._x, self._y),
            self._withBgColor,
            self._useAct,
            self._cropType,
            self._sequential,
            ("stretch", 1)
        )
        
        scaleBox = hGroupBox(u"倍率", self._scale)
        scaleBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        rightLayout = vBoxLayout(
            scaleBox,
            (self._imageView, 1)
        )
        mainLayout = vBoxLayout(
            (hBoxLayout(leftLayout, rightLayout), 1),
            buttonBox,
        )
        self.setLayout(mainLayout)
    
    def pos(self):
        return QPoint(self.x(), self.y())
    
    def setPos(self, p):
        if self.pos() == p:
            return
        
        with blockSignals(self._x, self._y):
            self.setX(p.x())
            self.setY(p.y())
        self.posChanged.emit(p)
    
    @classmethod
    def get(cls, image, parent=None):
        ins = cls(parent=parent)
        ins.setImage(image)
        return ins.ask()
    
    def ask(self):
        if not self.exec_():
            return None
        else:
            kw = {}
            for name in "group index x y useAct cropType withBgColor".split():
                kw[name] = getattr(self, name)()
            return kw, self.sequential()


def main():
    app = QApplication([])
    
    import os.path
    imagePath = os.path.join(os.path.dirname(__file__),
                             r"..\testdata\DarkPrison.bmp")
    
    image = Image256(imagePath)
    print(AddSprsDialog.get(image))
    
    
    
if "__main__" == __name__:
    main()