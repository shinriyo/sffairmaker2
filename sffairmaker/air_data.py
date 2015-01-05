#encoding:shift-jis
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker import airlib
from sffairmaker.id_ import IdDispatcher
from sffairmaker.qutil import *
from sffairmaker.clsn import *
from sffairmaker.alpha import *
from sffairmaker.holder import createHolder

from operator import methodcaller
import copy
from collections import namedtuple
from collections import OrderedDict

def inserted(t, pos, item):
    """
    >>> inserted("abc", 1, "*")
    ('a', '*', 'b', 'c')
    >>> inserted("abc", 0, "*")
    ('*', 'a', 'b', 'c')
    >>> inserted("abc", 4, "*")
    ('a', 'b', 'c', '*')
    >>> inserted("abc", -1, "*")
    ('a', 'b', '*', 'c')
    """
    t = tuple(t)
    return t[:pos] + (item,) + t[pos:]
    
def removed(t, item):
    """
    >>> removed("abc", "a")
    ('b', 'c')
    >>> removed("abc", "x")
    Traceback (most recent call last):
    ValueError: tuple.index(x): x not in list
    """
    t = tuple(t)
    pos = t.index(item)
    return t[:pos] + t[pos+1:]
    
def moved(t, pos, item):
    """
    >>> moved("abcde", 0, "c")
    ('c', 'a', 'b', 'd', 'e')
    >>> moved("abcde", 1, "c")
    ('a', 'c', 'b', 'd', 'e')
    >>> moved("abcde", 2, "c")
    ('a', 'b', 'c', 'd', 'e')
    >>> moved("abcde", 3, "c")
    ('a', 'b', 'c', 'd', 'e')
    >>> moved("abcde", 4, "c")
    ('a', 'b', 'd', 'c', 'e')
    >>> moved("abcde", 5, "c")
    ('a', 'b', 'd', 'e', 'c')
    """
    t = tuple(t)
    oldpos = t.index(item)
    if pos < 0:
        pos = len(t) + pos
    
    if pos in [oldpos, oldpos + 1]:
        return t
    elif pos < oldpos:
        return t[:pos] + (item,) + t[pos:oldpos] + t[oldpos+1:]
    else:
        return t[:oldpos] + t[oldpos+1:pos] + (item,) + t[pos:]


class AnimAttrs(createHolder("AnimAttr", "index loop clsn1 clsn2".split())):
    def __init__(self, index=-1, loop=None, clsn1=Clsn(), clsn2=Clsn()):
        self._init(
            index=index,
            loop=loop,
            clsn1=clsn1,
            clsn2=clsn2,
        )

Anim = namedtuple("Anim", "attrs elmIds")

class Elm(createHolder("Elm", "x y time group index h v alpha clsn1 clsn2".split())):
    def __init__(self, x=0, y=0, time=1, group=-1, index=-1, h=False, v=False, alpha=AlphaBlend.N(),
                 clsn1=Clsn(), clsn2=Clsn()):
        kw = locals()
        kw.pop("self")
        self._init(**kw)
    
    def group_index(self):
        return (self.group(), self.index())
    
    def pos(self):
        return (self.x(), self.y())

class ParsingError(StandardError):
    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line
        msg = "Parsing Error in line {0} of action ('{1}').".format(lineno, line)
        StandardError.__init__(self, msg)

class SectionMissingError(StandardError):
    def __init__(self):
        msg = "action is not found.".format()
        StandardError.__init__(self, msg)

class PasingSectionNameError(StandardError):
    def __init__(self, section_name):
        self.section_name = section_name
        msg = "Invalid section name '{0}'".format(section_name)
        StandardError.__init__(self, msg)

