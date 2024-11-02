# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type


from sffairmaker.qutil import *
from sffairmaker import sfflib
from sffairmaker.holder import createHolder
from sffairmaker.id_ import IdDispatcher
from sffairmaker.qutil import *
from sffairmaker.image_op import (
    Image256,
    Format_Indexed8,
    pilimage_to_qimage,
    qimage_to_pilimage,
)
    
from sffairmaker.dummy_image import dummyImage
from sffairmaker import const

import os
from collections import namedtuple

from collections import OrderedDict
import copy
from collections import namedtuple
from operator import attrgetter, methodcaller
import csv

from enum import Enum
from iterutils import grouper


class CsvSaveFormat:
    def __init__(self, nameFormat, ext):
        self._nameFormat = nameFormat
        self._ext = ext
    
    def imageName(self, csvPath, spr):
        group = spr.group()
        index = spr.index()
        
        from os.path import basename, splitext
        name, _ = splitext(basename(csvPath))
        
        return self._nameFormat.format(
            name=name,
            group=group,
            index=index
        )
    
    def imageBasename(self, csvPath, spr):
        return self.imageName(csvPath, spr) + "." + self.ext()
    
    def imagePath(self, csvPath, spr):
        from os.path import dirname, join
        return join(dirname(csvPath), self.imageBasename(csvPath, spr))
    
    exec(def_qgetter("nameFormat", "ext"))
    
    def __repr__(self):
        return "{0}({1}, {2})".format(
            self.__class__.__name__,
            repr(self._nameFormat),
            repr(self._ext)
        )



class Spr(createHolder("Spr", "group index useAct x y image".split())):
    def __init__(self, x=0, y=0, group=-1, index=-1, useAct=False, image=None):
        assert image is not None
        assert image.format() == Format_Indexed8
        self._init(
            x = x,
            y = y,
            group = group,
            index = index,
            useAct = useAct,
            image = image,
        )
    
    def group_index(self):
        return (self.group(), self.index())
    
    def __eq__(self, other):
        def astuple(x):
            t = [getattr(x, "_" + name)
                 for name in x._fields if name != "image"]
            t.append(id(x.image()))
            return tuple(t)
        return astuple(self) == astuple(other)
    

def saveToPcx(image, filename):
    qimage_to_pilimage(image).save(filename)

def pilpalette_to_qcolortable(palette):
    colorTable = []
    for r, g, b in grouper(3, palette):
        colorTable.append(qRgb(r, g, b))
    return colorTable

class ImageSaveError(IOError):
    def __init__(self, filename):
        self.filename = filename
        IOError.__init__(self, filename)

class CsvSaveError(IOError):
    def __init__(self, filename):
        self.filename = filename
        IOError.__init__(self, filename)



