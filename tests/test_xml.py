# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
from pyrekordbox import RekordboxXml
from pyrekordbox.xml import encode_path, decode_path
import pytest


TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")


@pytest.mark.parametrize(
    "path,expected",
    [
        (
            r"C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3",
            "file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3",
        ),
        (
            r"C:\Music\PioneerDJ\Demo Tracks\Demo Track 2.mp3",
            "file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%202.mp3",
        ),
    ],
)
def test_encode_path(path, expected):
    assert encode_path(path) == expected


@pytest.mark.parametrize(
    "s,expected",
    [
        (
            "file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3",
            r"C:/Music/PioneerDJ/Demo Tracks/Demo Track 1.mp3",
        ),
        (
            "file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%202.mp3",
            r"C:/Music/PioneerDJ/Demo Tracks/Demo Track 2.mp3",
        ),
    ],
)
def test_decode_path(s, expected):
    assert decode_path(s) == os.path.normpath(expected)


def test_parse_xml_tracks_v5():
    path = os.path.join(TEST_ROOT, "rekordbox 5", "database.xml")
    xml = RekordboxXml(path)
    assert os.path.exists(path)

    assert xml.num_tracks == 6

    track = xml.get_track(1)
    assert track.Name == "NOISE"
    assert len(track.tempos) == 0
    assert len(track.marks) == 0

    track = xml.get_track(5)

    tempo = track.tempos[0]
    assert tempo.Bpm == 128.0
    assert tempo.Inizio == 0.025
    assert tempo.Metro == "4/4"
    assert tempo.Battito == 1

    positions = track.marks
    assert len(positions) == 4
    assert positions[0].Name == ""
    assert positions[0].Type == "cue"
    assert positions[0].Start == 0.025
    assert positions[0].Num == -1
