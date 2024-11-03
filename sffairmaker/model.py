# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.qutil import *
from sffairmaker import (
    sff_data,
    air_data,
    image_op,
    const,
    act,
    null,
)

from sffairmaker.image_op import Image256, NullImage, Format_Indexed8
from sffairmaker.model_proxy import Proxy
from sffairmaker.model_null import (
    NullProxy,
    NullSpr,
    NullAnim,
    NullElm,
)
Null = NullProxy

from sffairmaker.sort_path import key_path
from sffairmaker.allfiles import allfiles

from sffairmaker import spr_display
from sffairmaker import gif, apng
import sffairmaker.settings
from fractions import Fraction

import os
from contextlib import contextmanager
from collections import namedtuple, defaultdict
from operator import methodcaller, attrgetter
from weakref import WeakKeyDictionary
from subprocess import Popen

import itertools
import math
import types

from sffairmaker.trash import trash
from sffairmaker import spr_display
import hashlib


def editExternal_(tempFileNameMetName, startEditingMetName):
    def editExternal(self):
        fileName = getattr(self, tempFileNameMetName)()
        if not self.saveAs(fileName):
            return False
        if not getattr(self, startEditingMetName)(fileName):
            return False
        if not self.waitExternalEditing():
            return False
        self.swap(fileName)
        
        return True
    return editExternal
    

class Palette(QObject):
    def __init__(self, model=None):
        QObject.__init__(self)
        self._model = model
    
    def setColorTable(self, colorTable):
        raise NotImplimentedError
    
    def colorTable(self):
        raise NotImplimentedError
    
    def open(self, filename):
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == ".act":
            _open = act.open
        elif ext == ".txt":
            _open = act.openText
        else:
            _open = act.openImage
        
        try:
            colorTable = _open(filename)
        except EnvironmentError as e:
            self.cannotOpenFileMsg(filename)
            return False
        else:
            self.setColorTable(colorTable)
            return True
    
    swap = open
    
    def save(self, filename):
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == ".act":
            _save = act.save
        elif ext == ".txt":
            _save = act.saveToText
        else:
            _save = act.saveToImage
        
        try:
            _save(filename, self.colorTable())
        except EnvironmentError as e:
            self.cannotSaveFileMsg(filename)
            return False
        else:
            self._filename = self._source = filename
            return True
    
    def title(self):
        return self.filename()
    
    def display(self):
        self._model.setPalette(self)
    
    def xview(self):
        return self._model.xview()
    
    def __getattr__(self, name):
        return getattr(self._model, name)
    

class SprPalette(Palette):
    def __init__(self, spr):
        Palette.__init__(self, model=spr._model)
        self._spr = spr
    
    def colorTable(self):
        return self._spr.image().colorTable()
    
    def setColorTable(self, colorTable):
        return self._spr.setColorTable(colorTable)