class Air:
    def __init__(self):
        self._anims = OrderedDict()
        self._elms  = OrderedDict()
        
        self._animIdDispatcher = IdDispatcher(repr(self) + "_Anim")
        self._elmIdDispatcher = IdDispatcher(repr(self) + "_Elm")
        
        self._newAnimId = self._animIdDispatcher.new_id
        self._newElmId = self._elmIdDispatcher.new_id
    
    def __copy__(self):
        c = self.__class__()
        c._anims = OrderedDict(self._anims)
        c._elms  = OrderedDict(self._elms)
        return c
    
    @classmethod
    def create(cls):
        """
        return Air instance with 1 anim.
        The anim has 1 element.
        
        >>> a = Air.create()
        >>> len(a.animIds())
        1
        >>> animId = a.animIds()[0]
        >>> len(a.elmIds(animId))
        1
        >>> len(a._elms)
        1
        """
        ins = cls()
        ins.newAnim()
        return ins
    
    @classmethod
    def open(cls, filename):
        # ファイルが見つからない場合、IOErrorを返す可能性がある
        ins = cls()
        for i, a in airlib.open(filename).items():
            ins._addAnimFromAirlib(i, a)
        if not ins.animIds():
            ins.newAnim()
        return ins
    
    def save(self, filename):
        anims = [(animId, self.animById(animId)) for animId in self.animIds()]
        def animIndex(x):
            animId, animAttrs = x
            return animAttrs.index()
        anims.sort(key=animIndex)
        with open(filename, "w") as fp:
            for animId, _ in anims:
                fp.write(self.animToString(animId))
                fp.write("\n\n")
    
    def animById(self, animId):
        if animId in self._anims:
            return self._anims[animId].attrs
        else:
            return None
    
    def elmById(self, elmId):
        return self._elms.get(elmId, None)
    
    def animIds(self):
        return list(self._anims)
    
    def elmIds(self, animId):
        return self._anims[animId].elmIds
    
    def elms(self, animId):
        return map(self.elmById, self.elmIds(animId))
    
    def _addElm(self, elm):
        elmId = self._newElmId()
        self._elms[elmId] = elm
        return elmId
    
    def _addElms(self, elms):
        return [self._addElm(elm) for elm in elms]
    
    def animIdOfElm(self, elmId):
        """
        >>> a = Air.create()
        >>> animId = a.animIds()[0]
        >>> elmId = a.elmIds(animId)[0]
        >>> a.animIdOfElm(elmId) == animId
        True
        >>> a.animIdOfElm("not a elmId") == animId
        False
        """
        for animId, anim in self._anims.iteritems():
            if elmId in anim.elmIds:
                return animId
        return None
    
    def newAnim(self, **kw):
        """
        >>> a = Air.create()
        >>> animId = a.newAnim(index=3)
        >>> a.animById(animId).index()
        3
        """
        elmId = self._newElmId()
        self._elms[elmId] = Elm()
        
        animId = self._newAnimId()
        self._anims[animId] = Anim(AnimAttrs(**kw), (elmId,))
        return animId
    
    def changeAnim(self, animId, **kw):
        """
        >>> a = Air.create()
        >>> animId = a.animIds()[0]
        >>> a.animById(animId).index()
        -1
        >>> a.changeAnim(animId, index=2)
        True
        >>> a.animById(animId).index()
        2
        >>> a.changeAnim(animId, index=2)
        False
        >>> a.animById(animId).index()
        2
        """
        
        elmIds = self.elmIds(animId)
        oldattrs = self._anims[animId].attrs
        newattrs = oldattrs._replace(**kw)
        self._anims[animId] = Anim(newattrs, elmIds)
        return newattrs != oldattrs
    
    def cloneAnim(self, animId):
        """
        >>> a = Air.create()
        >>> animId = a.newAnim(index=3)
        >>> a.animById(animId).index()
        3
        >>> cloneAnimId = a.cloneAnim(animId)
        >>> a.animById(cloneAnimId).index()
        3
        """
        elmIds = self.elmIds(animId)
        animAttrs = self._anims[animId].attrs
        
        cloneElmIds = []
        for elmId in elmIds:
            cloneElmId = self._newElmId()
            self._elms[cloneElmId] = self._elms[elmId]
            cloneElmIds.append(cloneElmId)
        
        cloneAnimId = self._newAnimId()
        self._anims[cloneAnimId] = Anim(animAttrs, tuple(cloneElmIds))
        return cloneAnimId
    
    def removeAnim(self, animId):
        """
        >>> a = Air.create()
        >>> animId = a.newAnim()
        >>> a.animById(animId) is None
        False
        >>> a.removeAnim(animId)
        >>> a.animById(animId) is None
        True
        """
        anim = self._anims.pop(animId)
        for elmId in anim.elmIds:
            del self._elms[elmId]
        
    def changeElm(self, elmId, **kw):
        
        oldElm = self._elms[elmId]
        newElm = oldElm._replace(**kw)
        self._elms[elmId] = newElm
        return oldElm != newElm
    
    def newElm(self, animId, pos, **kw):
        elmId = self._addElm(Elm(**kw))
        
        animAttrs, elmIds = self._anims[animId]
        self._anims[animId] = Anim(animAttrs, inserted(elmIds, pos, elmId))
        return elmId
        
    def copyElm(self, animId, pos, elmId):
        """
            >>> a = Air.create()
            >>> animId = a.animIds()[0]
            >>> elmId = a.elmIds(animId)[0]
            >>> a.changeElm(elmId, group=99)
            True
            >>> _ = a.copyElm(animId, 0, elmId)
            >>> _ = a.copyElm(animId, 0, elmId)
            >>> a.elms(animId)[0].group()
            99
            >>> a.elms(animId)[1].group()
            99
            >>> a.elms(animId)[2].group()
            99
            >>> len(a.elms(animId))
            3
        """
        elmId = self._addElm(self._elms[elmId])
        
        animAttrs, elmIds = self._anims[animId]
        self._anims[animId] = Anim(animAttrs, inserted(elmIds, pos, elmId))
        return elmId
    
    def removeElm(self, animId, elmId):
        """
        >>> a = Air.create()
        >>> animId = a.animIds()[0]
        >>> a.changeElm(a.elmIds(animId)[0], group=0)
        True
        >>> for i in xrange(4):
        ...     _ = a.newElm(animId, len(a.elmIds(animId)), group=i+1)
        ...
        >>> a.changeAnim(animId, loop=4)
        True
        >>> toRemove = a.elmIds(animId)[2]
        >>> a.removeElm(animId, toRemove)
        >>> [e.group() for e in a.elms(animId)]
        [0, 1, 3, 4]
        >>> a.animById(animId).loop() is None
        True
        >>> a.elmById(toRemove)
        >>> a.elmById(toRemove) is None
        True
        """
        
        animAttrs, elmIds = self._anims[animId]
        elmIds1 = removed(elmIds, elmId)
        del self._elms[elmId]
        
        if len(elmIds1) <= animAttrs.loop():
            animAttrs = animAttrs._replace(loop=None)
        self._anims[animId] = Anim(animAttrs, elmIds1)
        
    def moveElm(self, animId, pos, elmId):
        """
        >>> a = Air.create()
        >>> animId = a.animIds()[0]
        >>> for i in xrange(4):
        ...     _ = a.newElm(animId, len(a.elmIds(animId)), group=i, index=2*i+1)
        ...
        >>> [e.group() for e in a.elms(animId)]
        [-1, 0, 1, 2, 3]
        >>> a.moveElm(animId, 0, a.elmIds(animId)[2])
        >>> [e.group() for e in a.elms(animId)]
        [1, -1, 0, 2, 3]
        """
        
        animAttrs, elmIds = self._anims[animId]
        self._anims[animId] = Anim(animAttrs, moved(elmIds, pos, elmId))
    
    def _getAnimFromAirlib(self, i, a):
        elms = []
        for e in a.elem:
            x, y = e.pos
            elms.append(Elm(
                x=x,
                y=y,
                time = e.time,
                group = e.group,
                index = e.index,
                h = e.H,
                v = e.V,
                alpha = AlphaBlend(e.alpha.source, e.alpha.dest, e.alpha.sub),
                clsn1 = Clsn(tuple(c) for c in e.clsn[1]),
                clsn2 = Clsn(tuple(c) for c in e.clsn[2]),
            ))
        animAttrs = AnimAttrs(
            index = i,
            loop = a.loopPos if a.hasLoop else None,
            clsn1 = Clsn(tuple(c) for c in a.clsnDefault[1]),
            clsn2 = Clsn(tuple(c) for c in a.clsnDefault[2]),
        )
        if not elms:
            elms.append(Elm())
        
        return animAttrs, elms
    
    def _addAnimFromAirlib(self, i, a):
        animattrs, elms = self._getAnimFromAirlib(i, a)
        elmIds = self._addElms(elms)
        animId = self._newAnimId()
        self._anims[animId] = Anim(animattrs, tuple(elmIds))
        return animId

    def _animToAirlib(self, animId):
        animAttrs = self.animById(animId)
        a = airlib.Action()
        if animAttrs.loop() is None:
            a.hasLoop = False
        else:
            a.hasLoop = True
            a.loopPos = animAttrs.loop()
        
        for rc in animAttrs.clsn1():
            r = airlib.Rect(rc.left(), rc.top(), rc.width(), rc.height())
            a.clsnDefault[1].append(r)
        for rc in animAttrs.clsn2():
            r = airlib.Rect(rc.left(), rc.top(), rc.width(), rc.height())
            a.clsnDefault[2].append(r)
        
        for elm in self.elms(animId):
            e = airlib.Elem()
            e.pos = (elm.x(), elm.y())
            e.time= elm.time()
            e.group= elm.group()
            e.index= elm.index()
            e.H = elm.h()
            e.V = elm.v()
            e.alpha = airlib.AlphaBlend(
                elm.alpha().source,
                elm.alpha().dest,
                elm.alpha().sub
            )
            for rc in elm.clsn1():
                r = airlib.Rect(rc.left(), rc.top(), rc.width(), rc.height())
                e.clsn[1].append(r)
            for rc in elm.clsn2():
                r = airlib.Rect(rc.left(), rc.top(), rc.width(), rc.height())
                e.clsn[2].append(r)
            a.elem.append(e)
            
        return animAttrs.index(), a
    
    def animToString(self, animId):
        i, a = self._animToAirlib(animId)
        return a.to_string(i)
    
    def _getAnimFromString(self, ss):
        try:
            i, action = airlib.Action.from_string(str(ss))
        except airlib.ParsingError as e:
            raise ParsingError(e.lineno, e.line)
        except airlib.PasingSectionNameError as e:
            raise PasingSectionNameError(e.section_name)
        except airlib.SectionMissingError:
            raise SectionMissingError
        else:
            return self._getAnimFromAirlib(i, action)

    def addAnimFromString(self, ss):
        r'''
        >>> air = Air()
        >>> s = """\
        ... [Begin Action 99]\n\
        ... Clsn2Default:2\n\
        ...   Clsn2[0] = -13,-79,16,0\n\
        ...   Clsn2[1] = -7,-93,5,-79\n\
        ... 0, 0, 0, 0, 10\n\
        ... 0, 1, 0, 0, 7\n\
        ... 0, 2, 0, 0, 7\n\
        ... 0, 3, 0, 0, 7\n\
        ... 0, 4, 0, 0, 7\n\
        ... 0, 5, 0, 0, 45"""
        >>> animId = air.addAnimFromString(s)
        >>> air.animToString(animId) == s
        True
        '''
        animAttrs, elms = self._getAnimFromString(ss)
        elmIds = self._addElms(elms)
        animId = self._newAnimId()
        self._anims[animId] = Anim(animAttrs, tuple(elmIds))
        return animId
    
    def changeAnimFromString(self, animId, ss):
        newAnimAttrs, newElms = self._getAnimFromString(ss)
        
        animAttrs = self.animById(animId)
        elms = self.elms(animId)
        
        assert type(animAttrs) == type(newAnimAttrs)
        assert type(elms[0]) == type(newElms[0])
        
        if newAnimAttrs == animAttrs and elms == newElms:
            return False
        else:
            for elmId in self._anims[animId].elmIds:
                del self._elms[elmId]
            elmIds = self._addElms(newElms)
            self._anims[animId] = Anim(newAnimAttrs, tuple(elmIds))
            return True
        
            
