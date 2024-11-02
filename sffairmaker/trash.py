# coding: utf-8
# MacおよびLinux用のモジュール
import sys
from send2trash import send2trash

if sys.platform == "win32":
    # Windows用のモジュール
    from win32com.shell import shell
    from win32com.shell.shellcon import FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_SILENT, FO_DELETE

def trash(path, dlg=False):
    path = os.path.abspath(path)
    
    if sys.platform == "win32":
        # Windows用処理
        path = path.replace("/", "\\")
        
        # `\` で終わっていると削除できないので、不要なバックスラッシュを削除
        for i, c in enumerate(reversed(path)):
            if c != "\\":
                if i > 0:
                    path = path[:-i]
                break
        
        if not dlg:
            Flags = FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_SILENT
        else:
            Flags = FOF_NOCONFIRMATION | FOF_ALLOWUNDO

        s = (
            0,  # hwnd
            FO_DELETE,  # operation
            path,
            "",  # unused
            Flags
        )
        shell.SHFileOperation(s)

    else:
        # MacおよびLinux用処理
        send2trash(path)
    

def main():
    import doctest
    doctest.testmod()

if "__main__" == __name__:
    main()