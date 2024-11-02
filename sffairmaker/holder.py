# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
import copy
from collections import OrderedDict


from sffairmaker.qutil import *

def createHolder(name, fields):
    class Holder:
        _fields = list(fields)
        def __init__(self, **kw):
            self._init(**kw)
        
        def _init(self, **kw):
            assert set(kw) == set(self._fields)
            self.__dict__.update(("_"+k, v)for k, v  in kw.items())
        
        exec(def_qgetter(*_fields))
        
        def _replace(self, **kw):
            assert set(kw) <= set(self._fields)
            c = copy.copy(self)
            for k, v in kw.items():
                setattr(c, "_" + k, v)
            return c
        
        def __repr__(self):
            s = self.__class__.__name__ + "("
            s += ", ".join(repr(v) for v in self._astuple())
            s += ")"
            return s
            
        def __eq__(self, other):
            return self._astuple() == other._astuple()
        
        def __ne__(self, other):
            return not(self == other)
        
        __hash__ = None
        
        def __lt__(self, other):
            return self._astuple() < other._astuple()
        
        def _astuple(self):
            return tuple(getattr(self, "_" +name) for name in self._fields)
        
        def _asdict(self):
            return OrderedDict((name, getattr(self, "_" +name))
                        for name in self._fields)
        
        
    Holder.__name__ = name
    return Holder
    


def main():
    pass

if "__main__" == __name__:
    main()