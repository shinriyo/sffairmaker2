# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
# from PyQt4.QtCore import *
from PyQt5.QtCore import *


class Clsn(tuple):
    def __new__(cls, items=[]):
        return tuple.__new__(cls, map(cls._rect, items))
    
    @classmethod
    def _rect(cls, item):
        if isinstance(item, QRect):
            return item.normalized()
        else:
            left, top, width, height = item
            return QRect(left, top, width, height).normalized()
    
    def append(self, rect):
        return Clsn(self + (self._rect(rect),))
    
    def remove_at(self, i):
        return Clsn(self[:i] + self[i + 1:])
    
    def replace_at(self, i, x):
        return Clsn(self[:i] + (x,) + self[i + 1:])
    
    def move_all(self, delta):
        return Clsn([r.translated(delta) for r in self])
    
    def __repr__(self):
        return "Clsn({0})".format(tuple.__repr__(self))
    
def main():
    pass
    
if __name__ == "__main__":
    main()