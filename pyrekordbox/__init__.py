# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

# mypy: disable-error-code="attr-defined"
from .anlz import AnlzFile, get_anlz_paths, read_anlz_files, walk_anlz_paths
from .config import get_config, show_config, update_config
from .db6 import Rekordbox6Database
from .logger import logger
from .mysettings import (
    DevSettingFile,
    DjmMySettingFile,
    MySetting2File,
    MySettingFile,
    get_mysetting_paths,
    read_mysetting_file,
)
from .rbxml import RekordboxXml, XmlAttributeKeyError, XmlDuplicateError

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "unknown"
