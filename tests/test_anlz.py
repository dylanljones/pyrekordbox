# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import os

import numpy as np
import pytest
from numpy.testing import assert_equal

from pyrekordbox import anlz

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
ANLZ_ROOT = os.path.join(TEST_ROOT, "export", "PIONEER", "USBANLZ")
ANLZ_DIRS = list(anlz.walk_anlz_paths(ANLZ_ROOT))
ANLZ_FILES = [paths for _, paths in ANLZ_DIRS]


def test_parse():
    for root, files in ANLZ_DIRS:
        for path in files.values():
            anlz.AnlzFile.parse_file(path)


def test_rebuild():
    for root, files in ANLZ_DIRS:
        for path in files.values():
            file = anlz.AnlzFile.parse_file(path)
            data = file.build()
            assert len(data) == file.file_header.len_file
            _ = anlz.AnlzFile.parse(data)


def test_read_anlz_files():
    for root, files in ANLZ_DIRS:
        anlz_files = anlz.read_anlz_files(root)
        assert len(files) == len(anlz_files)


# -- Tags ------------------------------------------------------------------------------


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_pqtz_tag_getters(paths):
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PQTZ")
    beats, bpms, times = tag.get()
    nbeats = len(beats)
    # Check that shape of arrays are equal
    assert nbeats == len(bpms)
    assert nbeats == len(times)
    # Check that the beats array only contains the values 1-4
    if nbeats:
        assert_equal(np.sort(np.unique(beats)), [1, 2, 3, 4])

    # Check other getters
    assert_equal(beats, tag.get_beats())
    assert_equal(bpms, tag.get_bpms())
    assert_equal(times, tag.get_times())


def test_pqtz_tag_set_beats():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PQTZ")

    beats = np.ones(tag.count)
    tag.set_beats(beats)
    assert_equal(tag.get_beats(), beats)


def test_pqtz_tag_set_bpms():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PQTZ")

    bpms = 100 * np.ones(tag.count, dtype=np.float64)
    tag.set_bpms(bpms)
    assert_equal(tag.get_bpms(), bpms)


def test_pqtz_tag_set_times():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PQTZ")

    times = 0.5 * np.arange(tag.count)
    tag.set_times(times)
    assert_equal(tag.get_times(), times)


def test_pqtz_tag_set():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PQTZ")

    beats = np.ones(tag.count)
    bpms = 100 * np.ones(tag.count, dtype=np.float64)
    times = 0.5 * np.arange(tag.count)
    tag.set(beats, bpms, times)
    assert_equal(tag.get_bpms(), bpms)
    assert_equal(tag.get_bpms(), bpms)
    assert_equal(tag.get_times(), times)


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_ppth_tag_getters(paths):
    tmp = ""
    for path in paths.values():
        file = anlz.AnlzFile.parse_file(path)
        tag = file.get_tag("PPTH")
        p = tag.get()
        if not tmp:
            tmp = p
        else:
            assert tmp == p


def test_ppth_tag_setters():
    paths = ANLZ_FILES[0]
    extected = r"C:/new/path/to/file.mp3"
    for path in paths.values():
        file = anlz.AnlzFile.parse_file(path)
        tag = file.get_tag("PPTH")
        tag.set(r"C:\new\path\to\file.mp3")
        assert tag.get() == extected


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_pwav_tag_getters(paths):
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PWAV")

    heights, color = tag.get()
    assert len(heights) == len(color)
    assert np.all(np.logical_and(0 <= heights, heights <= 31))
    assert np.all(np.logical_and(0 <= color, color <= 7))


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_pwv2_tag_getters(paths):
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    tag = file.get_tag("PWV2")

    heights, color = tag.get()
    assert len(heights) == len(color)
    assert np.all(np.logical_and(0 <= heights, heights <= 31))
    assert np.all(np.logical_and(0 <= color, color <= 7))


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_pwv3_tag_getters(paths):
    file = anlz.AnlzFile.parse_file(paths["EXT"])
    tag = file.get_tag("PWV3")

    heights, color = tag.get()
    assert len(heights) == len(color)
    assert np.all(np.logical_and(0 <= heights, heights <= 31))
    assert np.all(np.logical_and(0 <= color, color <= 7))


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_pwv4_tag_getters(paths):
    file = anlz.AnlzFile.parse_file(paths["EXT"])
    tag = file.get_tag("PWV4")

    heights, colors, blues = tag.get()
    assert len(heights) == len(colors)
    assert len(heights) == len(blues)


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_pwv5_tag_getters(paths):
    file = anlz.AnlzFile.parse_file(paths["EXT"])
    tag = file.get_tag("PWV5")

    heights, colors = tag.get()
    assert len(heights) == colors.shape[0]


# -- File ------------------------------------------------------------------------------


def test_anlzfile_getall_tags():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    key = "PPTH"
    tags = file.getall_tags(key)
    assert len(tags) == 1
    assert tags[0].get() == file.get(key)


def test_anlzfile_get():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    key = "PPTH"
    tag = file.get_tag(key)
    assert file.get(key) == tag.get()


def test_anlzfile_getall():
    paths = ANLZ_FILES[0]
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    key = "PPTH"
    tag = file.get_tag(key)
    values = file.getall(key)
    assert len(values) == 1
    assert values[0] == tag.get()
