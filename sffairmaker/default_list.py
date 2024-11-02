# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 

class DefaultList(list):
    def __init__(self, alist=[], default=None):
        list.__init__(self, alist)
        self.default = default
    
    def __getitem__(self, i):
        if i in xrange(len(self)):
            return list.__getitem__(self, i)
        else:
            return self.default
            
    def __setitem__(self, i, v):
        if i < len(self):
            list.__setitem__(self, i, v)
        else:
            self.extend([self.default]*(i - len(self)))
            self.append(v)
    
    def __delitem__(self, i):
        if i < len(self):
            list.__delitem__(self, i)
    

def main():
    pass
    
if "__main__" == __name__:
    main()