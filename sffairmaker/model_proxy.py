#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from sffairmaker.qutil import *

class Error(StandardError):pass

class Proxy(QObject):
    __slots__ = ("_id", "_submodel")
    def __init__(self, submodel, id):
        QObject.__init__(self)
        self._id = id
        self._submodel = submodel
    
    @property
    def _model(self):
        return self._submodel._model
    
    @property
    def _data(self):
        return self._submodel._data
    
    @property
    def updated(self):
        return self._submodel.updated
    
    def xview(self):
        return self._model.xview()
    
    def _updating(self):
        return self._submodel._updating()
    
    def _notifyUpdate(self):
        return self._submodel._notifyUpdate()
    
    def _subject(self):
        raise NotImplementedError
    
    def isValid(self):
        return self._subject() is not None
    
    exec def_qgetter("id")
    def __eq__(self, other):
        if (not isinstance(other, (Proxy, NullProxy)) or 
            not hasattr(other, "_id")
        ):
            if __debug__:
                print("compareted to {0}".format(other))
                import inspect
                for i in xrange(5):
                    f = inspect.currentframe(i)
                    print("  ", f.f_globals["__file__"], f.f_lineno)
            return False
        
        return self._id == other._id
        
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash(self._id)
    
    def __repr__(self):
        return "<{0} of {1}>".format(self.__class__.__name__, self._id)
    
    def __getattr__(self, name):
        subject = self._subject()
        if subject is None:
            raise Error("subject does not exist", self._id)
        if name in subject._fields:
            return getattr(subject, name)
        else:
            return getattr(self._model, name)


class NullSignal:
    def connect(self, *a, **kw): pass
    def disconnect(self, *a, **kw): pass
    def emit(self, *a, **kw): pass


class NullProxy:
    __slots__ = ("_id",)
    _id = None
    
    @property
    def updated(self):
        return NullSignal()
        
    def isValid(self):
        return False
    
    def __hash__(self):
        return 0
    
    def __repr__(self):
        return "Null()"
    
    def __getattr__(self, name):
        raise Error("this Proxy is Null")
    

def main():
    Proxy(None, None)
    

if "__main__" == __name__:
    main()