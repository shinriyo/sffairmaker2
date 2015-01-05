#encoding:shift-jis
from __future__ import division, print_function, unicode_literals
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.lineedit_with_browse import LineEditWithBrowse

import os
import os.path
import sys
import itertools
from functools import partial


class CloseButtonBox(QDialogButtonBox):
    def __init__(self, parent):
        flags = QDialogButtonBox.Close
        QDialogButtonBox.__init__(self, flags, parent=parent)
        self.clicked.connect(lambda _:parent.hide())

class CommandLineEdit(LineEditWithBrowse):
    def browse(self):
        path = self.xview().askExternalEditPath()
        if path:
            return '"{0}" "%1"'.format(path)
        else:
            return None
    
    def sizeHint(self):
        sz = LineEditWithBrowse.sizeHint(self)
        w = self.fontMetrics().width("#" * 64)
        return QSize(max(w, sz.width()), sz.height())
    exec def_xview()


class GridColorsTextEdit(QPlainTextEdit):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        self._value = []
        self.textChanged.connect(self._onTextChanged)
    
    def value(self):
        return list(self._value)
    
    def setValue(self, v):
        if self.colorsEq(self._value, v):
            return
        
        self._value = v
        with blockSignals(self):
            self.setText(self.colorsToText(self._value))
        self.valueChanged.emit(self._value)
        
    @classmethod
    def colorsToText(cls, colors):
        lines = []
        for c in colors:
            s = "#{0:02X}{1:02X}{2:02X}".format(c.red(),  c.green(), c.blue())
            lines.append(s)
        return "\n".join(lines)
    
    @classmethod
    def textToColors(cls, text):
        text = unicode(text).strip()
        colors = []
        pat = r"#(?P<R>[0-9A-Z]{1,2})?(?P<G>[0-9A-Z]{1,2})?(?P<B>[0-9A-Z]{1,2})?"
        reRgb = re.compile(pat, re.I)
        import string
        
        whitespace=set(string.whitespace)
        def isSpace(c):
            return c in whitespace
        
        from itertools import ifilterfalse
        for line in text.splitlines():
            line = "".join(ifilterfalse(isSpace, line))
            m = reRgb.match(line)
            if m:
                rgb = []
                for key in "RGB":
                    s = m.group(key)
                    if s:
                        rgb.append(int(s, 16))
                    else:
                        rgb.append(0)
                c = QColor(*rgb)
            else:
                c = QColor(line)
            colors.append(c)
        return colors
    
    @classmethod
    def colorsEq(cls, colors1, colors2):
        return [c.rgb() for c in colors1] == [c.rgb() for c in colors2]
    
    def _onTextChanged(self):
        colors = self.textToColors(self.text())
        if self.colorsEq(self._value, colors):
            return
        self._value = colors
        self.valueChanged.emit(colors)
    
    def sizeHint(self):
        t = "---#999999---"
        w = self.fontMetrics().width(t)
        h = self.fontMetrics().height() * 20
        return QSize(w, h)
    exec def_alias("text", "toPlainText")
    exec def_alias("setText", "setPlainText")
    


class BgImagePathLineEdit(LineEditWithBrowse):
    def browse(self):
        return self.xview().askBgImagePath()
    exec def_xview()

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
        self.setBgImageDelta(self.bgImageDelta() - self._moveDelta())
        self.update()

class BgImageViewCore(AbstractImageViewCore):
    bgImageDeltaChanged = pyqtSignal(QPoint)
    def __init__(self, parent=None):
        AbstractImageViewCore.__init__(self, parent)
        syncAttrTo(self, self.xview(), ("bgImage", "bgImage"))
        syncAttr(self, self.xview(), ("bgImageDelta", "bgImageDelta"))
        syncAttrTo(self, self.xview(), ("bgImageTile", "bgImageTile"))
        self.setTransparent(False)
    
    exec def_xview()
    
    def setBgImageDelta(self, v):
        v = QPoint(v)
        if self._bgImageDelta == v:
            return
        self._bgImageDelta = QPoint(v)
        self.bgImageDeltaChanged.emit(self._bgImageDelta)
        self.update()
    
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
        self._drawBg(painter, event, -self._dragDelta())
        self._drawAxis(painter, event)
        
BgImageView = createImageViewClass(BgImageViewCore)

