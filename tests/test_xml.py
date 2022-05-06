# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
import pytest
from pyrekordbox import RekordboxXml
from pyrekordbox.xml import Tempo, PositionMark

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
XML5 = os.path.join(TEST_ROOT, "rekordbox 5", "database.xml")
XML6 = os.path.join(TEST_ROOT, "rekordbox 6", "database.xml")


V5_TRACK_INFOS = [
    {
        "TrackID": 1,
        "Name": "NOISE",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "WAV File",
        "Size": 1382226,
        "TotalTime": 5,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-04",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/NOISE.wav",
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 2,
        "Name": "SINEWAVE",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "WAV File",
        "Size": 1515258,
        "TotalTime": 5,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-04",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/SINEWAVE.wav",  # noqa: E501
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 3,
        "Name": "SIREN",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "WAV File",
        "Size": 1941204,
        "TotalTime": 7,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-04",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/SIREN.wav",
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 4,
        "Name": "HORN",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "WAV File",
        "Size": 2010816,
        "TotalTime": 7,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-04",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/HORN.wav",
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 5,
        "Name": "Demo Track 1",
        "Artist": "Loopmasters",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "MP3 File",
        "Size": 6899624,
        "TotalTime": 172,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 128.0,
        "DateAdded": "2022-04-04",
        "BitRate": 320,
        "SampleRate": 44100.0,
        "Comments": "Tracks by www.loopmasters.com",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Demo Tracks/Demo Track 1.mp3",
        "Remixer": "",
        "Tonality": "",
        "Label": "Loopmasters",
        "Mix": "",
    },
    {
        "TrackID": 6,
        "Name": "Demo Track 2",
        "Artist": "Loopmasters",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "MP3 File",
        "Size": 5124342,
        "TotalTime": 128,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 120.0,
        "DateAdded": "2022-04-04",
        "BitRate": 320,
        "SampleRate": 44100.0,
        "Comments": "Tracks by www.loopmasters.com",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Demo Tracks/Demo Track 2.mp3",
        "Remixer": "",
        "Tonality": "",
        "Label": "Loopmasters",
        "Mix": "",
    },
]

