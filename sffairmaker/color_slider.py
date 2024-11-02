# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
import string

def textToColor(t):
    t = str(t).lower()
    t = "".join(c for c in t if c in string.hexdigits)
    if len(t) == 3:
        # #RGB ‚ÌŒ`‚Ìê‡
        r = t[0:1]
        g = t[1:2]
        b = t[2:3]
        return QColor(int(r*2, 16), int(g*2, 16), int(b*2, 16))
    if len(t) == 6:
        # #RRGGBB ‚ÌŒ`‚Ìê‡
        r = t[0:2]
        g = t[2:4]
        b = t[4:6]
        return QColor(int(r, 16), int(g, 16), int(b, 16))
    else:
        return None

def colorRegex():
    return QRegExp(r"#?[0-9A-F]{0,6}$", Qt.CaseInsensitive)
    
class ColorValidator(QRegExpValidator):
     def __init__(self, parent=None):
        QRegExpValidator.__init__(self, colorRegex(), parent)

class ColorLineEdit(QLineEdit):
    valueChanged = pyqtSignal(QColor)
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self._value = QColor(0, 0, 0)
        self.setText("000000")
        self.setValidator(ColorValidator(self))
        self.textChanged.connect(self._onTextChanged)
    
    def value(self):
        return QColor(self._value)
    
    def sizeHint(self):
        size = []
        for c in string.hexdigits:
            s = self.fontMetrics().size(Qt.TextSingleLine, c*8)
            size.append(QSize(s.width(), s.height()))
        return max(size)
    
    @emitSetter
    def setValue(self):
        if textToColor(self.text()) != self.value():
            with blockSignals(self):
                t = "{0:02X}{1:02X}{2:02X}".format(*crgb(self.value()))
                self.setText(t)
    
    def _onTextChanged(self, text):
        c = textToColor(text)
        if c is not None:
            self.setValue(c)


class ColorLabel(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._color = QColor()
        self._currentNumber = 0
        
    exec(def_update_accessor("color", "currentNumber"))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color())
        
        t = str(self._currentNumber)
        rc = self.fontMetrics().boundingRect(t)
        rc.setWidth(rc.width() * 1.3)
        rc.setHeight(rc.height() * 1.3)
        rc.moveCenter(self.rect().center())
        
        painter.eraseRect(rc)
        painter.drawText(rc, Qt.AlignCenter, t)
        
    
class ColorSlider(QWidget):
    valueChanged = pyqtSignal(QColor)
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._label = ColorLabel(self)
        self._label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        
        self._edit  = ColorLineEdit(self)
        self._scrs = []
        for i in range(3):
            scr = QScrollBar(Qt.Horizontal, parent=self)
            self._scrs.append(scr)
            scr.setRange(0, 255)
            scr.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            
            @scr.valueChanged.connect
            def setColor(v, i=i):
                rgb = list(crgb(self.value()))
                rgb[i] = v
                self.setValue(QColor(*rgb))
        
        @self._edit.valueChanged.connect
        def setScroll(color):
            for i, v in enumerate(crgb(color)):
                self._scrs[i].setValue(v)
        
        self._edit.valueChanged.connect(self._label.setColor)
        relaySignal(self, self._edit, "valueChanged")
        
        self.setLayout(
            hBoxLayout(
                vBoxLayout(
                    (self._label, 1),
                    self._edit,
                ),
                (vBoxLayout(*self._scrs), 1)
            )
        )
    
    exec(def_delegate("_edit", "value", "setValue"))
    exec(def_delegate("_label", "setCurrentNumber"))
    

def main():
    app = QApplication([])
    
    w = QWidget()
    c = ColorSlider()
    c.valueChanged.connect(lambda c:print(c.name()))
    
    w.setLayout(vBoxLayout(
        c,
        ("stretch", 1)
    ))
    w.show()
    
    app.exec_()

if "__main__" == __name__:
    main()