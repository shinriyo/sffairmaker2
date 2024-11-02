# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type

from sffairmaker.qutil import *
from sffairmaker.radio_group import RadioGroup
from sffairmaker.const import ColorTableType
from sffairmaker.model_null import NullSpr

from sffairmaker.spr_list_view import (
    AllSprListWidget,
    SprListWidget,
    AddSprButton,
    RemoveSprButton
)
from sffairmaker.sff_jump_dialog import SprPreviewSelector
from sffairmaker.sff_edit import SprImageLabel
from sffairmaker.lineedit_with_browse import LineEditWithBrowse
from sffairmaker.clsn_text_edit import ClsnTextEdit
from sffairmaker.scale import ScaleWidget
from sffairmaker.clsn_image_view import ClsnImageView

from enum import Enum

class TaskType:
    def __init__(self):
        self._taskNames = []
    
    def register(self, taskclass):
        m = re.match("(.*)Task", taskclass.__name__)
        name = m.group(1)
        self._taskNames.append(name)
        taskclass._enum = name
        return taskclass
        
    def __call__(self, *a, **kw):
        return self.register(*a, **kw)
    
    def __getattr__(self, name):
        if name in self._taskNames:
            return name
        else:
            raise attributeError(self, name)
    
TaskType = TaskType()

class TaskBase:
    def __init__(self, widget):
##        assert isinstance(widget, self._widgetClass)
        self._widget = widget
    
    exec(def_qgetter("text", "widget"))
    def value(self):
        return self.widget().value()
    
    def enum(self):
        return self._enum