class Spr(Proxy):
    Null = NullSpr
    
    def _subject(self):
        return self._data.sprById(self._id)
    
    def change(self, **kw):
        if self._change(**kw):
            self._notifyUpdate()
            return True
        else:
            return False
    
    def _change(self, **kw):
        if self.isUseActFixed():
            kw.pop("useAct", None)
        return self._data.changeSpr(self._id, **kw)
    
    def isUseActFixed(self):
        # (0, 0) と (9000, 0) は キャラ用SFFでは常にAct適用
        return self.group_index() in [(0, 0), (9000, 0)] and \
               self._submodel.isCharSff()
    
    def useAct(self):
        if self.isUseActFixed():
            return True
        else:
            return Proxy.__getattr__(self, "useAct")()
        
    def remove(self):
        if not self.isValid():
            return
        with self._updating():
            self._data.removeSpr(self._id)
    
    def clone(self):
        if not self.isValid():return
        with self._updating():
            spr = self._submodel._Spr(self._data.cloneSpr(self._id))
        self._submodel.xview().setSpr(spr)

    def swap(self, filename=None):
        filename = filename or self._submodel.askSprSwapPath()
        if not filename:
            return
        
        filename = str(filename)
        try:
            image = Image256(filename)
        except (IOError, OSError):
            self.invaildImageFormatMsg(filename)
            return
        self.change(image=image)
    
    def eraseRects(self, rects):
        rects = [rc.translated(self.pos()) for rc in rects]
        image = image_op.eraseRects(self.image(), rects)
        self.change(image=image)

    def eraseRectsColors(self, rects):
        rects = [rc.translated(self.pos()) for rc in rects]
        image = image_op.eraseRectsColors(self.image(), rects)
        self.change(image=image)
    
    def autoCrop(self):
        image1, delta = image_op.autoCrop(self.image())
        pos = self.pos() - delta
        self.change(image=image1, x=pos.x(), y=pos.y())
    
    def cropRect(self, rect):
        image1, delta = image_op.cropRect(self.image(), rect)
        pos = self.pos() - delta
        self.change(image=image1, x=pos.x(), y=pos.y())
    
    def allocBgColor(self):
        try:
            image1 = image_op.allocBgColor(self.image())
        except image_op.NoUnusedColorError:
            self.noUnusedColorMsg()
            return
        else:
            self.change(image=image1)
    
    def deleteColors(self, indexes):
        image = image_op.deleteColors(self.image(), indexes)
        return self.change(image=image)
    
    def deleteUnusedColors(self):
        self.change(image=image_op.deleteUnusedColors(self.image()))
    
    def replaceColorTable(self, colorTable=None):
        if colorTable is None:
            colorTable = self.commonColorTable()
        image1 = image_op.replaceColorTable(self.image(), colorTable)
        self.change(image=image1)
    
    def cleanColorTable(self, colorTable=None):
        if colorTable is None:
            colorTable = self.commonColorTable()
        image = image_op.cleanColorTable(self.image(), colorTable)
        self.change(image=image)
    
    def addColorsToCommonPalette(self):
        #画像色を全体パレットに追加し、Act適用にする
        colorTable, image = image_op.addImageColors(
            self.commonColorTable(), 
            self.commonUsedColorIndexes(),
            self.image()
        )
        
        r1 = self.sff()._setColorTable(colorTable)
        r2 = self._change(image=image, useAct=True)
        if r1 or r2:
            self._notifyUpdate()
    
    def invertH(self):
        return self.invert(True, False)
    
    def invertV(self):
        return self.invert(False, True)

    def invert(self, h, v):
        if not h and not v:
            return
        kw = {}
        kw["image"] = image = self.image().mirrored(horizontal=h, vertical=v)
        if h:
            kw["x"] = - self.x() + image.width()
        if v:
            kw["y"] = - self.y() + image.height()
        
        self.change(**kw)
        
    def setColorTable(self, colorTable):
        if self.image().colorTable() == colorTable:
            return
        image = QImage(self.image())
        image.setColorTable(colorTable)
        self.change(image=image)
        
    def colorTable(self):
        return self.image().colorTable()
    
    def palette(self):
        return SprPalette(self)
        
    def saveColorTable(self, filename=None):
        filename = filename or self.askActSavePath()
        if not filename:
            return
        self.palette().save(filename)
    
    def swapColorTable(self, filename=None):
        filename = filename or self.askActOpenPath()
        if not filename:
            return
        self.palette().open(filename)
    
    def save(self, filename=None):
        filename = filename or self._submodel.askSprSavePath()
        filename = str(filename)
        if not filename:
            return False
        
        def getColorTable(spr):
            return spr_display.colorTable(
                spr,
                self.actColorTable(),
                self.sprDisplayMode(),
            )
        try:
            self._data.saveSpr(self._id, filename, getColorTable)
            return True
        except sff_data.ImageSaveError as e:
            self.saveImageErrorMsg(e.filename)
            return False
    
    saveAs = save
    
    def saveGroup(self, filename=None):
        filename = filename or self.askCsvSavePath()
        filename = str(filename)
        if not filename:
            return
        
        format = self.askCsvSaveFormat(filename, self.groupSprs())
        if not format:
            return
        def getColorTable(spr):
            return spr_display.colorTable(
                spr,
                self.actColorTable(),
                self.sprDisplayMode(),
            )
        try:
            self._data.saveGroup(self.group(), filename, format, getColorTable)
        except sff_data.CsvSaveError as e:
            self.saveErrorMsg(e.filename)
        except sff_data.ImageSaveError as e:
            self.saveImageErrorMsg(e.filename)
    
    def groupSprs(self):
        return self.sff().groupSprs(self.group())
    
    def usedColorIndexes(self):
        return self.sff().imageUsedColorIndexes(self.image())
    
    
    editExternal = editExternal_("tempSprFileName", "startExternalSprEditing")
    
    #ここから、糖衣構文的・補助的メソッドの定義
    def group_index(self):
        return (self.group(), self.index())
    
    def pos(self):
        return QPoint(self.x(), self.y())
    
    def size(self):
        return self.image().size()
    
    def sff(self):
        return self._submodel
    
    def commonPalette(self):
        return self.sff().palette()
    
    def commonColorTable(self):
        return self.sff().colorTable()
    
    def commonUsedColorIndexes(self):
        return self.sff().usedColorIndexes()
    
    
