# coding: utf-8
from sffairmaker.section_file import isection, isection_from_string
from sffairmaker.alphablend import AlphaBlend
# import __builtin__
import builtins
from collections import namedtuple
import re

class Rect(namedtuple("Rect", "left top width height")):
    @property
    def right(self):
        return self.left + self.width
    @property
    def bottom(self):
        return self.top + self.height

class Error(Exception):
    """カスタムエラークラス"""
    pass

_ReBeginAction = re.compile(r"begin \s* action \s* ((\+|-)?\d+)",  re.I | re.X)

class AIR(dict):
    '''
    >>> import air
    >>> s = """
    ... ; Win
    ... [Begin Action 181]
    ... Clsn2Default: 1
    ...  Clsn2[0] =  17,  0,-12,-83
    ... 200,0, 0,0, 4
    ... 181,0, 0,0, 5
    ... 181,1, 0,0, 5
    ... 181,2, 0,0, 5
    ... 181,3, 0,0, 5
    ... 181,4, 0,0, 5
    ... 181,5, 0,0, 5
    ... 181,6, 0,0, 30
    ... 181,5, 0,0, 7
    ... 181,4, 0,0, 6
    ... 181,3, 0,0, 5
    ... 181,2, 0,0, -1
    ... """
    >>> a = air.AIR.from_string(s)
    >>> a[181].currentElemIndex(81)
    10
    >>> a[181].currentElemIndex(82)
    11
    >>> a[181].currentElemIndex(83)
    11
    '''
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError as e:
            raise Error("{0}\n{1}".format(e, tuple(self.keys())))
    
    def to_string(self):
        lines = []
        append = lines.append
        for index, action in sorted(self.iteritems()):
            append(action.to_string(index))
        return "\n\n".join(lines)
    
    def save(self, filename):
        with __builtin__.open(filename, "w") as fp:
            fp.write(self.to_string())
    
    
    @classmethod
    def open(cls, filename):
        return cls._from(isection(filename, _ReBeginAction), filename)
    
    @classmethod
    def from_string(cls, ss):
        return cls._from(isection_from_string(ss, _ReBeginAction), "<string>")
    
    @classmethod
    def _from(cls, isec, srcname):
        inst = cls()
        for section_name, m, lines in isec:
            index = int(m.group(1))
            try:
                inst[index] = ActionBuilder(lines).A
            except Error as e:  # ここを修正
                msg = "%s\n%s\nBegin Action %d" % (e, srcname, index)  # nをindexに変更
                raise Error(msg)
        return inst
    
class Action(object):
    """
    >>> s= '''
    ... [Begin Action 0]
    ... Clsn2Default:2
    ...   Clsn2[0] = -13,-79,16,0
    ...   Clsn2[1] = -7,-93,5,-79
    ... 0, 0, 0, 0, 9, ,
    ... 0, 1, 0, 0, 7, ,
    ... 0, 2, 0, 0, 7, ,
    ... 0, 3, 0, 0, 7, ,
    ... 0, 4, 0, 0, 7, ,
    ... 0, 5, 0, 0, 45, ,
    ... 0, 4, 0, 0, 7, ,
    ... 0, 3, 0, 0, 7, ,
    ... 0, 2, 0, 0, 7, ,
    ... 0, 1, 0, 0, 7, ,
    ... 0, 0, 0, 0, 40, ,
    ... '''
    >>> i, a = Action.from_string(s)
    >>> i
    0
    >>> a.elem[0].group
    0
    >>> a.elem[-1].alpha.source
    255
    """
    __slots__  = "clsnDefault loopPos hasLoop elem".split()
    def __init__(self):
        self.clsnDefault = {1:ClsnList(), 2:ClsnList()}
        self.loopPos = None
        self.hasLoop = False
        self.elem = []
    
    def __iter__(self):
        return iter(self.elem)
    
    def allTime(self):
        return sum(e.get_time() for e in self.elem)
    
    def inFirstLoop(self, time):
        return time < self.allTime()
    
    def currentElemIndex(self, time):
        return self.elem.index(self.currentElem(time))
    
    def currentElem(self, time):
        elms = self.elem
        if time < self.allTime():
            for e in elms:
                time -= e.utime()
                if time < 0:
                    return e
        elif elms[-1].inf():
            return elms[-1]
        elif not self.hasLoop:
            time %= self.allTime()
            for e in elms:
                time -= e.utime()
                if time < 0:
                    return e
        else:
            time -= self.allTime()
            time = time % self.loopTime()
            for e in elms[self.loopPos:]:
                time -= e.utime()
                if time < 0:
                    return e
    
    def loopTime(self):
        return sum(e.utime() for e in self.elem[self.loopPos:])
    
    def sumOfTime(self, index):
        return sum(e.time for e in self.elem[0:index])
    
    def animElemTime(self, index, time):
        return time - sum(e.time for e in self.elem[:index-1])
    
    def animElem(self, time):
        i = 0
        j = 0
        
        while 1:
            if time == 0:
                return i + 1
            elif time < 0:
                return None
            
            time -= self.elem[j].time
            
            i += 1
            j += 1
            if len(self.elem) - 1 < j:
                j = self.loopPos
    
    def animTime(self, time):
        return time - self.allTime()
    
    def to_string(self, index=None):
        lines = []
        append = lines.append
        
        if index is not None:
            append("[Begin Action {0}]".format(index))
        
        for clsnindex, clsns in self.clsnDefault.iteritems():
            if not clsns:
                continue
            
            append("Clsn{0}Default:{1}".format(clsnindex, len(clsns)))
            for k, rc in enumerate(clsns):
                rectstr = ",".join(map(str, [rc.left, rc.top, rc.right, rc.bottom]))
                append("  Clsn{clsnindex}[{k}] = {rect}"\
                        .format(clsnindex=clsnindex, k=k, rect=rectstr))
        
        for i, e in enumerate(self.elem):
            if self.loopPos == i != 0:
                append("LoopStart")
            append(e.to_string())
        
        return "\n".join(lines)
    
    @staticmethod
    def from_string(ss):
        for section_name, _, lines in isection_from_string(ss):
            m = _ReBeginAction.match(section_name)
            if not m:
                raise PasingSectionNameError(section_name)
            action = ActionBuilder(lines, True).A
            return int(m.group(1)), action
        raise SectionMissingError()

