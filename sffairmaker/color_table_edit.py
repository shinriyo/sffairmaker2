# coding: utf-8
from __future__ import division, print_function

from image_op import ipixelIndex
__metaclass__ = type 
from sffairmaker.qutil import *

from sffairmaker import (
    image_op,
    model,
    color_slider,
)

from sffairmaker.image_op import (
    Image256,
    Format_Indexed8,
)
from sffairmaker.radio_group import RadioGroup
from sffairmaker.choice_menu import choiceMenu
from sffairmaker.default_list import DefaultList

from collections import namedtuple
from itertools import product, izip_longest
import operator

from collections import OrderedDict
from enum import Enum


PaletteItemMimeType = 'application/x-sffairmaker-paletteitems'




def colorTableEqual(table1, table2):
    if len(table1) == len(table2):
        return table1 == table2
    
    if len(table1) < len(table2):
        short = table1
        long  = table2
    else:
        short = table2
        long  = table1
    
    return short == long[:len(short)] and \
           all([(qRed(i), qGreen(i), qBlue(i)) == (0, 0, 0) for i in long[len(short):]])

def pixelIndexEqual(im1, im2):
    return all(starmap(operator.eq, zip(ipixelIndex(im1), ipixelIndex(im2))))


def imageEqual(im1, im2):
    if im1.format() == Format_Invalid:
        return False
    if im2.format() == Format_Invalid:
        return False
    
    assert im1.format() == Format_Indexed8
    assert im2.format() == Format_Indexed8
    
    return im1.size() == im2.size() and \
           colorTableEqual(im1.colorTable(), im2.colorTable()) and \
           pixelIndexEqual(im1, im2)

    
class ColorTable(DefaultList):
    def __init__(self, alist):
        DefaultList.__init__(self, alist, qRgb(0, 0, 0))
    
    
