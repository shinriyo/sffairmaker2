#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from nose.tools import *
from sffairmaker.model import *
from sffairmaker.model import _Model
from os.path import *
from tempfile import gettempdir
import io

from sffairmaker import null

def testCharSff():
    app = QApplication([])
    sff = Sff(None)
    sff.setIsCharSff(False)
    
    assert not sff.hasChanged() #�L����SFF�ւ̐ݒ�͉����ω������Ȃ�
    
    spr_other  = sff.sprs()[0]
    spr_0_0    = sff.newSpr(group=0, index=0, useAct=False)
    spr_9000_0 = sff.newSpr(group=9000, index=0, useAct=False)
    
    assert not spr_other.useAct()
    assert not spr_0_0.useAct()
    assert not spr_9000_0.useAct()
    
    assert not spr_other.isUseActFixed()
    assert not spr_0_0.isUseActFixed()
    assert not spr_9000_0.isUseActFixed()
    
    class Incr:
        def __init__(self):
            self.value = 0
        def __call__(self):
            self.value += 1
    
    updated_count = Incr()
    sff.updated.connect(updated_count)
    
    sff.setIsCharSff(True)
    assert updated_count.value == 1, updated_count.value
    
    assert not spr_other.useAct()
    assert spr_0_0.useAct()
    assert spr_9000_0.useAct()
    
    assert not spr_other.isUseActFixed()
    assert spr_0_0.isUseActFixed()
    assert spr_9000_0.isUseActFixed()
    
    #char�pSFF�̂Ƃ��́A(0, 0), (9000, 0)��UseAct��ύX���悤�Ƃ��Ă�����
    spr_0_0.change(useAct=False)
    assert updated_count.value == 1, updated_count.value
    assert spr_0_0.useAct()
    
    spr_9000_0.change(useAct=True)
    assert updated_count.value == 1, updated_count.value
    assert spr_9000_0.useAct()
    
    #�������A����ȊO�͕ύX�\
    spr_other.change(useAct=True)
    assert updated_count.value == 2, updated_count.value
    assert spr_other.useAct()
    
    #group, index��ύX����΁A�uUseAct�ύX�s�\�v�̌��͖͂���
    spr_9000_0.change(group=1000, index=1000)
    assert updated_count.value == 3, updated_count.value
    assert spr_9000_0.group_index() == (1000, 1000)
    assert not spr_9000_0.useAct()
    
    
def testOpenMissingFile():
    #���݂��Ȃ��t�@�C�����J�����Ƃ����Ƃ�
    
    app = QApplication([])
    class Model_(_Model):
        def __init__(self):
            _Model.__init__(self)
            self.cannotOpenFileMsgCalled = 0
            self.invalidFormatMsgCalled = 0
            self.sffOpenErrorMsgCalled = 0

        def sffOpenErrorMsg(self, *a, **kw):
            self.sffOpenErrorMsgCalled += 1
        
        def cannotOpenFileMsg(self, filename):
            self.cannotOpenFileMsgCalled += 1
        
        def invalidFormatMsg(self):
            self.invalidFormatMsgCalled += 1
        
        def addRecentAirFile(self, *a, **kw):pass
        
        def addRecentSffFile(self, *a, **kw):pass
        
        def savingProgress(self): return null.Null()
        def openingProgress(self):return null.Null()
    
    m = Model_()
    for i, name in enumerate(["air", "sff", "act"], start=1):
        x = getattr(m, name)()
        assert_equals(x._model, m)
        
        x.open(u"*���݂��Ȃ��t�@�C��*")
        assert_equal(m.cannotOpenFileMsgCalled, i, name)
        
        filename = join(gettempdir(), u"some-invalid-file")
        with open(filename, "w") as fp:
            fp.write("���������������������ӂ�������")
        
        x.open(filename) #�o�O�����t�@�C�����A�Ƃ肠�����ǂݍ���
        assert_equal(m.invalidFormatMsgCalled, 0, name)
    
    
def testAnimTextEdit():
    app = QApplication([])
    
    class TestModel(_Model):
        def __init__(self):
            _Model.__init__(self)
            self._actionParsingErrorMsg = 0
            self._actionParsingSectionNameErrorMsg = 0
            self._text = None
        
        def actionParsingErrorMsg(self, *a, **kw):
            self._actionParsingErrorMsg += 1
        
        def actionParsingSectionNameErrorMsg(self, *a, **kw):
            self._actionParsingSectionNameErrorMsg += 1
        
        def textDialog(self, text):
            if self._text is None:
                return QString(text)
            else:
                return QString(self._text)
        def savingProgress(self): return null.Null()
        def openingProgress(self):return null.Null()

    m = TestModel()
    
    a = m.air().anims()[0]
    
    #��������ꍇ
    a.textEdit()
    
    #�Z�N�V�����������������ꍇ
    m._text = """\
[begin spamegg ]
-1, -1, 0, 0, 1, , AS255D0
"""
    a.textEdit()
    assert m._actionParsingSectionNameErrorMsg == 1
    assert m._actionParsingErrorMsg == 0
    
    #�Z�N�V�������ȊO�����������ꍇ
    m._text = """\
[begin action 0]
-1, -1, *****0, 0, 1, , AS255D0
"""
    a.textEdit()
    assert m._actionParsingSectionNameErrorMsg == 1
    assert m._actionParsingErrorMsg == 1
    
    
    #�R�}����Ȏ�
    m._text = """\
[begin action 0]
"""
    elms = a.elms()
    
    a.textEdit()
    #��O�͔������Ȃ�
    assert m._actionParsingSectionNameErrorMsg == 1
    assert m._actionParsingErrorMsg == 1
    
    #�������A�����ŃR�}���}�������
    assert len(a.elms()) == 1
    assert elms != a.elms(), (elms, a.elms())


