# coding: utf-8
from __future__ import division, with_statement, print_function
__metaclass__ = type
from sffairmaker.alpha import AlphaBlend
from enum import Enum
from collections import namedtuple

Title = "SFFAIRMaker2"
IniName = "SFFAIRMaker2.ini"
IniDir  = "%APPDATA%"

AlphaSourceRange = AlphaBlend.SourceRange
AlphaDestRange = AlphaBlend.DestRange

AnimInderange = (-32767, 32767)
ElmTimeRange = (-1, 32767)

ElmGroupRange = SprGroupRange = (-32767, 32767)
ElmInderange = SprInderange = (-32767, 32767)
Sprrange = SprYRange = (-32767, 32767)
Elmrange = ElmYRange = (-32767, 32767)

class ClsnKeys(Enum):
    _1 = "clsn1"
    _2 = "clsn2"
    _1d = "clsn1Default"
    _2d = "clsn2Default"

MaxRecentFiles = 10

PictureFilter = u";;".join([
    u"画像ファイル(*.bmp *.jpg *.jpeg *.jpe *.png *.pcx)",
    u"BMP - Windows Bitmap(*.bmp)",
    u"PCX - Zsoft Paint Brush(*.pcx)",
    u"JPG - JPEG Format(*.jpg *.jpeg *.jpe)",
    u"PNG - Portable Network Graphics(*.png)",
    u"All Files(*.*)",
])

NonPictureExts = ".air .sff .csv .def".split()

SffSaveFilter = "MUGEN SFF File(*.sff);;All File(*.*)"
SffOpenFilter = "MUGEN SFF File(*.sff);;CSV File(*.csv);;All File(*.*)"
CsvSaveFilter = "CSV File(*.csv);;All File(*.*)"

AirOpenFilter = AirSaveFilter = "MUGEN AIR File(*.air);;All File(*.*)"

ActOpenFilter = u";;".join([
    u"パレットに利用可能なファイル(*.act *.bmp *.pcx *.png *.jpg *.jpeg *.jpe)",
    u"ACT - MUGEN Palete(*.act)",
    u"BMP - Windows Bitmap(*.bmp)",
    u"PCX - Zsoft Paint Brush(*.pcx)",
    u"PNG - Portable Network Graphics(*.png)",
    u"JPG - JPEG Format(*.jpg *.jpeg *.jpe)",
    u"All Files(*.*)",
])

ActSaveFilter = u";;".join([
    u"パレットを保存可能なファイル(*.act *.png *.bmp *.pcx)",
    u"ACT - MUGEN Palete(*.act)",
    u"BMP - Windows Bitmap(*.bmp)",
    u"PCX - Zsoft Paint Brush(*.pcx)",
    u"PNG - Portable Network Graphics(*.png)",
    u"All Files(*.*)",
])

ExecutableFilter = u";;".join([
    u"実行ファイル(*.exe)",
    u"All Files(*.*)",
])

GifSaveFilter = u";;".join([
    u"GIF - Graphics Interchange Format(*.gif)",
    u"APNG - Animated Portable Network Graphic(*.apng)",
    u"All Files(*.*)",
])


class CropType(Enum):
    NoCrop = 1
    CropPosBefore = 2
    CropPosAfter = 3

class ImageZOrder(Enum):
    Front = 1
    Back = 2
    Middle = 3

GridOption = namedtuple("GridOption", "imageZOrder axis grid")

MaxCsvNameFormat = 5
DefaultCsvNameFormats = [u"{name}\{group:04}-{index:04}"]

def TitleFormat(type, filename, hasChanged):
    from os.path import abspath, basename
    if filename is None:
        t = u"新規"
    else:
        t = u"{0}: {1}".format(
            basename(filename),
            abspath(filename)
        )
    if hasChanged:
        return u"*" + t
    else:
        return t


ColorTableType = Enum("Sff", "Act", "File", "Spr")

MaxDisplayActMenuLength = 20

from sffairmaker import sfflib

OpeningCsvErrorInfo = namedtuple("OpeningCsvErrorInfo", "lineno type error")
OpeningCsvErrorType = Enum(*"X Y Group Index UseAct Image".split()) 
OpeningSffErrorInfo = sfflib.OpeningErrorInfo


DefaultExternalSprEditingCommand = 'mspaint "%1"'
DefaultExternalAirEditingCommand = 'notepad "%1"'