class Anim(Proxy):
    Null = NullAnim
    ParsingError           = air_data.ParsingError
    PasingSectionNameError = air_data.PasingSectionNameError
    
    def _subject(self):
        return self._data.animById(self._id)
    
    def elms(self):
        return [self._submodel.Elm(elmId) for elmId in self._data.elmIds(self._id)]
    
    def change(self, **kw):
        oldLoopElm = self.loopElm()
        if self._change(**kw):
            self._notifyUpdate()
    
    def _change(self, **kw):
        return self._data.changeAnim(self._id, **kw)
    
    def copyElm(self, pos, elm):
        with self._updating():
            return self._submodel.Elm(self._data.copyElm(self._id, pos, elm._id))
    
    def moveElm(self, pos, elm):
        with self._updating():
            return self._submodel.Elm(self._data.moveElm(self._id, pos, elm._id))
    
    def newElm(self):
        pos = self.askElmInsertPos(
            self,
            caption=u"新しいコマの挿入先"
        )
        if pos is None:
            return
        
        with self._updating():
            elm = self._submodel.Elm(self._data.newElm(self._id, pos))
        self.setElm(elm)
    
    
    def remove(self):
        with self._updating():
            self._data.removeAnim(self._id)
    
    def clone(self):
        if not self.isValid():return
        with self._updating():
            anim = self._submodel.Anim(self._submodel._data.cloneAnim(self._id))
        self._submodel.xview().setSpr(anim)
    
    def toString(self):
        return self._data.animToString(self._id)
    
    def changeFromString(self, ss):
        hasChanged = self._data.changeAnimFromString(self._id, ss)
        if hasChanged:
            self._notifyUpdate()
    
    def textEdit(self):
        s = self.textDialog(self.toString())
        if s.isNull():
            return
        s = str(s)
        
        try:
            self.changeFromString(s)
        except self.ParsingError as e:
            self.actionParsingErrorMsg(e.lineno, e.line)
        except self.PasingSectionNameError as e:
            self.actionParsingSectionNameErrorMsg(e.section_name)
        else:
            pass
    
    def _saveToGif(self, filename):
        gifElms = []
        loopTime = 60 * 1.5
        
        beforeLoop = list(self.timeLineBeforeLoop())
        loop = list(self.timeLineLoop())
        
        if not beforeLoop and len(loop) == 1:
            timeLine = loop
        elif loop:
            loopCount = int(math.ceil(loopTime / len(loop)))
            timeLine = beforeLoop + loop * loopCount
        else:
            timeLine = beforeLoop
            
        for elm, group in itertools.groupby(timeLine):
            time = len(list(group))
            spr = elm.spr()
            if not spr.isValid() or spr.image().isNull():
                image = Image256()
                pos = QPoint(0, 0)
            else:
                image = spr_display.image(
                    spr,
                    self.actColorTable(),
                    self.sprDisplayMode(),
                )
                pos = elm.pos() - elm.spr().pos()
                image, pos = image_op.mirrored(image, pos, spr.pos(), *elm.hv())
                
            gifElms.append(gif.Element(
                image= image,
                pos  = pos,
                time = Fraction(time, 60),
            ))
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in [".png", ".apng"]:
            apng.save(filename, gifElms)
        else:
            gif.save(filename, gifElms)
    
    def saveToGif(self, filename=None):
        filename = filename or self.askGifSavePath()
        if not filename:
            return
        
        savingThread = SimpleThread(
            partial(self._saveToGif, filename),
            parent=self
        )
        savingThread.start()
        with self.savingProgress():
            while savingThread.isRunning():
                QApplication.processEvents()
                QThread.msleep(50)
        
        try:
            savingThread.reraise()
        except EnvironmentError as e:
            self.saveImageErrorMsg(e.filename)
            return False
        else:
            return True
        
    def timeLineLoop(self):
        elms = [(e, e.utime()) for e in self.elms()]
        
        e, t = elms[-1]
        if e.inf():
            yield e
        
        if self.loop() is not None:
            for e, t in elms[self.loop():]:
                for _ in range(t):
                    yield e
    
    def timeLineBeforeLoop(self):
        elms = [(e, e.utime()) for e in self.elms()]
        if all(t == 0 for e, t in elms):
            e, _ = elms[0]
            yield e
        else:
            for e, t in elms:
                for _ in range(t):
                    yield e
    
    #ここから、糖衣構文的・補助的メソッドの定義
    def timeLine(self):
        from itertools import cycle, chain
        return cycle(
                chain(
                    self.timeLineBeforeLoop(),
                    cycle(
                        self.timeLineLoop())))
    
    def hasLoop(self):
        return self.loop() is not None
    
    def loopTime(self):
        return sum(e.utime() for e in self.elms()[self.loop():])
    
    def preLoopTime(self):
        return sum(e.utime() for e in self.elms()[:self.loop()])
    
    def loopElm(self):
        if self.loop() is not None:
            return self.elms()[self.loop()]
        else:
            return None
        
    def allTime(self):
        return sum(e.utime() for e in self.elms())
    
    def elmStartTime(self, elmId):
        elms = self.elms()
        i = elms.index(elmId)
        return sum(e.utime() for e in elms[:i])
    

class Elm(Proxy):
    Null = NullElm

    def _subject(self):
        return self._data.elmById(self._id)
    
    @property
    def _model(self):
        return self._submodel._model
    
    @property
    def model(self):
        return self._submodel._model
    
    def spr(self):
        return self._model.sff().sprByIndex(self.group(), self.index())
    
    def anim(self):
        return self._submodel.Anim(self._data.animIdOfElm(self._id))
    
    def clsn1Default(self):
        return self.anim().clsn1()
    
    def clsn2Default(self):
        return self.anim().clsn2()
    
    def change(self, **kw):
        kw0 = dict(kw)
        
        anim_changed = False
        if "loopStart" in kw:
            if kw.pop("loopStart"):
                loop = self.indexInAnim()
            else:
                loop = None
            anim_changed = anim_changed or self.anim()._change(loop=loop)
        
        for i in [1, 2]:
            name = "clsn{0}Default".format(i)
            if name in kw:
                v = kw.pop(name)
                key = "clsn{0}".format(i)
                anim_changed = anim_changed or self.anim()._change(**{key: v})
        
        if self._change(**kw) or anim_changed:
            self._notifyUpdate()
        
        for k, v in kw0.items():
            assert getattr(self, k)() == v
        
    def _change(self, **kw):
        return self._data.changeElm(self._id, **kw)
    
    def move(self):
        pos = self.askElmInsertPos(
            self.anim(),
            caption=u"移動先"
        )
        if pos is not None:
            self.anim().moveElm(pos, self)
    
    def clone(self):
        pos = self.askElmInsertPos(
            self.anim(),
            caption=u"コピーの挿入先"
        )
        if pos is None:
            return
        elm = self.anim().copyElm(pos, self)
        self.setElm(elm)

    def remove(self):
        with self._updating():
            self._data.removeElm(self.anim()._id, self._id)
    
    def moveAllClsn(self, delta):
        self.change(clsn1Default=self.anim().clsn1().move_all(delta),
                    clsn2Default=self.anim().clsn2().move_all(delta),
                    clsn1=self.clsn1().move_all(delta),
                    clsn2=self.clsn2().move_all(delta),
        )
    
    def moveAllClsnPos(self, delta):
        pos = self.pos() + delta
        
        self.change(clsn1Default=self.anim().clsn1().move_all(delta),
                    clsn2Default=self.anim().clsn2().move_all(delta),
                    clsn1=self.clsn1().move_all(delta),
                    clsn2=self.clsn2().move_all(delta),
                    x=pos.x(),
                    y=pos.y()
        )

        
    #ここから、糖衣構文的・補助的メソッドの定義
    def utime(self):
        return max(self.time(), 0)
    
    def inf(self):
        return self.time() < 0
    
    def group_index(self):
        return (self.group(), self.index())
    
    def image(self):
        spr = self.spr()
        if spr:
            return spr.image()
        else:
            return NullImage()
    
    def pos(self):
        return QPoint(self.x(), self.y())
    
    def hv(self):
        return (self.h(), self.v())
        
    def indexInAnim(self):
        return self.anim().elms().index(self)
    
    def loopStart(self):
        return self.indexInAnim() == self.anim().loop()
    
    def startTime(self):
        return self.anim().elmStartTime(self)



