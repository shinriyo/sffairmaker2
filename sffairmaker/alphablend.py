# coding: utf-8
from __future__ import (
    with_statement, 
    division,
    print_function,
)

import inspect
from operator import attrgetter

def def_getter(*names):
    frame = inspect.currentframe(1)
    locals = frame.f_locals
    for name in names:
        locals[name] = property(attrgetter("_" + name))

def inrange(v, vmax, vmin):
    return max(vmax, min(v, vmin))
    
class AlphaBlend(object):
    # def_getter(*"source dest sub".split())
    def def_getter(self, source, dest, sub):
        print(f"Source: {source}, Destination: {dest}, Sub: {sub}")

    def __init__(self, source, dest, sub=False):
        self._source = source
        self._dest = dest
        self._sub = sub
    
    def __str__(self):
        return "AlphaBlend(source={0}, dest={1}, sub={2})"\
            .format(self.source, self.dest, self.sub)
    
    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, v):
        self._source = inrange(int(v), 0, 255)

    @property
    def dest(self):
        return self._dest
    
    @property
    def sub(self):
        return self._sub

    @dest.setter
    def dest(self, v):
        self._dest = inrange(int(v), 0, 255)
    
    @sub.setter
    def sub(self, v):
        self._sub = bool(v)
    
    @classmethod
    def N(cls):
        return cls(255, 128)
    
    @classmethod
    def A(cls):
        return cls(255, 255)
    
    @classmethod
    def A1(cls):
        return cls(255, 128)
    
    @classmethod
    def S(cls):
        return cls(255, 0, sub=True)
    
    def to_string(self):
        if self.sub:
            return "S"
        elif self.source>=255 and self.dest>=255:
            return "A"
        elif self.source>=255 and self.dest==128:
            return "A1"
        elif self.source>=255 and self.dest==0:
            return "" #���������Ȃ�
        else:
            return "AS{0}D{1}".format(self.source, self.dest)

def main():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    main()

