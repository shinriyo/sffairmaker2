#encoding:shift-jis
from __future__ import division, print_function

from sffairmaker.qutil import *
import PIL.Image
import PIL.PcxImagePlugin

import struct
import cStringIO
import copy
import itertools
from collections import namedtuple

__metaclass__ = type

PCXPALSIZE = 3*256

SFF_HEADER = (
    "12s" + #00-11 "ElecbyteSpr\0" signature [12]
    "4B" + #12-15 1 verhi, 1 verlo, 1 verlo2, 1 verlo3 [04]
    "I"+#16-19 Number of groups [04]
    "I"+    #20-24 Number of Images [04]
    "I"+#24-27 File offset where first subfile is located [04]
    "I"+#28-31 Size of subheader in bytes [04]
    "B"+#32 Palette type (1=SPRPALTYPE_SHARED or 0=SPRPALTYPE_INDIV) [01]
    "3B"+#33-35 Blank; set to zero [03]
    "476s"#36-511 Blank; can be used for comments [476]
    )

SFF_SUB_HEADER = (
    "i"+#00-03 File offset where next subfile in the "linked list" is [04]
        #located. Null if last subfile
    "I"+#04-07 Subfile length (not including header) [04]
        #Length is 0 if it is a linked sprite
    "h"+#08-09 Image axis X coordinate [02]
    "h"+#10-11 Image axis Y coordinate [02]
    "h"+#12-13 Group number [02]
    "h"+#14-15 Image number (in the group) [02]
    "H"+#16-17 Index of previous copy of sprite (linked sprites only) [02]
        #This is the actual
    "b"+#18 True if pal is same as previous Image [01]
    "13s"#19-31 Blank; can be used for comments [13]

    #32- PCX graphic data. If pal data is available, it is the last
    #768 bytes.
    )

class SprBase:
    def __eq__(self, other):
        return all(getattr(self, k) == getattr(other, k) for k in self.__slots__)
    
    __hash__ = None
        
    @property
    def pos(self):
        return self.x, self.y
    
    @pos.setter
    def pos(self, p):
        self.x, self.y = map(int, p)
    
    @property
    def group_index(self):
        return self.group, self.index
    
    @group_index.setter
    def group_index(self, v):
        self.group, self.index = map(int, v)
    
    @property
    def size(self):
        return self.image.size
    
    @property
    def string(self):
        return self.image.tostring()
    
    @property
    def pal(self):
        return self.image.getpalette()
    
    def image_data(self):
        mem = cStringIO.StringIO()
        self.image.save(mem, format="pcx")
        return mem.getvalue()

class ExternalSpr(SprBase):
    __slots__ = "x y group index link image dependentPalette isBroken".split()
    def __init__(self):
        self.x = 0
        self.y = 0
        self.group = None
        self.index = None
        self.link = None
        self.image = None
        self.dependentPalette = False
        self.isBroken = False
    
    def __str__(self):
        return "ExternalSpr(group={0.group}, index={0.index}, dependentPalette={0.dependentPalette}, link={0.link}, isBroken={0.isBroken})"\
                .format(self)
    
class InternalSpr(SprBase):
    __slots__ = "x y group index image useAct".split()
    def __init__(self):
        self.x = 0
        self.y = 0
        self.group = None
        self.index = None
        self.image = None
        self.useAct = False
    
    def __str__(self):
        return "InternalSpr(group={0.group}, index={0.index}, useAct={0.useAct})"\
                .format(self)

    
DefaultPalette = [0]*256*3
OpeningErrorInfo = namedtuple("OpeningErrorInfo", "number group index error")