class Act(Palette):
    def __init__(self, model=None):
        Palette.__init__(self, model)
        self._filename = ""
        self._colorTable = None
    
    exec(def_qgetter("filename"))
    
    def colorTable(self):
        assert self._colorTable is not None
        return self._colorTable
    
    def setColorTable(self, colorTable):
        self._colorTable = colorTable
    
    def open(self, filename):
        r = Palette.open(self, filename)
        if r:
            self._filename = filename
        return r

class ActSubModel(QObject):
    listUpdated = pyqtSignal()
    def __init__(self, model):
        QObject.__init__(self)
        self._model = model
        self._acts = []
    
    def xview(self):
        return self._model.xview()
    
    def acts(self):
        return list(self._acts)
    
    def open(self, filename=None, display=True):
        print(filename)
        filename = filename or self.askActOpenPath()
        if not filename:
            return
        return self._open(filename)
    
    def _open(self, filename):
        a = Act(self._model)
        r = a.open(filename)
        if r:
            try:
                self._acts = [a]
                a.display()
                return a
            finally:
                self.listUpdated.emit()
        else:
            return None
    
    def __getattr__(self, name):
        return getattr(self._model, name)
    

UndoState = namedtuple("UndoState", "view data")



class SimpleThread(QThread):
    def __init__(self, callable, parent=None):
        QThread.__init__(self, parent=parent)
        self._callable = callable
        self._exception = None
        self._result = None
        self._exc_info = None
    
    exec(def_qgetter("callable", "exception", "result", "exc_info"))
    
def run(self):
    try:
        self._result = self._callable()
    except Exception as e:  # 一時的な変数名に変更
        import sys
        self._exception = e  # 一時変数の値をインスタンス変数に代入
        self._exc_info = sys.exc_info()
        pass

    
def reraise(self):
    if self._exc_info:
        type, value, trace = self.exc_info()
        raise value.with_traceback(trace)  # 新しい構文


