#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose
from nose.tools import *
from sffairmaker.sff_data import *
from sffairmaker import model

def add_to_class(klass, name=None):
    def add_to_class_(f):
        setattr(klass, name or f.__name__, f)
    return add_to_class_

@add_to_class(Sff, "_open")
@classmethod
def _open(cls, filename):
    return cls.open(filename)[0]

@add_to_class(Sff)
def _sprByIndex(self, group, index):
    return self.sprById(self.sprIdByIndex(group, index))


    
def test_sff():
    s = Sff.create()
    assert len(s.sprIds()) == 1
    
    s.newSpr()
    assert len(s.sprIds()) == 2
    
    id = s.sprIds()[0]
    assert s.sprById(id).group() == -1
    
    old = s.sprById(id)
    r = s.changeSpr(id, group=2)
    assert r
    assert s.sprById(id).group() == 2
    assert s.sprById(id) != old
    assert s.sprById(id) is not old
    
    old = s.sprById(id)
    r = s.changeSpr(id, group=2)
    assert not r
    assert s.sprById(id).group() == 2
    assert s.sprById(id) == old
    assert s.sprById(id) is not old
    

def test_memento():
    app = QApplication([])
    d = SffData()
    id = d.sprIds()[0]
    assert d.sprById(id).x() == 0
    m = d.memento()
    
    d.changeSpr(id, x=2)
    assert d.sprById(id).x() == 2
    
    d.restore(m)
    assert d.sprById(id).x() == 0

def test_remove_last_spr():
    app = QApplication([])
    s = SffData()
    
    assert len(s.sprIds()) == 1
    sprId, = s.sprIds()
    s.removeSpr(sprId)
    
    assert len(s.sprIds()) == 1
    assert sprId != s.sprIds()[0]



def test_open_empty_file():
    #空ファイルを開いた場合、デフォルトのSprが追加されている
    import tempfile
    from os.path import join, dirname

    app = QApplication([])
    filename = join(tempfile.gettempdir(), u"test.sff")
    with open(filename, "w") as fp:
        pass
    x = Sff._open(filename)
    
    assert len(x.sprIds()) == 1
    

def testCopyCommonPaletteToSprUseAct():
    import tempfile
    from os.path import join, dirname
    app = QApplication([])
    filename = join(tempfile.gettempdir(), "test.sff")
    
    s = Sff.create()
    
    im0 = QImage(1, 1, QImage.Format_Indexed8)
    im0.setColorTable([qRgb(1, 1, 1)]*256)
    im1 = QImage(1, 1, QImage.Format_Indexed8)
    im1.setColorTable([qRgb(2, 2, 2)]*256)
    
    s.newSpr(group=9000, index=0, image=im0)
    s.newSpr(group=9000, index=1, image=im1, useAct=False)
    s.setColorTable([qRgb(100, 100, 100)]*256)
    s.save(filename)
    
    sff1 = Sff._open(filename)
    
    spr0 = sff1.sprById(sff1.sprIdByIndex(9000, 0))
    spr1 = sff1.sprById(sff1.sprIdByIndex(9000, 1))
    assert spr0.useAct()
    assert not spr1.useAct()
    
    im0_1 = spr0.image()
    im1_1 = spr1.image()
    assert im0_1.colorTable() == [qRgb(100, 100, 100)]*256, im0_1.colorTable()
    assert im1_1.colorTable() == [qRgb(2, 2, 2)]*256, im1_1.colorTable()
    


def testIncompleteSff():
    "9000, 0が無い"
    app  = QApplication([])
    from os.path import join
    import tempfile
    sffpath = join(tempfile.gettempdir(), "test.sff")
    
    sff = Sff()
    sff.newSpr(group=0, index=0, useAct=True)
    sff.save(sffpath)
    sff._open(sffpath)


def testImageOriginalPalette():
    #画像本来のパレットが保持されるか
    from cStringIO import StringIO
    fp = StringIO()
    
    class Sff_(Sff):
        @classmethod
        def _saveSprList(self, filename, sprList):
            sfflib.writeSprList(fp, sprList)
        
        @classmethod
        def _openSprList(cls, filename):
            fp.seek(0)
            return sfflib.readSprList(fp)
    
    sff = Sff_()
    sff.newSpr(group=9000, index=0)
    
    group_index_list = [
        (0, 1, True),
        (0, 2, True),
        (0, 3, True),
        (1, 1, False),
        (1, 2, False),
        (1, 3, False),
        (9000, 1, False),
    ]
    
    for group, index, useAct in group_index_list:
        image = Image256(16, 16)
        image.setColorTable([qRgb(group, index, i) for i in xrange(256)])
        sff.newSpr(group=group, index=index, useAct=useAct, image=image)
    
    sff.save("*")
    sff1, errors = Sff_.open("*")
    
    for group, index, useAct in group_index_list:
        s0 = sff._sprByIndex(group, index)
        s1 = sff1._sprByIndex(group, index)
        assert s1 is not None, (group, index)
        assert s1.useAct() == useAct, (group, index)
        
        c0 = s0.image().colorTable()
        c1 = s1.image().colorTable()
        assert c0 == c1, (group, index)



def main():
    nose.runmodule()
    
if __name__ == '__main__':
    main()
