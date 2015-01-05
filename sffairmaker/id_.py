#encoding:shift-jis
from __future__ import division, with_statement, print_function
__metaclass__ = type

class IdDispatcher:
    def __init__(self, prefix):
        self.count = -1
        self.id_class = self.create_id_class(prefix)
    
    def create_id_class(self, prefix):
        class klass(str):
            def __new__(cls, count):
                s = "{0}_id({1})".format(prefix, count)
                return str.__new__(cls, s)
        klass.__name__ = prefix + "_id"
        return klass
        
    def new_id(self):
        self.count += 1
        return self.id_class(self.count)

def main():
    pass
    
if __name__ == "__main__":
    main()