class SubModel(QObject):
    _DataClass = None
    updated = pyqtSignal()
    filenameChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, model):
        QObject.__init__(self)
        self._model = model
        self._data = self._DataClass()
        self._data.filenameChanged.connect(self.filenameChanged.emit)
        self._undoBuffer = UndoBuffer(self._memento())
        self.create()
        
        self._blockNofifyUpdating = 0
    
    def __getattr__(self, name):
        return getattr(self._model, name)
        
    def xview(self):
        return self._model.xview()
    
    def filename(self):
        return self._data.filename()
    
    def name(self):
        if self.filename() is None:
            return "NoName"
        else:
            name, _ = os.path.splitext(os.path.basename(self.filename()))
            return name
        
    def _memento(self):
        return UndoState(
            None,
            self._data.memento(),
        )
    
    def _restore(self, m):
        if m is None:
            return False
        self._data.restore(m.data)
        return True
    
    @contextmanager
    def _updating(self):
        """
        dataに変更を加えるような操作をwith x._updating():で囲むと、
        with 文を抜けるときにサブモデルに変更があったことを通知する。
        """
        
        try:
            yield
        except Exception:
            raise
        else:
            self._notifyUpdate()
    
    def _notifyUpdate(self):
        if self._blockNofifyUpdating:
            return
        self._undoBuffer.push(self._memento())
        self.updated.emit()

    @contextmanager
    def _blockingNotifyUpdating(self):
        self._blockNofifyUpdating += 1
        yield
        self._blockNofifyUpdating -= 1
    
    def _undoReset(self):
        self._undoBuffer.reset(self._memento())
    
    def _undoSave(self):
        self._undoBuffer.save()
    
    def undo(self):
        m = self._undoBuffer.undo()
        if self._restore(m):
            self.updated.emit()
        else:
            self.cannotUndo()
        
    def redo(self, *a):
        m = self._undoBuffer.redo()
        if self._restore(m):
            self.updated.emit()
        else:
            self.cannotRedo()
        
    def askSavePath(self):
        raise NotImplementedError
        
    def askOpenPath(self):
        raise NotImplementedError
    
    def askSaveBefore(self):
        raise NotImplementedError
    
    def hasChanged(self):
        return self._undoBuffer.hasChanged()
    
    def askIfChanged(self):
        if not self.hasChanged():
            return True
        r = self.askSaveBefore()
        if r == "cancel":
            return False
        elif r == "no":
            return True
        elif r == "yes":
            return self.save()
        else:
            assert False, r
    
    def create(self):
        if not self.askIfChanged():
            return
        self._data.create()
        self.updated.emit()
        self._undoReset()
        
    def open(self, filename=None):
        if not self.askIfChanged():
            return
        
        filename = filename or self.askOpenPath()
        if not filename:
            return
        
        openingThread = SimpleThread(
            partial(self._open, filename),
            parent=self,
        )
        openingThread.start()
        with self.openingProgress():
            while openingThread.isRunning():
                QApplication.processEvents()
                QThread.msleep(50)
        
        try:
            openingThread.reraise()
        except EnvironmentError as e:
            self.cannotOpenFileMsg(filename)
            return False
        else:
            if openingThread.result():
                self.showOpeningErrors(openingThread.result())
            self.addRecentFile(filename)
            self._undoReset()
            self.updated.emit()
            return True
        

    def swap(self, filename):
        filename = filename or self.askOpenPath()
        if not filename:
            return
        
        openingThread = SimpleThread(
            partial(self._open, filename),
            parent=self,
        )
        openingThread.start()
        with self.openingProgress():
            while openingThread.isRunning():
                QApplication.processEvents()
                QThread.msleep(50)
        
        try:
            openingThread.reraise()
        except EnvironmentError as e:
            self.cannotOpenFileMsg(filename)
            return False
        else:
            if openingThread.result():
                self.showOpeningErrors(openingThread.result())
            self._notifyUpdate()
            self.updated.emit()
            return True
            
    def _open(self, filename):
        filename = os.path.abspath(filename)
        return self._data.open(filename)
    
    def reload(self):
        assert self._data.filename() is not None
        if self._data.filename() is None:
            return
        
        if self.hasChanged() and not self.askReloadModified():
            return
        try:
            self._open(self.filename())
        except EnvironmentError as e:
            self.cannotOpenFileMsg(filename)
            return
        except StandardError as e:
            self.invaildFormatMsg(filename)
            return
        
        self._undoReset()
        self.updated.emit()
        
    def getdir(self, filename):
        if filename is not None:
            return os.path.dirname(str(filename))
        else:
            return os.getcwd()
    
    def dir(self):
        return self.getdir(self._data.filename())
    
    def saveAs(self, filename=None):
        filename = filename or self.askSavePath()
        if not filename:
            return False
        
        if os.path.isfile(filename) and self.backupToRecycle():
            try:
                trash(filename)
            except EnvironmentError:
                pass
                
        savingThread = SimpleThread(
            partial(self._data.save, filename=filename),
            parent=self
        )
        savingThread.start()
        with self.savingProgress():
            while savingThread.isRunning():
                QApplication.processEvents()
                QThread.msleep(50)
        
        try:
            savingThread.reraise()
        except EnvironmentError as e:
            self.cannotSaveFileMsg(filename)
            return False
        else:
            if savingThread.result():
                self.showSavingErrors(savingThread.result())
            self.addRecentFile(filename)
            self._undoSave()
            self.updated.emit()
            return True

    def save(self):
        return self.saveAs(self._data.filename())
    
    def addRecentFile(self, filename):
        raise NotImplementedError
    
    
class UsedColorIndexes:
    def __init__(self):
        self._d = WeakKeyDictionary()
    
    # shinriyo完全置き換え
    def __call__(self, image):
        hashable_image = image_op.usedColorIndexes(image)
        if hashable_image not in self._d:
            self._d[hashable_image] = image_op.usedColorIndexes(image)

def def_method_for_plural_sprs(*methodNames):
    execstrs = []
    for methodName in methodNames:
        execstr = """\
def {methodName}Sprs(self, sprs, *a, **kw):
    if not sprs: return
    with self._blockingNotifyUpdating():
        for spr in sprs:
            spr.{methodName}(*a, **kw)
    self._notifyUpdate()
{methodName}Sprs_ = {methodName}Sprs""".format(methodName=methodName)
        execstrs.append(execstr)
    return "\n".join(execstrs)


def def_colortable_method_for_plural_sprs(*methodNames):
    execstrs = []
    for methodName in methodNames:
        execstr = """\
def {methodName}Sprs(self, sprs, *a, **kw):
    if not sprs: return
    with self._blockingNotifyUpdating():
        for spr in sprs:
            spr.{methodName}(*a, **kw)
    self._notifyUpdate()

def {methodName}Sprs_(self, sprs, colorTableType, *a, **kw):
    colorTable = self.getColorTableForOperation(colorTableType)
    if colorTable is None:
        return
    return self.{methodName}Sprs(sprs, colorTable, *a, **kw)""".format(methodName=methodName)
        execstrs.append(execstr)
    return "\n".join(execstrs)
    

