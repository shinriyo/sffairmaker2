# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type

import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sffairmaker.qutil import *
from sffairmaker import (
    version,
    const,
    model,
)

from sffairmaker.csv_save_format import CsvSaveFormatDialog
from sffairmaker.main_window import MainWindow
from sffairmaker.add_sprs_dialog import AddSprsDialog
from sffairmaker.colors import ColorsHolder, ColorIndexes
from sffairmaker.text_dialog import TextDialog

from sffairmaker.scale import ScaleObject
from sffairmaker.onion import Onion
from sffairmaker.elm_insert_pos_dialog import ElmInsertPosDialog
from sffairmaker.message import Message

from sffairmaker.settings import Settings
from sffairmaker import spr_display
from sffairmaker.select_dialog import SelectDialog
from sffairmaker.sff_wizard import SffWizard
from sffairmaker import option_window

from sffairmaker.error_dialog import ErrorDialog

class MyProgressDialog(QDialog):
    def __init__(self, text, parent=None):
        flags = Qt.WindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        QDialog.__init__(self, flags=flags, parent=parent)
        self.setWindowTitle(text)
        
        self._bar = QProgressBar(parent=self)
        self._bar.setRange(0, 0)
        self._text = QLabel(text, parent=self)
        
        self._bar.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )
        
        L = QVBoxLayout()
        L.addWidget(self._text, 1, Qt.AlignCenter)
        L.addWidget(self._bar)
        
        self.setLayout(L)
        self.resize(200, 100)
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, *a, **kw):
        self.hide()
        self.close()
        return False
        


