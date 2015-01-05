#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
import ctypes

def cmp_to_key(cmpf):
    '''
    Convert a cmp= function into a key= function
    >>> key = cmp_to_key(lambda a, b:int(a) - int(b))
    >>> key("1") < key("2")
    True
    >>> key("1") < key("01")
    False
    '''

    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return cmpf(self.obj, other.obj) < 0
        def __gt__(self, other):
            return cmpf(self.obj, other.obj) > 0
        def __eq__(self, other):
            return cmpf(self.obj, other.obj) == 0
        def __le__(self, other):
            return cmpf(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return cmpf(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return cmpf(self.obj, other.obj) != 0
        def __hash__(self):
            return hash(self.obj)
    return K


SHLWAPI = ctypes.windll.LoadLibrary("SHLWAPI.dll")
StrCmpLogicalW = SHLWAPI.StrCmpLogicalW

def cmp_path(f1, f2):
    return StrCmpLogicalW(unicode(f1), unicode(f2))

def key_path(path):
    return cmp_to_key(SHLWAPI.StrCmpLogicalW)(unicode(path))

def main():
    import doctest
    doctest.testmod()

if "__main__" == __name__:
    main()