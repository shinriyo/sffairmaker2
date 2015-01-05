#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 

from os.path import abspath, normpath, join
from operator import methodcaller
from collections import defaultdict

from sffairmaker.qutil import *
from sffairmaker import const
from sffairmaker.sff_data import CsvSaveFormat
from itertools import product

ExtValues = ["png", "bmp", "pcx"]

class ImagePathPreview(QTextEdit):
    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)
        self.setLineWrapMode(self.NoWrap)
        self.setReadOnly(True)
        
        self._isValid = True
        self._csvPath = ""
        self._sprs = []
        self._format = CsvSaveFormat("", "")
        self._updatePreview()
    
    exec def_qgetter("isValid")
    
    def setCsvPath(self, csvPath):
        csvPath = normpath(abspath(csvPath))
        if self._csvPath == csvPath:
            return
        self._csvPath = csvPath
        self._updatePreview()
    
    def setSprs(self, sprs):
        self._sprs = sorted(sprs, key=methodcaller("group_index"))
        self._updatePreview()
        
    def setFormat(self, format):
        self._format = format
        self._updatePreview()
    
    def _findDuplicate(self, imageNames):
        d = defaultdict(list)
        for name, s in imageNames:
            d[name].append(s.group_index())
        dups = [(name, sprs) for name, sprs in d.items() if len(sprs) >= 2]
        if dups:
            return dups[0]
        else:
            return None
        
    def _updatePreview(self):
        self.clear()
        try:
            imageNames = []
            for spr in self._sprs:
                if not spr.isValid():continue
                name = self._format.imageBasename(self._csvPath, spr)
                imageNames.append((name, spr))
        except StandardError as e:
            self._isValid = False
            self.setHtml("<font color='red'>" + 
                e.__class__.__name__ + ":" + str(e) + 
                "</font>")
            return
        
        #重複の検出
        dup = self._findDuplicate(imageNames)
        if dup is not None:
            self._isValid = False
            name, sprs = dup
            self.setHtml("<font color='red'>" + 
                u"重複: " + "".join(str(s) for s in sprs) + 
                "->" + name +
                "</font>")
        else:
            self._isValid = True
            self.setText("\n".join(name for name, spr in imageNames))
        
        

class CsvSaveFormatDialog(QDialog):
    formatChanged = pyqtSignal(CsvSaveFormat)
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"画像の形式")
        
        self._name = QComboBox()
        self._name.setAutoCompletion(True)
        self._name.setEditable(True)
        self._name.setInsertPolicy(QComboBox.NoInsert)
        self._name.setEditText("{name}_{group}_{index}")
        
        self._ext = QComboBox()
        self._ext.addItems(ExtValues)
        self._ext.setCurrentIndex(0)
        
        self._buttons = dialogButtons(self)
        
        self._preview = ImagePathPreview(self)
        def setPreviewFormat(*_a, **_kw):
            self._preview.setFormat(CsvSaveFormat(self.name(), self.ext()))
            self._buttons.okButton().setEnabled(self._preview.isValid())
            
        self._name.editTextChanged.connect(setPreviewFormat)
        self._ext.editTextChanged.connect(setPreviewFormat)
        setPreviewFormat()
        
        #レイアウトここから
        self.setLayout(vBoxLayout(
            hBoxLayout(
                (self._name, 1),
                self._ext
            ),
            (groupBox(u"プレビュー", self._preview), 1),
            self._buttons,
        ))
        self.setMinimumWidth(300)
    
    def setCsvPath(self, csvPath):
        self._preview.setCsvPath(csvPath)
        self._buttons.okButton().setEnabled(self._preview.isValid())
        
    def setSprs(self, sprs):
        self._preview.setSprs(sprs)
        self._buttons.okButton().setEnabled(self._preview.isValid())
        
    def name(self):
        return unicode(self._name.currentText())
    
    def setName(self, s):
        self._name.setEditText(s)
    
    def ext(self):
        return unicode(self._ext.currentText())
    
    def setExt(self, s):
        s = unicode(s)
        if s in ExtValues:
            i = ExtValues.index(s)
        else:
            i = 0
        self._ext.setCurrentIndex(i)
    
    def names(self):
        return [unicode(self._name.itemText(i))
                for i in xrange(self._name.count())]
    
    def setNames(self, names):
        self._name.clear()
        for s in names:
            self._name.addItem(s)
    
    def format(self):
        return CsvSaveFormat(self.name(), self.ext())
    
    def ask(self):
        if self.exec_():
            return self.format()
        else:
            return None
    
    
def main():
    pass

if "__main__" == __name__:
    main()