def testSaveSpr():
    app = QApplication([])
    
    class Model_(_Model):
        def askCsvSaveFormat(self, csvPath=None, sprs=[]):
            return sff_data.CsvSaveFormat("{name}\{group}_{index}", "png")
        def savingProgress(self): return null.Null()
        def openingProgress(self):return null.Null()
                
        
    m = Model_()
    m.sff().create()
    import tempfile
    from os.path import join
    
    m.sff().sprs()[0].save(join(tempfile.gettempdir(), "spam.png"))
    m.sff().sprs()[0].saveGroup(join(tempfile.gettempdir(), "spam.csv"))

def testSaveSprError():
    app = QApplication([])
    class Model_(_Model):
        def __init__(self, *a, **kw):
            _Model.__init__(self, *a, **kw)
            
            self._saveImageErrorMsg = 0
            self._saveErrorMsg = 0
            self._saveFormat = "{name}_{group}_{index}"
        
        def saveImageErrorMsg(self, *a, **kw):
            self._saveImageErrorMsg += 1
        
        def saveErrorMsg(self, *a, **kw):
            self._saveErrorMsg += 1
        
        def askCsvSaveFormat(self, csvPath=None, sprs=[]):
            return sff_data.CsvSaveFormat(self._saveFormat, "png")
        def savingProgress(self): return null.Null()
        def openingProgress(self):return null.Null()

    m = Model_()
    
    m.sff().create()
    
    #�P�̕ۑ�
    m.sff().sprs()[0].save("*some-invalid-path*")
    assert m._saveImageErrorMsg == 1
    
    #�O���[�v
    #csv�ɕۑ��ł��Ȃ�
    m.sff().sprs()[0].saveGroup("*some-invalid-path*")
    assert m._saveErrorMsg == 1
    m.sff().saveCsv("*some-invalid-path*")
    assert m._saveErrorMsg == 2
    
    #�摜��ۑ��ł��Ȃ�
    import tempfile
    from os.path import join
    import os
    
    csvPath = os.path.join(tempfile.gettempdir(), "kfm.csv")
    m.askCsvSaveFormat = lambda *a,**kw:sff_data.CsvSaveFormat("{name}\***\spam", "pcx")
    m.sff().sprs()[0].saveGroup(csvPath)
    assert m._saveImageErrorMsg == 2, m.saveImageErrorMsg
    
    m.sff().saveCsv(csvPath)
    assert m._saveImageErrorMsg == 3, m._saveImageErrorMsg
    
    #�f�B���N�g�������Ȃ�
    m.askCsvSaveFormat = lambda *a,**kw:sff_data.CsvSaveFormat("{name}\***\spam", "png")
    m.sff().sprs()[0].saveGroup(csvPath)
    assert m._saveImageErrorMsg == 4
    
    m.sff().saveCsv(csvPath)
    assert m._saveImageErrorMsg == 5
    
    
def testUsedColorIndexes():
    app = QApplication([])
    m = _Model()
    sff = m.sff()
    
    im1 = Image256(100, 1)
    for x in range(100):
        im1.setPixel(x, 0, x)
        
    im2 = Image256(100, 1)
    for x in range(100):
        im2.setPixel(x, 0, 0)
    
    spr = sff.newSpr(image=im1)
    assert set(range(100)) == spr.usedColorIndexes()
    
    spr.change(image=im2)
    assert set([0]) == spr.usedColorIndexes()
    
    
def testExternalEdit():
    app = QApplication([])
    im1 = Image256(100, 1)
    for x in range(100):
        im1.setPixel(x, 0, x)
    im2 = Image256(100, 1)
    for x in range(100):
        im2.setPixel(x, 0, 0)
    
    testAir = u"""
[begin action 666]
17,42,0,1
"""
    
    class Model_(_Model):
        def startExternalSprEditing(self, fileName):
            assert im2.save(fileName), fileName
            return True
        
        def startExternalAirEditing(self, fileName):
            with io.open(fileName, "w", encoding="ascii") as fp:
                fp.write(testAir)
                return True
        
        def waitExternalEditing(self):
            return True
        
        def savingProgress(self):
            return null.Null()
            
        def openingProgress(self):
            return null.Null()
            
        
    m = Model_()
    
    sff = m.sff()
    spr = sff.newSpr(image=im1)
    spr.editExternal()
    assert_equals(spr.image(), im2)
    
    m.air().editExternal()
    
    assert_equals(len(m.air().anims()), 1, m.air().anims())
    anim, = m.air().anims()
    assert_equals(len(anim.elms()), 1, anim.elms())
    elm, = anim.elms()
    assert_equals(
        [elm.group(), elm.index(), elm.x(), elm.y()],
        [17, 42, 0, 1]
    )
    

def main():
    nose.runmodule()
    
    
if __name__ == '__main__':
    main()
