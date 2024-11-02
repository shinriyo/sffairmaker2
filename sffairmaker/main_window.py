# coding: utf-8
from __future__ import division, print_function, unicode_literals
__metaclass__ = type

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sffairmaker import (
    version,
    const,
    model,
)

from sffairmaker.qutil import *
from sffairmaker.colors import ColorsSelector
from sffairmaker.sff_tab import SffTab
from sffairmaker.air_tab import AirTab
from sffairmaker.act_tab import ActTab

from sffairmaker.scale import ScaleWidget
from sffairmaker.dir_watcher import ActDirWatcher
from sffairmaker.choice_menu import choiceMenu
from sffairmaker.radio_group import RadioGroup
from sffairmaker.onion import OnionWidget

from sffairmaker.sort_path import key_path

import string
import re


class ShowAxis(ValueCheckBox):
    def __init__(self, parent=None):
        ValueCheckBox.__init__(self, u"��", parent=None)
        
        @self.valueChanged.connect
        def setView(v):
            self.xview().setGridOption(
                self.xview().gridOption()._replace(axis=v))
        
        self.xview().gridOptionChanged.connect(
            lambda opt:self.setValue(opt.axis))
        
        self.setValue(self.xview().gridOption().axis)

    def xview(self):
        import sffairmaker.view
        return sffairmaker.view.View()


class ShowGrid(ValueCheckBox):
    def __init__(self, parent=None):
        ValueCheckBox.__init__(self, u"�O���b�h", parent=None)
        
        @self.valueChanged.connect
        def setView(v):
            self.xview().setGridOption(
                self.xview().gridOption()._replace(grid=v))
        
        self.xview().gridOptionChanged.connect(
            lambda opt:self.setValue(opt.grid))
        
        self.setValue(self.xview().gridOption().grid)
    
    def xview(self):
        import sffairmaker.view
        return sffairmaker.view.View()


class RecentFileMenu(QMenu):
    pathSelected = pyqtSignal("PyQt_PyObject")
    actions_alt_char = True
    
    def __init__(self, title=u"�ŋߎg�����t�@�C��(&F)", parent=None):
        QMenu.__init__(self, parent)
        self._files = []
        self._actions = []
        self.setTitle(title)
    
    def setFiles(self, files):
        from os.path import normpath, abspath
        files = [normpath(abspath(unicode(f))) for f in files]
        if self._files == files:
            return
        
        self._files = files
        
        self._actions = self._actions[:len(self._files)]
        for i in xrange(len(self._files) - len(self._actions)):
            a = self.addAction("")
            a.triggered.connect(self._onActionTriggered)
            self._actions.append(a)
        
        assert len(self._actions) == len(self._files)
        
        for i, (a, f) in enumerate(zip(self._actions, self._files)):
            if i < 10:
                a.setText("(&{0}) {1}".format(i, f))
            else:
                a.setText(f)
            a.setData(f)
        
    def _onActionTriggered(self, _):
        a = self.sender()
        if a:
            path = unicode(a.data().toString())
            self.pathSelected.emit(path)
    

class DisplayActMenu(QMenu):
    def __init__(self, title, parent=None):
        QMenu.__init__(self, parent)
        self.setTitle(title)
        
        self._watcher = ActDirWatcher(self.xmodel().sff().dir(), parent=self)
        self.updateDisplayActMenu(self._watcher.files())
        
        self.xmodel().sff().dirChanged.connect(self._watcher.setDirPath)
        self._watcher.filesChanged.connect(self.updateDisplayActMenu)
    
    def updateDisplayActMenu(self, files):
        from os.path import join, relpath, abspath
        self.clear()
        
        a = self.addAction(u"SFF�{���̃p���b�g")
        a.triggered.connect(lambda :self.xmodel().sff().palette().display())
        
        self.addSeparator()
        
        root = self.xmodel().sff().dir()
        
        files = list(files)
        files.sort(key=key_path)
        for f in files[:const.MaxDisplayActMenuLength]:
            text = relpath(f, root)
            a = self.addAction(text)
            a.triggered.connect(lambda _, f=f:self.xmodel().act().open(f))
        
        self.addSeparator()
        a = self.addAction(u"�Q��")
        a.triggered.connect(lambda :self.xmodel().act().open())
    
    def xmodel(self):
        return model.Model()
    

