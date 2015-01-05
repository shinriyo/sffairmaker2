#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.colors import *

from nose.tools import  *

def testColorIndexes():
    c0 = ColorIndexes(0,1,2,3)
    v = c0.toVariant()
    c1 = ColorIndexes.fromVariant(v)
    
    eq_(c0, c1)
    assert_raises(ValueError, ColorIndexes.fromVariant, QVariant(""))
    assert_raises(ValueError, ColorIndexes.fromVariant, QVariant("aaa"))
    


def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
