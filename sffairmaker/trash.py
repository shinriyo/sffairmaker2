# coding: utf-8
from __future__ import division, print_function
__metaclass__ = type 
import os
from win32com.shell import shell
from win32com.shell.shellcon import FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_SILENT, FO_DELETE

def trash(path , dlg=False):
    path = os.path.abspath(path)
    path = unicode(path)
    #��؂蕶���̓o�b�N�X���b�V��
    path = path.replace("/", "\\")
    
    #\�ŏI����Ă���ƍ폜�ł��Ȃ�
    for i,c in enumerate(reversed(path)):
        if c != u"\\":
            if i==0:
                pass
            else:
                path = path[0:-i]
            break
    if not dlg:
        Flags = FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_SILENT
    else:
        Flags = FOF_NOCONFIRMATION | FOF_ALLOWUNDO# �t���O
    
    s = (
        0, # hwnd,
        FO_DELETE, #operation
        path,
        u"",
        Flags
    )
    shell.SHFileOperation(s)
    

def main():
    import doctest
    doctest.testmod()

if "__main__" == __name__:
    main()