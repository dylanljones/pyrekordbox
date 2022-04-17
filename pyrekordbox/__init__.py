# coding: utf-8
#
# This code is part of rekordtools.
#
# Copyright (c) 2022, Dylan Jones

from .logger import logger
from .config import show_config, get_config
from .xml import RekordboxXml
from .anlz import get_anlz_paths, walk_anlz_paths, read_anlz_files, AnlzFile
from .mysettings import (
    get_mysetting_paths,
    read_mysetting_file,
    MySettingFile,
    MySetting2File,
    DjmMySettingFile,
    DevSettingFile,
)
from .db6 import Rekordbox6Database, open_rekordbox_database

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