def allocate_char_to_menus(menu):
    chars = set(string.ascii_uppercase)
    
    pat = r"(?P<text>[^\t]*?)(\(&(?P<char>[A-Z])\))?(\t(?P<shortcut>.*))?$"
    actions = [a for a in menu.actions() if not a.isSeparator()]
    
    for a in actions:
        m = re.match(pat, unicode(a.text()))
        assert m
        if m.group("char"):
            chars.remove(m.group("char"))
    
    for a in actions:
        m = re.match(pat, unicode(a.text()))
        if not m.group("char"):
            c = sorted(chars)[0]
            chars.remove(c)
            
            t = "{0}(&{1})".format(m.group("text"), c)
            if m.group("shortcut"):
                t += "\t" + m.group("shortcut")
            a.setText(t)
    
    submenus = [a.menu() for a in menu.actions()
        if a.menu() and not getattr(a.menu(), "actions_alt_char", False)]
    
    for m in submenus:
        allocate_char_to_menus(m)
    
    
class MainWindow(QMainWindow):
    def __init__(self, view):
        QMainWindow.__init__(self)
        
        self._view = view
        self._tab = QTabWidget(self)
        self._tabTitles = {}
        
        self._sff = SffTab(self)
        self._air = AirTab(self)
        
        for i, t in enumerate([self._sff, self._air]):
            self._tab.addTab(t, t.label())
            t.labelChanged.connect(partial(self._tab.setTabText, i))
            def setTabTitle(title, i=i):
                self._tabTitles[i] = title
                if i == self._tab.currentIndex():
                    self.setWindowTitle(title)
            t.titleChanged.connect(setTabTitle)
            setTabTitle(t.title())
        
        self._tab.currentChanged.connect(lambda i:self.setWindowTitle(self._tabTitles[i]))
        
        colorSelector = ColorsSelector(self)
        syncAttr(colorSelector, self._view, "colorIndexes", "colorList")
        
        self._scale = ScaleWidget(self)
        syncAttr(self._scale, self.xview().scaleObject(),
            "index", "maximum", "minimum")
        
        self._transparent = ValueCheckBox("���ߕ\��", parent=self)
        syncAttr(self._transparent, self.xview().transparentObject(), "value")
        
        onion = OnionWidget(self)
        syncAttr(onion, self.xview().onionObject(), "value")
        
        showGrid = ShowGrid()
        showAxis = ShowAxis()
        
        self.statusBar()
        self.setupMenu()
        self.setupShortcut()
        
        #���C�A�E�g��������
        @commandButton("showtest")
        def showtest():
            lineEdit.show()
        
        leftLayout = vBoxLayout(
            groupBox(u"�{��", self._scale),
            groupBox(u"���ߕ\��", self._transparent),
            groupBox(u"�F�ꗗ", colorSelector),
            vGroupBox(
                u"�\��", 
                showGrid,
                showAxis,
            ),
            groupBox(u"�I�j�I��", onion),
            ("stretch", 1),
        )
        w = QWidget()
        w.setLayout(vBoxLayout(
            hBoxLayout(
                leftLayout,
                (self._tab, 1)
            ),
        ))
        self.setCentralWidget(w)
        
        
    exec def_qgetter("sff", "air")
    
    exec def_delegate("_sff", 
        "spr", "setSpr")
    
    exec def_delegate("_air", 
        "anim", "setAnim", "elm", "setElm")

    def _tabs(self):
        for i in xrange(self.count()):
            yield self._tab.widget(i)
    
    def currentTab(self):
        return ["sff", "air"][self._tab.currentIndex()]
    
    def setCurrentTab(self, key):
        i = {"sff":0, "air":1}[key]
        self._tab.setCurrentIndex(i)
        
    def closeEvent(self, event):
        if self.xmodel().closing():
            event.accept()
        else:
            event.ignore()
            self.xmodel().exit()
    
    def setupMenu(self):
        def action(text, statusTip, callback):
            a = QAction(text, self)
            a.setStatusTip(statusTip)
            if isinstance(callback, basestring):
                callback = eval("lambda self=self:" + callback)
            a.triggered.connect(lambda _:callback())
            return a
        
        sffCreate = action(u'�V�K�쐬\tCtrl+N', 
            u'�V����SFF�����܂��B',
            "self.xmodel().sff().create()"
        )
        sffOpen = action(u'�J��\tCtrl+O', 
            u'������SFF���J���܂��B',
            "self.xmodel().sff().open()"
        )
        sffSave = action(u'�㏑���ۑ�', 
            u'���݂�SFF��ۑ����܂��B',
            "self.xmodel().sff().save()"
        )
        sffSaveAs = action(u'���O��t���ĕۑ�', 
            u'���݂�SFF��V�������O�ŕۑ����܂��B',
            "self.xmodel().sff().saveAs()"
        )
        sffSaveCsv = action(u"CSV�ɕۑ�",
            u"SFF��Execl�⃁�����ŕҏW�ł���`���ŕۑ����܂��B",
            "self.xmodel().sff().saveCsv()"
        )
        sffReload = action(u"�ēǂݍ���(&R)",
            u"SFF���t�@�C������ǂݒ����܂��B",
            "self.xmodel().sff().reload()"
        )
        def setReloadEnabled(filename):
            sffReload.setEnabled(filename is not None)
        
        self.xmodel().sff().filenameChanged.connect(setReloadEnabled)
        setReloadEnabled(self.xmodel().sff().filename())
        
        airCreate = action(u'�V�K�쐬(&N)', 
            u'�V����AIR�����܂��B',
            "self.xmodel().air().create()"
        )
        airOpen = action(u'�J��(&O)',
            u'������AIR���J���܂��B',
            "self.xmodel().air().open()"
        )
        airSave = action(u'�㏑���ۑ�(&S)', 
            u'���݂�AIR��ۑ����܂��B',
            "self.xmodel().air().save()"
        )
        airSaveAs = action(u'���O��t���ĕۑ�(&A)', 
            u'���݂�AIR��V�������O�ŕۑ����܂��B',
            "self.xmodel().air().saveAs()"
        )
        airReload = action(u"�ēǂݍ���(&R)",
            u"AIR���t�@�C������ǂݒ����܂��B",
            "self.xmodel().air().reload()"
        )
        self.xmodel().air().filenameChanged.connect(
            lambda p:airReload.setEnabled(p is not None))
        airReload.setEnabled(self.xmodel().air().filename() is not None)
        
        sffUndo = action(u'���ɖ߂�(&U)', 
            u'SFF�ɒ��O�ɍs����������������܂��B',
            "self.xmodel().sff().undo()"
        )
        sffRedo = action(u'�J��Ԃ�(&R)', 
            u'SFF�̎��������������蒼���܂��B',
            "self.xmodel().sff().redo()"
        )
        sffSaveSpr = action(u'�摜�̕ۑ�', 
            u'�摜���t�@�C���ɕۑ����܂��B',
            "self.xview().spr().save()"
        )
        sffSaveGroup = action(u'Group�̕ۑ�', 
            u'Group�̉摜���܂Ƃ߂ăt�@�C���ɕۑ����܂��B',
            "self.xview().spr().saveGroup()",
        )
        
        sffSaveSprAct = action(u"�摜�̃p���b�g��ۑ�",
            u"�摜�ŗL�̃p���b�g���AAct��摜�Ƃ��ĕۑ����܂��B",
            "self.xview().spr().saveColorTable()",
        )
        sffSwapSprAct = action(u"�摜�̃p���b�g��ǂݍ���",
            u"�摜�̃p���b�g���AAct�t�@�C������ǂݍ��݂܂��B",
            "self.xview().spr().swapColorTable()",
        )
        
        sffSaveSffAct = action(u"SFF�̃p���b�g��ۑ�",
            u"SFF�S�̂̃p���b�g���AAct��摜�Ƃ��ĕۑ����܂��B",
            "self.xmodel().sff().saveColorTable()",
        )
        sffSwapSffAct = action(u"SFF�̃p���b�g��ǂݍ���",
            u"SFF�S�̂̃p���b�g���AAct�t�@�C������ǂݍ��݂܂��B",
            "self.xmodel().sff().swapColorTable()",
        )
        
        sffCrop = action(u"Crop�i�]���̍폜�j(&C)",
            u"�]�����������A�摜�����������܂��B",
            "self.xview().spr().autoCrop()"
        )
        sffCleanSpr = action(u"�p���b�g�̃N���[��",
            u"SFF�S�̂̃p���b�g�ɖ����F��w�i�F�Œu�������A" \
            u"�摜�ŗL�̃p���b�g���ASFF�S�̂̃p���b�g�Œu�������܂��B",
            "self.xview().spr().cleanColorTable()"
        )
        sffReplaceColorTable = action(u"�p���b�g�̒u��",
            u"�摜�ŗL�̃p���b�g���ASFF�S�̂̃p���b�g�Œu�������܂��B",
            "self.xview().spr().replaceColorTable()"
        )
        sffDeleteUnusedColor = action(u"���g�p�F�̍폜",
            u"�摜�ŗL�̃p���b�g����A���g�p�F���폜���܂��B",
            "self.xview().spr().deleteUnusedColors()",
        )
        sffAllocBgColor = action(u"�w�i�F�̊m��",
            u"�g�p���̐F���P�����炵�A�p���b�g��0�ԂɐV�����F��p�ӂ��܂��B",
            "self.xview().spr().allocBgColor()",
        )
        sffAddColorsToCommonPalette = action(u"�S�̃p���b�g�ɉ摜�F��ǉ�",
            u"�S�̃p���b�g�ɉ摜�̃p���b�g�̐F��ǉ����AAct�K�p�ɂ��܂��B",
            "self.xview().spr().addColorsToCommonPalette()",
        )
        sffInvH = action(u"���E���](&H)",
            u"�摜�����E���]���܂��B",
            "self.xview().spr().invertH()",
        )
        sffInvV = action(u"�㉺���](&V)",
            u"�摜���㉺���]���܂��B",
            "self.xview().spr().invertV()",
        )
        
        
        sffJump = action(u"�w�肵���ԍ��Ɉړ�(&J)\tCtrl+J",
            u"�w�肵���ԍ��̉摜�Ɉړ����܂��B",
            "self.xview().sff().jump()",
        )
        sffWizard = action(u"�ꊇ����(&W)",
            u"�����̉摜�ɑ΂��Ĉ�x�ɕϊ������܂�",
            "self.xmodel().sff().wizard()",
        )
        sffEditExternal = action(u"�O���ҏW",
            u"�摜��ʂ̃\�t�g���g���ĕҏW���܂��B",
            "self.xview().spr().editExternal()",
        )
        
        sffNext = action(u"���̉摜(&N)\tCtrl+.",
            u"���̉摜�B",
            "self._sff.nextItem()",
        )
        sffPrev = action(u"�O�̉摜(&P)\tCtrl+,",
            u"�O�̉摜�B",
            "self._sff.prevItem()",
        )
        
        
        airUndo = action(u'���ɖ߂�(&U)', 
            u'AIR�ɒ��O�ɍs����������������܂��B',
            "self.xmodel().air().undo()"
        )
        airRedo = action(u'�J��Ԃ�(&R)', 
            u'AIR�̎��������������蒼���܂��B',
            "self.xmodel().air().redo()"
        )
        airEditExternal = action(u'�O���ҏW', 
            u"AIR��ʂ̃\�t�g���g���ĕҏW���܂��B",
            "self.xmodel().air().editExternal()"
        )
        airSaveToGif = action(u'GIF/APNG�ɕۑ�', 
            u"GIF/APNG�t�@�C���ɕۑ����܂��B",
            "self.xview().anim().saveToGif()"
        )
        airSaveToGifAll = action(u'�S�ẴA�j����GIF�ɕۑ�', 
            u"�S�ẴA�j�����A�j���[�V����GIF�t�@�C���ɕۑ����܂��B",
            "self.xmodel().air().saveToGifAll(ext='gif')"
        )
        airSaveToApngAll = action(u'�S�ẴA�j����APNG�ɕۑ�', 
            u"�S�ẴA�j�����A�j���[�V����PNG�t�@�C���ɕۑ����܂��B",
            "self.xmodel().air().saveToGifAll(ext='apng')"
        )
        airJump = action(u"�w�肵���ԍ��Ɉړ�(&J)\tCtrl+J",
            u"�w�肵���ԍ��̃A�j���Ɉړ����܂��B",
            "self.xview().air().jump()",
        )
        airNext = action(u"���̃A�j��(&N)\tCtrl+.",
            u"���̃A�j���B",
            "self._air.nextItem()",
        )
        airPrev = action(u"�O�̃A�j��(&P)\tCtrl+,",
            u"�O�̃A�j���B",
            "self._air.prevItem()",
        )
        
        exit_ = action(u"�I��(&X)", 
            "{0.name}���I�����܂��B".format(version),
            "self.xmodel().exit()"
        )
        
        option = action(u"�I�v�V����(&O)", 
            "�I�v�V����",
            "self.xview().showOptionWindow()"
        )
        
        sffRecent = RecentFileMenu(parent=self.menuBar())
        sffRecent.setFiles(self.xview().recentSffFiles())
        self.xview().recentSffFilesChanged.connect(sffRecent.setFiles)
        sffRecent.pathSelected.connect(self.xmodel().sff().open)
        
        airRecent = RecentFileMenu(parent=self.menuBar())
        airRecent.setFiles(self.xview().recentAirFiles())
        self.xview().recentAirFilesChanged.connect(airRecent.setFiles)
        airRecent.pathSelected.connect(self.xmodel().air().open)
        
        def menu(m, name, *items):
            menu = m.addMenu(name)
            for a in items:
                if a == "-":
                    menu.addSeparator()
                elif isinstance(a, QMenu):
                    menu.addMenu(a)
                else:
                    menu.addAction(a)
            allocate_char_to_menus(menu)
            return menu
        
        menu(self.menuBar(), u"SFF�t�@�C��(&S)", 
            sffCreate,
            sffOpen, sffSave, sffSaveAs, sffSaveCsv, 
            "-",
            sffReload,
            "-",
            sffRecent,
            "-",
            exit_
        )
        
        menu(self.menuBar(), u"SFF�ҏW(&E)", 
            sffUndo, sffRedo,
            "-",
            sffSaveSpr, sffSaveGroup,
            "-",
            sffSaveSprAct, sffSwapSprAct,
            sffSaveSffAct, sffSwapSffAct,
            sffEditExternal,
            "-",
            sffCrop, sffInvH, sffInvV,
            "-",
            sffCleanSpr, sffReplaceColorTable,
            sffDeleteUnusedColor, sffAllocBgColor,
            sffAddColorsToCommonPalette,
            "-",
            sffWizard,
            "-",
            sffPrev,
            sffNext,
            sffJump,
        )
        
        menu(self.menuBar(), u"AIR�t�@�C��(&A)", 
            airCreate, airOpen, airSave, airSaveAs,
            "-", 
            airReload,
            "-",
            airSaveToGifAll,
            "-",
            airRecent,
            "-", 
            exit_
        )
        menu(self.menuBar(), u"AIR�ҏW(&G)",
            airUndo, airRedo,
            "-",
            airEditExternal,
            "-",
            airSaveToGif,
            airSaveToGifAll,
            airSaveToApngAll,
            "-",
            airPrev,
            airNext,
            airJump,
        )
        menu(self.menuBar(), u"�c�[��(&T)",
            option,
        )
        
        a = self.menuBar().addAction(u"���ʒu�����ɖ߂�(&R)")
        a.triggered.connect(self.xview().resetAxisDelta)
        
        self.menuBar().addMenu(DisplayActMenu(u"�\���pACT(&P)", parent=self.menuBar()))
        
        
        aboutQtVersion = action(u"Qt�ɂ���",
            u"�{�\�t�g�Ŏg�p���Ă���Qt�ɂ��Ă̏��ł��B",
            u"self.xview().aboutQtVersion()",
        )
        aboutVersion = action(u"SFFAIRMaker�ɂ���",
            u"�o�[�W�������⃉�C�Z���X��񓙂�\�����܂��B",
            u"self.xview().aboutVersion()",
        )
        
        menu(self.menuBar(), u"Help(&H)",
            aboutVersion,
            aboutQtVersion,
        )
                
    def setupShortcut(self):
        def action(name, shortcut):
            a = QAction(self)
            a.setShortcut(shortcut)
            
            assert hasattr(self.xmodel().sff(), name)
            assert hasattr(self.xmodel().air(), name)
            
            @a.triggered.connect
            def callback(_):
                key = self.currentTab()
                submodel = getattr(self.xmodel(), key)()
                getattr(submodel, name)()
            self.addAction(a)
        
        action("open", "Ctrl+O")
        action("save", "Ctrl+S")
        action("saveAs", "Ctrl+Shift+S")
        action("undo", "Ctrl+Z")
        action("redo", "Ctrl+Shift+Z")
        action("redo", "Ctrl+Y")
        
        def tabaction(name, shortcut):
            a = QAction(self)
            a.setShortcut(shortcut)
            @a.triggered.connect
            def callback(_):
                getattr(self._tab.currentWidget(), name)()
            self.addAction(a)
        
        tabaction("nextItem", "Ctrl+.")
        tabaction("prevItem", "Ctrl+,")
        
        @createAction(self, "Ctrl+9")
        def resetAxisDelta():
            self.xview().resetAxisDelta()
    
        @createAction(self, "Ctrl+0")
        def resetAxisDelta():
            self.xview().scaleZoomReset()
        
        @createAction(self, "Ctrl+;")
        def zoomIn():
            self.xview().scaleZoomIn()
        
        @createAction(self, "Ctrl+-")
        def zoomOut():
            self.xview().scaleZoomOut()
    
    def memento(self, *a):
        return {}
    
    def restore(self, m, *a):
        pass
    
    def xmodel(self):
        return model.Model()
    
    def xview(self):
        return self._view
    
    def cannotUndo(self):
        self.statusBar().showMessage(u"���ɍł��Â���Ԃł��B")
        QApplication.beep()
    
    def cannotRedo(self):
        self.statusBar().showMessage(u"���ɍł��V������Ԃł��B")
        QApplication.beep()
    
    def dragEnterEvent(self, evt):
        from os.path import splitext
        if evt.mimeData().hasUrls():
            files = [unicode(u.toLocalFile()) for u in evt.mimeData().urls()]
            if all(files):
                evt.accept()
                return
        evt.ignore()
    
    dragMoveEvent = dragEnterEvent
    
    def dropEvent(self, evt):
        if not evt.mimeData().hasUrls(): return
        
        from os.path import splitext, isfile
        files = [unicode(u.toLocalFile()) for u in evt.mimeData().urls()]
        
        if len(files) != 1:
            self.xmodel().loadFiles(files)
        else:
            f = files[0]
            _, ext = splitext(f)
            ext = ext.lower()
            if ext not in const.NonPictureExts and isfile(f):
                globalPos = self.mapToGlobal(evt.pos())
                v = choiceMenu(u"�ǉ� ����".split(), globalPos, parent=self)
                
                if v == 0:
                    self.xmodel().sff().addSprs(files)
                elif v == 1:
                    self.spr().swap(files[0])
            else:
                self.xmodel().loadFiles(files)
                
def main():
    pass
    
if __name__ == "__main__":
    main()