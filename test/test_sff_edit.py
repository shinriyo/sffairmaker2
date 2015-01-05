#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.sff_edit import *
from sffairmaker import model

def testUseActEdit():
    app = QApplication([])
    m = model._Model()
    m.sff().create()
    m.sff().setIsCharSff(False)
    spr = m.sff().newSpr(group=9000, index=0, useAct=False)
    
    class TestSprUseActEdit(SprUseActEdit):
        def xmodel(self):return m
    
    useAct = TestSprUseActEdit()
    useAct.setSpr(spr)
    
    assert not useAct.value()
    assert useAct.isEnabled()
    
    m.sff().setIsCharSff(True)
    assert useAct.value()
    assert not useAct.isEnabled()
    
    m.sff().setIsCharSff(False)
    assert not useAct.value()
    assert useAct.isEnabled()
    
    spr.change(useAct=True)
    assert useAct.value()
    assert useAct.isEnabled()


def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
