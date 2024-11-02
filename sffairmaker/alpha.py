# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from collections import namedtuple 

def inrange(v, vmin, vmax):
    if v < vmin:
        return vmin
    elif vmax < v:
        return vmax
    else:
        return v

_AlphaBlend = namedtuple("AlphaBlend", "source dest sub")
class AlphaBlend(_AlphaBlend):
    """
        >>> AlphaBlend(0, 0)
        AlphaBlend(source=0, dest=0, sub=False)
        >>> AlphaBlend(-10, 300)
        AlphaBlend(source=0, dest=256, sub=False)
        >>> AlphaBlend(-10, 300, False)
        AlphaBlend(source=0, dest=256, sub=False)
        >>> AlphaBlend(5, 10) != AlphaBlend(20, 30)
        True
    """
    SourceRange = (0, 256)
    DestRange = (0, 256)
    def __new__(cls, source, dest, sub=False):
        return _AlphaBlend.__new__(
            cls,
            inrange(source, *cls.SourceRange),
            inrange(dest, *cls.DestRange),
            sub,
        )
    
    def change(self, **kw):
        for k in "source dest sub".split():
            kw.setdefault(k, getattr(self, k))
        return AlphaBlend(**kw)
    
    @classmethod
    def N(cls):
        return cls(255, 0)
    
    @classmethod
    def A(cls):
        return cls(255, 255)
    
    @classmethod
    def A1(cls):
        return cls(255, 128)
    
    @classmethod
    def S(cls):
        return cls(255, 0, sub=True)

def main():
    pass
    
if __name__ == "__main__":
    main()