class Sff(SubModel):
    _DataClass = sff_data.SffData
    dirChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, *a, **kw):
        SubModel.__init__(self, *a, **kw)
        self._dir = self.getdir(self._data.filename())
        self._data.filenameChanged.connect(self.onModelFilenameChanged)
        self._isCharSff = True
    
    def usedColorIndexes(self):
        indexes = set()
        update = indexes.update
        for spr in self.sprs():
            if spr.useAct():
                update(spr.usedColorIndexes())
        return indexes
    
    def onModelFilenameChanged(self, f):
        dir = self.getdir(f)
        if self._dir != dir:
            self._dir = dir
            self.dirChanged.emit(self._dir)
    
    exec(def_qgetter("isCharSff"))
    def setIsCharSff(self, v):
        if self.isCharSff() == v:
            return
        self._isCharSff = v
        self.updated.emit()
    
    def dir(self):
        return self._dir
    
    def _Spr(self, *a, **kw):
        return Spr(self, *a, **kw)
    
    def spr(self, i):
        sprId = self._data.sprIds()[i]
        return self._Spr(sprId)
    
    def sprs(self):
        return [self._Spr(sprId) for sprId in self._data.sprIds()]
    
    def sprCount(self):
        return self._data.sprCount()
    
    def sprByIndex(self, group, index):
        return self._Spr(self._data.sprIdByIndex(group, index))
    
    def newSpr(self, cropType=const.CropType.NoCrop, **kw):
        if "image" in kw:
            image = kw["image"]
            pos = QPoint(kw.get("x", 0), kw.get("y", 0))
            
            if not kw.get("withBgColor", True):
                image = image_op.allocBgColor(image)
            else:
                if cropType == const.CropType.NoCrop:
                    pass
                elif cropType == const.CropType.CropPosBefore:
                    delta, image = image_op.crop(image)
                    pos = pos + delta
                elif cropType == const.CropType.CropPosAfter:
                    delta, image = image_op.crop(image)
            kw.update(image=image, x=pos.x(), y=pos.y())
        
        if "withBgColor" in kw:
            del kw["withBgColor"]
        
        with self._updating():
            spr = self._Spr(self._data.newSpr(**kw))
            return spr
    
    def newSprs(self, images, index, cropType=const.CropType.NoCrop, **kw):
        sprs = []
        with self._updating():
            for i, image in enumerate(images, start=index):
                pos = QPoint(kw.get("x", 0), kw.get("y", 0))
                
                if not kw.get("withBgColor", True):
                    image = image_op.allocBgColor(image)
                else:
                    if cropType == const.CropType.NoCrop:
                        pass
                    elif cropType == const.CropType.CropPosBefore:
                        delta, image = image_op.crop(image)
                        pos = pos + delta
                    elif cropType == const.CropType.CropPosAfter:
                        delta, image = image_op.crop(image)
                
                kw1 = dict(kw)
                kw1.update(image=image, x=pos.x(), y=pos.y(), index=i)
                if "withBgColor" in kw1:
                    del kw1["withBgColor"]
                
                spr = self._Spr(self._data.newSpr(**kw1))
                sprs.append(spr)
        return sprs
    
    def askOpenPath(self):
        return self.askSffOpenPath()
    
    def askSavePath(self):
        return self.askSffSavePath()
    
    def askSaveBefore(self):
        return self.askSaveSffBefore()
    
    def askReloadModified(self):
        return self.askReloadModifiedSff()
    
    def saveCsv(self, filename=None):
        filename = filename or self.askCsvSavePath()
        if not filename:
            return
        
        format = self.askCsvSaveFormat(filename, self.sprs())
        if not format:
            return
        
        def getColorTable(spr):
            return spr_display.colorTable(
                spr,
                self.actColorTable(),
                self.sprDisplayMode(),
            )
        savingThread = SimpleThread(
            partial(self._data.saveCsv, filename=filename, format=format, getColorTable=getColorTable),
            parent=self
        )
        savingThread.start()
        with self.savingProgress():
            while savingThread.isRunning():
                QApplication.processEvents()
                QThread.msleep(50)
        
        try:
            savingThread.reraise()
        except sff_data.CsvSaveError as e:
            self.saveErrorMsg(e.filename)
            return False
        except sff_data.ImageSaveError as e:
            self.saveImageErrorMsg(e.filename)
            return False
        else:
            if savingThread.result():
                self.showSavingErrors(savingThread.result())
            self.addRecentCsvFormat(format)
            self.addRecentFile(filename)
            return True
        
    def _open(self, filename):
        filename = os.path.abspath(filename)
        _, ext = os.path.splitext(filename)
        
        if ext.lower() == ".csv":
            errors = self._data.openCsv(filename)
        else:
            errors = self._data.open(filename)
        for sprData in self._data.sprs():
            self._model.registerUsedColorIndexes(sprData.image())
        self.palette().display()
        return errors
        
    def addSprs(self, filenames=None):
        if isinstance(filenames, types.StringTypes):
            filenames = [filenames]
        
        filenames = filenames or self.askSprAddPaths()
        if not filenames:
            return
        
        images = []
        for f in sorted(filenames, key=key_path):
            try:
                image = Image256(f)
            except IOError:
                self.invaildImageFormatMsg(f)
                return
            if image.format() != QImage.Format_Indexed8:
                image = image.convertToFormat(QImage.Format_Indexed8)
            images.append(image)
        
        if len(images) == 1:
            image = images[0]
            r = self.askAddSprs(image)
            if r is None:
                return
            kw, _ = r
            self.setSpr(self.newSpr(image=image, **kw))
        else:
            while images:
                r = self.askAddSprs(images[0])
                if r is None:
                    return
                
                kw, sequential = r
                if sequential:
                    sprs = self.newSprs(images, **kw)
                    self.setSpr(sprs[-1])
                    return
                
                image = images.pop(0)
                spr = self.newSpr(image=image, **kw)
                self.setSpr(spr)
    
    def groupSprs(self, group):
        return [s for s in self.sprs() if s.group() == group]
    
    def palette(self):
        return SffPalette(self)
    
    def saveColorTable(self, filename=None):
        filename = filename or self.askActSavePath()
        if not filename:
            return
        self.palette().save(filename)
    
    def swapColorTable(self, filename=None):
        filename = filename or self.askActOpenPath()
        if not filename:
            return
        self.palette().open(filename)
        
    def colorTable(self):
        return self.palette().colorTable()
    
    
    def setColorTable(self, colorTable):
        if self._setColorTable(colorTable):
            self._notifyUpdate()
            return True
        else:
            return False
    
    def _setColorTable(self, colorTable):
        return self._data.setColorTable(colorTable)
    
    def deleteColors(self, indexes):
        with self._blockingNotifyUpdating():
            changed = False
            for spr in self.sprs():
                if spr.useAct():
                    r = spr.deleteColors(indexes) 
                    changed = r or changed
        if changed:
            self._notifyUpdate()
    
    def wizard(self):
        r = self.sffWizard()
        if r is None:
            return
        type, sprs, kw = r
        name = str(type)
        methodname = name[0].lower() + name[1:] + "Sprs_"
        getattr(self, methodname)(sprs, **kw)
    
    exec(def_method_for_plural_sprs(
        'autoCrop',
        'allocBg',
        'invert',
        'eraseRects',
        'eraseRectsColors',
    ))
    
    exec(def_colortable_method_for_plural_sprs(
        'cleanColorTable',
        'replaceColorTable',
    ))
    
    def getColorTableForOperation(self, x):
        type = x[0]
        if type == const.ColorTableType.Sff:
            return self.colorTable()
        elif type == const.ColorTableType.Act:
            return self._model.colorTable()
        elif type == const.ColorTableType.Spr:
            spr = x[1]
            assert spr is not None
            if not spr.isValid():
                self.invalidSprIndexMsg()
                return None
            else:
                return spr.colorTable()
        elif type == const.ColorTableType.File:
            path = x[1]
            try:
                return act.open(path)
            except EnvironmentError:
                self.cannotOpenFileMsg(path)
                return None
        else:
            assert False
        
        
    def addRecentFile(self, filename):
        self.addRecentSffFile(filename)
    

