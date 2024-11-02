# coding: utf-8
#独立させるまでもない関数・クラスの巣窟

from __future__ import division, with_statement, print_function
#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# from contextlib import contextmanager, nested
#from PyQt5.QtWidgets import QCheckBox, QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtWidgets import *
from contextlib import contextmanager
import re
import copy

import io
from functools import wraps, partial
from sffairmaker.line import VLine, HLine
# import cStringIO
from io import StringIO
import PIL.Image


def upper_head_string(s):
    return s[0].upper() + s[1:]

def list_get(alist, i, default=None):
    if 0 <= i < len(alist):
        return alist[i]
    return default

def list_range(alist):
    return range(len(alist))

def def_alias(newname, oldname):
    return """
@property
def {0}(self):
    return self.{1}""".format(newname, oldname)

def def_delegate(delegateto, *names):
    """
    >>> class A:
    ...     x = 10
    ...     spam = 20
    ...
    >>> class B:
    ...     exec def_delegate("_a", "x", ("egg", "spam"))
    ...     def __init__(self):
    ...         self._a = A()
    ...
    >>> b = B()
    >>> b.x
    10
    >>> b.egg
    20
    >>> b.spam
    Traceback (most recent call last):
    AttributeError: B instance has no attribute 'spam'
    """
    exec_strs = []
    for name in names:
        if isinstance(name, tuple):
            methodName, subjectMethodName = name
        else:
            methodName = subjectMethodName = name
        execstr = """
@property
def {methodName}(self):
    return self.{delegateto}.{subjectMethodName}
        """.format(
            delegateto=delegateto,
            subjectMethodName=subjectMethodName,
            methodName=methodName, 
        )
        exec_strs.append(execstr)
    return "\n".join(exec_strs).rstrip()


def def_qgetter(*names):
    execstrs = []
    for name in names:
        s = """\
def {getter}(self):
    return self.{attr}""".format(
            getter=name,
            attr="_"+name
        )
        execstrs.append(s)
    return "\n\n".join(execstrs)

def qsetter_name(name):
    return "set" + name[0].upper() + name[1:]

def def_qsetter(*names):
    execstrs = []
    for name in names:
        s = """\
def {setter}(self, v):
    self.{attr} = v""".format(
            setter=qsetter_name(name),
            attr="_"+name
        )
        execstrs.append(s)
    return "\n\n".join(execstrs)

def def_qaccessor(*names):
    s = def_qgetter(*names) + "\n" + def_qsetter(*names)
    return s

def def_sff():
    s = "def sff(self):return self.xmodel().sff()"
    return def_xmodel() + "\n" + s

def def_air():
    s = "def air(self):return self.xmodel().air()"
    return def_xmodel() + "\n" + s

def def_xview():
    return """\
def xview(self):
    if not hasattr(self, "_xview") or getattr(self, "_xview") is None:
        import sffairmaker.view
        self._xview = sffairmaker.view.View()
    return self._xview
"""

def def_xmodel():
    return """\
def xmodel(self):
    if not hasattr(self, "_xmodel") or getattr(self, "_xmodel") is None:
        import sffairmaker.model
        self._xmodel = sffairmaker.model.Model()
    return self._xmodel
"""

def def_settings():
    return """\
def settings(self):
    if not hasattr(self, "_settings") or getattr(self, "_settings") is None:
        if hasattr(self.parent(), "settings"):
            return self.parent().settings()
        else:
            import sffairmaekr.settings
            return sffairmaker.settings.Settings()
    return self._settings
"""

def cycle_pairwise(alist):
    alist = list(alist)
    return zip(alist, alist[1:] + [alist[0]])

def syncAttr(obj1, obj2, *names):
    _syncAttr(obj1, obj2, True, *names)

def syncAttrTo(slave, master, *names):
    _syncAttr(slave, master, False, *names)
    
def _syncAttr(obj1, obj2, both, *names):
    def setter_name(name):
        return "set" + name[0].upper() + name[1:]
    def getter_name(name):
        return name
    def signal_name(name):
        return name + "Changed"
    def getter(x, name):
        return getattr(x, getter_name(name))
    def setter(x, name):
        return getattr(x, setter_name(name))
    def signal(x, name):
        return getattr(x, signal_name(name))
    def connect(x1, name1, x2, name2):
        signal(x1, name1).connect(setter(x2, name2))
    
    for name in names:
        if isinstance(name, str):
            n1 = n2 = name
        else:
            n1, n2 = name
        setter(obj1, n1)(getter(obj2, n2)())
        connect(obj2, n2, obj1, n1)
        
        if both:
            connect(obj1, n1, obj2, n2)


