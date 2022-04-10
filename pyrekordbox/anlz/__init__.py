# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
import re
from . import structs
from .file import AnlzFile

RE_ANLZ = re.compile("ANLZ[0-9]{4}.(DAT|EXT|2EX)")


def get_anlz_paths(root):
    paths = {"DAT": None, "EXT": None, "2EX": None}
    for fname in os.listdir(root):
        if RE_ANLZ.match(fname):
            ext = os.path.splitext(fname)[1][1:]
            paths[ext] = os.path.join(root, fname)
    return paths


def walk_anlz_dirs(path):
    path = os.path.abspath(path)
    for root, _, names in os.walk(path):
        for fname in names:
            if RE_ANLZ.match(fname):
                yield root


def walk_anlz_paths(path):
    path = os.path.abspath(path)
    for root, _, names in os.walk(path):
        files = dict()
        for fname in names:
            if RE_ANLZ.match(fname):
                ext = os.path.splitext(fname)[1]
                files[ext[1:].upper()] = os.path.join(root, fname)
        if files:
            yield root, files


def read_anlz_files(root=""):
    paths = get_anlz_paths(root)
    return {key: AnlzFile.parse_file(path) for key, path in paths.items()}
