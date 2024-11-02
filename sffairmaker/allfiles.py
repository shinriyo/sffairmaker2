# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
import os
from fnmatch import fnmatch
    
def pattern_to_filt(pat):
    if isinstance(pat, basestring):
        def filt(filename):
            name = os.path.basename(filename)
            return fnmatch(name, pat)
        return filt
    elif isinstance(pat, (list, tuple)):
        def filt(filename):
            name = os.path.basename(filename)
            return any(fnmatch(name, p) for p in pat)
        return filt
    else:
        return pat
    
def allfiles(root="./", pattern="*" , single_level=False , yield_folders=False):
    filt = pattern_to_filt(pattern)
    root = os.path.abspath(str(root))
    for path, subdirs, files in os.walk(root):
        if yield_folders:
            files.extend(subdirs)
        
        for name in files:
            filename = os.path.abspath(os.path.join(path, name))
            if filt(filename):
                yield filename
            
        if single_level:
            break


def alldirs(root="./", pattern="*", single_level=False):
    filt = pattern_to_filt(pattern)
    root = os.path.abspath(str(root))
    for path, subdirs, files in os.walk(root):
        for dir in subdirs:
            dirpath = os.path.abspath(os.path.join(path, dir))
            if filt(dirpath):
                yield dirpath
        
        if single_level:
            break


def main():
    import doctest
    doctest.testmod()

if "__main__" == __name__:
    main()