ColorRole = Qt.UserRole
DisplayColorRole = Qt.UserRole + 1
UsedRole =  Qt.UserRole + 2
class ColorTableModelBase(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._preview = None
        self._colorTable = ColorTable([])
        self._usedColorNumbers = set()
        
        def resetPreview(*a, **kw):
            self._preview = None
        self.dataChanged.connect(resetPreview)
        self.modelReset.connect(resetPreview)
    
    def setColorTable(self, colorTable):
        changed_indexes = []
        append = changed_indexes.append 
        for i, (v0, v1) in enumerate(izip_longest(self._colorTable, colorTable)):
            if v0 != v1:
                append(i)
        
        if changed_indexes:
            self._colorTable = ColorTable(colorTable)
            for index in map(self.numberToIndex, changed_indexes):
                self.dataChanged.emit(index, index)
            return True
        else:
            return False
        
    def colorTable(self):
        return list(self._colorTable)
    
    def colorTable_(self):
        return ColorTable(self._colorTable)
    
    def usedColorNumbers(self):
        return set(self._usedColorNumbers)
    
    def setUsedColorNumbers(self, usedColorNumbers):
        usedColorNumbers = set(usedColorNumbers)
        if self._usedColorNumbers == usedColorNumbers:
            return
        
        changed_indexes = self._usedColorNumbers.symmetric_difference(usedColorNumbers)
        self._usedColorNumbers = usedColorNumbers
        for index in map(self.numberToIndex, changed_indexes):
            self.dataChanged.emit(index, index)
    
    def setColor(self, qindex, color):
        colorTable = self.colorTable_()
        colorTable[self.indexToNumber(qindex)] = color.rgb()
        self.setColorTable(colorTable)
        
    def indexToNumber(self, modelIndex):
        return modelIndex.row() * 16 + modelIndex.column()
    
    def numberToIndex(self, number):
        return self.createIndex(number // 16, number % 16)
    
    def clearPreview(self):
        self._preview = None
        self.emitAllDataChanged()
        
    def emitAllDataChanged(self):
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(15, 15))
        
    def previewMoveRgb(self, targetNumber, startNumber, rgbMap):
        self._preview = ColorTable(
            image_op.moveRgb(self.colorTable(), targetNumber, startNumber, rgbMap))
        self.emitAllDataChanged()
    
    def previewCopyRgb(self, targetNumber, startNumber, rgbMap):
        self._preview = ColorTable(
            image_op.copyRgb(self.colorTable(), targetNumber, startNumber, rgbMap))
        self.emitAllDataChanged()
    
    def previewSwapRgb(self, targetNumber, startNumber, rgbMap):
        self._preview = ColorTable(
            image_op.swapRgb(self.colorTable(), targetNumber, startNumber, rgbMap))
        self.emitAllDataChanged()
    
    previewSwapImageColor = previewSwapRgb
    
    def moveRgb(self, targetNumber, startNumber, rgbMap):
        colorTable = image_op.moveRgb(self.colorTable(), targetNumber, startNumber, rgbMap)
        self.setColorTable(colorTable)
    
    def copyRgb(self, targetNumber, startNumber, rgbMap):
        colorTable = image_op.copyRgb(self.colorTable(), targetNumber, startNumber, rgbMap)
        self.setColorTable(colorTable)
    
    def swapRgb(self, targetNumber, startNumber, rgbMap):
        colorTable = image_op.swapRgb(self.colorTable(), targetNumber, startNumber, rgbMap)
        self.setColorTable(colorTable)
    
    def swapImageColor(self, targetNumber, startNumber, rgbMap):
        raise NotImplementedError
    
    def deleteColors(self, indexes):
        raise NotImplementedError

    #��������AQAbstractTableModel�̎�������K�v������virtual���\�b�h
    def rowCount(self, parent=None):
        return 16
    
    def columnCount(self, parent=None):
        return 16
    
    def data(self, index, role):
        if not index.isValid():
            return None
        
        i = index.column() + index.row() * 16
        if role in [ColorRole, DisplayColorRole]:
            if role == DisplayColorRole:
                if self._preview is None:
                    colorTable = self._colorTable
                else:
                    colorTable = self._preview
            else:
                colorTable = self._colorTable
            
            assert isinstance(colorTable, ColorTable), (self, type(colorTable))
            return QColor.fromRgb(colorTable[i])
        elif role == UsedRole:
            return i in self.usedColorNumbers()
        else:
            return None
        
    
    def headerData(self, section, orientation, role):
        if role == Qt.SizeHintRole:
            return QSize(1, 1)
        return None
    

class SprColorTableModel(ColorTableModelBase):
    def __init__(self, parent=None, xmodel=None):
        ColorTableModelBase.__init__(self, parent)
        self._spr = model.Spr.Null()
        
        if xmodel is None:
            import sffairmaker.model
            self._xmodel = sffairmaker.model.Model()
        else:
            self._xmodel = xmodel
        
        def setValue():
            if not self._spr.isValid():
                return
            self.setColorTable(self.spr().colorTable())
            self.setUsedColorNumbers(self.spr().usedColorIndexes())
        self.xmodel().sff().updated.connect(setValue)
        setValue()
    
    exec def_qgetter("spr", "xmodel")
    
    def setSpr(self, spr):
        if self.spr() == spr:
            return
        self._spr = spr
        self.setColorTable(self._spr.colorTable())
        self.setUsedColorNumbers(self._spr.usedColorIndexes())
    
    def setColorTable(self, *a, **kw):
        r = ColorTableModelBase.setColorTable(self, *a, **kw)
        if r and self.spr().isValid():
            self.spr().setColorTable(self.colorTable())
    
    def deleteColors(self, indexes):
        self.spr().deleteColors(indexes)
    
    def swapImageColor(self, targetNumber, startNumber, rgbMap):
        if not self.spr().isValid():
            return
        
        image = image_op.swapImageColor(
            self.spr().image(), 
            targetNumber,
            startNumber,
            rgbMap
        )
        
        assert image is not self.spr().image()
##        assert image != self.spr().image()
        self.spr().change(image=image)


class CommonColorTableModel(ColorTableModelBase):
    def __init__(self, parent=None, xmodel=None):
        ColorTableModelBase.__init__(self, parent)
        if xmodel is None:
            import sffairmaker.model
            self._xmodel = sffairmaker.model.Model()
        else:
            self._xmodel = xmodel
        
        def setValue():
            self.setColorTable(self.sff().colorTable())
            self.setUsedColorNumbers(self.sff().usedColorIndexes())
        self.sff().updated.connect(setValue)
        setValue()
        
    exec def_qgetter("xmodel")
    
    def sff(self):
        return self.xmodel().sff()
    
    def setColorTable(self, *a, **kw):
        r = ColorTableModelBase.setColorTable(self, *a, **kw)
        if r:
            self.xmodel().sff().setColorTable(self.colorTable())
        
    def deleteColors(self, indexes):
        self.sff().deleteColors(indexes)
    
class ColorDelegate(QAbstractItemDelegate):
    def __init__(self, cellSize=10, view=None):
        QAbstractItemDelegate.__init__(self, view)
        self._cellSize = cellSize
        self._view = view
    
    def paint(self, painter, option, index):
        color = index.model().data(index, DisplayColorRole)
        used  = index.model().data(index, UsedRole)
        selected = option.state & QStyle.State_Selected
        current  = self._view.currentIndex() == index
        
        with savePainter(painter):
            painter.fillRect(option.rect, color)
            
            rc = QRect(option.rect)
            rc.setSize(rc.size() - QSize(1, 1))
            
            if not used:
                painter.setPen(Qt.black)
                painter.drawLine(
                    rc.left(),
                    rc.top() + 1,
                    rc.right(),
                    rc.bottom() + 1
                )
            
            if selected:
                pen = QPen(Qt.black)
                if current:
                    pen.setStyle(Qt.SolidLine)
                else:
                    pen.setStyle(Qt.DotLine)
                painter.setPen(pen)
                painter.drawRect(QRect(
                    rc.topLeft() + QPoint(1, 1),
                    rc.bottomRight()
                ))
            
            if not used:
                painter.setPen(Qt.white)
                painter.drawLine(
                    rc.left(),
                    rc.top(), 
                    rc.right(),
                    rc.bottom()
                )
            
            if selected:
                pen = QPen(Qt.white)
                if current:
                    pen.setStyle(Qt.SolidLine)
                else:
                    pen.setStyle(Qt.DotLine)
                painter.setPen(pen)
                painter.drawRect(QRect(
                    rc.topLeft(),
                    rc.bottomRight() - QPoint(1, 1)
                ))
            
            
    def sizeHint(self, option, index):
        return QSize(self._cellSize, self._cellSize)


class ColorTableView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        
        self.setSelectionBehavior(QTableView.SelectItems)
        
        self.horizontalHeader().setMinimumSectionSize(1)
        self.verticalHeader().setMinimumSectionSize(1)


ColorTableDragMode = Enum("Move", "Copy", "Swap", "SwapImageColor")

class ColorTableEditBase(ColorTableView):
    dragModeChanged = pyqtSignal("PyQt_PyObject")
    currentColorChanged = pyqtSignal("PyQt_PyObject")
    currentNumberChanged = pyqtSignal(int)
    
    _Model = None
    _CellSize = 10
    def __init__(self, parent=None, xmodel=None):
        ColorTableView.__init__(self, parent)
        self.setModel(self._Model(self, xmodel=xmodel))
        self.setItemDelegate(ColorDelegate(self._CellSize, self))
        
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setCurrentIndex(self.index(0, 0))
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        w = sum(self.sizeHintForRow(r) for r in xrange(self.model().rowCount()))
        h = sum(self.sizeHintForColumn(r) for r in xrange(self.model().columnCount()))
        self.setFixedSize(w+4, h+4)
        
        self.setShowGrid(True)
        self.setAcceptDrops(True)
        
        self._dragMode = ColorTableDragMode.Copy
        
        def emitColorChanged(curr, prev):
            c = self.model().data(curr, ColorRole)
            self.currentColorChanged.emit(c)
        self.selectionModel().currentChanged.connect(emitColorChanged)
        
        
        def emitColorChanged(topLeft, bottomRight):
            if topLeft <= self.currentIndex() <= bottomRight:
                c = self.model().data(self.currentIndex(), ColorRole)
                self.currentColorChanged.emit(c)
        self.model().dataChanged.connect(emitColorChanged)
        
        def emitCurrentNumberChanged(curr, prev):
            self.currentNumberChanged.emit(self.indexToNumber(curr))
        self.selectionModel().currentChanged.connect(emitCurrentNumberChanged)
        
    exec def_qgetter("dragMode")
    
    @emitSetter
    def setDragMode(self):
        pass
    
    def posToNumber(self, pos):
        return self.indexToNumber(self.indexAt(pos))
        
    def deleteSelectedColors(self):
        self.deleteColors(self.selectedNumbers())
    
    def selectedNumbers(self):
        return [self.indexToNumber(index)
                    for index in self.selectedIndexes()]
    
    def startDrag(self, pos):
        startNumber = self.posToNumber(pos)
        
        selected = self.selectedNumbers()
        if startNumber not in selected:
            return
        
        colorTable = self.model().colorTable_()
        rgbMap = dict((i, colorTable[i]) for i in selected)
        
        x = (id(self), startNumber, rgbMap)
        
        mimeData = QMimeData()
        mimeData.setData(PaletteItemMimeType, QByteArray(repr(x)))
        
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.start(Qt.MoveAction)
    
    def popupMenu(self, pos):
        globalPos = self.mapToGlobal(pos)
        
        actions = [
            (u"�I��F�̍폜", self.deleteSelectedColors)
        ]
        
        v = choiceMenu([t for t, _ in actions], globalPos, parent=self)
        if v is None: return
        
        assert 0 <= v < len(actions)
        actions[v][1]()
    
    def mousePressEvent(self, event):
        ColorTableView.mousePressEvent(self, event)
        if event.button() == Qt.LeftButton:
            self.startDrag(event.pos())
        elif event.button() == Qt.RightButton:
            self.popupMenu(event.pos())
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(PaletteItemMimeType):
            event.accept()
        else:
            event.ignore()
            return
        
        targetNumber = self.posToNumber(event.pos())
        if targetNumber is None:
            return
        data = event.mimeData().data(PaletteItemMimeType)
        
        xid, startNumber, rgbMap = eval(bytes(data))
        if xid != id(self):
            self.previewCopyRgb(targetNumber, startNumber, rgbMap)
        else:
            m = {
                ColorTableDragMode.Move: self.previewMoveRgb,
                ColorTableDragMode.Copy: self.previewCopyRgb,
                ColorTableDragMode.Swap: self.previewSwapRgb,
                ColorTableDragMode.SwapImageColor: self.previewSwapImageColor,
            }
            m[self.dragMode()](targetNumber, startNumber, rgbMap)
    dragMoveEvent = dragEnterEvent
    
    def dragLeaveEvent(self, event):
        self.clearPreview()
    
    def dropEvent(self, event):
        if event.mimeData().hasFormat(PaletteItemMimeType):
            event.accept()
        else:
            event.ignore()
            return
        
        targetNumber = self.posToNumber(event.pos())
        if targetNumber is None:
            return
        data = event.mimeData().data(PaletteItemMimeType)
        
        xid, startNumber, rgbMap = eval(bytes(data))
        if xid != id(self):
            self.copyRgb(targetNumber, startNumber, rgbMap)
        else:
            m = {
                ColorTableDragMode.Move: self.moveRgb,
                ColorTableDragMode.Copy: self.copyRgb,
                ColorTableDragMode.Swap: self.swapRgb,
                ColorTableDragMode.SwapImageColor: self.swapImageColor,
            }
            m[self.dragMode()](targetNumber, startNumber, rgbMap)
    
    def setCurrentColor(self, color):
        self.setColor(self.currentIndex(), color)
    
    def currentColor(self):
        qindex = self.currentIndex()
        return self.model().data(qindex, ColorRole)
    
    def currentNumber(self):
        return self.indexToNumber(self.currentIndex())
    
    def setCurrentNumber(self, number):
        index = self.numberToIndex(number)
        
        with blockSignals(self):
            self.selectionModel().clear()
        self.setCurrentIndex(index)
        
    def __getattr__(self, name):
        return getattr(self.model(), name)
    
    
class SprColorTableEdit(ColorTableEditBase):
    _Model = SprColorTableModel

class CommonColorTableEdit(ColorTableEditBase):
    _Model = CommonColorTableModel


class ColorTableDragModeRadio(RadioGroup):
    def __init__(self, title=u"�h���b�O���̑���", *a, **kw):
        items = [
            (ColorTableDragMode.Move, u"�ړ�"),
            (ColorTableDragMode.Copy, u"�R�s�["),
            (ColorTableDragMode.Swap, u"����"),
            (ColorTableDragMode.SwapImageColor, u"�F�ʒu�̓���"),
        ]
        RadioGroup.__init__(self, title, items, *a, **kw)
    
    def connectEdits(self, *edits):
        for w in edits:
            self.valueChanged.connect(w.setDragMode)
            w.setDragMode(self.value())


class ColorSlider(color_slider.ColorSlider):
    def __init__(self, colorTableEdit, parent=None):
        color_slider.ColorSlider.__init__(self, parent)
        
        self.setValue(colorTableEdit.currentColor())
        self.valueChanged.connect(colorTableEdit.setCurrentColor)
        colorTableEdit.currentColorChanged.connect(self.setValue)
        
        self.setCurrentNumber(colorTableEdit.currentNumber())
        colorTableEdit.currentNumberChanged.connect(self.setCurrentNumber)


def main():
    from sffairmaker.radio_group import RadioGroup
    from sffairmaker.color_slider import ColorSlider
    from os.path import join
    app = QApplication([])
    
    m = model.Model()
    m.sff().open(join(debugDataDir(), "kfm.sff"))
##        image = image_op.Image256(128, 1)
##        for x in xrange(128):
##            image.setPixel(x, 0, x)
##        colorTable = []
##        for i in xrange(256):
##            colorTable.append(qRgb(i, i, i))
##        image.setColorTable(colorTable)
    
##        spr = m.sff().newSpr(image=image)
    spr = m.sff().sprs()[0]
    table = SprColorTableEdit()
    table.setSpr(spr)
    
    slider = ColorSlider()
    slider.setValue(table.currentColor())
    slider.valueChanged.connect(table.setCurrentColor)
    table.currentColorChanged.connect(slider.setValue)
    
    ctable = CommonColorTableEdit()
    cslider = ColorSlider()
    cslider.setValue(ctable.currentColor())
    cslider.valueChanged.connect(ctable.setCurrentColor)
    ctable.currentColorChanged.connect(cslider.setValue)
    
    w = QWidget()
    w.setLayout(hBoxLayout(
        vBoxLayout(
            (table, 1),
            slider,
        ),
        vBoxLayout(
            (ctable, 1),
            cslider,
        ),
    ))
    w.show()
    
    app.exec_()


if "__main__" == __name__:
    main()