class Dialog:
    def __init__(self, parent=None):
        self._csvSaveFormatDialog = CsvSaveFormatDialog()
        self._csvSaveFormatDialog.setExt(str(self.settings().value("CsvSaveFormatExt")))
        self._csvFormats = RecentCsvFormats()
        def setNames(formats):
            self._csvSaveFormatDialog.setNames(formats)
        setNames(self._csvFormats.formats())
        self._csvFormats.formatsChanged.connect(setNames)
        
        self._sffWizard = None
        
    def xmodel(self):
        return model.Model()
    
    def askSffSavePath(self):
        return str(QFileDialog.getSaveFileName(
            directory=self.xmodel().sff().dir(),
            filter=const.SffOpenFilter,
        ))
    
    def askSprSavePath(self):
        return str(QFileDialog.getSaveFileName(
            filter=const.PictureFilter,
        ))
    
    def askSprAddPaths(self):
        r = QFileDialog.getOpenFileNames(
            filter=const.PictureFilter,
        )
        return [str(s) for s in r]
    
    def askSprSwapPath(self):
        return str(QFileDialog.getOpenFileName(
            filter=const.PictureFilter,
        ))
    
    def askAirSavePath(self):
        return str(QFileDialog.getSaveFileName(
            directory=self.xmodel().air().dir(),
            filter=const.AirSaveFilter
        ))
    
    def askCsvSavePath(self):
        return str(QFileDialog.getSaveFileName(
            directory=self.xmodel().sff().dir(),
            filter=const.CsvSaveFilter,
        ))
    
    def askCsvSaveFormat(self, csvPath, sprs):
        self._csvSaveFormatDialog.setSprs(sprs)
        self._csvSaveFormatDialog.setCsvPath(csvPath)
        return self._csvSaveFormatDialog.ask()
        
    def askSffOpenPath(self):
        return str(QFileDialog.getOpenFileName(
            directory=self.xmodel().sff().dir(),
            filter=const.SffOpenFilter,
        ))
    
    def askAirOpenPath(self):
        return str(QFileDialog.getOpenFileName(
            directory=self.xmodel().air().dir(),
            filter=const.AirOpenFilter
        ))
    
    def askSaveBefore(self, name):
        ret = QMessageBox.question(
                  self.mainWindow(),
                  version.name,
                  name + u"�̕ύX��ۑ����܂����H",
                  QMessageBox.Save | QMessageBox.Discard
                                   | QMessageBox.Cancel,
                  QMessageBox.Save)
        return {
            QMessageBox.Save:"yes",
            QMessageBox.Discard:"no",
            QMessageBox.Cancel:"cancel"
        }[ret]
        
        
    def askSaveSffBefore(self):
        return self.askSaveBefore("Sff")
    
    def askSaveAirBefore(self):
        return self.askSaveBefore("Air")
    
    def askActOpenPath(self):
        return str(QFileDialog.getOpenFileName(
            directory=self.xmodel().sff().dir(),
            filter=const.ActOpenFilter
        ))
    
    def askActSavePath(self):
        return str(QFileDialog.getSaveFileName(
            directory=self.xmodel().sff().dir(),
            filter=const.ActSaveFilter
        ))
    
    def askGifSavePath(self):
        return str(QFileDialog.getSaveFileName(
            directory=self.xmodel().sff().dir(),
            filter=const.GifSaveFilter
        ))
    
    def askGifSaveDirPath(self):
        return str(QFileDialog.getExistingDirectory(
            directory=self.xmodel().air().dir(),
        ))
        
    def createAddSprsDialog(self):
        d = AddSprsDialog()
        self.colorsChanged.connect(d.setColors)
        return d
    
    def askAddSprs(self, image):
        if not hasattr(self, "_addSprsDialog"):
            self._addSprsDialog = self.createAddSprsDialog()
        self._addSprsDialog.setImage(image)
        return self._addSprsDialog.ask()
    
    def askElmInsertPos(self, *a, **kw):
        return ElmInsertPosDialog.get(*a, **kw) 
    
    def textDialog(self, text):
        return TextDialog.get(text)
    
    def askReloadModifiedSff(self):
        return self.askReloadModified("sff")
    
    def askReloadModifiedAir(self):
        return self.askReloadModified("air")
    
    def addRecentCsvFormat(self, fmt):
        self._csvFormats.add(fmt.nameFormat())
    
    def addRecentGifFormat(self, format):
        self._gifFormats.add(format)
    
    def sffWizard(self):
        if self._sffWizard is None:
            self._sffWizard = SffWizard()
        return self._sffWizard.ask()
    
    def showOpeningErrors(self, errors):
        lines = []
        for e in errors:
            if isinstance(e, const.OpeningSffErrorInfo):
                msg = u"{0.number}番目の画像({0.group}, {0.index})を読み込めませんでした。"\
                        .format(e)
            elif isinstance(e, const.OpeningCsvErrorInfo):
                if const.OpeningCsvErrorType.Image == e.type:
                    msg = u"{0.lineno}行目の画像{0.path}を読み込めませんでした。" \
                            .format(e)
                else:
                    name = {
                        const.OpeningCsvErrorType.Group:u"グループ",
                        const.OpeningCsvErrorType.Index:u"番号",
                        const.OpeningCsvErrorType.X:u"X座標",
                        const.OpeningCsvErrorType.Y:u"Y座標",
                        const.OpeningCsvErrorType.UseAct:u"Act適用",
                    }[e.type]
                    msg = u"{0.lineno}行目の{1}を読み込めませんでした。"\
                            .format(e, name)
            else:
                msg = str(e)
            lines.append(msg)
            
        ErrorDialog.showMessage(
            "\n".join(lines),
            parent=self._mainWindow
        )
    
    def _selectPath(self, caption, paths):
        paths = list(paths)
        index = SelectDialog.get(caption, paths)
        if index is None:
            return None
        else:
            return paths[index]
    
    def selectSffPath(self, paths):
        return self._selectPath(u"Sffを開く", paths)
    
    def selectAirPath(self, paths):
        return self._selectPath(u"AIRを開く", paths)
    
    def progress(self, text):
        return MyProgressDialog(text, parent=self._mainWindow)
    
    def openingProgress(self):
        text = u"開いています"
        return self.progress(text)
    
    def savingProgress(self):
        text = u"保存しています"
        return self.progress(text)
    
    def waitExternalEditing(self):
        QMessageBox.information(
            None, 
            u"外部編集",
            u"編集が終わったらOKを押してください",
        )
        return True
    
    def askExternalEditPath(self):
        path = str(QFileDialog.getOpenFileName(
            filter=const.ExecutableFilter,
        ))
        if not path:
            return path
        else:
            return os.path.abspath(path)
    
    def askBgImagePath(self):
        path = str(QFileDialog.getOpenFileName(
            filter=const.PictureFilter,
        ))
        if not path:
            return path
        else:
            return os.path.abspath(path)
    
    
class Holder(QObject):
    valueChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, v):
        QObject.__init__(self)
        self._value = v
    exec(def_qgetter("value"))
    
    @emitSetter
    def setValue(self):
        pass


