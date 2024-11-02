# coding: utf-8
"""
apng出力のためのモジュール

pngについては
http://www14.ocn.ne.jp/~setsuki/ext/png.htm

apngについては
https://wiki.mozilla.org/APNG_Specification#.60acTL.60:_The_Animation_Control_Chunk

などを参照のこと
"""

from __future__ import division, print_function, unicode_literals
__metaclass__ = type 
import io
from sffairmaker.qutil import *
from sffairmaker.gif import globalRect
import struct
import zlib

AnimationControlFormat = (
    b"!"
    b"I" #num_frames  	unsigned int  	フレーム数
    b"I" #num_plays 	unsigned int 	APNGのループ回数。0を指定すると無限ループ。
)

FrameControlFormat = (
    b"!"
    b"I" # sequence_number  	unsigned int  	アニメーションチャンクのシーケンス番号、0から始まる
    b"I" # width unsigned int 	後に続くフレームの幅
    b"I" # height unsigned int 	後に続くフレームの高さ
    b"I" # x_offset unsigned int 	後に続くフレームを描画するx座標
    b"I" # y_offset unsigned int 	後に続くフレームを描画するy座標
    b"H" # delay_num 	unsigned short 	フレーム遅延の分子
    b"H" # delay_den 	unsigned short 	フレーム遅延の分母
    b"b" # dispose_op 	byte 	フレームを描画した後にフレーム領域を廃棄するか?
    b"b" # blend_op 	byte 	フレーム描画方法のタイプ
)
APNG_DISPOSE_OP_NONE = 0 #次のフレームを描画する前に消去しない。出力バッファをそのまま使用する。
APNG_DISPOSE_OP_BACKGROUND = 1 #次のフレームを描画する前に、出力バッファのフレーム領域を「完全に透過な黒」で塗りつぶす。
APNG_DISPOSE_OP_PREVIOUS = 2 #次のフレームを描画する前に、出力バッファのフレーム領域をこのフレームに入る前の状態に戻す。

APNG_BLEND_OP_SOURCE = 0 #アルファ値を含めた全ての要素をフレームの出力バッファ領域に上書きする。
APNG_BLEND_OP_OVER = 1 #書き込むデータのアルファ値を使って出力バッファに合成する。

def writeAnimationControl(fp, elms):
    writeChunk(fp, b"acTL", struct.pack(AnimationControlFormat, len(elms), 0))

def writeFrameControl(fp, number, elm, canvasRect):
    from fractions import Fraction
    time = Fraction(elm.time).limit_denominator(0xFFFF)
    
    p = elm.pos - canvasRect.topLeft()
    b = struct.pack(FrameControlFormat,
        number, # sequence_number  	unsigned int  	アニメーションチャンクのシーケンス番号、0から始まる
        elm.image.width(), # width unsigned int 	後に続くフレームの幅
        elm.image.height(), # height unsigned int 	後に続くフレームの高さ
        p.x(), # x_offset unsigned int 	後に続くフレームを描画するx座標
        p.y(), # y_offset unsigned int 	後に続くフレームを描画するy座標
        time.numerator, # delay_num 	unsigned short 	フレーム遅延の分子
        time.denominator, # delay_den 	unsigned short 	フレーム遅延の分母
        APNG_DISPOSE_OP_BACKGROUND, # dispose_op 	byte 	フレームを描画した後にフレーム領域を廃棄するか?
        APNG_BLEND_OP_OVER, # blend_op 	byte 	フレーム描画方法のタイプ
    )
    writeChunk(fp, b"fcTL", b)
    
    return number + 1
    
