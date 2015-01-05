#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.default_list import *

def testDefaultList():
    L = DefaultList()
    assert L[0] is None
    
    L[3] = 1
    assert L == [None, None, None, 1]
    
    del L[2]
    assert L == [None, None, 1]

    del L[4]
    assert L == [None, None, 1]

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