V6_TRACK_INFOS = [
    {
        "TrackID": 253529738,
        "Name": "Demo Track 1",
        "Artist": "Loopmasters",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "Mp3-Datei ",
        "Size": 6899624,
        "TotalTime": 172,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 128.0,
        "DateAdded": "2022-04-09",
        "BitRate": 320,
        "SampleRate": 44100.0,
        "Comments": "Tracks by www.loopmasters.com",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Demo Tracks/Demo Track 1.mp3",
        "Remixer": "",
        "Tonality": "Fm",
        "Label": "Loopmasters",
        "Mix": "",
    },
    {
        "TrackID": 17109519,
        "Name": "Demo Track 2",
        "Artist": "Loopmasters",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "Mp3-Datei ",
        "Size": 5124342,
        "TotalTime": 128,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 120.0,
        "DateAdded": "2022-04-09",
        "BitRate": 320,
        "SampleRate": 44100.0,
        "Comments": "Tracks by www.loopmasters.com",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Demo Tracks/Demo Track 2.mp3",
        "Remixer": "",
        "Tonality": "Fm",
        "Label": "Loopmasters",
        "Mix": "",
    },
    {
        "TrackID": 49557014,
        "Name": "HORN",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "Wav-Datei ",
        "Size": 2010816,
        "TotalTime": 7,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-09",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/HORN.wav",
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 209873516,
        "Name": "NOISE",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "Wav-Datei ",
        "Size": 1382226,
        "TotalTime": 5,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-09",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/NOISE.wav",
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 55231398,
        "Name": "SINEWAVE",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "Wav-Datei ",
        "Size": 1515258,
        "TotalTime": 5,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-09",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/SINEWAVE.wav",  # noqa: E501
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
    {
        "TrackID": 92396897,
        "Name": "SIREN",
        "Artist": "",
        "Composer": "",
        "Album": "",
        "Grouping": "",
        "Genre": "",
        "Kind": "Wav-Datei ",
        "Size": 1941204,
        "TotalTime": 7,
        "DiscNumber": 0,
        "TrackNumber": 0,
        "Year": 0,
        "AverageBpm": 0.0,
        "DateAdded": "2022-04-09",
        "BitRate": 2116,
        "SampleRate": 44100.0,
        "Comments": "",
        "PlayCount": 0,
        "Rating": 0,
        "Location": "C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/SIREN.wav",
        "Remixer": "",
        "Tonality": "",
        "Label": "",
        "Mix": "",
    },
]

TEMPOS = [
    [{"Inizio": 0.025, "Bpm": 128.0, "Metro": "4/4", "Battito": 1}],
    [
        {"Inizio": 0.025, "Bpm": 120.0, "Metro": "4/4", "Battito": 1},
        {"Inizio": 48.026, "Bpm": 120.0, "Metro": "4/4", "Battito": 1},
        {"Inizio": 48.525, "Bpm": 120.0, "Metro": "4/4", "Battito": 2},
        {"Inizio": 49.026, "Bpm": 120.0, "Metro": "4/4", "Battito": 3},
        {"Inizio": 49.525, "Bpm": 120.0, "Metro": "4/4", "Battito": 4},
        {"Inizio": 50.026, "Bpm": 120.0, "Metro": "4/4", "Battito": 1},
        {"Inizio": 50.525, "Bpm": 120.0, "Metro": "4/4", "Battito": 2},
        {"Inizio": 51.026, "Bpm": 120.0, "Metro": "4/4", "Battito": 3},
        {"Inizio": 51.525, "Bpm": 120.0, "Metro": "4/4", "Battito": 4},
        {"Inizio": 52.026, "Bpm": 120.0, "Metro": "4/4", "Battito": 1},
    ],
]

POSITION_MARKS = [
    [
        {"Name": "", "Type": "cue", "Start": 0.025, "Num": -1},
        {"Name": "", "Type": "cue", "Start": 15.025, "Num": -1},
        {"Name": "", "Type": "cue", "Start": 30.025, "Num": -1},
        {"Name": "", "Type": "cue", "Start": 45.025, "Num": -1},
    ],
    [
        {"Name": "", "Type": "cue", "Start": 0.025, "Num": -1},
        {"Name": "", "Type": "cue", "Start": 16.025, "Num": -1},
        {"Name": "", "Type": "cue", "Start": 32.025, "Num": -1},
        {"Name": "", "Type": "cue", "Start": 48.026, "Num": -1},
    ],
]


def test_track_attribs_v5():
    xml = RekordboxXml(XML5)

    for i, track in enumerate(xml.get_tracks()):
        for attr in track.ATTRIBS:
            info = V5_TRACK_INFOS[i]
            value = track[attr]
            if attr == "Location":
                assert os.path.normpath(value) == os.path.normpath(info[attr])
            elif attr in info:
                assert value == info[attr]
            else:
                assert value is None


def test_track_attribs_v6():
    xml = RekordboxXml(XML6)

    for i, track in enumerate(xml.get_tracks()):
        for attr in track.ATTRIBS:
            info = V6_TRACK_INFOS[i]
            value = track[attr]
            if attr == "Location":
                assert os.path.normpath(value) == os.path.normpath(info[attr])
            elif attr in info:
                assert value == info[attr]
            else:
                assert value is None


def test_tempos_v5():
    xml = RekordboxXml(XML5)

    for i in range(3):
        track = xml.get_track(i)
        assert len(track.tempos) == 0

    track = xml.get_track(4)
    tempos = TEMPOS[0]
    for info, tempo in zip(tempos, track.tempos):
        for attr in Tempo.ATTRIBS:
            value = tempo[attr]
            if attr in info:
                assert value == info[attr]
            else:
                assert value is None

    track = xml.get_track(5)
    tempos = TEMPOS[1]
    for info, tempo in zip(tempos, track.tempos):
        for attr in Tempo.ATTRIBS:
            value = tempo[attr]
            if attr in info:
                assert value == info[attr]
            else:
                assert value is None


def test_marks_v5():
    xml = RekordboxXml(XML5)

    for i in range(3):
        track = xml.get_track(i)
        assert len(track.tempos) == 0

    track = xml.get_track(4)
    tempos = POSITION_MARKS[0]
    for info, posmark in zip(tempos, track.marks):
        for attr in PositionMark.ATTRIBS:
            value = posmark[attr]
            if attr in info:
                assert value == info[attr]
            else:
                assert value is None

    track = xml.get_track(5)
    tempos = POSITION_MARKS[1]
    for info, posmark in zip(tempos, track.marks):
        for attr in PositionMark.ATTRIBS:
            value = posmark[attr]
            if attr in info:
                assert value == info[attr]
            else:
                assert value is None


def test_add_track():
    xml = RekordboxXml()
    track1 = xml.add_track("C:/path/to/file1.wav")

    raw_location = os.path.normpath(track1._element.attrib["Location"])
    assert track1.TrackID == 1
    assert raw_location == os.path.normpath("file:/localhost/C:/path/to/file1.wav")
    assert track1.Location == os.path.normpath("C:/path/to/file1.wav")

    # test auto-increment of TrackID
    track2 = xml.add_track("C:/path/to/file2.wav")
    assert track2.TrackID == 2

    # test manual TrackID
    track3 = xml.add_track("C:/path/to/file3.wav", TrackID=10)
    assert track3.TrackID == 10

    # test auto-increment after manual TrackID
    track4 = xml.add_track("C:/path/to/file4.wav")
    assert track4.TrackID == 11

    # Location exists
    with pytest.raises(ValueError):
        xml.add_track("C:/path/to/file1.wav")

    # TrackID exists
    with pytest.raises(ValueError):
        xml.add_track("C:/path/to/file_new.wav", TrackID=track1)


def test_update_track_count():
    xml = RekordboxXml()
    track1 = xml.add_track("C:/path/to/file1.wav")
    assert xml.num_tracks == 1

    track2 = xml.add_track("C:/path/to/file2.wav")
    assert xml.num_tracks == 2

    xml.remove_track(track1)
    assert xml.num_tracks == 1

    xml.remove_track(track2)
    assert xml.num_tracks == 0


def test_get_playlist():
    xml = RekordboxXml(XML5)

    playlist = xml.get_playlist("Playlist1")
    assert playlist.is_playlist
    assert not playlist.is_folder

    folder = xml.get_playlist("Folder")
    assert folder.is_folder
    assert not folder.is_playlist

    sub_playlist = xml.get_playlist("Folder", "Sub Playlist")
    assert sub_playlist.is_playlist
    assert not sub_playlist.is_folder

    assert folder.get_playlist("Sub Playlist").name == sub_playlist.name


def test_playlist_entries():
    xml = RekordboxXml(XML5)

    playlist = xml.get_playlist("Playlist1")
    key_type = playlist.key_type
    for key in playlist.get_tracks():
        kwargs = {key_type: key}
        xml.get_track(**kwargs)


def test_add_playlist():
    xml = RekordboxXml()
    playlist = xml.add_playlist("Playlist")

    assert playlist.is_playlist
    assert not playlist.is_folder

    with pytest.raises(ValueError):
        playlist.add_playlist("Sub Playlist")


def test_add_playlist_folder():
    xml = RekordboxXml()
    folder = xml.add_playlist_folder("Folder")

    assert not folder.is_playlist
    assert folder.is_folder

    folder.add_playlist("Sub Playlist")


def test_update_folder_count():
    xml = RekordboxXml()
    folder = xml.add_playlist_folder("Folder")

    folder.add_playlist("P1")
    assert folder.count == 1

    folder.add_playlist_folder("F1")
    assert folder.count == 2

    folder.remove_playlist("P1")
    assert folder.count == 1

    folder.remove_playlist("F1")
    assert folder.count == 0


def test_update_playlist_entries():
    xml = RekordboxXml()
    playlist = xml.add_playlist("Playlist")

    playlist.add_track(0)
    assert playlist.entries == 1

    playlist.add_track(1)
    assert playlist.entries == 2

    playlist.remove_track(1)
    assert playlist.entries == 1

    playlist.remove_track(0)
    assert playlist.entries == 0
