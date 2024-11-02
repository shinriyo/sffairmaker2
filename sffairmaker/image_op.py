# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from itertools import starmap, product
from sffairmaker.qutil import *
from sffairmaker.mm import multimethod

from itertools import chain, product, starmap
from iterutils import grouper

import PIL.Image
    
def pilimage_to_qimage(pilimage):
    fp = StringIO()
    pilimage.save(fp, "BMP")
    qimage = QImage()
    qimage.loadFromData(fp.getvalue(), "BMP")
    return qimage

def qimage_to_pilimage(qimage):
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    qimage.save(buffer, "BMP")
    
    fp = StringIO()
    fp.write(buffer.data())
    buffer.close()
    fp.seek(0)
    return PIL.Image.open(fp)

def pilpalette_to_qcolortable(palette):
    from iterutils import grouper
    return list(starmap(qRgb, grouper(3, palette)))

def qcolortable_to_pilpalette(colorTable):
    """
    >>> palette = [i % 256  for i in range(256*3)]
    >>> palette1 = qcolortable_to_pilpalette(pilpalette_to_qcolortable(palette))
    >>> palette == palette1
    True
    """
    return [x for c in colorTable for x in (qRed(c), qGreen(c), qBlue(c))]
    

def rectPixels(rect):
    rect = rect.normalized()
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            yield QPoint(x, y)
            
def imagePixels(image):
    return rectPixels(image.rect())

def eraseRects(image, rects):
    image = Image256(image)
    for rc in rects:
        for p in rectPixels(image.rect().intersected(rc)):
            image.setPixel(p, 0)
    return image
    

def indexesToErase(image, rectsToErase):
    rectsToErase = [rc.normalized() for rc in rectsToErase]
    
    indexes = set()
    for rc in rectsToErase:
        for p in rectPixels(rc):
            if not image.rect().contains(p):
                continue
            indexes.add(image.pixelIndex(p))
    if 0 in indexes:
        indexes.remove(0)
    
    return indexes


def eraseRectsColors(image, rects):
    indexes = indexesToErase(image, rects)
    
    colorTable = colorTable256(image.colorTable())
    for i in indexes:
        if i != 0 and i < len(colorTable):
            colorTable[i] = qRgb(0, 0, 0)
    old2new = {}
    for i in range(256):
        if i in indexes:
            old2new[i] = 0
        else:
            old2new[i] = i
    
    return transformImagePixel(image, colorTable, old2new)


def colorTable256(colorTable=[]):
    return colorTable + [qRgb(0, 0, 0)] * (256 - len(colorTable))

@multimethod(QImage)
def Image256(im):
    if im.isNull():
        raise ValueError("null image")
    im = im.convertToFormat(Format_Indexed8)
    im.setColorTable(colorTable256(im.colorTable()))
    return im
    
@multimethod(str)
# @multimethod(unicode)
# @multimethod(QString)
def Image256(filename):
    im = QImage(filename)
    if im.isNull():
        raise IOError(filename)
    return Image256(im)

@multimethod()
def Image256():
    im = QImage(1, 1, Format_Indexed8)
    im.setColorTable(colorTable256(im.colorTable()))
    return im
    
@multimethod(QSize)
@multimethod(int, int)
def Image256(*a):
    a += (QImage.Format_Indexed8,)
    im = QImage(*a)
    im.setColorTable(colorTable256())
    return im

Format_Indexed8 = QImage.Format_Indexed8

def NullImage():
    return QImage()

def rectToCrop(image):
    def emptyVLine(x):
        return all(image.pixelIndex(x, y) == 0 for y in range(image.height()))
    
    def emptyHLine(y):
        return all(image.pixelIndex(x, y) == 0 for x in range(image.width()))
    
    #左端
    for x in range(image.width() - 1):
        if not emptyVLine(x):
            left = x
            break
    else:
        left = image.width() - 1
    
    #右端
    for x in range(image.width() - 1, left, -1):
        if not emptyVLine(x):
            right = x
            break
    else:
        right = left
    
    #上端
    for y in range(image.height() - 1):
        if not emptyHLine(y):
            top = y
            break
    else:
        top = image.height() - 1
    
    #下端
    for y in range(image.height() - 1, top, -1):
        if not emptyHLine(y):
            bottom = y
            break
    else:
        bottom = top
    
    return QRect(left, top, right - left + 1, bottom - top + 1)