def writeSigneture(fp):
    fp.write(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A")


CrcFormat = b"!I"

GreyScale = 0 #1, 2, 4, 8, 16 	Each pixel is a greyscale sample
TrueColor = 2 #8, 16 	Each pixel is an R,G,B triple
IndexedColor = 3 #1, 2, 4, 8 	Each pixel is a palette index; a PLTE chunk shall appear.
GreyScaleWithAlpha = 4 #8, 16 	Each pixel is a greyscale sample followed by an alpha sample.
TrueColourWithAlpha = 6 #8, 16 	Each pixel is an R,G,B triple followed by an alpha sample.

def writeChunk(fp, chunkType, chunkData):
    assert len(chunkType) == 4
    fp.write(struct.pack(b"!I", len(chunkData)))
    b = struct.pack(b"!4s", chunkType) + chunkData
    fp.write(b)
    fp.write(struct.pack(CrcFormat, zlib.crc32(b)))

def writeImageHeader(fp, elms, canvasRect):
    ImageHeaderFormat = (
        b"!"
        b"I" #イメージの横幅(4) ピクセル単位
        b"I" #イメージの高さ(4) ピクセル単位
        b"B" #ビットの深さ(1) 整数(1,2,4,8,16)
        b"B" #カラータイプ(1) 整数(0,2,3,4,6)
        b"B" #圧縮方式(1) 固定値０
        b"B" #フィルター方式(1) 固定値０
        b"B" #インタレース方式(1) 整数(0,1)
    )
    b = struct.pack(ImageHeaderFormat,
        canvasRect.width(),
        canvasRect.height(),
        8,
        TrueColourWithAlpha,#IndexedColor,
        0,
        0,
        0,
    )
    writeChunk(fp, b"IHDR", b)


def writePalette(fp, qcolorTable):
    b = b"".join(chr(x) for c in qcolorTable for x in [qRed(c), qGreen(c), qBlue(c)])
    writeChunk(fp, b"PLTE", b)


from sffairmaker.image_op import ipixelIndex

def allPixels(image):
    w = image.width()
    scanLine = image.scanLine
    for y in range(image.height()):
        p = scanLine(y)
        for x, i in enumerate(imap(ord, p.asstring(w))):
            yield QPoint(x, y), i

def imageDataChanks(image):
    w = image.width()
    scanLine = image.scanLine
    
    data = []
    extend = data.extend
    
    pixelTable = dict(
        (chr(i), 
         [qRed(c), qGreen(c), qBlue(c), 255 if i else 0])
        for i, c in enumerate(image.colorTable()))
    
    for y in range(image.height()):
        data.append(0)
        extend(chain.from_iterable(pixelTable[i] for i in scanLine(y).asstring(w)))
    
    cpdata = zlib.compress(bytes(bytearray(data)), 0)
    
    from math import ceil
    chank_size = 64*1024
    for i in range(int(ceil(len(cpdata) / chank_size))):
        yield cpdata[i*chank_size : (i + 1)*chank_size]
    
    

def writeDefaultImageData(fp, elms, canvasRect):
    elm0 = elms[0]
    defaultImage = QImage(canvasRect.size(), QImage.Format_Indexed8)
    defaultImage.setColorTable(elm0.image.colorTable())
    
    delta = elm0.pos - canvasRect.topLeft()
    for p in imagePixels(defaultImage):
        if elm0.image.rect().contains(p - delta):
            defaultImage.setPixel(p, elm0.image.pixelIndex(p - delta))
        else:
            defaultImage.setPixel(p, 0)
    
    writeImageData(fp, defaultImage)
    
    
def writeImageData(fp, image):
    for chank_data in imageDataChanks(image):
        writeChunk(fp, b"IDAT", chank_data)
        

def writeFrameData(fp, number, elm):
    for chank_data in imageDataChanks(elm.image):
        b = struct.pack(b"!I", number) + chank_data
        writeChunk(fp, b"fdAT", b)
        number += 1
    return number
    
    
def writeImageTrailer(fp):
    writeChunk(fp, b"IEND", b"")
    

from sffairmaker.image_op import *


def write(fp, elms):
    canvasRect = globalRect(elms)
    
    writeSigneture(fp)
    writeImageHeader(fp, elms, canvasRect)
    writeAnimationControl(fp, elms)
    
    writeDefaultImageData(fp, elms, canvasRect)
    number = 0
    for i, elm in enumerate(elms):
        number = writeFrameControl(fp, number, elm, canvasRect)
        number = writeFrameData(fp, number, elm)
    writeImageTrailer(fp)
    

def save(path, *a, **kw):
    with io.open(path, "wb") as fp:
        write(fp,  *a, **kw)

def main():
    import warnings
    warnings.simplefilter('ignore', Warning)

    app = QApplication([])
    elms = []
    from sffairmaker.gif import Element
    from fractions import Fraction
    from sffairmaker.model import Model
    m = Model()
    print("sff")
    m.sff().open("D:\\owner\\My Documents\\MUGEN\\winmugen\\chars\\DragonClaw\\dc.sff")
##    m.sff().open("D:\\owner\\My Documents\\My Dropbox\\Python\\sffairmaker\\kfmt.sff")
    print("air")
    m.air().open("D:\\owner\\My Documents\\MUGEN\\winmugen\\chars\\DragonClaw\\dc.air")
##    m.air().open("D:\\owner\\My Documents\\My Dropbox\\Python\\sffairmaker\\kfmt.air")
    
    a0, = [a for a in m.air().anims() if a.index() == 0]
    print(a0)
##    a0.saveToGif("D:\\owner\\temp\\dc.png")
    
    m.air().saveToGifAll(r"D:\Owner\temp\dc-apng", "png")
##    m.air().saveToGifAll(r"D:\Owner\temp\dc-gif", "gif")
    
if "__main__" == __name__:
    main()