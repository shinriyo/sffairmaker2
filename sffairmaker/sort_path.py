# coding: utf-8
from __future__ import division, print_function
import sys
__metaclass__ = type 
import ctypes
import re

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


if sys.platform == "win32":
    # Windowsの場合
    SHLWAPI = ctypes.windll.LoadLibrary("SHLWAPI.dll")
    StrCmpLogicalW = SHLWAPI.StrCmpLogicalW
    SHLWAPI = None

    def cmp_path(f1, f2):
        return StrCmpLogicalW(str(f1), str(f2))

    def key_path(path):
        return cmp_to_key(StrCmpLogicalW)(str(path))

else:
    # Macまたは他のOSの場合
    def natural_keys(text):
        return [int(chunk) if chunk.isdigit() else chunk.lower() for chunk in re.split(r'(\d+)', text)]

    def cmp_path(f1, f2):
        return (natural_keys(str(f1)) > natural_keys(str(f2))) - (natural_keys(str(f1)) < natural_keys(str(f2)))

    def key_path(path):
        return cmp_to_key(cmp_path)(str(path))
# SHLWAPI = ctypes.windll.LoadLibrary("SHLWAPI.dll")
# StrCmpLogicalW = SHLWAPI.StrCmpLogicalW
# SHLWAPI = None

# def cmp_path(f1, f2):
#     return StrCmpLogicalW(str(f1), str(f2))

# def key_path(path):
#     return cmp_to_key(SHLWAPI.StrCmpLogicalW)(str(path))

def main():
    import doctest
    doctest.testmod()

if "__main__" == __name__:
    main()