def autoCrop(image):
    return cropRect(image, rectToCrop(image))
    
def cropRect(image, rect):
    delta = rect.topLeft()
    
    image1 = Image256(rect.size())
    image1.setColorTable(colorTable256(image.colorTable()))
    
    for p in imagePixels(image1):
        image1.setPixel(p, image.pixelIndex(p + delta))
    return image1, delta
    

def transformImagePixel(image, colorTable, old2new):
    image1 = Image256(image)
    get = old2new.get
    setPixel = image1.setPixel
    for p, i in ipixelIndex(image1):
        setPixel(p, get(i, 0))
    
    assert len(colorTable) == 256
    image1.setColorTable(colorTable)
    return image1


def ipixelIndex(image):
    w = image.width()
    scanLine = image.scanLine
    for y in range(image.height()):
        p = scanLine(y)
        for x, i in enumerate(map(ord, p.asstring(w))):
            yield QPoint(x, y), i


def saveToPcx(image, filename):
    qimage_to_pilimage(image).save(filename)



def deleteColors(image, indexes):
    colorTable = list(image.colorTable())
    for i in indexes:
        colorTable[i] = qRgb(0, 0, 0)
    
    old2new = dict((i, i) for i in range(256))
    old2new.update((i, 0) for i in indexes)
    return transformImagePixel(image, colorTable, old2new)


def deleteUnusedColors(image):
    used = usedColorIndexes(image)
    used = set(used)
    used.add(0)
    
    colorTable = colorTable256(image.colorTable())
    for i, c in enumerate(colorTable):
        if i not in used:
            colorTable[i] = qRgb(0, 0, 0)
    
    image1 = Image256(image)
    image1.setColorTable(colorTable)
    return image1

class NoUnusedColorError(ValueError):pass
    
def allocBgColor(image, bg=qRgb(255, 0, 255)):
    #パレットの0番を背景用に確保します。
    
    used = usedColorIndexes(image)
    unused = set(range(256)) - used
    
    if not unused:
        raise NoUnusedColorError(u"There is no unused color.")
    
    firstUnused = min(unused)
    old2new = {}
    newColorTable = [bg] + \
                    image.colorTable()[:firstUnused] + \
                    image.colorTable()[firstUnused + 1:]
    
    newColorTable = colorTable256(newColorTable)
    
    for k in range(firstUnused):
        old2new[k] = k + 1
    for k in range(firstUnused, 256):
        old2new[k] = k
    
    return transformImagePixel(image, newColorTable, old2new)


def replaceColorTable(image, colorTable):
    image1 = Image256(image)
    image1.setColorTable(colorTable256(colorTable))
    return image1

def irgb(i):
    return QColor(i).rgb()

def cleanColorTable(image, colorTable):
    colorTable = colorTable256(colorTable)
    
    old2new = {}
    for iold, color in enumerate(image.colorTable()):
        try:
            inew = colorTable.index(irgb(color))
        except ValueError:
            old2new[iold] = 0
        else:
            old2new[iold] = inew
    old2new[0] = 0


    return transformImagePixel(image, colorTable, old2new)


def moveRgb(colorTable, targetIndex, startIndex, srcs):
    colorTable1 = colorTable256(colorTable)
    
    srcs = list(srcs)
    startIndex %= len(colorTable1)
    targetIndex%= len(colorTable1)
    
    if not srcs or targetIndex == startIndex:
        return colorTable1
    
    assert all(k in range(len(colorTable)) for k in srcs), srcs
    
    for i in srcs:
        k = (targetIndex - startIndex + i) % len(colorTable1)
        colorTable1[k] = colorTable1[i]
        colorTable1[i] = qRgb(0,0,0)
    return colorTable1


