# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import os
import struct
from typing import List

import numpy as np
import pytest
from numpy.testing import assert_equal

from pyrekordbox import anlz

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
ANLZ_ROOT = os.path.join(TEST_ROOT, "export", "PIONEER", "USBANLZ")
ANLZ_DIRS = list(anlz.walk_anlz_paths(ANLZ_ROOT))
ANLZ_FILES = [paths for _, paths in ANLZ_DIRS]


def _build_file(*tags):
    """Wraps raw tag sections in a minimal ANLZ file header."""
    body = b"".join(tags)
    return b"PMAI" + struct.pack(">II", 28, 28 + len(body)) + bytes(16) + body


def _build_pvb2(entries, total_samples):
    body = b"".join(struct.pack(">QQI", *entry) for entry in entries)
    header = struct.pack(">IQII", 0, total_samples, len(entries), 20)
    return b"PVB2" + struct.pack(">II", 32, 32 + len(body)) + header + body


def _build_vbr_analysis_file(tag_type: str) -> bytes:
    if tag_type == "PVBR":
        tag_content = struct.pack(
            ">I400II",
            0,
            *([0] * 400),
            0,
        )
        tag = (
            struct.pack(
                ">4sII",
                tag_type.encode("ascii"),
                16,
                1620,
            )
            + tag_content
        )
    else:
        tag_content = b"PVDI-test-payload"
        tag = (
            struct.pack(
                ">4sII",
                tag_type.encode("ascii"),
                16,
                12 + len(tag_content),
            )
            + tag_content
        )
    return (
        struct.pack(
            ">4s6I",
            b"PMAI",
            28,
            28 + len(tag),
            0,
            0,
            0,
            0,
        )
        + tag
    )


def _build_pvdi_analysis_file(confidence: List[int]) -> bytes:
    body = bytes(confidence)
    tag = (
        struct.pack(
            ">4sIIIII",
            b"PVDI",
            24,
            24 + len(body),
            0x400,
            0x56220001,
            len(body),
        )
        + body
    )
    return (
        struct.pack(
            ">4s6I",
            b"PMAI",
            28,
            28 + len(tag),
            0,
            0,
            0,
            0,
        )
        + tag
    )


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


def test_pvbr_tag_parse():
    file = anlz.AnlzFile.parse(_build_vbr_analysis_file("PVBR"))
    assert file.tag_types == ["PVBR"]
    tag = file.get_tag("PVBR")
    assert tag.type == "PVBR"
    assert len(tag.get()) == 400
    assert np.all(tag.get() == 0)


@pytest.mark.parametrize("size", [20, 3731])
def test_pvdi_tag_parse(size, caplog):
    confidence = [i % 5 for i in range(size)]
    file = anlz.AnlzFile.parse(_build_pvdi_analysis_file(confidence))
    assert file.tag_types == ["PVDI"]
    tag = file.get_tag("PVDI")
    assert tag.type == "PVDI"
    assert tag.get() == confidence
    assert not caplog.records
    assert file.build() == _build_pvdi_analysis_file(confidence)


def test_pvb2_tag_parse(caplog):
    entries = [(0, 128, 4096), (4096, 8192, 4608), (2**32 + 1, 2**33 + 2, 1024)]
    total_samples = 2**32 + 1025
    data = _build_file(_build_pvb2(entries, total_samples))
    file = anlz.AnlzFile.parse(data)
    assert file.tag_types == ["PVB2"]
    tag = file.get_tag("PVB2")
    assert tag.type == "PVB2"
    assert tag.count == len(entries)
    assert tag.total_samples == total_samples
    samples, offsets, frame_samples = tag.get()
    assert_equal(samples, [0, 4096, 2**32 + 1])
    assert_equal(offsets, [128, 8192, 2**33 + 2])
    assert_equal(frame_samples, [4096, 4608, 1024])
    assert samples.dtype == np.dtype(np.uint64)
    assert offsets.dtype == np.dtype(np.uint64)
    assert frame_samples.dtype == np.dtype(np.uint32)
    assert not caplog.records
    assert file.build() == data


def test_len_and_keys_do_not_recurse():
    # Regression: AnlzFile.__len__ returned len(self.keys()), but keys() comes
    # from the abc.Mapping base and returns a KeysView whose __len__ delegates
    # back to AnlzFile.__len__, so len(file)/list(file.keys()) recursed until
    # RecursionError on any AnlzFile (even an empty one).
    file = anlz.AnlzFile()
    assert len(file) == 0
    assert list(file.keys()) == []


@pytest.mark.parametrize("paths", ANLZ_FILES)
def test_len_matches_distinct_tag_types(paths):
    file = anlz.AnlzFile.parse_file(paths["DAT"])
    assert len(file) == len(list(file.keys()))
    assert len(file) == len(set(file.tag_types))


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


def test_pvb2_tag_getters():
    entries = [(0, 0, 4096), (4096, 8192, 4096), (8192, 15000, 4096)]
    file = anlz.AnlzFile.parse(_build_file(_build_pvb2(entries, 12288)))
    tag = file.get_tag("PVB2")

    assert tag.count == len(entries)
    assert tag.total_samples == 12288

    samples, offsets, frame_samples = tag.get()
    assert_equal(samples, [0, 4096, 8192])
    assert_equal(offsets, [0, 8192, 15000])
    assert_equal(frame_samples, [4096, 4096, 4096])


def test_pvb2_rebuild():
    data = _build_file(_build_pvb2([(0, 0, 4608), (4608, 9000, 4608)], 9216))
    file = anlz.AnlzFile.parse(data)
    assert file.build() == data


def test_rebuild_keeps_unsupported_tags():
    # A tag type pyrekordbox has no struct for must survive a parse/build round trip
    payload = bytes(range(24))
    unknown = b"PZZZ" + struct.pack(">II", 12, 12 + len(payload)) + payload
    data = _build_file(_build_pvb2([(0, 0, 4096)], 4096), unknown)

    file = anlz.AnlzFile.parse(data)
    assert "PZZZ" in file.tag_types
    assert file.get("PZZZ") == payload
    assert file.build() == data