def join_if_need(delimiter, items):
    """
    >>> join_if_need(",", ["1", "", "3", ""])
    u'1,,3'
    >>> join_if_need(",", ["1", "", ""])
    u'1'
    >>>
    """
    items = list(map(unicode, items))
    for i in xrange(len(items) - 1, -1, -1):
        if items[i]:
            break
    return delimiter.join(items[:i + 1])

class Elem(object):
    __slots__ = "group index pos time clsn H V alpha".split()
    def __init__(self):
        self.group = 0
        self.index = 0
        self.pos   = () 
        self.time = 0
        self.H = 0
        self.V = 0
        self.clsn = {1:ClsnList(), 2:ClsnList()}
        self.alpha = AlphaBlend.N()
    
    def get_time(self):
        return self.time if self.time >= 0 else 0
    utime = get_time
    
    def inf(self):
        return self.time < 0
    
    def to_string(self):
        lines = []
        append = lines.append
        for index, clsns in self.clsn.iteritems():
            if not clsns:
                continue
            
            append("Clsn{0}:{1}".format(index, len(clsns)))
            rcformat = "{0.left}, {0.top}, {0.right}, {0.bottom}".format
            for k, rc in enumerate(clsns):
                append("  Clsn{index}[{k}] = {rect}"\
                        .format(index=index, k=k, rect=rcformat(rc)))
        
        hv = ("H" if self.H else "") + \
             ("V" if self.V else "")
        
        L = ", ".join(map(str, [
            self.group,
            self.index,
            self.pos[0],
            self.pos[1],
            self.time,
        ]))
        
        
        append(join_if_need(", ", [L, hv, self.alpha.to_string()]))
        
        return "\n".join(lines)
        

class ClsnList(list):
    def copy(self):
        c = ClsnList(self)
        for i, rc in enumerate(c):
            c[i] = copy.copy(rc)
        return c
    __copy__ = copy

ReLoopStart     = re.compile(r"\s* loopstart(?P<excess>.*)", re.I|re.X)
ReClsn          = re.compile(r"""
    \s* clsn.*? \[ .* \] \s* = \s* 
        (?P<left> (?:\-|\+)?[0-9]+) \s* , \s*
        (?P<top> (?:\-|\+)?[0-9]+) \s* , \s*
        (?P<right> (?:\-|\+)?[0-9]+) \s* , \s*
        (?P<bottom> (?:\-|\+)?[0-9]+)
    (?P<excess>.*)
    """, re.I |re.X)

