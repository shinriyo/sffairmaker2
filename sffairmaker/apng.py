# coding: utf-8
"""
apng�o�͂̂��߂̃��W���[��

png�ɂ��Ă�
http://www14.ocn.ne.jp/~setsuki/ext/png.htm

apng�ɂ��Ă�
https://wiki.mozilla.org/APNG_Specification#.60acTL.60:_The_Animation_Control_Chunk

�Ȃǂ��Q�Ƃ̂���
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
    b"I" #num_frames  	unsigned int  	�t���[����
    b"I" #num_plays 	unsigned int 	APNG�̃��[�v�񐔁B0���w�肷��Ɩ������[�v�B
)

FrameControlFormat = (
    b"!"
    b"I" # sequence_number  	unsigned int  	�A�j���[�V�����`�����N�̃V�[�P���X�ԍ��A0����n�܂�
    b"I" # width unsigned int 	��ɑ����t���[���̕�
    b"I" # height unsigned int 	��ɑ����t���[���̍���
    b"I" # x_offset unsigned int 	��ɑ����t���[����`�悷��x���W
    b"I" # y_offset unsigned int 	��ɑ����t���[����`�悷��y���W
    b"H" # delay_num 	unsigned short 	�t���[���x���̕��q
    b"H" # delay_den 	unsigned short 	�t���[���x���̕���
    b"b" # dispose_op 	byte 	�t���[����`�悵����Ƀt���[���̈��p�����邩?
    b"b" # blend_op 	byte 	�t���[���`����@�̃^�C�v
)
APNG_DISPOSE_OP_NONE = 0 #���̃t���[����`�悷��O�ɏ������Ȃ��B�o�̓o�b�t�@�����̂܂܎g�p����B
APNG_DISPOSE_OP_BACKGROUND = 1 #���̃t���[����`�悷��O�ɁA�o�̓o�b�t�@�̃t���[���̈���u���S�ɓ��߂ȍ��v�œh��Ԃ��B
APNG_DISPOSE_OP_PREVIOUS = 2 #���̃t���[����`�悷��O�ɁA�o�̓o�b�t�@�̃t���[���̈�����̃t���[���ɓ���O�̏�Ԃɖ߂��B

APNG_BLEND_OP_SOURCE = 0 #�A���t�@�l���܂߂��S�Ă̗v�f���t���[���̏o�̓o�b�t�@�̈�ɏ㏑������B
APNG_BLEND_OP_OVER = 1 #�������ރf�[�^�̃A���t�@�l���g���ďo�̓o�b�t�@�ɍ�������B

def writeAnimationControl(fp, elms):
    writeChunk(fp, b"acTL", struct.pack(AnimationControlFormat, len(elms), 0))

def writeFrameControl(fp, number, elm, canvasRect):
    from fractions import Fraction
    time = Fraction(elm.time).limit_denominator(0xFFFF)
    
    p = elm.pos - canvasRect.topLeft()
    b = struct.pack(FrameControlFormat,
        number, # sequence_number  	unsigned int  	�A�j���[�V�����`�����N�̃V�[�P���X�ԍ��A0����n�܂�
        elm.image.width(), # width unsigned int 	��ɑ����t���[���̕�
        elm.image.height(), # height unsigned int 	��ɑ����t���[���̍���
        p.x(), # x_offset unsigned int 	��ɑ����t���[����`�悷��x���W
        p.y(), # y_offset unsigned int 	��ɑ����t���[����`�悷��y���W
        time.numerator, # delay_num 	unsigned short 	�t���[���x���̕��q
        time.denominator, # delay_den 	unsigned short 	�t���[���x���̕���
        APNG_DISPOSE_OP_BACKGROUND, # dispose_op 	byte 	�t���[����`�悵����Ƀt���[���̈��p�����邩?
        APNG_BLEND_OP_OVER, # blend_op 	byte 	�t���[���`����@�̃^�C�v
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
        b"I" #�C���[�W�̉���(4) �s�N�Z���P��
        b"I" #�C���[�W�̍���(4) �s�N�Z���P��
        b"B" #�r�b�g�̐[��(1) ����(1,2,4,8,16)
        b"B" #�J���[�^�C�v(1) ����(0,2,3,4,6)
        b"B" #���k����(1) �Œ�l�O
        b"B" #�t�B���^�[����(1) �Œ�l�O
        b"B" #�C���^���[�X����(1) ����(0,1)
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
    for y in xrange(image.height()):
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
    
    for y in xrange(image.height()):
        data.append(0)
        extend(chain.from_iterable(pixelTable[i] for i in scanLine(y).asstring(w)))
    
    cpdata = zlib.compress(bytes(bytearray(data)), 0)
    
    from math import ceil
    chank_size = 64*1024
    for i in xrange(int(ceil(len(cpdata) / chank_size))):
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