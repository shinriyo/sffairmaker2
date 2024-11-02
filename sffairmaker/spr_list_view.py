# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *
from sffairmaker import model

from bisect import bisect_right
from operator import methodcaller
from iterutils import unique_everseen

class SprListModelBase(QAbstractListModel):
    SprRole = Qt.UserRole
    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self._sortingEnabled  = True
        self._key = methodcaller("group_index")
        self._sprs = []
        self.reset()
        self.sff().updated.connect(self.reset)
    
    exec def_qgetter("sortingEnabled")
    def setSortingEnabled(self, v):
        self._sortingEnabled = v
        if self._sortingEnabled:
            self.sort()
    
    def sff(self):
        return self.xmodel().sff()
    
    def xmodel(self):
        return model.Model()
    
    def reset(self):
        raise NotImplementedError
    
    def sprs(self):
        return list(self._sprs)
    
    def rowCount(self, index=None):
        return len(self._sprs)
    
    def spr(self, index):
        if not index.isValid():
            return model.Spr.Null()
        else:
            return list_get(self._sprs, index.row(), model.Spr.Null())
    
    def data(self, index, role=Qt.DisplayRole):
        if role == self.SprRole:
            return self.spr(index)
        
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            spr = list_get(self._sprs, index.row())
            if spr is not None:
                return str(spr.group_index())
            else:
                return None
        else:
            return None
    
    def setSprs(self, sprs):
        sprs = list(sprs)
        if self._sprs == sprs:
            return
        self.beginResetModel()
        self._sprs = sprs
        if self._sortingEnabled:
            self._sprs.sort(key=self._key)
        self.endResetModel()

    def sort(self, key=None):
        if key is not None:
            self._key = key
        
        self.layoutAboutToBeChanged.emit()
        indexes = [(self._key(s), i, s) for i, s in enumerate(self._sprs)]
        indexes.sort()
        
        fromIndexes = []
        toIndexes = []
        for to, (_, from_, _) in enumerate(indexes):
            fromIndexes.append(self.index(from_))
            toIndexes.append(self.index(to))
        self._sprs = [s for _, _, s in indexes]
        
        self.changePersistentIndexList(fromIndexes, toIndexes)
        self.layoutChanged.emit()
    
    def currentSpr(self):
        index = self.currentIndex()
        return self.data(index, role=self.SprRole)
    

class AllSprListModel(SprListModelBase):
    def reset(self):
        self.beginResetModel()
        self._sprs = self.sff().sprs()
        self.endResetModel()
    
    
class SprListModel(SprListModelBase):
    def reset(self):
        self.clear()
    
    def clear(self):
        self.beginResetModel()
        self._sprs = []
        self.endResetModel()
    
    def removeSprs(self, sprs):
        for s in sprs:
            try:
                row = self._sprs.index(s)
            except ValueError:
                continue
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._sprs[row]
            self.endRemoveRows()
    
    def addSprs(self, sprs):
        sprs0 = set(self._sprs)
        sprs = [spr for spr in sprs if spr not in sprs0]
        sprs = list(unique_everseen(sprs))
        if not sprs:
            return
        
        if not self.sortingEnabled():
            startrow = len(self._sprs)
            lastrow  = len(self._sprs) + len(sprs)
            self.beginInsertRows(QModelIndex(), startrow, lastrow)
            self._sprs.extend(sprs)
            self.endInsertRows()
        else:
            allsprs = [(spr, False) for spr in self._sprs] + \
                      [(spr, True) for spr in sprs]
            allsprs.sort(key=lambda x:self._key(x[0]))
            
            from itertools import groupby
            def isNewSpr(x):
                i, (spr, t) = x
                return bool(t)
            
            count_appended = 0
            for k, group in groupby(enumerate(allsprs), key=isNewSpr):
                if not k:
                    continue
                
                group = list(group)
                startrow, _ = group[0]
                lastrow,  _ = group[-1]
                
                self.beginInsertRows(QModelIndex(), startrow, lastrow)
                self._sprs[startrow:startrow] = [spr for _, (spr, _) in group]
                self.endInsertRows()
            
            assert [spr for spr, _ in allsprs] == self._sprs, self._sprs
            
##        for spr in sprs:
##            if self.sortingEnabled():
##                k = self._key(spr)
##                keys = [self._key(s) for s in self._sprs]
##                row = bisect_right(keys, k)
##            else:
##                row = len(self._sprs)
##            self.beginInsertRows(QModelIndex(), row, row)
##            self._sprs.append(sprs)
##            self.endInsertRows()



class SprListItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index=None):
        fm = QFontMetrics(option.font)
        return fm.boundingRect("(-9999, -9999)").size()

class SprListWidgetBase(QListView):
    currentSprChanged = pyqtSignal("PyQt_PyObject")
    
    def __init__(self, parent=None):
        QListView.__init__(self, parent)
        self.setModel(self._createModel())
        self.setItemDelegate (SprListItemDelegate(self))
        
        #view�̐ݒ�
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.selectionModel().currentChanged.connect(self.emitCurrentSprChanged)
        
        #model�̐ݒ�
        self.setSortingEnabled(True)
    
    def selectedSprs(self):
        return [self.data(index, role=self.SprRole)
                    for index in self.selectedIndexes()]
    
    def minimumSizeHint(self):
        sz = QListView.minimumSizeHint(self)
        w = max(sz.width(), self.sizeHint().width())
        return QSize(w, sz.height())
        
    def sizeHint(self):
        option = QStyleOptionViewItemV4()
        option.font = self.font()
        
        sizes = [
            self.itemDelegate().sizeHint(option),
        ]
        for row in xrange(self.model().rowCount()):
            index = self.model().index(row)
            sizes.append(self.itemDelegate().sizeHint(option, index))
        
        import functools
        width = max(s.width() for s in sizes)
        height_list = sorted((s.height() for s in sizes), reverse=True)
        #���10�̘a
        if len(height_list) < 10:
            height_list.extend(height_list[:1]*(10 - len(height_list)))
        height = sum(height_list[:10])
        
        
        if self.verticalScrollBarPolicy() != Qt.ScrollBarAlwaysOff:
            vbar = self.verticalScrollBar()
            width += vbar.width()
        if self.horizontalScrollBarPolicy != Qt.ScrollBarAlwaysOff:
            hbar = self.horizontalScrollBar()
            height += hbar.height()
        
        f = self.frameWidth()
        return QSize(width + 2 * f, height + 2 * f)
    
    def _createModel(self):
        raise NotImplemantedError
        
    def emitCurrentSprChanged(self, currIndex, prevIndex):
        currSpr = self.data(currIndex, role=self.SprRole)
        prevSpr = self.data(prevIndex, role=self.SprRole)
        
        if currSpr != prevSpr:
            self.currentSprChanged.emit(currSpr)

    def __getattr__(self, name):
        return getattr(self.model(), name)
    
    
class SprListWidget(SprListWidgetBase):
    def __init__(self, *a, **kw):
        SprListWidgetBase.__init__(self, *a, **kw)
        
        remove = QAction(self)
        remove.setShortcut("Delete")
        @remove.triggered.connect
        def removeSelection(_):
            self.removeSprs(self.selectedSprs())
        self.addAction(remove)
        
    def _createModel(self):
        return SprListModel(parent=self)
    
    
class AllSprListWidget(SprListWidgetBase):
    def __init__(self, *a, **kw):
        SprListWidgetBase.__init__(self, *a, **kw)
        
    def _createModel(self):
        return AllSprListModel(parent=self)


class AddSprButton(QPushButton):
    def __init__(self, selectedSprList, allSprList, text="->", parent=None):
        QPushButton.__init__(self, text, parent)
        def callback(*a):
            selectedSprList.addSprs(allSprList.selectedSprs())
        self.clicked.connect(callback)
        
class RemoveSprButton(QPushButton):
    def __init__(self, selectedSprList, allSprList=None, text="<-", parent=None):
        QPushButton.__init__(self, text, parent)
        def callback():
            selectedSprList.removeSprs(selectedSprList.selectedSprs())
        self.clicked.connect(callback)


def main():
    from os.path import join
    app = QApplication([])
    from sffairmaker.model import Model
    from sffairmaker.image_op import Image256
    
    Model().sff().open(ur"..\test_with_file\data\suwako.sff")
    print(len(Model().sff().sprs()))
    
    allSprs = AllSprListWidget()
    selectedSprs = SprListWidget()
    
    add = AddSprButton(selectedSprs, allSprs)
    remove = RemoveSprButton(selectedSprs)
    
    w = QWidget()
    w.setLayout(
        hBoxLayout(
            groupBox("all", allSprs),
            vBoxLayout(
                ("stretch", 1),
                add,
                remove,
                ("stretch", 1),
            ),
            groupBox("selected", selectedSprs),
            ("stretch", 1),
        ),
    )
    w.show()
    
    
    app.exec_()

if "__main__" == __name__:
    main()