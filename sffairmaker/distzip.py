#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type 
from zipfile import ZipFile

from allfiles import allfiles
from contextlib import closing
from os.path import *
from sffairmaker import version
from datetime import date, datetime
import re
import shutil
import sys

def main():
    with open("readme.txt") as fp:
        for line in fp:
            if line.startswith(":Date:"):
                d = datetime.strptime(line[6:].strip(), "%Y/%m/%d").date()
                assert d == date.today()
            if line.startswith(":Version:"):
                m = re.match(":Version: *(?P<ver>[\d\.]+) *Beta *(?P<aver>\d+)", line, re.I)
                assert m
                assert version.py2exe_version == m.group("ver")
                assert version.version_info[4] == int(m.group("aver"))
    
    with closing(ZipFile("sffairmaker2.zip", "w")) as z:
        z.write("dist/main.exe", "sffairmaker.exe")
        sdist_path = "dist/sffairmaker-{0[0]}.{0[1]}.{0[2]}.zip".format(version.version_info)
        z.write(sdist_path, "src.zip")
        
        for name in ["python{0[0]}{0[1]}.dll".format(sys.version_info)]:
            z.write("dist/" + name, name)
        
        files = [u"readme.txt"]
        files.extend(allfiles(u"docs", "*.txt"))
        for f in files:
            f = f.encode("mbcs")
            z.write(f, basename(f))
    
    shutil.copy(
        "sffairmaker2.zip",
        "old/sffairmaker" + version.version + ".zip",
    )
    
    
    
if "__main__" == __name__:
    main()