class Sff:
    def __init__(self):
        self._sprs = OrderedDict()
        self._dummyImage = None
        
        self._idDispatcher = IdDispatcher(repr(self))
        self._new_id = self._idDispatcher.new_id
        self._colorTable = [qRgb(255,0,255)] + [qRgb(0,0,0)]*255
    
    def getDummyImage(self):
        if self._dummyImage is None:
            self._dummyImage = dummyImage()
        return self._dummyImage
    
    @classmethod
    def _fromSprList(cls, sprList):
        ins = cls()
        for s in sprList:
            ins._sprs[ins._new_id()] = s
        
        commonPaletteCandidates = (
            [s for s in sprList if s.group_index() == (9000, 0)] + 
            [s for s in sprList if s.group_index() == (0, 0)] + 
            sorted([s for s in sprList if s.useAct()],
                   key=methodcaller("group_index"))
        )
        
        if commonPaletteCandidates:
            s = commonPaletteCandidates[0]
            ins.setColorTable(s.image().colorTable())
        
        assert all(qAlpha(i) == 255 for i in ins._colorTable)
        
        if not ins._sprs:
            ins.newSpr()
        return ins
    
    def __copy__(self):
        c = self.__class__()
        c._sprs = OrderedDict(self._sprs)
        c._colorTable = list(self._colorTable)
        return c
    
    @classmethod
    def create(cls):
        ins = cls()
        ins.newSpr()
        return ins
    
    @classmethod
    def _openSprList(cls, filename):
        return sfflib.openSprList(filename)
    
    @classmethod
    def open(cls, filename):
        sprs = []
        sprList, errors = cls._openSprList(filename)
        for s in sprList:
            sprs.append(Spr(
                x=s.pos[0],
                y=s.pos[1],
                group=s.group,
                index=s.index,
                useAct=s.useAct,
                image=pilimage_to_qimage(s.image),
            ))
        return cls._fromSprList(sprs), errors
    
    @classmethod
    def openCsv(cls, filename):
        from os.path import dirname, join
        sprs = []
        errors = []
        
        class NextLine(Exception):pass
        
        with open(filename, "rb") as fp:
            for lineno, row in enumerate(csv.reader(fp), start=1):
                try:
                    row = [str(col.strip(), "mbcs") for col in row]
                    if len(row) < 7:
                        raise NextLine
                    
                    image_path = join(dirname(filename), row[5] + "." + row[6])
                    image = QImage(image_path)
                    if image.isNull():
                        errors.append(const.OpeningCsvErrorInfo(
                            lineno = lineno,
                            type = const.OpeningCsvErrorType.Image,
                            error = IOError("Cannot load image '{0}'".format(image_path)),
                        ))
                        raise NextLine
                    
                    kw = {}
                    for key, col, default in zip("group index x y useAct".split(), row, [-1, -1, 0, 0, True]):
                        if not col:
                            kw[key] = default
                            continue
                        try:
                            v = int(col)
                        except ValueError:
                            errors.append(const.OpeningCsvErrorInfo(
                                lineno = lineno,
                                type = getattr(const.OpeningCsvErrorType, upper_head_string(key)),
                                error = IOError("Cannot load image '{0}'".format(image_path)),
                            ))
                            raise NextLine
                        else:
                            kw[key] = v
                        
                    kw["useAct"] = bool(kw["useAct"])
                    sprs.append(Spr(image=image, **kw))
                except NextLine:
                    pass
        return cls._fromSprList(sprs), errors
    
    @classmethod
    def _saveSprList(cls, filename, sprList):
        sfflib.saveSprList(filename, sprList)
    
    def save(self, filename):
        sprList = []
        for spr in self._sprs.values():
            s = sfflib.InternalSpr()
            s.group_index = spr.group_index()
            s.pos = (spr.x(), spr.y())
            if spr.group_index() in [(9000, 0), (0, 0)]:
                im = QImage(spr.image())
                im.setColorTable(self.colorTable())
            else:
                im = spr.image()
            s.image = qimage_to_pilimage(im)
            
            s.useAct = spr.useAct()
            sprList.append(s)
        self._saveSprList(filename, sprList)
    
    
    def saveSpr(self, sprId, *a, **kw):
        self._saveSpr(self.sprById(sprId), *a, **kw)
        
    def _saveSpr(self, spr, filename, getColorTable=None):
        image = spr.image()
        if getColorTable is not None:
            image.setColorTable(getColorTable(spr))
        
        filename = os.path.abspath(filename)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            try:
                os.makedirs(dirname)
            except EnvironmentError:
                ImageSaveError(filename)
            
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext != ".pcx":
            r = image.save(filename)
            if not r:
                raise ImageSaveError(filename)
        else:
            try:
                saveToPcx(image, filename)
            except EnvironmentError:
                raise ImageSaveError(filename)
        
    def saveGroup(self, group, filename, format, getColorTable=None):
        sprs = [spr for spr in self._sprs.values() if spr.group() == group]
        self._saveCsv(sprs, filename, format, getColorTable) 
    
    def saveCsv(self, filename, format,  getColorTable=None):
        self._saveCsv(self._sprs.values(), filename, format, getColorTable) 
    
    def _saveCsv(self, sprs, filename, format,  getColorTable=None):
        dirname = os.path.dirname(filename)
        sprs = sorted(sprs, key=methodcaller("group_index"))
        
        paths = []
        rows = []
        for spr in sprs:
            imgname = format.imageName(filename, spr)
            path    = format.imagePath(filename, spr)
            
            rows.append(list(map(str, [
                spr.group(),
                spr.index(),
                spr.x(),
                spr.y(),
                int(spr.useAct()),
                imgname,
                format.ext(),
            ])))
            paths.append(path)
        try:
            with open(filename, "wb") as fp:
                w = csv.writer(fp)
                w.writerows(rows)
        except EnvironmentError:
            raise CsvSaveError(filename)
        
        for spr, path in zip(sprs, paths):
            self._saveSpr(spr, path, getColorTable)
            
            
    def sprById(self, id):
        return self._sprs.get(id, None)
    
    def sprIdByIndex(self, group, index):
        sprs = {}
        for id, spr in self._sprs.items():
            sprs[spr.group_index()] = id
        return sprs.get((group, index), None)
    
    def sprCount(self):
        return len(self._sprs)
    
    def sprIds(self):
        return list(self._sprs)
    
    def sprs(self):
        return self._sprs.values()
    
    def newSpr(self, **kw):
        id = self._new_id()
        if "image" not in kw:
            kw["image"] = self.getDummyImage()
        
        assert kw["image"].format() == Format_Indexed8, kw["image"].format()
        
        self._sprs[id] = Spr(**kw)
        return id
    
    def changeSpr(self, id, **kw):
        old = self.sprById(id)
        if "image" in kw:
            assert kw["image"].format() == Format_Indexed8, kw["image"].format()
            
        new = old._replace(**kw)
        self._sprs[id] = new
        return old != new
    
    def removeSpr(self, id):
        del self._sprs[id]
    
    def cloneSpr(self, id):
        newId = self._new_id()
        self._sprs[newId] = self.sprById(id)
        return newId
    
    def colorTable(self):
        return self._colorTable
    
    def setColorTable(self, colorTable):
        if self._colorTable == colorTable:
            return False
        self._colorTable = colorTable
        return True
    
    def changeColor(self, i, color):
        assert qAlpha(color) == 255
        if self._colorTable[i] != color:
            self._colorTable[i] = color
            return True
        return False
    
    def changeColors(self, colors):
        changed = False
        for i, color in colors.iteritems():
            if self.changeColor(i, color):
                changed = True
        return changed
    
    


