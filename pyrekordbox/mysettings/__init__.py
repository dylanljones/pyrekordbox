# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import re
from pathlib import Path
from typing import List, Union

from . import structs
from .file import (
    FILES,
    DevSettingFile,
    DjmMySettingFile,
    MySetting2File,
    MySettingFile,
    SettingsFile,
)

RE_MYSETTING = re.compile(".*SETTING[0-9]?.DAT$")


def get_mysetting_paths(root: Union[str, Path], deep: bool = False) -> List[Path]:
    files = list()
    root = Path(root)
    iteator = root.rglob("*") if deep else root.iterdir()
    for path in iteator:
        if path.is_file() and RE_MYSETTING.match(path.name):
            files.append(path)
    return files


def read_mysetting_file(path: Union[str, Path]) -> SettingsFile:
    obj = FILES[str(Path(path).name)]
    return obj.parse_file(path)
