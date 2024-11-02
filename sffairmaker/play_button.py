# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *


class PlayButton(ValueButton):
    def __init__(self, parent=None):
        ValueButton.__init__(self, parent)
        self.setCheckable(True)
        self.toggled.connect(self._toggleLabel)
        
        from os.path import dirname, join
        self._icons = {
            True:QIcon(QPixmap.fromImage(stopButton())),
            False:QIcon(QPixmap.fromImage(startButton())),
        }
        self._toggleLabel(self.isChecked())
    
    def _toggleLabel(self, checked):
        self.setIcon(self._icons[checked])

def startButton():
    im = QImage(128, 128, QImage.Format_ARGB32)
    painter = QPainter(im)
    
    painter.setBackground(QColor(0, 0, 0, 0))
    painter.setBrush(QColor(0, 0, 255))
    painter.setPen(QColor(0, 0, 255))
    painter.drawPolygon(QPoint(0, 0), QPoint(126, 63), QPoint(0, 126))
    return im

def stopButton():
    im = QImage(128, 128, QImage.Format_ARGB32)
    painter = QPainter(im)
    
    painter.setBackground(QColor(0, 0, 0, 0))
    painter.fillRect(im.rect(), Qt.red)
    
    return im

def main():
    app = QApplication([])
    
    p = PlayButton()
    w = QWidget()
    w.setLayout(QHBoxLayout())
    w.layout().addWidget(p)
    w.show()
    
    app.exec_()
    

if "__main__" == __name__:
    main()