class SffData(QObject):
    filenameChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self):
        QObject.__init__(self)
        self._filename = self._source = None
        self.create()
    
    exec(def_qgetter("filename", "source"))
    
    @emitSetter
    def setFilename(self):
        assert isinstance(self._filename, str) or self._filename is None, type(self._filename)
    
    def memento(self, *a):
        return (copy.copy(self._sff), self._source)
    
    def restore(self, m, *a):
        sff, self._source = m
        self._sff = copy.copy(sff)
    
    def create(self):
        self._sff = Sff.create()
        self._source  = None
        self.setFilename(None)
    
    def open(self, filename):
        self._sff, errors = Sff.open(filename)
        self._source  = filename
        self.setFilename(filename)
        return errors
    
    def openCsv(self, filename):
        self._sff, errors = Sff.openCsv(filename)
        self._source = filename
        self.setFilename(None)
        return errors
    
    def saveCsv(self, filename, *a, **kw):
        self._sff.saveCsv(filename, *a, **kw)
        self._source = filename
    
    def save(self, filename=None):
        if filename is None:
            assert self._filename is not None
            self._sff.save(self._filename)
        else:
            self._sff.save(filename)
            self.setFilename(filename)
            self._source  = filename
    
    def removeSpr(self, sprId, *a, **kw):
        self._sff.removeSpr(sprId, *a, **kw)
        if not self._sff.sprIds():
            self._sff.newSpr()
        
    
    def __getattr__(self, name):
        if not name.startswith("_"):
            return getattr(self._sff, name)
        else:
            raise AttributesError(name)
                