class BgImageEdit(QWidget):
    deltaChanged = pyqtSignal("QPoint")
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        
        self._filename = BgImagePathLineEdit(parent=self)
        
        self._tile = ValueCheckBox(u"繰り返し", parent=self)
        
        self._deltaX = QSpinBox(self)
        self._deltaX.setRange(-300, 300)
        self._deltaX.setValue(0)
        
        self._deltaY = QSpinBox(self)
        self._deltaY.setRange(-300, 300)
        self._deltaY.setValue(0)
        
        self._delta = QPoint()
        
        self._bgView = BgImageView(self)
        syncAttr(self, self._bgView, ("delta", "bgImageDelta"))
        syncAttr(self._tile, self.xview(), ("value", "bgImageTile"))
        
        syncAttr(self._filename, self.xview(), ("text", "bgImageFilename"))
    
        self.deltaXChanged.connect(lambda x:self.setDelta(QPoint(x, self.delta().y())))
        self.deltaYChanged.connect(lambda y:self.setDelta(QPoint(self.delta().x(), y)))
        
        self.setLayout(vBoxLayout(
            (self._filename, 0),
            (self._tile, 0),
            (hGroupBox("位置", self._deltaX, self._deltaY), 0),
            (self._bgView , 1),
        ))
    exec def_xview()

    exec def_delegate("_bgView", 
        ("bgDelta", "delta"), 
        ("setBgDelta", "setDelta"), 
        ("bgDeltaChanged", "deltaChanged"),
    )
    exec def_delegate("_tile", 
        ("tile", "value"), 
        ("setTile", "setValue"), 
        ("tileChanged", "valueChanged")
    )
    exec def_delegate("_deltaX", ("deltaX", "value"), ("setDeltaX", "setValue"), ("deltaXChanged", "valueChanged"))
    exec def_delegate("_deltaY", ("deltaY", "value"), ("setDeltaY", "setValue"), ("deltaYChanged", "valueChanged"))
    
    
    def setDelta(self, v):
        v = QPoint(v)
        if v == self._delta: return
        
        self._delta = v
        with blockSignals(self):
            self._deltaX.setValue(v.x())
            self._deltaY.setValue(v.y())
        self.deltaChanged.emit(v)
        
        
    def delta(self): return self._delta


class OptionWindow(QWidget):
    def __init__(self, parent=None, settings=None):
        QWidget.__init__(self, parent)
        self._settings = settings
        self.setWindowTitle(u"設定")
        
        # 外部編集とバックアップ
        self._sprExternalEdit = CommandLineEdit()
        self._airExternalEdit = CommandLineEdit()
        
        self._sprExternalEdit.setText(self.settings().externalSprEditingCommand())
        self._sprExternalEdit.textChanged.connect(self.settings().setExternalSprEditingCommand)
        
        self._airExternalEdit.setText(self.settings().externalAirEditingCommand())
        self._airExternalEdit.textChanged.connect(self.settings().setExternalAirEditingCommand)
        
        self._backup = ValueCheckBox("ゴミ箱にバックアップ")
        self._backup.setValue(self.settings().backupToRecycle())
        self._backup.valueChanged.connect(self.settings().setBackupToRecycle)
        
        #背景表示
        self._gridColors = GridColorsTextEdit()
        syncAttr(self._gridColors, self.xview(), ("value", "colorList"))
        
        self._bgImage = BgImageEdit()
        
        # レイアウトここから
        formLayout = QFormLayout()
        formLayout.addRow("画像", self._sprExternalEdit)
        formLayout.addRow("AIR", self._airExternalEdit)
        
        self._panel = QWidget()
        self._panel.setLayout(vBoxLayout(
            groupBox("外部編集", formLayout),
            groupBox("グリッドの色", self._gridColors),
            groupBox("バックアップ", self._backup),
        ))
        
        self._tab = QTabWidget(parent=self)
        self._tab.addTab(self._panel, "基本")
        self._tab.addTab(self._bgImage, "背景")
        
        self.setLayout(vBoxLayout(
            self._tab,
            CloseButtonBox(self),
        ))
    
    exec def_settings()
    exec def_xview()
    
        
def main():
    app = QApplication([])
##    o = OptionWindow()
##    o.show()
    b = BgImageEdit()
    b.show()

    app.exec_()

if "__main__" == __name__:
    main()