# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
from pyrekordbox import RekordboxXml

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
XML = os.path.join(TEST_ROOT, "xml")


def test_parse_xml_tracks():
    path = os.path.join(XML, "demo_tracks", "database.xml")
    xml = RekordboxXml(path)

    assert xml.num_tracks == 6

    track = xml.get_track(1)
    assert track.name == "NOISE"
    assert len(track.tempos) == 0
    assert len(track.cue_points()) == 0

    track = xml.get_track(5)

    tempo = track.tempos[0]
    assert tempo.bpm == 128.0
    assert tempo.inizio == 0.025
    assert tempo.metro == "4/4"
    assert tempo.battito == 1

    positions = track.cue_points()
    assert len(positions) == 4
    assert positions[0].name == ""
    assert positions[0].type == 0
    assert positions[0].start == 0.025
    assert positions[0].num == -1