class RecentStrings(QObject):
    stringsChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        
        # 設定値を取得
        v = Settings().value(self._keys())
        
        # vがNoneの場合をチェック
        if v is None:
            self._strings = list(self._default())  # デフォルト値を使用
        else:
            self._strings = [str(i.toString()) for i in v.toList()]  # toList()を使用
        
        # もし_stringsが空ならデフォルトを再度使用
        if not self._strings:
            self._strings = list(self._default())
    
    def add(self, s):
        strings = self.strings()
        s = self._normalize(s)
        if not s:
            return
        if s in strings:
            strings.remove(s)
        strings.insert(0, s)
        self.setStrings(strings)
        
    def strings(self):
        return list(self._strings)
        
    def setStrings(self, strings):
        strings = strings[:self._maxCount()]
        if self._strings == strings:
            return
        self._strings = strings
        
        self.settings().setValue(self._keys(), self.strings())
        self.stringsChanged.emit(self.strings())
    
    def _normalize(self, s):
        return s

    def _keys(self):
        raise NotImplementedError
    
    def _maxCount(self):
        raise NotImplementedError
    
    def settings(self):
        return getattr(self.parent(), "settings", Settings)()
        

class RecentCsvFormats(RecentStrings):
    exec(def_alias("formats", "strings"))
    exec(def_alias("formatsChanged", "stringsChanged"))
    
    def _keys(self):
        return "RecentCsvFormats"
    
    def _maxCount(self):
        return const.MaxCsvNameFormat
    
    def _default(self):
        return const.DefaultCsvNameFormats

class RecentFiles(RecentStrings):
    def __init__(self, name, parent=None):
        self._name = name
        RecentStrings.__init__(self, parent)
    
    exec(def_alias("files", "strings"))
    exec(def_alias("filesChanged", "stringsChanged"))
    
    def _keys(self):
        return "RecentFiles/" + self._name
    
    def _normalize(self, filename):
        return os.path.abspath(filename)
    
    def _maxCount(self):
        return const.MaxRecentFiles
    
    def _default(self):
        return []


class SettingColorsHolder(ColorsHolder):
    def __init__(self, parent=None):
        ColorsHolder.__init__(self, parent)
        
        if self.settings().contains("ColorList"):
            variant = self.settings().value("ColorList")
            colorList = [QColor(v) for v in variant.toList()]
            self.setColorList(colorList)
        
        if self.settings().contains("ColorIndexes"):
            v = self.settings().value("ColorIndexes")
            try:
                indexes = ColorIndexes.fromVariant(v)
            except ValueError:
                pass
            else:
                self.setColorIndexes(indexes)
        
        self.colorListChanged.connect(partial(self.settings().setValue, "ColorList"))
        self.colorIndexesChanged.connect(
            lambda indexes:self.settings().setValue("ColorIndexes", indexes.toVariant()))
    
    def settings(self):
        return getattr(self.parent(), "settings", Settings)()


class BgImageHolder(QObject):
    filenameChanged = pyqtSignal("QString")
    imageChanged = pyqtSignal("QImage")
    
    exec(def_qgetter("filename"))
    
    Key = "BgImageFilename"
    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        
        # 設定値を取得
        v = self.settings().value(self.Key)

        # vがNoneの場合をチェック
        if v is None:
            self._image = QImage()  # デフォルトのQImageを設定
            self._filename = ""  # デフォルトのファイル名を設定
        elif v.isValid():
            self._filename = str(v.toString())
            self._image = QImage(self._filename)
        else:
            self._image = QImage()  # 何かの理由でisValidがFalseの場合
            self._filename = ""
    
    def settings(self):
        return getattr(self.parent(), "settings", Settings)()
    
    def setFilename(self, filename):
        if self._filename != filename:
            self._filename = filename
            im = QImage(filename)
            self._image = im
            self.filenameChanged.emit(filename)
            self.imageChanged.emit(im)
            self.settings().setValue(self.Key, QString(self._filename))
    
    def image(self):
        return QImage(self._image)
    
    