class SffPalette(Palette):
    updated = pyqtSignal()
    def __init__(self, sff):
        self._submodel = sff
        Palette.__init__(self, model=sff._model)
    
    def colorTable(self):
        return self._submodel._data.colorTable()
    
    def setColorTable(self, colorTable):
        if self._submodel._data.setColorTable(colorTable):
            self.updated.emit()
    
    def changeColor(self, i, color):
        if self._submodel._data.changeColor(i, color):
            self.updated.emit()
    
    def changeColors(self, colors):
        if self._submodel._data.changeColors(i, color):
            self.updated.emit()
    
    def title(self):
        return u"SFFのパレット"
    
    def __eq__(self, other):
        return False
    
    def __ne__(self, other):
        return not(self == other)
    
    def __hash__(self):
        return 1
    

def writeGifIndexPage(fp, name, images):
    fmt = u'''
<?xml version="1.0" encoding="Shift_JIS"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=Shift_JIS" />
<title>{name}</title>
</head>
<body>
    <h1>{name}</h1>
    <dl>{imagePaths}</dl>
</body>
</html>
'''
    s = fmt.format(name=name,
        imagePaths="\n".join('<dt>{0}</dt><dd><img src="{1}" /></dd>'.format(i, p) for i, p in images))
    fp.write(s)


class Air(SubModel):
    _DataClass = air_data.AirData
    
    def Anim(self, *a, **kw):
        return Anim(self, *a, **kw)
    
    def Elm(self, *a, **kw):
        return Elm(self, *a, **kw)
    
    def newAnim(self):
        with self._updating():
            return self.Anim(self._data.newAnim())
    
    def elms(self, anim):
        return [self.Elm(elmId) for elmId in self._data.animIds(anim._id)]
    
    def anims(self):
        return [self.Anim(animId) for animId in self._data.animIds()]
    
    def saveToGifAll(self, dirname=None, ext="gif"):
        assert ext in ["png", "apng", "gif"], ext
        dirname = dirname or self.askGifSaveDirPath()
        if not dirname:
            return
        
        name = self.name()
        def save():
            imageNames = []
            from operator import methodcaller
            for anim in sorted(self.anims(), key=methodcaller("index")):
                basename = "{0}-{1}.{2}".format(name, anim.index(), ext)
                filename = os.path.join(dirname, basename)
                anim._saveToGif(filename)
                imageNames.append((anim.index(), basename))
            
            htmlname = os.path.join(dirname, name + ".html")
            with io.open(htmlname, "w", encoding="mbcs") as fp:
                writeGifIndexPage(fp, name, imageNames)
        
        savingThread = SimpleThread(
            save,
            parent=self
        )
        savingThread.start()
        with self.savingProgress():
            while savingThread.isRunning():
                QApplication.processEvents()
                QThread.msleep(50)
        
        try:
            savingThread.reraise()
        except EnvironmentError as e:
            self.saveImageErrorMsg(e.filename)
            return False
        else:
            return True
        
    def askOpenPath(self):
        return self.askAirOpenPath()
    
    def askSavePath(self):
        return self.askAirSavePath()
    
    def askSaveBefore(self):
        return self.askSaveAirBefore()
    
    def askReloadModified(self):
        return self.askReloadModifiedAir()

    def addRecentFile(self, filename):
        self.addRecentAirFile(filename)
    
    editExternal = editExternal_("tempAirFileName", "startExternalAirEditing")


