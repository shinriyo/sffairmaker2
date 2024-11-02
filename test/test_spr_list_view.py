#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.spr_list_view import *
from sffairmaker.null import Null

def testSorting():
    from pprint import pformat, pprint
    
    class TestModel(SprListModel):
        def reset(self):
            pass
        def sff(self):
            return Null()
    class TestSpr:
        def __init__(self, group, index):
            self._group = group
            self._index = index
        exec def_qgetter("group", "index")
        def group_index(self):
            return self._group, self._index
        def __repr__(self):
            return str(self.group_index())
        
    app = QApplication([])
    v = QListView()
    m = TestModel(parent=v)
    m.setSortingEnabled(False)
    v.setSelectionMode(QListView.ExtendedSelection)
    v.setModel(m)
    
    sprs = [TestSpr(group, index) for group in range(5) for index in range(5)]
    m.setSprs(sprs[:len(sprs)] + sprs[len(sprs):])
    
    sel = set()
    for i in range(5):
        row = i**2
        sel.add(sprs[row])
        v.selectionModel().select(m.index(row), QItemSelectionModel.Select)
    
    m.sort(key=methodcaller("group_index"))
    msprs = [m.data(m.index(i), role=m.SprRole) for i in range(m.rowCount())]
    assert msprs == sprs
    
    msel = set(m.data(index, role=m.SprRole) for index in v.selectedIndexes())
    assert sel == msel, pformat([sel, msel])
    
    import random
    d = {}
    for s in sprs:
        d[s] = random.random()
    m.sort(key=d.__getitem__)
    msel = set(m.data(index, role=m.SprRole) for index in v.selectedIndexes())
    assert sel == msel, pformat([sel, msel])
    
    m.sort(key=methodcaller("group_index"))
    msprs = [m.data(m.index(i), role=m.SprRole) for i in range(m.rowCount())]
    assert msprs == sprs, d
    msel = set(m.data(index, role=m.SprRole) for index in v.selectedIndexes())
    assert sel == msel, pformat([sel, msel])
    
    #�ǉ��������̂́A�����̕�����ɒǉ������
    m.setSortingEnabled(True)
    newspr = TestSpr(1, 4) # sprs[9].group_index() == (1, 4)
    m.addSprs([newspr])
    msel = set(m.data(index, role=m.SprRole) for index in v.selectedIndexes())
    assert sel == msel, pformat([sel, msel])
    
    msprs = [m.data(m.index(i), role=m.SprRole) for i in range(m.rowCount())]
    assert msprs[3**2 + 1] == newspr
    msprs.pop(3**2 + 1)
    assert msprs == sprs
    
    numberstoremove = [5, 13, 19]
    sprs1 = [s for i, s in enumerate(sprs) if i not in numberstoremove]
    sprsToRemove = [s for i, s in enumerate(sprs) if i in numberstoremove]
    
    m.removeSprs(sprsToRemove)
    msel = set(m.data(index, role=m.SprRole) for index in v.selectedIndexes())
    assert sel == msel, pformat([sel, msel])

    
def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