class _View(QObject, Dialog, Message):
    _instance = None
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        QDialog.__init__(self)  # QDialogの初期化
        
        self._mainWindow = None
        self._optionWindow = None
        
        self._colorsHolder = SettingColorsHolder(parent=self)
        self._scaleObject = ScaleObject()
        
        opt = const.GridOption(const.ImageZOrder.Middle, True, True)
        self.setupHolder("gridOption", opt)
        self.setupHolder("axisDelta", QPoint(0, 0))
        self.setupHolder("onion", Onion(0))
        self.setupHolder("transparent", True)
        self.setupHolder("sprDisplayMode", spr_display.Mode.Act)
        
        self._bgImage = BgImageHolder()
        self.setupHolder("bgImageDelta", QPoint(0, 0))
        self.setupHolder("bgImageTile", False)
        
        BgImageDelta = "BgImageDelta"
        BgImageTile = "BgImageTile"
        
        # QSettingsからの値取得時にNoneチェック
        bg_image_delta_value = self.settings().value(BgImageDelta)
        bg_image_tile_value = self.settings().value(BgImageTile)
        
        self.setBgImageDelta(bg_image_delta_value.toPoint() if bg_image_delta_value is not None else QPoint(0, 0))
        self.setBgImageTile(bool(bg_image_tile_value) if bg_image_tile_value is not None else False)
        
        self.bgImageDeltaChanged.connect(
            lambda v: self.settings().setValue(BgImageDelta, QPoint(v)))
        self.bgImageTileChanged.connect(
            lambda v: self.settings().setValue(BgImageTile, bool(v)))
        
        self._recentSff = RecentFiles("Sff")
        self._recentAir = RecentFiles("Air")

    def settings(self):
        return QSettings()  # 適切なQSettingsインスタンスを返すように実装

    
    def sff(self):
        return self.mainWindow().sff()
    
    def air(self):
        return self.mainWindow().sff()
    
    exec(def_delegate("_recentSff", 
        ("recentSffFilesChanged", "filesChanged"),
        ("recentSffFiles", "files"),
        ("addRecentSffFile", "add"),
    ))
    exec(def_delegate("_recentAir", 
        ("recentAirFilesChanged", "filesChanged"),
        ("recentAirFiles", "files"),
        ("addRecentAirFile", "add"),
    ))
    exec(def_delegate("_bgImage",
        ("bgImage", "image"),
        ("bgImageChanged", "imageChanged"),
        ("bgImageFilename", "filename"),
        ("setBgImageFilename", "setFilename"),
        ("bgImageFilenameChanged", "filenameChanged"),
    ))
    
    exec(def_delegate("_colorsHolder", *"""
        colorsChanged
        colorIndexesChanged
        colorListChanged
        
        colors
        colorList
        colorIndexes
        
        setColorIndexes
        setColorList
        """.split()))
    
    exec(def_delegate("_scaleObject", 
        "scale",
        "scaleChanged",
        "setScale",
        ("scaleIndex", "index"),
        ("setScaleIndex", "setIndex"),
        ("scaleIndexChanged", "indexChanged"),
        ("scaleZoomIn", "zoomIn"),
        ("scaleZoomOut", "zoomOut"),
        ("scaleZoomReset", "zoomReset"),
    ))
    exec(def_qgetter("scaleObject"))
    
    exec(def_delegate("mainWindow().statusBar()",
        ("statusBarShowMessage", "showMessage"),
        ("statusBarCurrentMessage", "currentMessage"),
        ("statusBarClearMessage", "clearMessage"),
    ))
    
    exec(def_xmodel())
    exec(def_delegate("xmodel()",
        "actColorTable",
        "actColorTableChanged"
    ))
    
    
    def setupHolder(self, name, defaultValue):
        h = Holder(defaultValue)
        setattr(self, "_" + name + "Object", h)
        setattr(self, name + "Object", lambda :h)
        
        setter = "set" + name[0].upper() + name[1:]
        signal = name + "Changed"
        
        setattr(self, name, h.value)
        setattr(self, setter, h.setValue)
        setattr(self, signal, h.valueChanged)
    
    def resetAxisDelta(self):
        self.setAxisDelta(QPoint(0, 0))
    
    exec(def_qgetter("mainWindow"))
    
    def showMainWindow(self):
        if self._mainWindow is None:
            self._mainWindow = MainWindow(self)
        self._mainWindow.show()
    
    def showOptionWindow(self):
        if self._optionWindow is None:
            self._optionWindow = option_window.OptionWindow(settings=self.settings())
        self._optionWindow.show()
    
    def __getattr__(self, name):
        return getattr(self._mainWindow, name)
    
    def settings(self):
        return Settings()

def View():
    return _View.instance()
    
def main():
    app = QApplication([])
    app.exec_()
    
    
if __name__ == "__main__":
    main()