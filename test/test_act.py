#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.act import *
from tempfile import gettempdir

import os.path

def test1():
    colorTable = [qRgb(i, (i*5)%256, (i*17)%256) for i in range(256)]
    for open_, save_, ext in [(open, save, ".act"),
                              (openText, saveToText, ".txt"),
                              (openImage, saveToImage, ".bmp"),]:
        
        f = os.path.join(gettempdir(), "test_act" + ext)
        save_(f, colorTable)
        colorTable1 = open_(f)
        
        nose.tools.assert_equals(colorTable, colorTable1, open_)
        
    
def test2():
    import io
    fp = io.BytesIO()
    
    write(fp, [])
    fp.seek(0)
    colorTable = read(fp)
    assert colorTable == colorTable256([])
    
    fp = io.BytesIO()
    write(fp, colorTable)
    fp.seek(0)
    assert colorTable == read(fp)
    
    import tempfile
    import os.path
    filename = os.path.join(tempfile.gettempdir() + "test.act")
    save(filename, colorTable)
    assert open(filename) == colorTable
    
    

def main():
    nose.runmodule()
    
if __name__ == '__main__':
    main()
