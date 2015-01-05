#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 

class Null:
    def __init__(self, *a, **kw):pass
    def __call__(self, *a, **kw):return self
    def __getattr__(self, name): return self
    def __setattr__(self, name, value):pass
    def __delattr__(self, name):pass
    def __nonzero__(self):return False
    def __enter__(self):return self
    def __exit__(self, *a, **kw):return False
    
def main():
    import doctest
    doctest.testmod()

if "__main__" == __name__:
    main()