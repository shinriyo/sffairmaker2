# coding: utf-8
"""
A Implementation of multidict (multimap).
multidict in this module has novel methods - get1, pop1, asdict1 and ***_m.
"""
# import itertools
import copy
# from UserDict import DictMixin
from collections.abc import MutableMapping

def def_deligators(locals, member_str, method_names):
    """
        def_deligators(locals, member_str, method_names)
        
        define methods that merely deligate to member.
    """
    for method in method_names:
        defstr0 = "def %(method)s(self, *a, **kw):" \
                     "return %(member)s.%(method)s(*a, **kw)"
        
        defstr = defstr0 % {"method":method, 
                            "member":member_str}
        exec(defstr) in {}, locals

def throws(t, f, *a, **kw):
    """
    throws(t, f, *a, **kw) -> bool
    Return whether f(*a, **kw) raise exception t.
    
    >>> from multidict import throws
    >>> throws(ValueError, int, "xyz")
    True
    >>> throws(ValueError, int, "1")
    False
    """
    #this function is used for doctest only.
    
    try:
        f(*a, **kw)
    except t:
        return True
    else:
        return False

# class multidict(DictMixin):
class multidict(MutableMapping):
    def __init__(self, items=()):
        self._dict = {}
        for k, v in items:
            self[k] = v
    
    def __getitem__(self, key):
        return copy.copy(self._dict[key])
    
    def __setitem__(self, key, value):
        self._dict.setdefault(key, []).append(value)
    
    def_deligators(locals(), "self._dict", 
        """__delitem__ keys __contains__ 
        __iter__ iteritems __str__ """.split())
    
    def __copy__(self):
        return self.__class__(item for item in self.iteritems_m())
    
    def addlist(self, key, values):
        for v in values:
            self[key] = v
    
    def updatelist(self, **kw):
        for k, v in kw.items():
            self.addlist(k, v)
    
    def remove(self, key, val):
        """
        removes the specified value from the list of values 
        for the specified key;
        
        raises KeyError if key not found,
        raises ValueError if val not found.
        """
        self._dict[key].remove(val)
    
    def get1(self, *a):
        """\
        D.get1(key[,default]) -> value, 
        
        If there is exactly one value corresponding specified key, 
        return the value.
        
        If two or more values is corresponded for specified key,
        ValueError is raised.
        
        If key is not found, default is returned if given, 
        otherwise KeyError is raised.
        
        >>> from multidict import multidict, throws
        >>> m = multidict([(0, "a"), (0, "b"), (2, "c"), (1, "d")])
        >>> m.get1(1)
        'd'
        >>> throws(KeyError, m.get1, 3)
        True
        >>> m.get1(3, "e")
        'e'
        >>> throws(ValueError, m.get1, 0)
        True
        >>> throws(ValueError, m.get1, 0, 1)
        True
        """
        if len(a) == 0:
            raise TypeError("get1 expected at least 1 arguments, got 0")
        if len(a) == 2:
            key, default = a
            has_default = True
        elif len(a) == 1:
            key = a[0]
            default = None
            has_default = False
        else:
            msg = "get1 expected at least 1 arguments, got %d"%(len(a),)
            raise TypeError(msg)
        
        try:
            values = self[key]
        except KeyError:
            if has_default:
                return default
            else:
                raise
        else:
            if len(values) == 1:
                return values[0]
            else:
                msg = "There are multiple values for key %r"%(key,)
                raise ValueError(msg)
    
    def pop1(self, *a):
        """\
        D.pop1(key[,default]) -> value, 
        
        If there is exactly one value corresponding specified key, 
        remove the key and return the value.
        
        If two or more values is corresponded for specified key,
        ValueError is raised.
        
        If key is not found, default is returned if given, 
        otherwise KeyError is raised.
        
        >>> from multidict import multidict, throws
        >>> m = multidict([(0, "a"), (0, "b"), (2, "c"), (1, "d")])
        >>> m.pop1(1)
        'd'
        >>> m
        {0: ['a', 'b'], 2: ['c']}
        >>> throws(KeyError, m.pop1, 1)
        True
        >>> m.pop1(1, "e")
        'e'
        >>> throws(ValueError, m.pop1, 0, "e")
        True
        """
        v = self.get1(*a)
        key = a[0]
        self.pop(key, None)
        return v
    
    def asdict1(self, choice=None):
        """
        md.asdict1([choice=None]) -> dictionary.
        
        When there are multiple values for key, 
        if choice is None then ValueError is raised, 
        if choice is not None, dictionary[key] = choice(md, key, values).
        """
        d = {}
        for key, values in self.items():
            if len(values) == 1:
                d[key] = values[0]
            else:
                if choice is None:
                    raise ValueError("There are multiple values for key %r"%(key,))
                else:
                    d[key] = choice(self, key, values)
        return d
    
    def iteritems_m(self):
        """
        >>> from multidict import multidict
        >>> m = multidict([(0, "a"), (0, "b"), (2, "c"), (1, "d")])
        >>> list(m.iteritems_m())
        [(0, 'a'), (0, 'b'), (1, 'd'), (2, 'c')]
        """
        return ((key, value) 
                    for key, values in self.items()
                        for value in values)
    
    def iterkeys_m(self):
        """
        >>> from multidict import multidict
        >>> m = multidict([(0, "a"), (0, "b"), (2, "c"), (1, "d")])
        >>> list(m.iterkeys_m())
        [0, 0, 1, 2]
        """
        
        from operator import itemgetter
        return map(itemgetter(0), self.iteritems_m())
    
    def itervalues_m(self):
        """
        >>> from multidict import multidict
        >>> m = multidict([(0, "a"), (0, "b"), (2, "c"), (1, "d")])
        >>> list(m.itervalues_m())
        ['a', 'b', 'd', 'c']
        """
        from operator import itemgetter
        return map(itemgetter(1), self.iteritems_m())
    
    def items_m(self):
        return list(self.iteritems_m())
    
    def values_m(self):
        return list(self.itervalues_m())
    
    def keys_m(self):
        return list(self.iterkeys_m())
    
    @classmethod
    def choice_last(cls, md, key, values):
        """choice_last(cls, md, key, values) -> values[-1]"""
        return values[-1]
    
    @classmethod
    def choice_first(cls, md, key, values):
        """choice_last(cls, md, key, values) -> values[0]"""
        return values[0]
    

if __name__ == "__main__":
    import doctest
    doctest.testmod()
