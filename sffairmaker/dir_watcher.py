#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker.allfiles import alldirs, allfiles

from itertools import imap
import os

class DirTreeWatcher(QFileSystemWatcher):
    def __init__(self, parent=None):
        QFileSystemWatcher.__init__(self, parent=parent)
        self.directoryChanged.connect(self.addPath)
    
    @classmethod
    def normpath(cls, path):
        path = unicode(path)
        path = os.path.abspath(path)
        path = os.path.normcase(path)
        return path
    
    def addPath(self, path):
        self.addPaths([path])
    
    def addPaths(self, paths):
        dirs = set(imap(self.normpath, paths))
        for path in paths:
            assert os.path.isdir(path), path
            
            dirs.update(imap(self.normpath, alldirs(path)))
        dirs -= set(imap(self.normpath, self.directories()))
        if dirs:
            QFileSystemWatcher.addPaths(self, list(dirs))


class ActDirWatcher(QObject):
    filesChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, dir, parent=None):
        QObject.__init__(self, parent)
        
        self._dirPath = self.normpath(dir)
        self._d = DirTreeWatcher(parent=self)
        self._d.addPath(self._dirPath)
        self._d.directoryChanged.connect(self._updateFiles)
        self._files = self._allfiles(self._dirPath)
    
    exec def_qgetter("files", "dirPath")
    
    @classmethod
    def normpath(cls, path):
        return DirTreeWatcher.normpath(path)
    
    @classmethod
    def _allfiles(cls, dir):
        return set(imap(cls.normpath, allfiles(dir, "*.act")))
        
    def _updateFiles(self, _=None):
        files = self._allfiles(self._dirPath)
        if files == self._files:
            return
        self._files = files
        self.filesChanged.emit(files)
    
    def setDirPath(self, dir):
        self._dirPath = self.normpath(dir)
        self._d.directoryChanged.disconnect(self._updateFiles)
        
        self._d = DirTreeWatcher(parent=self)
        self._d.addPath(self._dirPath)
        self._d.directoryChanged.connect(self._updateFiles)
        self._updateFiles()
    
    
def main():
    import sys
    app = QApplication(sys.argv)
    dirname = r"D:\owner\temp"
    
    w = QTextEdit()
    w.setWordWrapMode(QTextOption.NoWrap)
    def setText(files):
        w.clear()
        for f in files:
            w.append(f)
    
    w.show()
    
    d = ActDirWatcher(dirname, parent=w)
    setText(d.files())

    d.filesChanged.connect(setText)
    @d.filesChanged.connect
    def callback(files):
        print(files)
        print(d.files())
    import os
    p = os.path.join(dirname, "spam.act")
    if os.path.isfile(p):
        os.remove(p)
    with open(p, "w") as fp:
        fp.write("xyzzy")
    
    app.exec_()
    
##    print("xyzzy")
##    d.terminate()

if "__main__" == __name__:
    main()