def readExternalSprList(fp):
    sprList = []
    errorList = []
    
    headstr = fp.read(struct.calcsize(SFF_HEADER))
    if len(headstr) < struct.calcsize(SFF_HEADER):
        return sprList, errorList
    
    head = struct.unpack(SFF_HEADER, headstr)
    nextImageOffset = head[7]
    
    n = -1
    while(nextImageOffset != 0):
        n += 1
        
        fp.seek(nextImageOffset)
        buf = fp.read(struct.calcsize(SFF_SUB_HEADER))
        if len(buf) < struct.calcsize(SFF_SUB_HEADER):
            break
        
        SubHead = struct.unpack(SFF_SUB_HEADER, buf)
        
        nextImageOffset = SubHead[0]
        length = SubHead[1]
        x = SubHead[2]
        y = SubHead[3]
        group = SubHead[4]
        index = SubHead[5]
        linkImageIndex = SubHead[6]
        usePrevPalette = (SubHead[7] > 0)
        
        exSpr = ExternalSpr()
        exSpr.group = group 
        exSpr.index = index 
        exSpr.x = x
        exSpr.y = y
        exSpr.dependentPalette = usePrevPalette
        
        if length:
            imageBytes = fp.read(length)
            i = cStringIO.StringIO(imageBytes)
            
            try:
                im = PIL.Image.open(i)
            except IOError as e:
                errorList.append(OpeningErrorInfo(
                    number=n, group=group, index=index, error=e)
                )
                exSpr.image = None
                exSpr.isBroken = True
            else:
                if im.getpalette() is None:
                    im.putpalette(DefaultPalette)
                exSpr.image = im
        else:
            exSpr.link = linkImageIndex
        
        sprList.append(exSpr)
    return sprList, errorList
    

def internalSprList(exSprList):
    sprList = []
    errorList = []
    link_map = {}
    append = sprList.append
    isPrevPaletteShared = False
    prevPalette = None
    
    for i, exSpr in enumerate(exSprList):
        if exSpr.isBroken:
            continue
            
        spr = InternalSpr()
        spr.group = exSpr.group
        spr.index = exSpr.index
        spr.pos   = exSpr.pos
        
        if exSpr.link is None:
            spr.image = exSpr.image
            spr.useAct = (exSpr.dependentPalette and isPrevPaletteShared) or \
                         (spr.group_index) in [(0, 0), (9000, 0)]
            if not spr.useAct:
                if exSpr.dependentPalette:
                    if prevPalette is not None:
                        exSpr.image.putpalette(prevPalette)
                else:
                    prevPalette = exSpr.image.getpalette()
        else:
            try:
                linked = link_map[exSpr.link]
            except KeyError as error:
                errorList.append(OpeningErrorInfo(
                    number=i,
                    group=spr.group,
                    index=spr.index,
                    error=error
                ))
                continue
            spr.image  = linked.image
            spr.useAct = linked.useAct
        
        isPrevPaletteShared = spr.useAct
        link_map[i] = spr
        append(spr)
    return sprList, errorList


def readSprList(fp):
    exSprList, errorList = readExternalSprList(fp)
    sprList, errorList2 = internalSprList(exSprList)
    return sprList, errorList + errorList2

def openSprList(filename):
    with open(filename, "rb") as fp:
        return readSprList(fp)

def writeSffSubHeader(fp, exSpr, nextImageOffset, length):
    head = (
        #00-03 File offset where next subfile in the "linked list" is [04]
        #located. Null if last subfile
        nextImageOffset,
        #04-07 Subfile length (not including header) [04]
        ##Length is 0 if it is a linked inSprite
        length,
        #08-09 Image axis X coordinate [02]
        exSpr.pos[0],
        #10-11 Image axis Y coordinate [02]
        exSpr.pos[1],
        #12-13 Group number [02]
        exSpr.group,
        #14-15 Image number (in the group) [02]
        exSpr.index,
        #16-17 Index of previous copy of inSprite (linked inSprites only) [02]
        0 if exSpr.link is None else exSpr.link,
        #This is the actual
        #18 True if pal is same as previous Image [01]
        (1 if exSpr.dependentPalette else 0),
        #19-31 Blank; can be used for comments [13]
        "",
        ##32- PCX graphic data. If pal data is available, it is the last
        ##768 bytes.
    )
    fp.write(struct.pack(SFF_SUB_HEADER , *head))


def writeSffSubFile(fp, exSpr, last=False):
    if exSpr.link is not None:
        pcxData = ""
        length = 0
    else:
        pcxData = exSpr.image_data()
        length = len(pcxData)
    
    if last:
        nextImageOffset = 0
    else:
        nextImageOffset = fp.tell() + length + struct.calcsize(SFF_SUB_HEADER)
    
    writeSffSubHeader(fp, exSpr, nextImageOffset, length)
    fp.write(pcxData)
    

