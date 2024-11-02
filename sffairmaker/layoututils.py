#encoding: shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from PyQt5.QtGui import (
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt

from sffairmaker.qutils import def_alias

class SquareButton(QPushButton):
    def sizeHint(self):
        sz = QPushButton.sizeHint(self)
        return QSize(sz.height(), sz.height())


class ValueMixin:
    exec(def_alias("valueChanged", "toggled"))
    exec(def_alias("value", "isChecked"))
    def setValue(self, v):
        return self.setChecked(v)

class ValueCheckBox(QCheckBox, ValueMixin):
    def __init__(self, *a, **kw):
        QCheckBox.__init__(self, *a, **kw)
        self.setCheckable(True)

class ValueButton(QPushButton, ValueMixin):
    def __init__(self, *a, **kw):
        QPushButton.__init__(self, *a, **kw)
        self.setCheckable(True)

def hGroupBox(caption, *a, **kw):
    groupBox = QGroupBox(caption)
    groupBox.setLayout(hBoxLayout(*a, **kw))
    return groupBox

groupBox = groupBoxH = hGroupBox

def vGroupBox(caption, *a, **kw):
    groupBox = QGroupBox(caption)
    groupBox.setLayout(vBoxLayout(*a, **kw))
    return groupBox
groupBoxV = vGroupBox


def boxLayout(orientation, *items, **kw):
    if orientation == Qt.Horizontal:
        layout = QHBoxLayout()
        lineClass = HLine
    else:
        layout = QVBoxLayout()
        lineClass = VLine
    layout.setMargin(0)
    layout.setSpacing(0)
    
    lastStretch=kw.pop("stretch", False)
    for item in items:
        if isinstance(item, (list, tuple)):
            x, w = item[:2]
            if item[2:]:
                alignment, = item[2:]
            else:
                alignment = Qt.Alignment(0)
        else:
            w = 0
            alignment = Qt.Alignment(0)
            x = item
            
        if x == "spacing":
            layout.addSpacing(w)
        elif x == "stretch":
            layout.addStretch(w)
        elif x == "line":
            layout.addWidget(lineClass(), w, alignment)
        elif isinstance(x, QLayout):
            layout.addLayout(x, w)
        else:
            layout.addWidget(x, w, alignment)
        
    if lastStretch:
        layout.addStretch(1)
    return layout


def hBoxLayout(*a, **kw):
    return boxLayout(Qt.Horizontal, *a, **kw)

def vBoxLayout(*a, **kw):
    return boxLayout(Qt.Vertical, *a, **kw)
    
def vBoxLayout(*a, **kw):
    L = hBoxLayout(*a, **kw)
    L.setDirection(L.TopToBottom)
    return L

class DialogButtons(QDialogButtonBox):
    def __init__(self, dlg):
        f = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        QDialogButtonBox.__init__(self, f, parent=dlg)
        self.accepted.connect(dlg.accept)
        self.rejected.connect(dlg.reject)
    
    def okButton(self):
        return self.button(QDialogButtonBox.Ok)
        
    def cancelButton(self):
        return self.button(QDialogButtonBox.Cancel)

dialogButtons = DialogButtons



def commandButton(caption):
    def f(callback):
        b = QPushButton(caption, parent=None)
        b.clicked.connect(lambda _:callback())
        return b
    f.__name__ = "commandButton"
    return f


def main():
    pass

if "__main__" == __name__:
    main()