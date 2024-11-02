#encoding:shift-jis
from setuptools import setup
import py2exe
import sys
from sffairmaker import version


try:
    # if this doesn't work, try import modulefinder
    import py2exe.mf as modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass

manifest = open("sffairmaker.exe.manifest").read()

import iterutils
requires = '''
    PIL.Image
    PIL.PcxImagePlugin
    PIL.JpegImagePlugin
    PIL.PngImagePlugin
    PIL.BmpImagePlugin
    
    PyQt4.QtCore
    PyQt4.QtGui
    enum
    mm
    sip
    win32com.shell
    win32con
    win32event
    win32file
'''.split()

excludes = '''
    pyreadline
'''.split()

py2exe_options = dict(
    compressed = True,
    optimize = 2,
    includes = requires,
    excludes = excludes,
    dll_excludes= "mswsock.dll powrprof.dll".split(),
    packages = [],
    bundle_files = 2,
)

kw = {}
for k in "author author_email url download_url description".split():
    kw[k] = getattr(version, k)

kw.update(
    name="sffairmaker",
    version=version.py2exe_version
)

setup(
    options = {'py2exe': py2exe_options},
    windows = [dict(
        script = 'sffairmaker/main.py',
        icon_resources  = [],
        other_resources = [(24, 1, manifest)],
    )],
    packages = ["sffairmaker"],
    py_modules = [],
    data_files = [],
    requires=requires,
    zipfile = None,
    test_suite="nose.collector",
    **kw
)