class _Model(QObject):
    actColorTableChanged = pyqtSignal("PyQt_PyObject")
    paletteChanged = pyqtSignal("PyQt_PyObject")
    _Sff = Sff
    _Air = Air
    _ActSubModel = ActSubModel
    
    _instance = None
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, xview=None):
        QObject.__init__(self)
        
        self._sff = self._Sff(self)
        self._air = self._Air(self)
        self._act = self._ActSubModel(self)
        self._palette = self._sff.palette()

        self._closing = False
        self._xview = xview
        
        self.imageUsedColorIndexes = UsedColorIndexes()
        self.registerUsedColorIndexes = self.imageUsedColorIndexes
        
    exec(def_qgetter("closing"))
    exec(def_qgetter("sff", "air", "act"))
    
    exec(def_delegate("_sff", "Spr"))
    exec(def_delegate("_air", "Anim", "Elm"))
    
    def actColorTable(self):
        return self._palette.colorTable()
        
    @emitSetter
    def setPalette(self):
        self.actColorTableChanged.emit(self.actColorTable())
    
    def palette(self):
        return self._palette
    
    def xview(self):
        if self._xview is None:
            import sffairmaker.view
            return sffairmaker.view.View()
        else:
            return self._xview
        
    def tempSprFileName(self):
        return self.tempFileName("bmp")
    
    def startExternalEditing(self, commandFormat, fileName):
        cmd = commandFormat.replace("%1", fileName)
        cmd = os.path.expandvars(cmd)
        try:
            Popen(cmd)
            return True
        except OSError as e:
            self.cannotPopenMsg(cmd)
            return False
            
    def startExternalSprEditing(self, fileName):
        return self.startExternalEditing(
            self.settings().externalSprEditingCommand(),
            fileName,
        )
    
    def startExternalAirEditing(self, fileName):
        return self.startExternalEditing(
            self.settings().externalAirEditingCommand(),
            fileName,
        )
    
    def tempAirFileName(self):
        return self.tempFileName("air")
    
    def tempFileName(self, ext):
        from tempfile import gettempdir
        from os.path import join, isfile
        import time
        import itertools
        
        for t in itertools.count(time.time()):
            tempPath = join(gettempdir(), "temp-{0}.{1}".format(t, ext))
            if not isfile(tempPath):
                return tempPath
    
    def settings(self):
        return sffairmaker.settings.Settings()
        
    def loadFiles(self, paths):
        sffpath = None
        airpath = None
        actpath = None
        imagepaths = []
        
        for f in filter(os.path.isfile, paths):
            _, ext = os.path.splitext(f)
            ext = ext.lower()
            if ext in [".sff", ".csv"]:
                if sffpath is None:
                    sffpath = f
            elif ext == ".air":
                if airpath is None:
                    airpath = f
            elif ext == ".act":
                if actpath is None:
                    actpath = f
            else:
                imagepaths.append(f) #ignore
        
        for d in filter(os.path.isdir, paths):
            if sffpath is None:
                paths = list(allfiles(d, "*.sff"))
                if len(paths) > 2:
                    sffpath = self.selectSffPath(paths)
                else:
                    sffpath = paths[0]
            if airpath is None:
                paths = list(allfiles(d, "*.air"))
                if len(paths) > 2:
                    airpath = self.selectAirPath(paths)
                else:
                    airpath = paths[0]
            break
        
        if sffpath is not None:
            self.sff().open(sffpath)
        if airpath is not None:
            self.air().open(airpath)
        if actpath is not None:
            self.act().open(airpath)
        if imagepaths:
            self.sff().addSprs(imagepaths)
        
    def exit(self):
        if self._sff.askIfChanged() and self._air.askIfChanged():
            self._closing = True
            QApplication.exit()
    
    def __getattr__(self, name):
        return getattr(self.settings(), name, None) or \
               getattr(self.xview(), name)
    
def Model():
    return _Model.instance()

class UndoBuffer:
    def __init__(self, firstState,  maxLen=64):
        self._maxLen = maxLen
        self.reset(firstState)
    
    def reset(self, state):
        self._savePos = self._pos = 0
        self._buffer = [state]
    
    def push(self, state):
        self._buffer = self._buffer[:self._pos + 1] + [state]
        if len(self._buffer) > self._maxLen:
            self._buffer.pop(0)
        else:
            self._pos += 1
        assert len(self._buffer) <= self._maxLen
    
    def undo(self):
        if self._pos <= 0:
            return None
        else:
            self._pos -= 1
            return self._buffer[self._pos]
    
    def redo(self):
        if self._pos == len(self._buffer) - 1:
            return None
        else:
            self._pos += 1
            return self._buffer[self._pos]
    
    def save(self):
        self._savePos = self._pos
    
    def hasChanged(self):
        return self._savePos != self._pos


def main():
    pass

    
if __name__ == "__main__":
    main()
