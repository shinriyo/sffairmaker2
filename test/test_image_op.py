#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.image_op import *

def testIndexesToErase():
    im = imageForTest(QSize(100, 100), QRect(20, 20, 80, 80))
    assert set([]) == indexesToErase(im, [QRect(0, 0, 20, 20)])
    assert set([1]) == indexesToErase(im, [QRect(0, 0, 30, 30)])
    

def testMoveRgb():
    colorTable = [qRgb(i,i,i) for i in xrange(12)]
    rgbMap = dict((i, qRgb(i,i,i)) for i in xrange(5, 10))
    
    colorTable1 = moveRgb(colorTable, 20, 5, rgbMap)
    
    assert colorTable1[:5] == [qRgb(i,i,i) for i in xrange(5)]
    assert colorTable1[5:10] == [qRgb(0,0,0) for i in xrange(5,10)]
    assert colorTable1[10:12] == [qRgb(i,i,i) for i in xrange(10,12)]
    assert colorTable1[12:20] == [qRgb(0,0,0) for i in xrange(12,20)]
    assert colorTable1[20:25] == [qRgb(i,i,i) for i in xrange(5, 10)]
    assert colorTable1[25:] == [qRgb(0,0,0) for i in xrange(25, 256)]

def testCopyRgb():
    colorTable = [qRgb(i,i,i) for i in xrange(256)]
    rgbMap = dict((i, qRgb(i,i,i)) for i in xrange(5, 10))
    
    colorTable1 = copyRgb(colorTable, 20, 5, rgbMap)
    
    assert colorTable1[:20] == [qRgb(i,i,i) for i in xrange(20)]
    assert colorTable1[20:25] == [qRgb(i,i,i) for i in xrange(5, 10)]
    assert colorTable1[25:] == [qRgb(i,i,i) for i in xrange(25, 256)]
    
   
def testSwapRgb():
    r = swapRgb(range(10), 5, 0, [0, 1])
    assert r[:10] == [5, 6, 2, 3, 4, 0, 1, 7, 8, 9]
    assert all(x == qRgb(0,0,0) for x in r[10:])
    
def testCrop():
    im = imageForTest(QSize(20, 20), QRect(0, 0, 0, 0))
    print(rectToCrop(im))
    assert rectToCrop(im).size() == QSize(1, 1)
    
    im = imageForTest(QSize(100, 100), QRect(20, 20, 80, 80))
    assert rectToCrop(im) == QRect(20, 20, 80, 80)
    
    im1, delta = autoCrop(im)
    assert delta == QPoint(20, 20)
    assert im1.size() == QSize(80, 80)
    assert all(im1.pixelIndex(p)==1 for p in imagePixels(im1))


def testAllocBgColor():
    #未使用色が無いとエラー
    image = Image256(1, 256)
    image.setColorTable([qRgb(i, i, i) for i in xrange(256)])
    for i in xrange(256):
        image.setPixel(0, i, i)
    
    try:
        image1 = allocBgColor(image)
    except NoUnusedColorError:
        pass
    else:
        assert False
    
    #未使用色が
    #最初の未使用色より前を、一つずらし、
    #最初の未使用色より後は不動。
    image = Image256(1, 16)
    image.setColorTable([qRgb(i, i, i) for i in xrange(16)])
    for i in xrange(16):
        if i % 5 == 0:
            image.setPixel(0, i, 0)
        else:
            image.setPixel(0, i, i)
    
    image1 = allocBgColor(image, bg=qRgb(1, 2, 3))
    assert image is not image1
    
    # ピクセルのチェック
    # 変換前: 0, 1, 2, 3, 4, 0, 6, 7, 8, 9, 0, 11, 12, 13, 14, 0, 16
    # 変換後: 1, 2, 3, 4, 5, 1, 6, 7, 8, 9, 1, 11, 12, 13, 14, 1, 16
    pixels = [image1.pixelIndex(0, i) for i in xrange(16)]
    expectedPixels = []
    for i in xrange(16):
        if i < 5:
            expectedPixels.append(i + 1)
        elif i % 5 == 0:
            expectedPixels.append(1)
        else:
            expectedPixels.append(i)
    assert pixels == expectedPixels
    
    #パレットのチェック
    # 変換前: #000, #111, ..., #FFF
    # 変換後: #123, #000, #111, #222, #333, #444, #666, #777, ..., #FFF, #000, #000, ...
    
    expectedColorTable = [qRgb(1, 2, 3)]
    for i in xrange(256):
        if i < 16:
            if i != 5:
                expectedColorTable.append(qRgb(i, i, i))
        else:
            expectedColorTable.append(qRgb(0, 0, 0))
    
    if image1.colorTable() != expectedColorTable:
        for i in xrange(256):
            if i < len(image1.colorTable()):
                x = QColor(image1.colorTable()[i])
                c1 = (x.red(), x.green(), x.blue())
            else:
                c1 = None
            if i < len(expectedColorTable):
                x = QColor(expectedColorTable[i])
                c2 = (x.red(), x.green(), x.blue())
            else:
                c2 = None
                
            if c1 != c2:
                print(i, c1, c2)
        assert False
        

def testImmutable():
    # input の QImage と outputのQImageが別オブジェクトであるかの検査
    im = Image256(16, 16)
    
    pal = [qRgb(i,i,i) for i in xrange(256)]
    assert im is not autoCrop(im)[0]
    assert im is not eraseRects(im, [QRect(0, 0, 5, 5)])
    assert im is not eraseRectsColors(im, [QRect(0, 0, 5, 5)])
    assert im is not deleteUnusedColors(im)
    assert im is not allocBgColor(im)
    assert im is not replaceColorTable(im, pal)
    assert im is not cleanColorTable(im, pal)