def copyRgb(colorTable, targetIndex, startIndex, rgbMap):
    colorTable1 = colorTable256(colorTable)
    if not rgbMap:
        return colorTable1
    startIndex %= len(colorTable1)
    targetIndex%= len(colorTable1)
    
    assert all(k in range(len(colorTable)) for k in rgbMap), list(rgbMap.keys())
    
    for i, c in rgbMap.items():
        k = (targetIndex - startIndex + i) % len(colorTable1)
        colorTable1[k] = c
    return colorTable1


def swapRgb(colorTable, targetIndex, startIndex, srcs):
    colorTable1 = colorTable256(colorTable)
    srcs = list(srcs)
    startIndex %= len(colorTable1)
    targetIndex%= len(colorTable1)
    if not srcs or targetIndex == startIndex:
        return colorTable1
    
    assert all(k in range(len(colorTable1)) for k in srcs), srcs
    
    for i in srcs:
        k = (targetIndex - startIndex + i) % len(colorTable1)
        colorTable1[k], colorTable1[i] = colorTable1[i], colorTable1[k]
    return colorTable1



def swapImageColor(image, targetIndex, startIndex, srcs):
    """
    >>> im = Image256(16, 1)
    >>> im.setColorTable(colorTable256([QColor(i, 0, 0).rgba() for i in range(16)]))
    >>> for i in range(16):
    ...     im.setPixel(i, 0, i)
    ...
    >>> im1 = swapImageColor(im, 5, 0, [0, 1])
    >>> [qRed(i) for i in im1.colorTable()[:20]]
    [5, 6, 2, 3, 4, 0, 1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0, 0, 0, 0]
    >>> [im1.pixelIndex(i, 0) for i in range(16)]
    [5, 6, 2, 3, 4, 0, 1, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    """
    
    srcs = list(srcs)
    colorTable = swapRgb(image.colorTable(), targetIndex, startIndex, srcs)
    image1 = Image256(image)
    image1.setColorTable(colorTable)
    
    indexMap = {}
    for i in srcs:
        k = (targetIndex - startIndex + i) % len(colorTable)
        indexMap[i] = k
        indexMap[k] = i
    
    for p, i in ipixelIndex(image1):
        if i in indexMap:
            image1.setPixel(p, indexMap[i])
    return image1

def usedColorIndexes(image):
    w = image.width()
    h = image.height()
    scanLine = image.scanLine
    return frozenset(chain.from_iterable(map(ord, scanLine(y).asstring(w))
                for y in range(h)))

def addImageColors(colorTable, usedIndexes, image):
    old2new = {}
    colorTable1 = colorTable256(colorTable)
    
    from itertools import chain
    lastUsedIndexes = max(chain(usedIndexes, [0]))
    spaces = [k for k in range(lastUsedIndexes + 1, 256) if k not in usedIndexes] + \
             [k for k in range(1, lastUsedIndexes) if k not in usedIndexes]
    #0番には例え(0, 0, 0)でも追加しない
    
    print(spaces)
    
    usedInImage = usedColorIndexes(image)
    for i, color in enumerate(image.colorTable()):
        if i not in usedInImage:
            continue
        if i == 0:
            continue
        
        def add(i, color):
            if not spaces:
                raise ValueError("no spaces")
            k = spaces.pop(0)
            colorTable1[k] = color
            old2new[i] = k
        try:
            k = 1 + colorTable1[1:].index(color)
        except ValueError:
            add(i, color)
        else:
            if k in usedIndexes:
                old2new[i] = k
            else:
                add(i, color)
        
        
    return colorTable1, transformImagePixel(image, colorTable1, old2new)


def mirrored(image, pos, spr_pos, h, v):
    if h or v:
        image = image.mirrored(h, v)
        if v:
            pos = QPoint(pos.x(), pos.y() - image.height() + 2 * spr_pos.y())
        if h:
            pos = QPoint(pos.x() - image.width() + 2*spr_pos.x(), pos.y())
    
    return image, pos