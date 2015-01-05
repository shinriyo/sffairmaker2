#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.spr_selector import *

def testIntComboBox():
    app = QApplication([])
    c = IntComboBox()
    log = []
    c.valueChanged.connect(log.append)
    
    #最初の値はNone
    assert c.isEditable()
    assert c.count() == 0
    assert c.value() is None
    
    #setItemsすると、itemsの最初の値がvalueになる
    c.setItems(xrange(5))
    assert c.count() == 5, c
    assert c.currentText() == "0", c.currentText()
    assert c.value() == 0, str(c.value())
    assert log == [0], log
    items = [int(c.itemText(i)) for i in xrange(c.count())] 
    assert items == range(5), items
    
    log[:] = []
    c.setEditText("3")
    assert c.currentText() == "3", c.currentText()
    assert c.value() == 3, c.value()
    assert log == [3], log
    
    log[:] = []
    c.setItems(xrange(5, 10))
    assert c.currentText() == "5", c.currentText()
    assert c.value() == 5, c.value()
    assert log == [5], log
    
    log[:] = []
    c.setEditText("+5")
    #文字列が変わっても、表現する整数が同じなら、emitされない
    assert c.currentText() == "+5", c.currentText()
    assert c.value() == 5
    assert log == []
    
    #不正な文字列のとき、値はNone
    #Noneに変わったときも、emitされる
    log[:] = []
    c.setEditText("spamegg")
    assert c.currentText() == "spamegg"
    assert c.value() is None
    assert log == [None], log
    
    #NoneをsetValueすると、文字列は空に
    c.setValue(1)
    c.setValue(None)
    assert c.currentText() == "", c.currentText()
    assert c.value() is None


def testGroupIndexSelector():
    app = QApplication([])
    from sffairmaker import model
    
    m = model._Model()
    sff = m.sff()
    sff.create()
    sff.newSpr(group=0, index=0)
    sff.newSpr(group=0, index=1)
    sff.newSpr(group=0, index=2)
    sff.newSpr(group=1, index=0)
    sff.newSpr(group=1, index=1)
    sff.sprByIndex(-1, -1).remove()
    
    #SFFの中身 -> (0, 0), (0, 1), (0, 2), (1, 0), (1, 1)
    
    s = GroupIndexSelector(sprs=m)
    assert s.value() == (0, 0), s.value()
    
    log = []
    s.valueChanged.connect(log.append)
    
    #groupかindexにNoneを設定すると、valueは(None, *)ではなくNone
    
    #groupにNone
    log[:] = []
    s.setGroup(None)
    assert s.value() is None
    assert log == [None]
    
    #indexにNone
    log[:] = []
    s.setGroup(0)
    assert s.value() == (0, 0)
    assert log == [(0, 0)]
    log[:] = []
    s.setIndex(None)
    assert s.value() is None
    assert log == [None]
    
    #元からvalueがNoneのときに、setGroup(None)しても何も起きない
    log[:] = []
    s.setGroup(None)
    assert s.value() is None
    assert log == []
    
    s.setValue((0, 2))
    log[:] = []
    #groupを変えると、indexは自動的にそのgroupの最小のindexになる
    s.setGroup(1)
    assert s.value() == (1, 0)
    assert log == [(1, 0)]
    
    #しかし、indexの値が変化せず、groupの値だけが変わったときも、しっかり通知される
    log[:] = []
    s.setGroup(0)
    assert s.value() == (0, 0)
    assert log == [(0, 0)]
    
    #groupに無い、不正なindexを設定することも出来る
    log[:] = []
    s.setIndex(10)
    assert s.value() == (0, 10)
    assert log == [(0, 10)]
    assert s._indexbox.currentText() == "10"
    
    #setValueはgroupとindexをatomicに変更しないといけない
    #すなわち、通知はgroupとindexが両方変更された後、１回だけ通知される
    log[:] = []
    s.setValue((1, 1))
    assert s.value() == (1, 1)
    assert log == [(1, 1)]
    
    #NoneをsetValueすると、groupもindexもNone
    log[:] = []
    s.setValue(None)
    assert s.value() == None
    assert log == [None]
    assert s.group() == None
    assert s.index() == None
    


def testSprSelector():
    app = QApplication([])
    from sffairmaker import model, view
    m = model._Model()
    sff = m.sff()
    sff.create()
    sff.newSpr(group=0, index=0)
    sff.newSpr(group=0, index=1)
    sff.newSpr(group=0, index=2)
    sff.newSpr(group=1, index=0)
    sff.newSpr(group=1, index=1)
    sff.sprByIndex(-1, -1).remove()
    #SFFの中身 -> (0, 0), (0, 1), (0, 2), (1, 0), (1, 1)
    
    s = SprSelector(sprs=m)
    assert s.spr().group_index() == (0, 0)
    
    log = []
    log1 = []
    s.sprChanged.connect(log.append)
    s.valueChanged.connect(log1.append)
    
    s.setValue((-1, -1))
    assert not s.spr().isValid()
    assert log1 == [(-1, -1)], log1
    assert log == [s.spr()], log
    
    log[:] = []
    log1[:] = []
    
    s.setValue((1, 1))
    assert s.spr().isValid()
    assert log1 == [(1, 1)], log1
    assert log == [s.spr()], log
    
    
def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
