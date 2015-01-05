#encoding:shift-jis
from __future__ import division, print_function, unicode_literals
__metaclass__ = type

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
        ValueCheckBox.__init__(self, u"軸", parent=None)
        
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
        ValueCheckBox.__init__(self, u"グリッド", parent=None)
        
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
    
    def __init__(self, title=u"最近使ったファイル(&F)", parent=None):
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
        
        a = self.addAction(u"SFF本来のパレット")
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
        a = self.addAction(u"参照")
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
        
        self._transparent = ValueCheckBox("透過表示", parent=self)
        syncAttr(self._transparent, self.xview().transparentObject(), "value")
        
        onion = OnionWidget(self)
        syncAttr(onion, self.xview().onionObject(), "value")
        
        showGrid = ShowGrid()
        showAxis = ShowAxis()
        
        self.statusBar()
        self.setupMenu()
        self.setupShortcut()
        
        #レイアウトここから
        @commandButton("showtest")
        def showtest():
            lineEdit.show()
        
        leftLayout = vBoxLayout(
            groupBox(u"倍率", self._scale),
            groupBox(u"透過表示", self._transparent),
            groupBox(u"色一覧", colorSelector),
            vGroupBox(
                u"表示", 
                showGrid,
                showAxis,
            ),
            groupBox(u"オニオン", onion),
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
        
        sffCreate = action(u'新規作成\tCtrl+N', 
            u'新しくSFFを作ります。',
            "self.xmodel().sff().create()"
        )
        sffOpen = action(u'開く\tCtrl+O', 
            u'既存のSFFを開きます。',
            "self.xmodel().sff().open()"
        )
        sffSave = action(u'上書き保存', 
            u'現在のSFFを保存します。',
            "self.xmodel().sff().save()"
        )
        sffSaveAs = action(u'名前を付けて保存', 
            u'現在のSFFを新しい名前で保存します。',
            "self.xmodel().sff().saveAs()"
        )
        sffSaveCsv = action(u"CSVに保存",
            u"SFFをExeclやメモ帳で編集できる形式で保存します。",
            "self.xmodel().sff().saveCsv()"
        )
        sffReload = action(u"再読み込み(&R)",
            u"SFFをファイルから読み直します。",
            "self.xmodel().sff().reload()"
        )
        def setReloadEnabled(filename):
            sffReload.setEnabled(filename is not None)
        
        self.xmodel().sff().filenameChanged.connect(setReloadEnabled)
        setReloadEnabled(self.xmodel().sff().filename())
        
        airCreate = action(u'新規作成(&N)', 
            u'新しくAIRを作ります。',
            "self.xmodel().air().create()"
        )
        airOpen = action(u'開く(&O)',
            u'既存のAIRを開きます。',
            "self.xmodel().air().open()"
        )
        airSave = action(u'上書き保存(&S)', 
            u'現在のAIRを保存します。',
            "self.xmodel().air().save()"
        )
        airSaveAs = action(u'名前を付けて保存(&A)', 
            u'現在のAIRを新しい名前で保存します。',
            "self.xmodel().air().saveAs()"
        )
        airReload = action(u"再読み込み(&R)",
            u"AIRをファイルから読み直します。",
            "self.xmodel().air().reload()"
        )
        self.xmodel().air().filenameChanged.connect(
            lambda p:airReload.setEnabled(p is not None))
        airReload.setEnabled(self.xmodel().air().filename() is not None)
        
        sffUndo = action(u'元に戻す(&U)', 
            u'SFFに直前に行った操作を取り消します。',
            "self.xmodel().sff().undo()"
        )
        sffRedo = action(u'繰り返し(&R)', 
            u'SFFの取り消した操作をやり直します。',
            "self.xmodel().sff().redo()"
        )
        sffSaveSpr = action(u'画像の保存', 
            u'画像をファイルに保存します。',
            "self.xview().spr().save()"
        )
        sffSaveGroup = action(u'Groupの保存', 
            u'Groupの画像をまとめてファイルに保存します。',
            "self.xview().spr().saveGroup()",
        )
        
        sffSaveSprAct = action(u"画像のパレットを保存",
            u"画像固有のパレットを、Actや画像として保存します。",
            "self.xview().spr().saveColorTable()",
        )
        sffSwapSprAct = action(u"画像のパレットを読み込み",
            u"画像のパレットを、Actファイルから読み込みます。",
            "self.xview().spr().swapColorTable()",
        )
        
        sffSaveSffAct = action(u"SFFのパレットを保存",
            u"SFF全体のパレットを、Actや画像として保存します。",
            "self.xmodel().sff().saveColorTable()",
        )
        sffSwapSffAct = action(u"SFFのパレットを読み込み",
            u"SFF全体のパレットを、Actファイルから読み込みます。",
            "self.xmodel().sff().swapColorTable()",
        )
        
        sffCrop = action(u"Crop（余白の削除）(&C)",
            u"余白部分を削り、画像を小さくします。",
            "self.xview().spr().autoCrop()"
        )
        sffCleanSpr = action(u"パレットのクリーン",
            u"SFF全体のパレットに無い色を背景色で置き換え、" \
            u"画像固有のパレットを、SFF全体のパレットで置き換えます。",
            "self.xview().spr().cleanColorTable()"
        )
        sffReplaceColorTable = action(u"パレットの置換",
            u"画像固有のパレットを、SFF全体のパレットで置き換えます。",
            "self.xview().spr().replaceColorTable()"
        )
        sffDeleteUnusedColor = action(u"未使用色の削除",
            u"画像固有のパレットから、未使用色を削除します。",
            "self.xview().spr().deleteUnusedColors()",
        )
        sffAllocBgColor = action(u"背景色の確保",
            u"使用中の色を１つずつずらし、パレットの0番に新しい色を用意します。",
            "self.xview().spr().allocBgColor()",
        )
        sffAddColorsToCommonPalette = action(u"全体パレットに画像色を追加",
            u"全体パレットに画像のパレットの色を追加し、Act適用にします。",
            "self.xview().spr().addColorsToCommonPalette()",
        )
        sffInvH = action(u"左右反転(&H)",
            u"画像を左右反転します。",
            "self.xview().spr().invertH()",
        )
        sffInvV = action(u"上下反転(&V)",
            u"画像を上下反転します。",
            "self.xview().spr().invertV()",
        )
        
        
        sffJump = action(u"指定した番号に移動(&J)\tCtrl+J",
            u"指定した番号の画像に移動します。",
            "self.xview().sff().jump()",
        )
        sffWizard = action(u"一括操作(&W)",
            u"複数の画像に対して一度に変換をします",
            "self.xmodel().sff().wizard()",
        )
        sffEditExternal = action(u"外部編集",
            u"画像を別のソフトを使って編集します。",
            "self.xview().spr().editExternal()",
        )
        
        sffNext = action(u"次の画像(&N)\tCtrl+.",
            u"次の画像。",
            "self._sff.nextItem()",
        )
        sffPrev = action(u"前の画像(&P)\tCtrl+,",
            u"前の画像。",
            "self._sff.prevItem()",
        )
        
        
        airUndo = action(u'元に戻す(&U)', 
            u'AIRに直前に行った操作を取り消します。',
            "self.xmodel().air().undo()"
        )
        airRedo = action(u'繰り返し(&R)', 
            u'AIRの取り消した操作をやり直します。',
            "self.xmodel().air().redo()"
        )
        airEditExternal = action(u'外部編集', 
            u"AIRを別のソフトを使って編集します。",
            "self.xmodel().air().editExternal()"
        )
        airSaveToGif = action(u'GIF/APNGに保存', 
            u"GIF/APNGファイルに保存します。",
            "self.xview().anim().saveToGif()"
        )
        airSaveToGifAll = action(u'全てのアニメをGIFに保存', 
            u"全てのアニメをアニメーションGIFファイルに保存します。",
            "self.xmodel().air().saveToGifAll(ext='gif')"
        )
        airSaveToApngAll = action(u'全てのアニメをAPNGに保存', 
            u"全てのアニメをアニメーションPNGファイルに保存します。",
            "self.xmodel().air().saveToGifAll(ext='apng')"
        )
        airJump = action(u"指定した番号に移動(&J)\tCtrl+J",
            u"指定した番号のアニメに移動します。",
            "self.xview().air().jump()",
        )
        airNext = action(u"次のアニメ(&N)\tCtrl+.",
            u"次のアニメ。",
            "self._air.nextItem()",
        )
        airPrev = action(u"前のアニメ(&P)\tCtrl+,",
            u"前のアニメ。",
            "self._air.prevItem()",
        )
        
        exit_ = action(u"終了(&X)", 
            "{0.name}を終了します。".format(version),
            "self.xmodel().exit()"
        )
        
        option = action(u"オプション(&O)", 
            "オプション",
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
        
        menu(self.menuBar(), u"SFFファイル(&S)", 
            sffCreate,
            sffOpen, sffSave, sffSaveAs, sffSaveCsv, 
            "-",
            sffReload,
            "-",
            sffRecent,
            "-",
            exit_
        )
        
        menu(self.menuBar(), u"SFF編集(&E)", 
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
        
        menu(self.menuBar(), u"AIRファイル(&A)", 
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
        menu(self.menuBar(), u"AIR編集(&G)",
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
        menu(self.menuBar(), u"ツール(&T)",
            option,
        )
        
        a = self.menuBar().addAction(u"軸位置を元に戻す(&R)")
        a.triggered.connect(self.xview().resetAxisDelta)
        
        self.menuBar().addMenu(DisplayActMenu(u"表示用ACT(&P)", parent=self.menuBar()))
        
        
        aboutQtVersion = action(u"Qtについて",
            u"本ソフトで使用しているQtについての情報です。",
            u"self.xview().aboutQtVersion()",
        )
        aboutVersion = action(u"SFFAIRMakerについて",
            u"バージョン情報やライセンス情報等を表示します。",
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
        self.statusBar().showMessage(u"既に最も古い状態です。")
        QApplication.beep()
    
    def cannotRedo(self):
        self.statusBar().showMessage(u"既に最も新しい状態です。")
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
                v = choiceMenu(u"追加 入替".split(), globalPos, parent=self)
                
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