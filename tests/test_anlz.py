# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
from pyrekordbox import anlz

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
ANLZ_ROOT = os.path.join(TEST_ROOT, "exports", "demo_tracks", "PIONEER", "USBANLZ")

ANLZ_ROOT1 = os.path.join(ANLZ_ROOT, "P016", "0000875E")
ANLZ_ROOT2 = os.path.join(ANLZ_ROOT, "P053", "0001D21F")


def test_parse():
    for root, files in anlz.walk_anlz_paths(ANLZ_ROOT):
        for path in files.values():
            anlz.AnlzFile.parse_file(path)


def test_rebuild():
    for root, files in anlz.walk_anlz_paths(ANLZ_ROOT):
        for path in files.values():
            file = anlz.AnlzFile.parse_file(path)
            data = file.build()
            assert len(data) == file.file_header.len_file
            _ = anlz.AnlzFile.parse(data)