def writeSffHeader(fp, sprList):
    head = (
        #00-11 "ElecbyteSpr\0" signature [12]
        "ElecbyteSpr",
        #12-15 1 verhi, 1 verlo, 1 verlo2, 1 verlo3 [04]
        0,1,0,1,
        #16-19 Number of groups [04]
        len(set(s.group for s in sprList)),
        #20-24 Number of Images [04]
        len(sprList),
        #24-27 File offset where first subfile is located [04]
        struct.calcsize(SFF_HEADER),
        #28-31 Size of subheader in bytes [04]
        struct.calcsize(SFF_SUB_HEADER),
        #32 Palette type (1=SPRPALTYPE_SHARED or 0=SPRPALTYPE_INDIV) [01]
        1,
        #33-35 Blank; set to zero [03]
        0,0,0,
        #36-511 Blank; can be used for comments [476]
        "",
    )
    fp.write(struct.pack(SFF_HEADER, *head))


def writeExternalSprList(fp, exSprList):
    writeSffHeader(fp , exSprList)
    #各画像の書き込み
    L = len(exSprList)
    for i, s in enumerate(exSprList):
        writeSffSubFile(fp, s, i==L-1)
    

def externalSprList(inSprList, forChar=True):
    if forChar:
        return externalSprListForChar(inSprList)
    else:
        return externalSprListForStage(inSprList)

def externalSprListForChar(inSprList):
    # 凡例:(group, index, useAct)
    #
    # 画像の並ぶ順番
    # (9000, 0, *)
    # (9000, 1, True)
    # (9000, 1, False)
    # (0, 0, False)
    # (0, 0, True)
    # (*, *, True)
    # (*, *, False)
    
    exSprList = []
    append = exSprList.append
    
    s_9000_0 = []
    s_9000_1_0 = []
    s_9000_1_1 = []
    s_0_0_0 = []
    s_0_0_1 = []
    s_x_x_0 = []
    s_x_x_1 = []
    
    groups = {
        (9000, 0): [s_9000_0, s_9000_0],
        (9000, 1): [s_9000_1_0, s_9000_1_1],
        (0, 0)   : [s_0_0_0, s_0_0_1],
    }
    other = [s_x_x_0, s_x_x_1]
    
    for s in inSprList:
        group = groups.get(s.group_index, other)
        group[bool(s.useAct)].append(s)
    
    if not s_0_0_0 and not s_0_0_1:
        # (0, 0) の画像が無い場合、仕方ないので空の画像を追加する
        exSpr = InternalSpr()
        exSpr.group_index = (0, 0)
        exSpr.image = PIL.Image.new("P", (1, 1))
        exSpr.useAct = True
        s_0_0_0.append(exSpr)
    
    for s in s_9000_0:
        exSpr = ExternalSpr()
        exSpr.group_index = s.group_index
        exSpr.pos = s.pos
        exSpr.image = s.image
        exSpr.dependentPalette = False # (9000, 0)は必ず独立パレット
        append(exSpr)
    
    for s in itertools.chain(s_9000_1_1, s_9000_1_0, s_0_0_0, s_0_0_1, s_x_x_1, s_x_x_0):
        exSpr = ExternalSpr()
        exSpr.group_index = s.group_index
        exSpr.pos = s.pos
        exSpr.image = s.image
        exSpr.dependentPalette = s.useAct
        append(exSpr)
        
    return exSprList
    

def externalSprListForStage(inSprList):
    exSprList = []
    append = exSprList.append
    
    for s in inSprList:
        exSpr = ExternalSpr()
        exSpr.group_index = s.group_index
        exSpr.pos = s.pos
        exSpr.image = s.image
        exSpr.dependentPalette = False
        append(exSpr)
        
    return exSprList
    
    

def writeSprList(fp, sprList):
    exSprList = externalSprList(sprList)
    writeExternalSprList(fp, exSprList)

def saveSprList(filename, sprList):
    with open(filename, "wb") as fp:
        writeSprList(fp, sprList)

def main():
    pass
    
if __name__ == "__main__":
    main()
