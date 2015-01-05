#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose
from nose.tools import *
from sffairmaker.sfflib import *
from sffairmaker.qutil import *
from sffairmaker.image_op import qcolortable_to_pilpalette
import PIL.Image


def test_read_with_error():
    # 画像データが破損している場合の読み込み
    
    from cStringIO import StringIO
    fp = StringIO()
    
    exSprList = []
    group_index_list = [
        (0, 1, True),
        (0, 2, True),
        (0, 3, True),
        (1, 1, False),
        (1, 2, False),
        (1, 3, False),
        (9000, 1, False),
        (9000, 0, True),
    ]
    for group, index, dependentPalette in group_index_list:
        image = PIL.Image.new("P", (16, 16))
        image.putpalette([x for i in xrange(256) for x in [group%256, index%256, i]])
        
        spr = ExternalSpr()
        spr.group=group
        spr.index=index
        spr.dependentPalette=dependentPalette
        spr.image=image
        exSprList.append(spr)
    
    
    writeSffHeader(fp, exSprList)

    def writeSffSubFile1(fp, exSpr, last=False):
        #わざと不完全なデータを書き込む
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
        fp.write(chr(0)*len(pcxData))
    
    for i, exSpr in enumerate(exSprList):
        if i % 2 == 0:
            writeSffSubFile(fp, exSpr, i == len(exSprList) - 1)
        else:
            writeSffSubFile1(fp, exSpr, i == len(exSprList) - 1)
    
    fp.seek(0)
    exSprList1, errorList = readExternalSprList(fp)
    
    assert_equal([s.group_index for s in exSprList1 if not s.isBroken],
                 [s.group_index for s in exSprList[::2]])
    assert_equal(len(errorList), len(exSprList) // 2)


def testImageOriginalPalette():
    #画像本来のパレットが保持されるか
    from cStringIO import StringIO
    fp = StringIO()
    
    sprList0 = []
    group_index_list = [
        (0, 1, True),
        (0, 2, True),
        (0, 3, True),
        (1, 1, False),
        (1, 2, False),
        (1, 3, False),
        (9000, 1, False),
        (9000, 0, True),
    ]
    for group, index, useAct in group_index_list:
        image = PIL.Image.new("P", (16, 16))
        image.putpalette([x for i in xrange(256) for x in [group%256, index%256, i]])
        
        spr = InternalSpr()
        spr.group=group
        spr.index=index
        spr.useAct=useAct
        spr.image=image
        sprList0.append(spr)
    
    writeSprList(fp, sprList0)
    fp.seek(0)
    
    sprList1, errorList = readSprList(fp)
    
    assert not errorList, errorList
    
    from operator import attrgetter
    from itertools import izip
    
    sprDict0 = dict((s.group_index, s) for s in sprList0)
    sprDict1 = dict((s.group_index, s) for s in sprList1)
    
    for group, index, useAct in group_index_list:
        s0 = sprDict0[group, index]
        s1 = sprDict1[group, index]
        
        assert s0.group_index == s1.group_index
        assert s0.useAct == s1.useAct
        assert s0.image.getpalette() == s1.image.getpalette()


def test_palette():
    externalSprList0 = []
    
    images = []
    colorTables = []
    for i in xrange(1, 5):
        im = PIL.Image.new("P", (1, 1))
        ct = [qRgb(k, 0, i) for k in xrange(256)]
        im.putpalette(qcolortable_to_pilpalette(ct))
        
        colorTables.append(ct)
        images.append(im)
    
    L = [
        (0, 0, False, images[0]),
        (0, 1, True, images[1]),
        (0, 2, False, images[2]),
        (0, 3, True, images[3]),
    ]
    
    for group, index, dependentPalette, image in L:
        exSpr = ExternalSpr()
        exSpr.group = group
        exSpr.index = index
        exSpr.dependentPalette = dependentPalette
        exSpr.image = image
        externalSprList0.append(exSpr)
    
    sprList, errorList = list(internalSprList(externalSprList0))
    
    assert not errorList
    
    nose.tools.assert_equal(sprList[0].group_index, (0, 0))
    assert sprList[0].useAct
    sprList[0].image.getpalette() == images[0].getpalette()
    
    nose.tools.assert_equal(sprList[1].group_index, (0, 1))
    assert sprList[1].useAct
    sprList[1].image.getpalette() == images[1].getpalette()

    nose.tools.assert_equal(sprList[2].group_index, (0, 2))
    assert not sprList[2].useAct
    sprList[2].image.getpalette() == images[2].getpalette()
    
    nose.tools.assert_equal(sprList[3].group_index, (0, 3))
    assert not sprList[3].useAct
    sprList[3].image.getpalette() == images[2].getpalette()
    
    
    
    

def main():
    nose.runmodule()

if __name__ == '__main__':
    main()
