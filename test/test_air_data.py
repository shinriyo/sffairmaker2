#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose
from nose.tools import *
from sffairmaker.air_data import *

def test_anim_new():
    #new
    a = Air.create()
    assert len(a.animIds()) == 1
    assert len(a._elms) == 1
    
    for animId in a.animIds():
        assert len(a.elmIds(animId)) == 1
    
    animId = a.newAnim()
    assert len(a.animIds()) == 2
    assert len(a._elms) == 2
    for animId in a.animIds():
        assert len(a.elmIds(animId)) == 1
    
    
def test_air_move():
    a = Air.create()
    animId = a.animIds()[0]
    for i in xrange(4):
        a.copyElm(animId, -1, a.elmIds(animId)[0])
    assert len(a.elms(animId)) == 5, len(a.elms(animId))
    
    for i in xrange(5):
        elmId = a.elmIds(animId)[i]
        a.changeElm(elmId, group=i)
    
    oldElmIds = a.elmIds(animId)
    a.moveElm(animId, 3, a.elmIds(animId)[0])
    newElmIds = a.elmIds(animId)
    
    assert oldElmIds != newElmIds, (oldElmIds, newElmIds)
    assert a.elms(animId)[2].group() == 0, a.elms(animId)[2].group()
    assert len(a.elms(animId)) == 5, len(a.elms(animId))
    
    a.moveElm(animId, 0, a.elmIds(animId)[4])
    assert a.elms(animId)[0].group() == 4, a.elms(animId)[0].group()
    assert len(a.elms(animId)) == 5, len(a.elms(animId))

def test_open_empty_file():
    #空ファイルを開いた場合、デフォルトのAnimが追加されている
    import tempfile
    from os.path import join, dirname
    filename = join(tempfile.gettempdir(), "test.air")
    with open(filename, "w") as fp:
        pass
    air = Air.open(filename)
    
    assert len(air.animIds()) == 1
    a, = air.animIds()
    
    assert len(air.elms(a)) == 1

def test_remove_last_anim():
    a = AirData()
    
    assert len(a.animIds()) == 1
    animId, = a.animIds()
    
    a.removeAnim(animId)
    assert len(a.animIds()) == 1
    assert animId != a.animIds()[0]

def test_remove_last_elm():
    a = AirData()
    
    assert len(a.animIds()) == 1
    animId, = a.animIds()
    
    assert len(a.elmIds(animId)) == 1
    elmId, = a.elmIds(animId)
    
    a.removeElm(animId, elmId)
    assert len(a.elmIds(animId)) == 1
    assert elmId != a.elmIds(animId)[0]


def testChangeAnimFromString():
    #アニメのテキスト編集で、編集前と内容が変わらなかったら、アンドゥに登録しない
    a = AirData()
    animId, = a.animIds()
    for index in xrange(10):
        a.newElm(
            animId,
            -1,
            index=index,
            clsn1=Clsn((i,i*3,i*5,i*9) for i in xrange(7)),
        )
    a.changeAnim(
        animId,
        loop=5,
        clsn1=Clsn((i,i*3,i*5,i*9)for i in xrange(7))
    )
    
    ss = a.animToString(animId)
    assert not a.changeAnimFromString(animId, ss)
    
    ss = """
[begin action 0]
13,15
"""
    assert a.changeAnimFromString(animId, ss)
    
    assert_equals(len(a.elms(animId)), 1)
    elm, =  a.elms(animId)
    assert_equals(elm.group_index(), (13, 15))
    assert_equals(elm.time(), 0)
    assert_equals(elm.pos(), (0, 0))
    

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