class AirData(QObject):
    filenameChanged = pyqtSignal("PyQt_PyObject")
    def __init__(self):
        QObject.__init__(self)
        self._filename = self._source = None
        self.create()
    
    exec def_qgetter("filename")
    
    @emitSetter
    def setFilename(self):
        pass
        
    def memento(self, *a):
        """
        >>> d = AirData()
        >>> m = d.memento()
        >>> animId = d.animIds()[0]
        >>> d.changeAnim(animId, index=47)
        True
        >>> m = d.memento()
        >>> d.animById(animId).index()
        47
        >>> m = d.memento()
        >>> d.changeAnim(animId, index=68)
        True
        >>> d.animById(animId).index()
        68
        >>> d.restore(m)
        >>> d.animById(animId).index()
        47
        """
        return copy.copy(self._air), self._source
        
    def restore(self, m):
        air, self._source = m
        self._air = copy.copy(air)
    
    def create(self):
        self._air = Air.create()
        self._source = None
        self.setFilename(None)
    
    def open(self, filename):
        self._air = Air.open(filename)
        filename = self._source = filename
        self.setFilename(filename)
        
    def save(self, filename):
        self._air.save(filename)
        filename = self._source = filename
        self.setFilename(filename)
    
    def removeAnim(self, *a, **kw):
        self._air.removeAnim(*a, **kw)
        if not self._air.animIds():
            self.newAnim()
    
    def removeElm(self, animId, *a, **kw):
        self._air.removeElm(animId, *a, **kw)
        if not self._air.elmIds(animId):
            self.newElm(animId, 0)

    def __getattr__(self, name):
        if not name.startswith("_"):
            return getattr(self._air, name)
        else:
            raise AttributeError(name)
    

def main():
    #アニメのテキスト編集で、編集前と内容が変わらなかったら、アンドゥに登録しない
    a = AirData()
    animId, = a.animIds()
    for index in xrange(10):
        a.newElm(
            animId,
            -1,
            index=index,
            clsn1=Clsn((i,i*3,i*5,i*9) for i in xrange(7)),
        )
    a.changeAnim(
        animId,
        loop=5,
        clsn1=Clsn((i,i*3,i*5,i*9)for i in xrange(7))
    )
    
    ss = a.animToString(animId)
    a.changeAnimFromString(animId, ss)
    
##    ss = """
##[begin action 0]
##0,0,0,0,1
##"""
##    assert a.changeAnimFromString(animId, ss)



    
if __name__ == "__main__":
    main()
