#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose
from nose.tools import *
from sffairmaker.item_scroll_bar import *

def test():
    app = QApplication([])
    scr = ItemScrollBar()
    
    log = []
    scr.currentItemChanged.connect(log.append)
    assert_equal(scr.currentItem(), None)
    assert_equal(scr.items(), [])
    
    #空リストを設定すると、値はデフォルト値
    scr.setItems([])
    assert_equal(scr.currentItem(), None)
    assert_equal(scr.items(), [])
    assert_equal(log, [])
    log[:] = []
    
    #空でないリストを設定すると、値は最初の要素
    scr.setItems([1, 2, 3, 4, 5])
    assert_equal(scr.currentItem(), 1)
    assert_equal(scr.items(), [1, 2, 3, 4, 5])
    assert_equal(log, [1])
    log[:] = []
    
    #同じリストを設定しても何も起こらない
    scr.setItems([1, 2, 3, 4, 5])
    assert_equal(scr.currentItem(), 1)
    assert_equal(scr.items(), [1, 2, 3, 4, 5])
    assert_equal(log, [])
    log[:] = []
    
    #前指していた要素が新しいリストに無いと、前のリストで一つ左にあった要素を指す
    scr.setItems([1, 2, 3, 4, 5])
    scr.setCurrentItem(3)
    log[:] = []
    
    scr.setItems([1, 2, "spam", 4, 5])
    assert_equal(scr.currentItem(), 2, scr.currentItem())
    assert_equal(scr.items(), [1, 2, "spam", 4, 5])
    assert_equal(log, [2], log)
    log[:] = []
    
    #前指していた要素が新しいリストに無く、前のリストで一番左を指していたとき、
    #右にあった要素を指す
    scr.setItems([3, 4, 5, 6])
    scr.setCurrentItem(3)
    log[:] = []
    
    scr.setItems(["spam", 4, 5, 6])
    assert_equal(scr.currentItem(), 4)
    assert_equal(scr.items(), ["spam", 4, 5, 6])
    assert_equal(log, [4])
    log[:] = []
    
    #新しいリストが、前のリストと共通の要素を全く持たないとき、
    #一番最初の要素をさす。
    scr.setItems(list("abcdefg"))
    assert_equal(scr.currentItem(), "a")
    assert_equal(scr.items(), list("abcdefg"))
    assert_equal(log, ["a"], log)
    log[:] = []
    
    #重複する要素は排除
    scr.setItems(list("abcaaa"))
    assert_equal(scr.items(), list("abc"))
    
    
def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
