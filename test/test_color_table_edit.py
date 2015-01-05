#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.color_table_edit import *

def testCurrentColorChanged():
    app = QApplication([])
    xmodel = model._Model()
    image = image_op.Image256(128, 1)
    for x in xrange(128):
        image.setPixel(x, 0, x)
    colorTable = [qRgb(i, 0, 0) for i in xrange(256)]
    image.setColorTable(colorTable)
    
    s = SprColorTableEdit(xmodel=xmodel)
    assert xmodel is s.xmodel()
    
    spr = xmodel.sff().newSpr(image=image)
    updated = []
    s.setSpr(spr)
    
    s.setCurrentIndex(s.createIndex(0, 0))
    
    log = []
    s.currentColorChanged.connect(log.append)
    
    s.setCurrentIndex(s.createIndex(0, 1))
    assert log == [QColor(1, 0, 0)]

    log[:] = []
    colorTable = [qRgb(0, i, 0) for i in xrange(256)]
    s.setColorTable(colorTable)
    assert log == [QColor(0, 1, 0)], log
    
    log[:] = []
    colorTable = [qRgb(0, 0, i) for i in xrange(256)]
    spr.setColorTable(colorTable)
    assert log == [QColor(0, 0, 1)], log
    
    log[:] = []
    s.setCurrentColor(QColor(1, 2, 3))
    assert log == [QColor(1, 2, 3)], log


def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
