# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import re
from pathlib import Path
from typing import Dict, Iterator, Tuple, Union

from . import structs
from .file import AnlzFile

RE_ANLZ = re.compile("ANLZ[0-9]{4}.(DAT|EXT|2EX)")


def is_anlz_file(path: Union[str, Path]) -> bool:
    """Checks if the name of a file matches the ANLZ file name pattern.

    Parameters
    ----------
    path : str or Path
        The file path to check

    Returns
    -------
    is_anlz : bool
        True if the file is an ANLZ file.

    Examples
    --------
    >>> is_anlz_file("ANLZ0000.DAT")
    True

    >>> is_anlz_file("/path/to/ANLZ0000.DAT")
    False

    >>> is_anlz_file("ANLZ.DAT")
    False
    """
    path = Path(path)
    if not path.exists() or not path.is_file():
        return False
    return bool(RE_ANLZ.match(path.name))


def get_anlz_paths(root: Union[str, Path]) -> Dict[str, Union[Path, None]]:
    """Returns the paths of all existing ANLZ files in a directory.

    Parameters
    ----------
    root : str or Path
        The path of the directory containing ANLZ files.

    Returns
    -------
    anlz_paths : dict[str, Path]
        The file paths stored as dictionary with the type of ANLZ file as keys
        ("DAT", "EXT", "EX2")

    Examples
    --------
    >>> p = get_anlz_paths("directory/")
    >>> p["DAT"]
    directory/ANLZ0000.DAT
    """
    paths: Dict[str, Union[Path, None]] = {"DAT": None, "EXT": None, "2EX": None}
    for path in Path(root).iterdir():
        if RE_ANLZ.match(path.name):
            paths[path.suffix[1:].upper()] = path
    return paths


def walk_anlz_dirs(root_dir: Union[str, Path]) -> Iterator[Path]:
    """Finds all ANLZ directory paths recursively.

    Parameters
    ----------
    root_dir : str or Path
        The path of the root directory.

    Yields
    ------
    anlz_dir : str
        The path of a directory containing ANLZ files
    """
    for path in Path(root_dir).rglob("*"):
        if path.is_dir():
            if any(is_anlz_file(f) for f in path.iterdir()):
                yield path


def walk_anlz_paths(root_dir: Union[str, Path]) -> Iterator[Tuple[Path, Dict[str, Path]]]:
    """Finds all ANLZ directory paths and the containing file paths recursively.

    Parameters
    ----------
    root_dir : str or Path
        The path of the root directory.

    Yields
    ------
    anlz_dir : str
        The path of a directory containing ANLZ files.
    anlz_files : Sequence of str
        The file paths of the ANLZ files in `anlz_dir`.
    """
    root_dir = Path(root_dir)
    assert root_dir.exists()
    for anlz_dir in walk_anlz_dirs(root_dir):
        files = {k: path for k, path in get_anlz_paths(anlz_dir).items() if path}
        yield anlz_dir, files


def read_anlz_files(root: Union[str, Path] = "") -> Dict[Path, AnlzFile]:
    """Open all ANLZ files in the given root directory.

    Parameters
    ----------
    root : str or Path, optional
        The root directory of the ANLZ files to open.

    Returns
    -------
    anlz_files : dict
        The opened ANLZ files stored in a dict with the corresponding file paths
        as keys.
    """
    paths = get_anlz_paths(root)
    return {path: AnlzFile.parse_file(path) for path in paths.values() if path}
