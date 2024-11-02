# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 

import sys
if hasattr(sys, "setdefaultencoding"):
    sys.setdefaultencoding("mbcs")

from sffairmaker.qutil import *
import sffairmaker.model
import sffairmaker.view
import sys
from optparse import OptionParser
from sffairmaker import version
import os.path

class Main:
    def xview(self):
        return sffairmaker.view.View()
    
    def xmodel(self):
        return sffairmaker.model.Model()
    
    def main(self):
        parser = OptionParser(
            usage="%prog [sff-path] [air-path] [act-path]",
            version="%prog " + version.version)
        
        if __debug__:
            parser.add_option(
                "--eval",
                type="string",
                dest="eval",
                metavar="STRING",
                help="JUST FOR DEBUG! evaluate given string",
            )
            
        
        parser.add_option(
            "--tab",
            type="string",
            dest="tab",
            metavar='("SFF"|"AIR")',
            default=None,
            help="active tab when starting",
        )
        
        (opts, args) = parser.parse_args()
        args = [str(f) for f in args]
        
        app = QApplication(sys.argv)
        self.xview().showMainWindow()
        self.xmodel().loadFiles(args)
        
        if opts.tab is not None:
            try:
                self.xview().setCurrentTab(opts.tab.lower())
            except KeyError:
                pass
        
        if __debug__:
            if opts.eval is not None:
                eval(opts.eval)
        
        app.exec_()
        

def main():
    Main().main()
    
if __name__ == "__main__":
    main()
