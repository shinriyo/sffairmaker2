#encoding:utf-8
from __future__ import division, print_function

import re
from itertools import *
from operator import *
from sffairmaker.multidict import multidict
from cStringIO import StringIO

def bufferedFileIO(filename):
    with open(filename) as fp:
        return StringIO(fp.read())

_ReSectionHead = re.compile(r"^\s* \[ \s* (.*?) \s* \] \s*$" , re.I|re.X)
_ReSectionHead_match = _ReSectionHead.match

def get_match_function(x):
    if isinstance(x, basestring):
        return re.compile(x, re.I).match
    if x is None:
        return lambda _:True
    else:
        if hasattr(x, "match"):
            return x.match
        else:
            return x

def _isection_from_fp(fp, match=None):
    name = None
    members = []
    mr = None
    match = get_match_function(match)
    
    for line in fp:
        p = line.find(";")
        if 0 <= p:
            line = line[:p]
        line = line.strip("\n @")
        if not line:continue
        
        mh = _ReSectionHead_match(line)
        if mh is None:
            members.append(line)
        else:
            if name is not None:
                yield (name, match(name), members)
            members = []
            name = mh.group(1)
    if name is not None:
        yield (name, match(name), members)

def isection_from_fp(*a, **kw):
    return ifilter(itemgetter(1), _isection_from_fp(*a, **kw))
    
def isection(filename, *a, **kw):
    return isection_from_fp(bufferedFileIO(filename), *a, **kw)

def isection_from_string(ss, *a, **kw):
    return isection_from_fp(StringIO(ss), *a, **kw)
    
def isection_param_from_fp(fp, *a, **kw):
    for section_name, mobj, members in isection_from_fp(fp, *a, **kw):
        params = multidict()
        for line in members:
            k, a, v = split_key_value(line)
            params[k.lower()] = (a, v)
        yield section_name, mobj, params
    
def isection_param_from_string(ss, *a, **kw):
    return isection_param_from_fp(StringIO(ss), *a, **kw)

def isection_param(filename, *a, **kw):
    return isection_param_from_fp(bufferedFileIO(filename), *a, **kw)

def parse_key_value(ss):
    paren_level = 0
    in_string = False
    escaped = False
    paren_begin = None
    paren_last  = None
    equal_pos = None
    
    def error(i):
        fmt = "in parsing %r as 'key(arg) = value' stopped (%d) char %r"
        return Error(fmt%(ss, i+1, ss[i]))
    
    for i, c in enumerate(ss):
        if in_string:
            if escaped:
                escaped = False
            elif c == '"':
                in_string = False
                escaped = False
        else:
            if c == '"':
                in_string = True
            elif c == '(':
                if paren_level == 0:
                    if not paren_begin is None:
                        raise error(i)
                    paren_begin = i
                paren_level += 1
            elif c == ')':
                paren_level -= 1
                if paren_level == 0:
                    if (paren_begin is None) or (not paren_last is None):
                        raise error(i)
                    paren_last = i
                
            elif paren_level == 0 and c == "=":
                if paren_begin is None != paren_last is None:
                    raise error(i)
                equal_pos = i
                break
    else:
        if equal_pos is None:
            fmt = "in parsing %r as 'key(arg) = value' '=' is not found"
            raise Error(fmt%(ss,))
        elif (not paren_begin is None) and (paren_last is None):
            fmt = "in parsing %r as 'key(arg) = value' ')' is not found"
            raise Error(fmt%(ss,))
    
    return paren_begin, paren_last, equal_pos

re_no_arg_key_value = re.compile(
    "(?P<key>[a-zA-Z0-9_\.]+) \s* = \s* (?P<value>.*)", 
    re.I | re.X)

def split_key_value(ss):
    m = re_no_arg_key_value.match(ss)
    if m:
        return m.group("key"), None, m.group("value")
    else:
        paren_begin, paren_last, equal_pos = parse_key_value(ss)
        assert not paren_begin is None, ss
        assert not paren_last is None, ss
        
        key = ss[:paren_begin].strip()
        arg = ss[paren_begin + 1:paren_last].strip()
        value = ss[equal_pos+1:].strip()
        return key, arg, value

def main():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    main()