class NoSetting(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        groupBox = QGroupBox(u"�ݒ�")
        layout = QHBoxLayout()
        layout.addWidget(QLabel(u"�ݒ荀�ڂ͂���܂���"))
        groupBox.setLayout(layout)
        
        self.setLayout(hBoxLayout(
            vBoxLayout(
                groupBox,
                ("stretch", 1),
            ),
            ("stretch", 1),
        ))
    
    def value(self):
        return {}
    
@TaskType
class AutoCropTask(TaskBase):
    _text = u"�]���̍폜"
    _widgetClass = NoSetting
    
@TaskType
class AllocBgTask(TaskBase):
    _text = u"�w�i�F�̊m��"
    _widgetClass = NoSetting

class InvertSetting(QWidget):
    def __init__(self, parent=None):
        TaskBase.__init__(self, parent)
        items = [
            ((True, False), u"���E"),
            ((False, True), u"�㉺"),
            ((True, True), u"�㉺���E"),
        ]
        self._direction = RadioGroup(u"���]���������", items, parent=self)
        self.setLayout(hBoxLayout(
            self._direction
        ))
    
    def value(self):
        h, v = self._direction().value()
        return dict(h=h, v=v)
    
@TaskType
class InvertTask(TaskBase):
    _text = u"���]"
    _widgetClass = NoSetting

    

class ActFileLineEdit(LineEditWithBrowse):
    def browse(self):
        return self.xview().askActOpenPath()
    exec(def_xview())
    
    
class PaletteSetting(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._sffPalette = QRadioButton(u"Sff�S�̂̃p���b�g")
        self._sffPalette.setChecked(True)
        self._actPalette = QRadioButton(u"Act�̃p���b�g")
        self._filePalette = QRadioButton(u"�t�@�C���̃p���b�g")
        self._sprPalette = QRadioButton(u"�w�肵���摜�̃p���b�g")
        
        self._filePath = ActFileLineEdit(self)
        self._filePalette.toggled.connect(self._filePath.setEnabled)
        self._filePath.setEnabled(self._filePalette.isChecked())
        self._filePath.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self._spr = SprPreviewSelector(self)
        self._sprPalette.toggled.connect(self._spr.setEnabled)
        self._spr.setEnabled(self._sprPalette.isChecked())
        self._spr.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self._sffPalette)
        layout.addWidget(self._actPalette)
        layout.addWidget(self._filePalette)
        layout.addWidget(self._filePath, 0)
        layout.addWidget(self._sprPalette)
        layout.addWidget(self._spr, 0, Qt.AlignRight)
        
        self.setLayout(vBoxLayout(
            groupBox(u"�g�p����p���b�g", layout),
            ("stretch", 1)
        ))
    
    exec(def_sff())
    
    def value(self):
        if self._sffPalette.isChecked():
            t = (ColorTableType.Sff,)
        elif self._actPalette.isChecked():
            t = (ColorTableType.Act,)
        elif self._sprPalette.isChecked():
            t = (ColorTableType.Spr, self._spr.spr())
        elif self._filePalette.isChecked():
            t = (ColorTableType.File, self._filePath.text())
        else:
            assert False
        return {"colorTableType":t}
        
        
@TaskType
class CleanColorTableTask(TaskBase):
    _text = u"�p���b�g�̃N���[��"
    _widgetClass = PaletteSetting

@TaskType
class ReplaceColorTableTask(TaskBase):
    _text = u"�p���b�g�̒u��"
    _widgetClass = PaletteSetting

##@TaskType
##class UnifyColorTableTask(PaletteTaskBase):
##    _text = u"�p���b�g�̓���"

class RectsSetting(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self._clsnEdit = ClsnTextEdit(parent=self)
        self._imageView = ClsnImageView(self)
        self._scale = ScaleWidget(self)
        
        syncAttrTo(self._imageView, self._scale, "scale")
        syncAttrTo(self._imageView, self.parent(), "spr")
        syncAttrTo(self._imageView, self.xview(), 
            "actColorTable",
            "sprDisplayMode",
        )
        syncAttr(self._imageView, self._clsnEdit, ("clsn", "value"))
        @createAction(self._imageView, "Ctrl+9")
        def resetAxisDelta():
            self._imageView.resetAxisDelta()

        @createAction(self._imageView, "Ctrl+0")
        def resetAxisDelta():
            self._scale.zoomReset()
        
        @createAction(self._imageView, "Ctrl+;")
        def zoomIn():
            self._scale.zoomIn()
        
        @createAction(self._imageView, "Ctrl+-")
        def zoomOut():
            self._scale.zoomOut()
        
        def wheelEvent(event):
            if event.orientation() != Qt.Vertical:
                return
            if event.delta() < 0:
                self._scale.zoomOut()
            elif event.delta() > 0:
                self._scale.zoomIn()
        
        self._imageView.wheelEvent = wheelEvent
        
        resetAxisDelta = QAction(self._imageView)
        resetAxisDelta.setShortcut("Ctrl+0")
        resetAxisDelta.triggered.connect(self._imageView.resetAxisDelta)
        self._imageView.addActions([resetAxisDelta])
        
        self.setLayout(hBoxLayout(
            hGroupBox(
                u"��������",
                vBoxLayout(
                    hBoxLayout(
                        vGroupBox(u"�{��", self._scale),
                        ("stretch", 1),
                    ),
                    (self._clsnEdit, 1), 
                ),
                (self._imageView, 1),
            ),
        ))
    
    exec(def_delegate("parent()", "xview"))
    def value(self):
        return {"rects":self._clsnEdit.value()}
    
@TaskType
class EraseRectsTask(TaskBase):
    _text = u"����"
    _widgetClass = RectsSetting

@TaskType
class EraseRectsColorsTask(TaskBase):
    _text = u"�F�̏���"
    _widgetClass = RectsSetting

##@TaskType
##class CropRectTask(TaskBase):
##    _text = u"�؂蔲��"
##    _widgetClass = RectsSetting


class SffWizard(QDialog):
    sprChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"�ꊇ����")
        
        self._spr = NullSpr()
        self._lastSprs = []
        
        self._allSprList = AllSprListWidget(self)
        self._sprList = SprListWidget(self)
        add    = AddSprButton(self._sprList, self._allSprList)
        remove = RemoveSprButton(self._sprList)
        
        @commandButton(u"�S�Ēǉ�")
        def all():
            self._sprList.addSprs(self._allSprList.sprs())
        
        @commandButton(u"�O��Ɠ���")
        def sameAsLast():
            self._sprList.clear()
            self._sprList.addSprs(spr for spr in self._lastSprs if spr.isValid())
        
        image = SprImageLabel()
        
        syncAttrTo(image, self, "spr")
        
        for L in [self._allSprList, self._sprList]:
            L.currentSprChanged.connect(self.setSpr)
            f = lambda index, L=L:self.setSpr(L.spr(index))
            L.clicked.connect(f)
            L.entered.connect(f)
            L.activated.connect(f)
        
        self._taskCombo = QComboBox(self)
        self._taskStack = QStackedLayout()
        self._tasks = []
        
        taskClasses = [
            EraseRectsTask,
            EraseRectsColorsTask,
##            CropRectTask,
            AutoCropTask,
            InvertTask,
            CleanColorTableTask,
            ReplaceColorTableTask,
            AllocBgTask,
        ]
        settingWidgets = {}
        for taskClass in taskClasses:
            if taskClass._widgetClass not in settingWidgets:
                widget = taskClass._widgetClass(self)
                settingWidgets[taskClass._widgetClass] = widget
                self._taskStack.addWidget(widget)
            
            task = taskClass(settingWidgets[taskClass._widgetClass])
            self._tasks.append(task)
            self._taskCombo.addItem(task.text())
        
        def setCurrentWidget(i):
            self._taskStack.setCurrentWidget(self._tasks[i].widget())
        self._taskCombo.currentIndexChanged.connect(setCurrentWidget)
        setCurrentWidget(self._taskCombo.currentIndex())
        
        leftLayout = hBoxLayout(
            groupBox("all", self._allSprList),
            vBoxLayout(
                add,
                remove,
                all,
                sameAsLast,
                ("stretch", 1),
                image,
            ),
            groupBox("selected", self._sprList),
        )
        self._taskCombo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        rightLayout = vBoxLayout(
            self._taskCombo,
            self._taskStack,
        )
        self.setLayout(vBoxLayout(
            hBoxLayout(
                leftLayout,
                (rightLayout, 1),
            ),
            dialogButtons(self)
        ))
    
    exec(def_xview())
    
    exec(def_qgetter("spr"))
    @mySetter(emit=True)
    def setSpr(self):
        pass
    
    exec(def_delegate("_sprList", "sprs", "setSprs"))
    def value(self):
        i = self._taskCombo.currentIndex()
        task = self._tasks[i]
        return task.enum(), self.sprs(), task.value()
    
    def saveLastSprs(self):
        self._lastSprs = self.sprs()
    
    @classmethod
    def get(cls, parent=None):
        ins = cls(parent=parent)
        return ins.ask()
    
    def ask(self):
        if not self.exec_():
            return None
        else:
            if self.sprs():
                self.saveLastSprs()
                return self.value()
            else:
                return None

def main():
    app = QApplication([])
    from sffairmaker.model import Model
    xmodel = Model()
    xmodel.sff().open(debugDataDir() + "\\kfm.sff")
    
    print(SffWizard.get())
    
##    xmodel.sff().Wizard()
##    app.exec_()
    
if "__main__" == __name__:
    main()