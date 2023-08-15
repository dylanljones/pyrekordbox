# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import os
import re
from . import structs
from .file import AnlzFile

RE_ANLZ = re.compile("ANLZ[0-9]{4}.(DAT|EXT|2EX)")


def is_anlz_file(path: str) -> bool:
    """Checks if the name of a file matches the ANLZ file name pattern.

    Parameters
    ----------
    path : str
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
    fname = os.path.split(path)[1]
    return bool(RE_ANLZ.match(fname))


def get_anlz_paths(root):
    """Returns the paths of all existing ANLZ files in a directory.

    Parameters
    ----------
    root : str
        The path of the directory containing ANLZ files.

    Returns
    -------
    anlz_paths : dict[str, str]
        The file paths stored as dictionary with the type of ANLZ file as keys
        ("DAT", "EXT", "EX2")

    Examples
    --------
    >>> p = get_anlz_paths("directory/")
    >>> p["DAT"]
    directory/ANLZ0000.DAT
    """
    paths = {"DAT": None, "EXT": None, "2EX": None}
    for fname in os.listdir(root):
        if RE_ANLZ.match(fname):
            ext = os.path.splitext(fname)[1][1:]
            paths[ext] = os.path.join(root, fname)
    return paths


def walk_anlz_dirs(root_dir):
    """Finds all ANLZ directory paths recursively.

    Parameters
    ----------
    root_dir : str
        The path of the root directory.

    Yields
    -------
    anlz_dir : str
        The path of a directory containing ANLZ files
    """
    for root, _, names in os.walk(os.path.normpath(root_dir)):
        for fname in names:
            if is_anlz_file(fname):
                yield root


def walk_anlz_paths(root_dir):
    """Finds all ANLZ directory paths and the containing file paths recursively.

    Parameters
    ----------
    root_dir : str
        The path of the root directory.

    Yields
    -------
    anlz_dir : str
        The path of a directory containing ANLZ files.
    anlz_files : Sequence of str
        The file paths of the ANLZ files in `anlz_dir`.
    """
    print(root_dir)
    assert os.path.exists(root_dir)
    for root, _, names in os.walk(os.path.normpath(root_dir)):
        files = dict()
        print(root)
        for fname in names:
            if is_anlz_file(fname):
                ext = os.path.splitext(fname)[1]
                files[ext[1:].upper()] = os.path.join(root, fname)
        if files:
            yield root, files


def read_anlz_files(root: str = "") -> dict:
    """Open all ANLZ files in the given root directory.

    Parameters
    ----------
    root : str, optional
        The root directory of the ANLZ files to open.

    Returns
    -------
    anlz_files : dict
        The opened ANLZ files stored in a dict with the corresponding file paths
        as keys.
    """
    paths = get_anlz_paths(root)
    return {path: AnlzFile.parse_file(path) for path in paths.values() if path}
