# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from PyQt5.QtGui import qRed, qGreen, qBlue, qRgb, QColor
from sffairmaker.image_op import colorTable256, Image256
from sffairmaker import image_op

import re
import io

def open(filename):
    with io.open(filename , "rb") as fp:
        return read(fp)

def read(fp):
    colorTable = colorTable256([])
    for i in range(255, -1, -1):
        chars = fp.read(3)
        assert isinstance(chars, str), "file object passd for 'act.read' must be 'binary mode'"
        if len(chars) < 3:
            break
        r, g, b = map(ord, chars)
        colorTable[i] = qRgb(r, g, b)
    return colorTable

def write(fp, colorTable):
    colorTable = colorTable256(colorTable)
    for i in range(255, -1, -1):
        x = colorTable[i]
        for f in (qRed, qGreen, qBlue):
            i = f(x)
            assert i in range(256)
            fp.write(chr(i))
    
def save(filename, colorTable):
    with io.open(filename, "wb") as fp:
        return write(fp, colorTable)

def writeText(fp, colorTable):
    for i in colorTable:
        print(u"{0}, {1}, {2},".format(qRed(i), qGreen(i), qBlue(i)),
            file=fp)

def saveToText(filename, colorTable):
    with io.open(filename, "w", encoding="ascii") as fp:
        writeText(fp, colorTable)
        
def openText(filename):
    colorTable = colorTable256([])
    with io.open(filename, "r") as fp:
        strs = re.split(r",|(?<!,)\s*\n", fp.read(), 256*3)
        from iterutils import grouper
        for i, rgb in enumerate(grouper(3, strs)):
            if i >= 256:
                break
            
            rgb = list(rgb)
            for k, s in enumerate(rgb):
                if s is None:
                    rgb[k] = 0
                else:
                    s = s.strip()
                    if not s:
                        rgb[k] = 0
                    else:
                        rgb[k] = int(s)
            colorTable[i] = qRgb(*rgb)
    return colorTable


def saveToImage(filename, colorTable):
    im = Image256(160, 160)
    im.setColorTable(colorTable)
    for p in image_op.imagePixels(im):
        x = p.x() // 10
        y = p.y() // 10
        i = x + y * 16
        im.setPixel(p, i)
    
    r = im.save(filename)
    if not r:
        raise IOError

def openImage(filename):
    image = Image256(filename)
    if image.isNull():
        raise IOError
    else:
        return colorTable256(image.colorTable())
    



def main():
    p = "D:\\Owner\\My Documents\\My Dropbox\\Python\\sffairmaker\\pal\\KFMT-LightBlue.act"
    colorTable = open(p)
    print(0, [str(QColor(i).name()) for i in colorTable[:7]])
    print(-1, [str(QColor(i).name()) for i in colorTable[-7:]])
    
    

if "__main__" == __name__:
    main()