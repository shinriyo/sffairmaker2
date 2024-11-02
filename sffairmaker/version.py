# coding: utf-8
from __future__ import with_statement, division, print_function

version_info = (2, 0, 0, "beta", 6)
if version_info[3] in ["alpha", "beta", "rc"]:
    c = {"alpha":"a", "beta":"b", "rc":"rc"}[version_info[3]]
    
    version = ".".join(map(str, version_info[:3])) + \
              c + \
              ".".join(map(str, version_info[4:]))
elif version_info[3] == "final":
    version = ".".join(map(str, version_info[:3]))
else:
    assert False

py2exe_version = ".".join(map(str, version_info[:3]))

ascii_name = name = "SFFAIRMaker"
author  = "doloop"
author_email = "doloopwhile@gmail.com"
url = "http://hc8.seikyou.ne.jp/home/doloop/index.html"
description = "Editor for MUGEN SFF and AIR"
download_url = url
license_name = "GPL ver.3"
copyright = "Copyright(C) 2008-2011 doloop All rights reserved."

