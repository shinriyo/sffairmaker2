# coding: utf-8
"""
gif�o�͂̂��߂̃��W���[��
http://d.hatena.ne.jp/chikuchikugonzalez/20100627/1277648358�̃R�[�h��啪�Q�l�ɂ����Ă����������B
gif�ɂ��ẮAhttp://www.tohoho-web.com/wwwgif.htm�Ȃǂ��Q�Ƃ̎�
"""
from __future__ import division, print_function, unicode_literals
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.image_op import qcolortable_to_pilpalette

import PIL.Image
import PIL.GifImagePlugin

import math
import struct
import io
from collections import namedtuple

Element = namedtuple("Element", "image time pos")

def save(path, elms):
    with io.open(path, "wb") as fp:
        write(fp, elms)


def globalRect(elms):
    rect = QRect()
    for elm in elms:
        rect = elm.image.rect().translated(QPoint(elm.pos)).united(rect)
    return rect


GlobalHeaderFormat = (
    b"<" #little endian
    b"6s" # Format Signature
    b"2h" # Global Screen Width and Height
    b"B" # Global Color Table (1bit) / Color Resolution (3B) / Sort Flag (1bit) / Size of Global Color Table (3B)
    b"B" # Background Color Index
    b"B" # Aspect Ratio
)

def writeGlobalHeader(fp, size):
    x = 0b1110000
    items = (b"GIF89a", size.width(), size.height(), x, 0, 0)
    packed_bytes = struct.pack(GlobalHeaderFormat , *items)
    fp.write(packed_bytes)
    

ApplicationExtensionBlockFormat = (
    b"<" #little endian
    b"B" # Extension Introducer
    b"B" # Extension Label
    b"B" # Block Size
    b"8s" # Application Indentifier
    b"3s" # Application Authentication Code
    b"B" # Block Size (1B, 1-255)
    b"B" # Application Data, (Unknown, Magic Number?)
    b"H" # Application Data, Loop Count
    b"B" # Block Terminator
)

def writeApplicationExtensionBlock(fp):
    packed_bytes = struct.pack(
        ApplicationExtensionBlockFormat,
        0x21,
        0xFF,
        11,
        b"NETSCAPE",
        b"2.0",
        3,
        0x01,
        0,
        0,
    )
    fp.write(packed_bytes)
    

GraphicControlExtensionBlockFormat = (
    b"b" # Extension Introducer
    b"B" # Graphic Control Label
    b"B" # Block Size (0x04, fixed)
    b"B" # Reserved (Unused, 3bits) / Disposal method (3bits) / User Input Flag (1bit) / Transparent Color Flag (1bit)
    b"h" # Delay Time (2bytes)
    b"B" # Transparent Color Index (1byte)
    b"b" # Block Terminator
)

def writeGraphicControlExtensionBlock(fp, elm, is_last_image):
    infiniteTime = 1000
    assert elm.time > 0
    
    delayTime = math.floor(elm.time * 100)
    
    packed_bytes = struct.pack(GraphicControlExtensionBlockFormat,
        0x21,
        0xf9,
        0x04, #fixed
        0b101 if is_last_image else 0b1001,
        delayTime,
        0,
        0,
    )
    fp.write(packed_bytes)


ImageBlockFormat = (
    b"<" #little endian
    b"b" # Image Separator (1B, 0x2c)
    b"h" # Image Left Position (2B)
    b"h" # Image Top Position (2B)
    b"h" # Image Width (2B)
    b"h" # Image Height (2B)
    b"B" # Local Color Table Flag (1bit) / Interlace Flag (1bit) / Sort Flag (1bit) / Reserved (2bits) / Size of Local Color Table (3bits)
)

def writeImageBlock(fp, elm, gifrect, bgColor):
    pos = elm.pos - gifrect.topLeft()
    
    if elm.image.isNull():
        im = PIL.Image.new(b"P", (gifrect.width(), gifrect.height()), 0)
    else:
        colorTable = elm.image.colorTable()
        palette = qcolortable_to_pilpalette(colorTable)
        im = qimage_to_pilimage(elm.image)
        im.putpalette(palette)
        
    imageData = PIL.GifImagePlugin.getdata(im)
    headerData = PIL.GifImagePlugin.getheader(im)
    paletteData = headerData[1]
    
    localColorTableFlag = 1 #(1bit)
    interlaceFlag = 0       #(1bit)
    sortFlag = 0            #(1bit)
    reserved = 0            #(2bits)
    sizeOfLocalColorTable = int(math.floor(math.log((len(palette) / 3), 2))) - 1 #(3bits)
    
    x = (
        localColorTableFlag << 7 |
        interlaceFlag << 6 |
        sortFlag << 5 |
        reserved << 3 |
        sizeOfLocalColorTable 
    )
    
    packed_bytes = struct.pack(ImageBlockFormat, 
        0x2c, # Image Separator (1B, 0x2c)
        pos.x(), # Image Left Position (2B)
        pos.y(), # Image Top Position (2B)
        im.size[0], # Image Width (2B)
        im.size[1], # Image Height (2B)
        x,
    )
    fp.write(packed_bytes)
    
    fp.write(paletteData) # Local Color Table
    fp.write(imageData[0][-1])
    for d in imageData[1:-1]:
        fp.write(d)
    fp.write(struct.pack(b"<B", 0))      # Block Terminator
    
    
def writeTrailer(fp):
    fp.write(struct.pack(b"<b", 59))
    
    
def write(fp, elms):
    gifrect = globalRect(elms)
    
    writeGlobalHeader(fp, gifrect.size())
    writeApplicationExtensionBlock(fp)
    
    bgColor = QColor(0, 0, 0)
    
    for index, elm in enumerate(elms):
        writeGraphicControlExtensionBlock(fp, elm, index == len(elms) - 1)
        writeImageBlock(fp, elm, gifrect, bgColor)
    
    writeTrailer(fp)


def main():
    pass
    

if "__main__" == __name__:
    main()