ReBeginClsnDef  = re.compile(r"\s* clsn (1|2) default \s*:\s*(\d*)(?P<excess>.*)", re.I | re.X)
ReBeginClsn     = re.compile(r"\s* clsn (1|2) \s*:\s*(\d*)(?P<excess>.*)",        re.I | re.X)
ReElem = re.compile(r"""
        (?P<group>(?:\-|\+)?[0-9]+) \s* , \s* 
        (?P<index>(?:\-|\+)?[0-9]+) \s*
        (, \s* (?P<x>(?:\-|\+)?[0-9]+) \s*
        (, \s*(?P<y>(?:\-|\+)?[0-9]+) \s*
        (, \s*(?P<time>(?:\-|\+)?[0-9]+)
            \s* 
            (?:
                , \s* (?P<hv>[HV]*)
                (?: \s* , \s*
                    (
                        (?P<alpha>AS(?P<as>\d+)D(?P<d>\d+))
                        |
                        (?P<a1>A([0-9]+))
                        |
                        (?P<a>A)
                        |
                        (?P<s>S)
                    )?
                )?
            )?
        )?)?)?
        (?P<excess>.*)$
        """,
        re.I | re.X)

class ParsingError(Error):
    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line
        msg = "Parsing Error in line {0} of action ('{1}').".format(lineno, line)
        Error.__init__(self, msg)

class SectionMissingError(Error):
    def __init__(self):
        msg = "action is not found."
        Error.__init__(self, msg)

class ActionBuilder(object):
    def __init__(self, lines, strict=False):
        self.A = Action()
        self.clsn = {1:ClsnList(), 2:ClsnList()}
        self.clsnIndex = 1
        self.inClsnDefault = False
        d = [
            (ReLoopStart.match, self.p_loop_start),
            (ReBeginClsn.match, self.p_begin_clsn),
            (ReBeginClsnDef.match, self.p_begin_clsn_default),
            (ReClsn.match, self.p_clsn),
            (ReElem.match, self.p_elem),
        ]
        
        for i, line in enumerate(lines):
            for f, p in d:
                m = f(line)
                if m is None or (strict and m.group("excess")):
                    continue
                else:
                    p(m)
                    break
            else:
                if strict:
                    raise ParsingError(i, line)
    
    def p_begin_clsn(self, m):
        self.inClsnDefault = False
        self.clsnIndex = int(m.group(1))
    
    def p_begin_clsn_default(self, m):
        self.inClsnDefault = True
        self.clsnIndex = int(m.group(1))
    
    def p_clsn(self, m):
        if self.clsnIndex is None:
            return
        left  = int(m.group("left"))
        top   = int(m.group("top"))
        right = int(m.group("right"))
        bottom= int(m.group("bottom"))
        if right < left:
            left, right = right, left
        if bottom < top:
            top, bottom = bottom, top
        
        rc = Rect(left, top, right - left, bottom - top)
        if self.inClsnDefault:
            self.A.clsnDefault[self.clsnIndex].append(rc)
        else:
            self.clsn[self.clsnIndex].append(rc)
        
    def p_loop_start(self, m):
        self.A.loopPos = len(self.A.elem)
        self.A.hasLoop = True
    
    def p_elem(self, m):
        e = Elem()
        if m.group("s"):
            e.alpha = AlphaBlend.S()
        elif m.group("a"):
            e.alpha = AlphaBlend.A()
        elif m.group("a1"):
            e.alpha = AlphaBlend.A1()
        else:
            e.alpha = AlphaBlend.A()
            if m.group("as"):
                source = int(m.group("as"))
            else:
                source = 255
            
            if m.group("d"):
                dest = int(m.group("d"))
            else:
                dest = 0
            
            e.alpha = AlphaBlend(source, dest)
            
        e.group = int(m.group("group"))
        e.index = int(m.group("index"))
        e.pos   = (int(m.group("x") or 0), int(m.group("y") or 0))
        e.time  = int(m.group("time") or 0)
        e.clsn  = self.clsn
        if m.group("hv"):
            e.H = 'h' in m.group("hv").lower()
            e.V = 'v' in m.group("hv").lower()
        else:
            e.H = e.V = False
        self.A.elem.append(e)
        
        self.clsn = {1:ClsnList(), 2:ClsnList()}
    

class PasingSectionNameError(Error):
    def __init__(self, section_name):
        self.section_name = section_name
        msg = "Invalid section name '{0}'".format(section_name)
        Error.__init__(self, msg)
        
open = AIR.open
from_string = AIR.from_string

def main():
    import doctest
    doctest.testmod()
    
    AIR.open("test.air").to_string()



if __name__ == "__main__":
    main()