def relaySignal(relayTo, relayFrom, *signalNames):
    for signalName in signalNames:
        sto = getattr(relayTo, signalName)
        sfrom = getattr(relayFrom, signalName)
        sfrom.connect(sto.emit)

def emitSetter(f):
    return mySetter(emit=True)(f)
    
def mySetter(emit=False, signal=None):
    def _mySetterDeco(f):
        m = re.match("set(.*)", f.__name__)
        name = m.group(1)
        name = name[0].lower() + name[1:]
        attrName = "_" + name
        emitSignalName = name + "Changed"
        
        @wraps(f)
        def _mySetterWrapper(self, v):
            oldvalue = getattr(self, attrName)
            if oldvalue == v:
                return False
            if signal is not None:
                signalName, callbackMethodName = signal
                getattr(oldvalue, signalName).disconnect(getattr(self, callbackMethodName))
            setattr(self, attrName, v)
            if signal is not None:
                signalName, callbackMethodName = signal
                getattr(v, signalName).connect(getattr(self, callbackMethodName))
            f(self)
            
            if emit:
                getattr(self, emitSignalName).emit(v)
            return True
        return _mySetterWrapper
    return _mySetterDeco

# def blockSignals(*widgets):
#     return nested(*[_blockAWidgetSignals(w) for w in widgets])

@contextmanager
def blockSignals(*widgets):
    # �������������������
    contexts = [_blockAWidgetSignals(w) for w in widgets]
    try:
        # ��������������������
        for context in contexts:
            context.__enter__()  # ��������������
        yield  # ��������������
    finally:
        # ����������������������
        for context in reversed(contexts):
            context.__exit__(None, None, None)  # ��������������

@contextmanager
def _blockAWidgetSignals(widget):
    if widget.signalsBlocked():
        yield widget
    else:
        widget.blockSignals(True)
        yield widget
        widget.blockSignals(False)
    
@contextmanager
def savePainter(painter):
    painter.save()
    yield
    painter.restore()


def def_update_setter(*names):
    execstrs = []
    for name in names:
        attr = "_" + name
        setter = "set" + name[0].upper() + name[1:]
        execstrs.append("""\
def {setter}(self, v):
    self.{attr} = v
    self.update()
""".format(setter=setter, attr=attr))
    return "\n".join(execstrs)

def def_update_accessor(*names):
    return def_qgetter(*names) + "\n\n" + def_update_setter(*names)

def add_dict(adict, k, v):
    d = dict(adict)
    d[k] = v
    return d

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
    layout.setContentsMargins(0, 0, 0, 0)  # 左, 上, 右, 下のマージンを設定
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


def colorXor(c1, c2=QColor(255, 255, 255)):
    return QColor(c1.rgb() ^ c2.rgb())

def pxy(p):
    return (p.x(), p.y())

def crgb(qcolor):
    if not isinstance(qcolor, QColor):
        qcolor = QColor(qcolor)
    return (qcolor.red(), qcolor.green(), qcolor.blue())

def rcvtx(qrect):
    return (qrect.left(), qrect.top(), qrect.right(), qrect.bottom())

def attributeError(self, name):
    """
    >>> obj = object()
    >>> try:
    ...     obj.name
    ... except AttributeError as e:
    ...     pass
    ...
    >>> e.args == attributeError(obj, "name").args
    True
    """
    return AttributeError("'{0.__class__.__name__}' object has no attribute '{1}'"
                            .format(self, name))


def createAction(obj, shortcut):
    def _createAction(callback):
        a = QAction(obj)
        a.setShortcut(shortcut)
        a.triggered.connect(callback)
        obj.addAction(a)
        return a
    return _createAction

    
def pilimage_to_qimage(pilimage):
    # fp = cStringIO.StringIO()
    fp = StringIO()
    pilimage.save(fp, "BMP")
    qimage = QImage()
    qimage.loadFromData(fp.getvalue(), "BMP")
    return qimage

def qimage_to_pilimage(qimage):
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    qimage.save(buffer, "BMP")
    
    # fp = cStringIO.StringIO()
    fp = StringIO()
    fp.write(buffer.data())
    buffer.close()
    fp.seek(0)
    return PIL.Image.open(fp)

def saveToPcx(image, filename):
    qimage_to_pilimage(image).save(filename)


if __debug__:
    def debugDataDir():
        from os.path import join, dirname
        return join(dirname(__file__), u"../test_with_file/data")


def main():
    from subprocess import call
    call(["nosetests", __file__, "--with-doctest"])
    
if __name__ == "__main__":
    main()