def testFullColorTable():
    # len(colorTable) == 256
    
    im = Image256(16, 16)
    pal = [qRgb(i,i,i) for i in xrange(256)]
    assert len(autoCrop(im)[0].colorTable()) == 256
    assert len(eraseRects(im, [QRect(0, 0, 5, 5)]).colorTable()) == 256
    assert len(eraseRectsColors(im, [QRect(0, 0, 5, 5)]).colorTable()) == 256
    assert len(deleteUnusedColors(im).colorTable()) == 256
    assert len(allocBgColor(im).colorTable()) == 256
    assert len(replaceColorTable(im, pal).colorTable()) == 256
    assert len(cleanColorTable(im, pal).colorTable()) == 256


def testAddImageColors():
    #隙間が無い場合
    colorTable = [qRgb(1, 1, 1)] * 256
    try:
        addImageColors(colorTable, set(xrange(256)), Image256(16, 1))
    except ValueError: pass
    else: assert False
    
    #隙間が無い場合
    colorTable = [qRgb(i,0,0) for i in xrange(128)] + [qRgb(0,0,0)]*128
    im = Image256(256, 1)
    im.setColorTable([qRgb(i,i,i) for i in xrange(256)])
    for x in xrange(256):
        im.setPixel(x, 0, x)
    try:
        addImageColors(colorTable, set(xrange(256)), im)
    except ValueError: pass
    else: assert False
    
    #隙間が無いけど、全部の色が既にある場合
    colorTable = [qRgb(i,0,0) for i in xrange(256)]
    im = Image256(256, 1)
    im.setColorTable([qRgb(i,0,0) for i in xrange(256)])
    for x in xrange(256):
        im.setPixel(x, 0, x)
    colorTable1, im1 = addImageColors(colorTable, set(xrange(256)), im)
    assert colorTable1 == colorTable
    assert im == im1
    
    #隙間がある場合
    colorTable = [qRgb(0, 0, 0) for i in xrange(256)]
    im = Image256(16, 1)
    im.setColorTable([qRgb(i,0,0) for i in xrange(256)])
    for x in xrange(16):
        im.setPixel(x, 0, x)
    colorTable1, im1= addImageColors(colorTable, set(), im)
    
    assert colorTable1 == im1.colorTable()
    assert pixelMap(im) == pixelMap(im1)
    
    
    #追加先パレットに、未使用だが同じ色があった場合
    colorTable = [qRgb(0, 0, 0), qRgb(255, 0, 0)]
    im = Image256(3, 1)
    im.setPixel(0, 0, 0)
    im.setPixel(1, 0, 1)
    im.setPixel(2, 0, 2)
    im.setColorTable(colorTable256([qRgb(0, 0, 0), qRgb(0, 255, 0), qRgb(255, 0, 0)]))
    colorTable1, im1 = addImageColors(colorTable, set(), im)
    
    assert im1.colorTable() == colorTable1
    assert pixelMap(im1) == pixelMap(im)
    assert colorTable1[:3] == [qRgb(0, 0, 0), qRgb(0, 255, 0), qRgb(255, 0, 0)]
    assert colorTable1[3:] == [qRgb(0, 0, 0)] * 253
    
def testDeleteUnusedColors():
    import nose.tools
    
    im0 = Image256(256, 1)
    im0.setColorTable([QColor(i, 0, 1).rgb() for i in xrange(256)])
    for i in xrange(16):
        im0.setPixel(i, 0, i)
    for i in xrange(16, 256):
        im0.setPixel(i, 0, 0)
    
    im1 = deleteUnusedColors(im0)
    
    nose.tools.assert_equal(
        list(ipixelIndex(im0)), 
        list(ipixelIndex(im1))
    )
    
    expected_color_table = [QColor(i,0,1).rgb() for i in xrange(16)] + \
                           [QColor(0,0,0).rgb() for i in xrange(16, 256)]
    nose.tools.assert_equal(im1.colorTable(), expected_color_table)

def testCleanColorTable():
    im = Image256(256, 1)
    im.setColorTable([qRgb(2, 2, 2), qRgb(1, 0, 0), qRgb(1,1,1)] + [qRgb(i,0,0) for i in xrange(3, 256)])
    for x in xrange(256):
        im.setPixel(x, 0, x)
    
    colorTable = [qRgb(i, i, i) for i in xrange(256)]
    im1 = cleanColorTable(im, colorTable)
    
    assert im1.colorTable() == colorTable
    
    im.pixelIndex(0, 0) == 2
    im.pixelIndex(1, 0) == 0
    im.pixelIndex(2, 0) == 1
    
    for x in xrange(3, 256):
        assert im.pixelIndex(x, 0) == x, x

#ここからテスト

def imageForTest(size, rect):
    im = Image256(size.width(), size.height())
    im.setColorTable(colorTable256([qRgb(255, 0, 0), qRgb(0, 255, 0)]))
    for p in imagePixels(im):
        if rect.contains(p):
            im.setPixel(p, 1)
        else:
            im.setPixel(p, 0)
    return im

def pixelMap(im):
    d = {}
    for p in imagePixels(im):
        i = im.pixelIndex(p)
        c = im.colorTable()[i]
        d[pxy(p)] = c

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
