# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pytest import mark
from sqlalchemy import text
from sqlalchemy.orm.query import Query

from pyrekordbox import Rekordbox6Database
from pyrekordbox.db6 import tables
from pyrekordbox.db6.smartlist import LogicalOperator, Operator, Property, SmartList
from pyrekordbox.db6.tables import datetime_to_str, string_to_datetime

TEST_ROOT = Path(__file__).parent.parent / ".testdata"
LOCKED = TEST_ROOT / "rekordbox 6" / "master_locked.db"
UNLOCKED = TEST_ROOT / "rekordbox 6" / "master_unlocked.db"
UNLOCKED_COPY = TEST_ROOT / "rekordbox 6" / "master_unlocked_copy.db"
UNLOCKED_OUT = TEST_ROOT / "rekordbox 6" / "master_unlocked_out.db"
MASTER_PLAYLIST_SRC = TEST_ROOT / "rekordbox 6" / "masterPlaylists6_template.xml"
MASTER_PLAYLIST_DST = TEST_ROOT / "rekordbox 6" / "masterPlaylists6.xml"
# Create a copy of the masterPlaylists6.xml file
shutil.copy(MASTER_PLAYLIST_SRC, MASTER_PLAYLIST_DST)

DB = Rekordbox6Database(UNLOCKED, unlock=False)

# Content IDs
CID1 = 178162577  # Demo Track 1
CID2 = 66382436  # Demo Track 2
CID3 = 181094952  # HORN
CID4 = 24401986  # NOISE

# Playlist ID
PID1 = 2602250856  # Trial playlist - Cloud Library Sync


@pytest.fixture
def db():
    """Return a clean Rekordbox v6 database instance and close it after tests."""
    shutil.copy(UNLOCKED, UNLOCKED_COPY)
    shutil.copy(MASTER_PLAYLIST_SRC, MASTER_PLAYLIST_DST)
    db = Rekordbox6Database(UNLOCKED_COPY, unlock=False)
    yield db
    db.close()


def test_open_rekordbox_database():
    db = Rekordbox6Database(UNLOCKED, unlock=False)
    db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    db.close()


def test_unlock_rekordbox_database():
    db = Rekordbox6Database(LOCKED, unlock=True)
    db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    db.close()


def test_close_open():
    db = Rekordbox6Database(UNLOCKED, unlock=False)
    db.close()
    db.open()
    _ = db.get_content()[0]  # Try to query the database
    db.close()


@mark.parametrize("dt", [datetime.now(), datetime.now(tz=timezone.utc)])
def test_datetime_to_string(dt):
    datetime_to_str(dt)


@mark.parametrize(
    "s",
    [
        "2025-04-12 19:11:29.274 +00:00",
        "2025-04-12 19:11:29.274 +01:00",
        "2025-04-12 19:11:29.274 -01:00",
        "2025-04-12 19:11:29.274 -05:00 (Central Daylight Time)",
    ],
)
def test_string_to_datetime(s):
    dt = string_to_datetime(s)
    # make sure no timezone is present
    assert dt.tzinfo is None


@mark.parametrize(
    "name,cls",
    [
        ("get_active_censor", tables.DjmdActiveCensor),
        ("get_album", tables.DjmdAlbum),
        ("get_artist", tables.DjmdArtist),
        ("get_category", tables.DjmdCategory),
        ("get_color", tables.DjmdColor),
        ("get_content", tables.DjmdContent),
        ("get_cue", tables.DjmdCue),
        ("get_device", tables.DjmdDevice),
        ("get_genre", tables.DjmdGenre),
        ("get_history", tables.DjmdHistory),
        ("get_hot_cue_banklist", tables.DjmdHotCueBanklist),
        ("get_key", tables.DjmdKey),
        ("get_label", tables.DjmdLabel),
        ("get_menu_items", tables.DjmdMenuItems),
        ("get_mixer_param", tables.DjmdMixerParam),
        ("get_my_tag", tables.DjmdMyTag),
        ("get_playlist", tables.DjmdPlaylist),
        ("get_property", tables.DjmdProperty),
        ("get_related_tracks", tables.DjmdRelatedTracks),
        ("get_sampler", tables.DjmdSampler),
        ("get_sort", tables.DjmdSort),
        ("get_agent_registry", tables.AgentRegistry),
        ("get_cloud_agent_registry", tables.CloudAgentRegistry),
        ("get_content_active_censor", tables.ContentActiveCensor),
        ("get_content_cue", tables.ContentCue),
        ("get_content_file", tables.ContentFile),
        ("get_hot_cue_banklist_cue", tables.HotCueBanklistCue),
        ("get_image_file", tables.ImageFile),
        ("get_setting_file", tables.SettingFile),
        ("get_uuid_map", tables.UuidIDMap),
    ],
)
def test_getter(name, cls):
    getter = getattr(DB, name)
    # Test return is query
    query = getter()
    assert isinstance(query, Query)
    assert query.column_descriptions[0]["type"] == cls

    # Test type of query result is the right table class
    res = query.first()
    assert res is None or isinstance(res, cls)


@mark.parametrize(
    "name,cls",
    [
        ("get_active_censor", tables.DjmdActiveCensor),
        ("get_album", tables.DjmdAlbum),
        ("get_artist", tables.DjmdArtist),
        ("get_category", tables.DjmdCategory),
        ("get_color", tables.DjmdColor),
        ("get_content", tables.DjmdContent),
        ("get_cue", tables.DjmdCue),
        ("get_device", tables.DjmdDevice),
        ("get_genre", tables.DjmdGenre),
        ("get_history", tables.DjmdHistory),
        ("get_hot_cue_banklist", tables.DjmdHotCueBanklist),
        ("get_key", tables.DjmdKey),
        ("get_label", tables.DjmdLabel),
        ("get_menu_items", tables.DjmdMenuItems),
        ("get_mixer_param", tables.DjmdMixerParam),
        ("get_my_tag", tables.DjmdMyTag),
        ("get_playlist", tables.DjmdPlaylist),
        # ("get_property", tables.DjmdProperty),
        ("get_related_tracks", tables.DjmdRelatedTracks),
        ("get_sampler", tables.DjmdSampler),
        ("get_sort", tables.DjmdSort),
        # ("get_agent_registry", tables.AgentRegistry),
        ("get_cloud_agent_registry", tables.CloudAgentRegistry),
        ("get_content_active_censor", tables.ContentActiveCensor),
        ("get_content_cue", tables.ContentCue),
        ("get_content_file", tables.ContentFile),
        ("get_hot_cue_banklist_cue", tables.HotCueBanklistCue),
        ("get_image_file", tables.ImageFile),
        ("get_setting_file", tables.SettingFile),
        ("get_uuid_map", tables.UuidIDMap),
    ],
)
def test_getter_by_id(name, cls):
    # Get method from class
    getter = getattr(DB, name)

    # Try to get a valid ID
    item = getter().first()
    if item is None:
        return
    id_ = item.ID

    # Test type of result is a table class, not the query
    res = getter(ID=id_)
    assert res is None or isinstance(res, cls)


@mark.parametrize(
    "parent_name,key,cls",
    [
        ("get_history", "HistoryID", tables.DjmdSongHistory),
        ("get_hot_cue_banklist", "HotCueBanklistID", tables.DjmdSongHotCueBanklist),
        ("get_my_tag", "MyTagID", tables.DjmdSongMyTag),
        ("get_playlist", "PlaylistID", tables.DjmdSongPlaylist),
        ("get_related_tracks", "RelatedTracksID", tables.DjmdSongPlaylist),
        ("get_sampler", "SamplerID", tables.DjmdSongPlaylist),
    ],
)
def test_songs_getters(parent_name, key, cls):
    # Get list (containing songs) getter
    getter = getattr(DB, parent_name)
    # Try to get a valid list ID
    query = getter()
    if not query.count():
        return  # No data to check...

    item = query.first()
    id_ = item.ID

    # Get list songs getter
    getter = getattr(DB, f"{parent_name}_songs")
    # Get song items
    query = getter(**{key: id_})
    if not query.count():
        return  # No data to check...

    assert isinstance(query.first(), cls)


def test_mixer_gain_setters(db):
    for item in db.get_mixer_param():
        # Check Gain setter
        low, high, value = int(item.GainLow), int(item.GainHigh), item.Gain
        item.Gain = value
        db.flush()
        assert item.GainLow == low
        assert item.GainHigh == high

        # Check Peak setter
        low, high, value = int(item.PeakLow), int(item.PeakHigh), item.Peak
        item.Peak = value
        db.flush()
        assert item.PeakLow == low
        assert item.PeakHigh == high


@mark.parametrize(
    "search,ids",
    [
        ("Demo Track 1", [CID1]),  # Title
        ("Demo Track 2", [CID2]),  # Title
        ("Loopmasters", [CID1, CID2]),  # Label/Artist Name
        ("Noise", [CID4]),  # lowercase
        ("NOIS", [CID4]),  # incomplete
    ],
)
def test_search_content(search, ids):
    results = DB.search_content(search)
    for id_, res in zip(ids, results):
        assert int(res.ID) == id_


def test_increment_local_usn(db):
    old = db.get_local_usn()
    db.increment_local_usn()
    assert db.get_local_usn() == old + 1

    db.increment_local_usn(1)
    assert db.get_local_usn() == old + 2

    db.increment_local_usn(2)
    assert db.get_local_usn() == old + 4

    with pytest.raises(ValueError):
        db.increment_local_usn(0)

    with pytest.raises(ValueError):
        db.increment_local_usn(-1)


def test_autoincrement_local_usn(db):
    old_usn = db.get_local_usn()  # store USN before changes
    track1 = db.get_content(ID=CID1)
    track2 = db.get_content(ID=CID2)
    track3 = db.get_content(ID=CID3)
    playlist = db.get_playlist(ID=PID1)
    with db.session.no_autoflush:
        # Change one field in first track (+1)
        track1.Title = "New title 1"
        # Change two fields in second track (+2)
        track2.Title = "New title 2"
        track2.BPM = 12900
        # Delete row from table )+1)
        db.delete(track3)
        # Change name of playlist (+1)
        playlist.Name = "New name"

        # Auto-increment USN
        new_usn = db.autoincrement_usn()

    # Check local Rekordbox USN and instance USN's
    assert new_usn == old_usn + 5
    assert track1.rb_local_usn == old_usn + 1
    assert track2.rb_local_usn == old_usn + 3
    # USN of deleted rows obviously don't get updated
    assert playlist.rb_local_usn == new_usn


def _check_playlist_xml(db):
    # Check that playlist is in XML and update time is correct
    for pl in db.get_playlist():
        plxml = db.playlist_xml.get(pl.ID)
        ts = plxml["Timestamp"]
        diff = pl.updated_at - ts
        if abs(diff.total_seconds()) > 1:
            return False
    return True


def _check_playlist_xml_delete(db):
    # Check that there are no items in the XML that are not in the db
    for plxml in db.playlist_xml.get_playlists():
        if plxml["Lib_Type"] != 0:
            continue
        pid = int(plxml["Id"], 16)
        if db.query(tables.DjmdPlaylist).filter_by(ID=pid).count() != 1:
            return False
    return True


def test_add_song_to_playlist(db):
    usn_old = db.get_local_usn()
    mtime_old = db.get_playlist(ID=PID1).updated_at

    # test adding song to playlist
    song = db.add_to_playlist(PID1, CID1)
    db.commit()

    pl = db.get_playlist(ID=PID1)
    assert len(pl.Songs) == 1
    assert pl.Songs[0].ContentID == str(CID1)
    assert song.TrackNo == 1

    # Test USN and update time are correct
    assert pl.updated_at == mtime_old
    assert song.rb_local_usn == usn_old + 1
    assert db.get_local_usn() == usn_old + 1

    # test raising error when adding song to playlist with wrong TrackNo
    with pytest.raises(ValueError):
        db.add_to_playlist(PID1, CID2, track_no=0)
    with pytest.raises(ValueError):
        db.add_to_playlist(PID1, CID2, track_no=3)

    assert _check_playlist_xml(db)


def test_add_song_to_playlist_trackno_end(db):
    old_usn = db.get_local_usn()
    song1 = db.add_to_playlist(PID1, CID1)
    song2 = db.add_to_playlist(PID1, CID2)
    song3 = db.add_to_playlist(PID1, CID3)
    db.commit()
    assert song1.TrackNo == 1
    assert song2.TrackNo == 2
    assert song3.TrackNo == 3
    assert db.get_local_usn() == old_usn + 3

    assert _check_playlist_xml(db)


def test_add_song_to_playlist_trackno_middle(db):
    song1 = db.add_to_playlist(PID1, CID1)
    song2 = db.add_to_playlist(PID1, CID2)
    assert song1.TrackNo == 1
    assert song2.TrackNo == 2
    db.commit()

    usn_old = db.get_local_usn()
    mtime_old = db.get_playlist(ID=PID1).updated_at

    # Insert song in the middle
    song3 = db.add_to_playlist(PID1, CID3, track_no=2)
    db.commit()
    assert song3.TrackNo == 2

    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: int(x.TrackNo))
    assert len(songs) == 3
    assert songs[0].ContentID == str(CID1)
    assert songs[0].TrackNo == 1
    assert songs[1].ContentID == str(CID3)
    assert songs[1].TrackNo == 2
    assert songs[2].ContentID == str(CID2)
    assert songs[2].TrackNo == 3

    # Test USN and update time are correct
    # First USN increment is for adding song, second for updating track no
    # of other songs in playlist
    assert pl.updated_at == mtime_old
    assert songs[1].rb_local_usn == usn_old + 2
    assert songs[2].rb_local_usn == usn_old + 2
    assert db.get_local_usn() == usn_old + 2

    assert _check_playlist_xml(db)


def test_remove_song_from_playlist_end(db):
    # Add songs to playlist
    db.add_to_playlist(PID1, CID1, track_no=1)
    db.add_to_playlist(PID1, CID2, track_no=2)
    song3 = db.add_to_playlist(PID1, CID3, track_no=3)
    sid3 = song3.ID
    db.commit()

    usn_old = db.get_local_usn()
    mtime_old = db.get_playlist(ID=PID1).updated_at

    # test removing song from playlist
    db.remove_from_playlist(PID1, sid3)
    db.commit()

    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
    assert len(songs) == 2
    assert songs[0].ContentID == str(CID1)
    assert songs[0].TrackNo == 1
    assert songs[1].ContentID == str(CID2)
    assert songs[1].TrackNo == 2
    pl = db.get_playlist(ID=PID1)
    # Test USN and update time are correct
    assert pl.updated_at == mtime_old
    assert db.get_local_usn() == usn_old + 1

    assert _check_playlist_xml(db)


def test_remove_song_from_playlist_middle(db):
    # Add songs to playlist
    db.add_to_playlist(PID1, CID1, track_no=1)
    song2 = db.add_to_playlist(PID1, CID2, track_no=2)
    db.add_to_playlist(PID1, CID3, track_no=3)
    sid2 = song2.ID
    db.commit()
    usn_old = db.get_local_usn()

    # test removing song from playlist
    db.remove_from_playlist(PID1, sid2)
    db.commit()

    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
    assert len(songs) == 2
    assert songs[0].ContentID == str(CID1)
    assert songs[0].TrackNo == 1
    assert songs[1].ContentID == str(CID3)
    assert songs[1].TrackNo == 2

    # Check USN is correct
    assert db.get_local_usn() == usn_old + 2
    assert songs[1].rb_local_usn == usn_old + 2

    assert _check_playlist_xml(db)


def test_move_in_playlist_forward(db):
    # Add songs to playlist
    s1 = db.add_to_playlist(PID1, CID1)
    s2 = db.add_to_playlist(PID1, CID2)
    s3 = db.add_to_playlist(PID1, CID3)
    s4 = db.add_to_playlist(PID1, CID4)
    db.commit()
    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
    assert [int(s.ContentID) for s in songs] == [CID1, CID2, CID3, CID4]
    usn_old = db.get_local_usn()

    # Move song forward
    db.move_song_in_playlist(PID1, s3, 1)
    db.commit()
    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
    assert [int(s.ContentID) for s in songs] == [CID3, CID1, CID2, CID4]

    # Check USN
    expected_usn = usn_old + 1
    assert db.get_local_usn() == expected_usn
    assert s1.rb_local_usn == expected_usn
    assert s2.rb_local_usn == expected_usn
    assert s3.rb_local_usn == expected_usn
    assert s4.rb_local_usn == usn_old

    assert _check_playlist_xml(db)


def test_move_in_playlist_backward(db):
    # Add songs to playlist
    s1 = db.add_to_playlist(PID1, CID1)
    s2 = db.add_to_playlist(PID1, CID2)
    s3 = db.add_to_playlist(PID1, CID3)
    s4 = db.add_to_playlist(PID1, CID4)
    db.commit()
    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
    assert [int(s.ContentID) for s in songs] == [CID1, CID2, CID3, CID4]
    usn_old = db.get_local_usn()

    # Move song backward
    db.move_song_in_playlist(PID1, s1, 3)
    db.commit()
    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
    assert [int(s.ContentID) for s in songs] == [CID2, CID3, CID1, CID4]

    # Check USN
    expected_usn = usn_old + 1
    assert db.get_local_usn() == expected_usn
    assert s1.rb_local_usn == expected_usn
    assert s2.rb_local_usn == expected_usn
    assert s3.rb_local_usn == expected_usn
    assert s4.rb_local_usn == usn_old

    assert _check_playlist_xml(db)


def test_create_playlist(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2
    old_usn = db.get_local_usn()

    # Create playlist
    pl = db.create_playlist("Test playlist")
    pid = pl.ID
    db.commit()

    # Check if playlist was created correctly
    pl = db.get_playlist(ID=pid)
    assert pl.Name == "Test playlist"
    assert pl.Seq == 3
    assert pl.Attribute == 0
    assert pl.Songs == []
    assert pl.ParentID == "root"
    assert pl.Children == []

    # Check USN is correct (+1 for creating, +1 for renaming)
    assert pl.rb_local_usn == old_usn + 2
    assert db.get_local_usn() == old_usn + 2

    # Try to add song to playlist
    db.add_to_playlist(pl, CID1)
    db.commit()

    pl = db.get_playlist(ID=pid)
    assert len(pl.Songs) == 1

    # Check if playlist was added to xml
    plxml = db.playlist_xml.get(pl.ID)
    assert plxml is not None
    assert _check_playlist_xml(db)


def test_create_playlist_seq_middle(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2
    old_usn = db.get_local_usn()

    # Create playlist
    pl = db.create_playlist("playlist1")
    pid1 = pl.ID
    assert pl.Seq == 3
    db.commit()
    # Check USN is correct (+1 for creating, +1 for renaming)
    assert pl.rb_local_usn == old_usn + 2
    assert db.get_local_usn() == old_usn + 2

    old_usn = db.get_local_usn()
    pl = db.create_playlist("playlist2", seq=3)
    pid2 = pl.ID
    db.commit()

    pl1 = db.get_playlist(ID=pid1)
    pl2 = db.get_playlist(ID=pid2)
    assert pl1.Seq == 4
    assert pl2.Seq == 3
    # Check USN is correct
    assert db.get_local_usn() == old_usn + 3  # +2 for creating, +1 for moving others
    assert pl1.rb_local_usn == old_usn + 1
    assert pl2.rb_local_usn == old_usn + 3

    assert _check_playlist_xml(db)


def test_create_playlist_folder(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2
    usn_old = db.get_local_usn()

    # Create playlist
    pl = db.create_playlist_folder("Test playlist folder")
    pid = pl.ID
    db.commit()

    # Check if playlist folder was created correctly
    pl = db.get_playlist(ID=pid)
    assert pl.Name == "Test playlist folder"
    assert pl.Seq == 3
    assert pl.Attribute == 1
    assert pl.Songs == []
    assert pl.ParentID == "root"
    assert pl.Children == []
    # Check USN is correct (+1 for creating, +1 for renaming)
    assert db.get_local_usn() == usn_old + 2
    assert pl.rb_local_usn == usn_old + 2

    # Try to add sub-playlist to playlist folder
    db.create_playlist("Test playlist", parent=pl)
    db.commit()

    pl = db.get_playlist(ID=pid)
    assert len(pl.Children) == 1

    assert _check_playlist_xml(db)


def test_create_smart_playlist(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2
    old_usn = db.get_local_usn()

    # Create smart list
    smart = SmartList(LogicalOperator.ALL)
    smart.add_condition(Property.ARTIST, Operator.EQUAL, "Loopmasters")

    # create smart playlist from smart list
    pl = db.create_smart_playlist("Smart playlist", smart)
    pid = pl.ID
    db.commit()

    # Check if playlist was created correctly
    pl = db.get_playlist(ID=pid)
    assert pl.Name == "Smart playlist"
    assert pl.Seq == 3
    assert pl.Attribute == 4
    assert pl.Songs == []
    assert pl.ParentID == "root"
    assert pl.Children == []

    # Check USN is correct (+1 for creating, +1 for renaming)
    assert pl.rb_local_usn == old_usn + 2
    assert db.get_local_usn() == old_usn + 2

    # Check if playlist was added to xml
    plxml = db.playlist_xml.get(pl.ID)
    assert plxml is not None
    assert _check_playlist_xml(db)


def test_delete_playlist_empty_end(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    pl2 = db.create_playlist("sub playlist 2", parent=folder.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    assert pl1.Seq == 1 and pl2.Seq == 2 and pl3.Seq == 3
    db.commit()
    usn_old = db.get_local_usn()

    # Delete playlist
    pl = db.get_playlist(Name="sub playlist 3").one()
    pid = pl.ID
    db.delete_playlist(pl)
    db.commit()

    # Check if playlist was deleted
    pl = db.get_playlist(ID=pid)
    assert pl is None
    # Check if playlist was deleted from xml
    plxml = db.playlist_xml.get(pid)
    assert plxml is None
    # Check USN is correct (+1 for deleting)
    assert db.get_local_usn() == usn_old + 1

    assert _check_playlist_xml(db)
    assert _check_playlist_xml_delete(db)


def test_delete_playlist_empty(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    pl2 = db.create_playlist("sub playlist 2", parent=folder.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    assert pl1.Seq == 1 and pl2.Seq == 2 and pl3.Seq == 3
    db.commit()
    usn_old = db.get_local_usn()

    # Delete playlist
    pl = db.get_playlist(Name="sub playlist 2").one()
    pid = pl.ID
    db.delete_playlist(pl)
    db.commit()

    # Check if playlist was deleted
    pl = db.get_playlist(ID=pid)
    assert pl is None
    # Check if playlist was deleted from xml
    plxml = db.playlist_xml.get(pid)
    assert plxml is None
    # Check USN is correct (+1 for deleting, all moved playlists get same USN)
    assert db.get_local_usn() == usn_old + 1
    # Check if seq numbers in parent were updated
    pl = db.get_playlist(Name="sub playlist 3").one()
    assert pl.Seq == 2
    assert pl.rb_local_usn == usn_old + 1

    assert _check_playlist_xml(db)
    assert _check_playlist_xml_delete(db)


def test_delete_playlist_folder_empty(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    pl2 = db.create_playlist_folder("sub playlist folder", parent=folder.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    assert pl1.Seq == 1 and pl2.Seq == 2 and pl3.Seq == 3
    db.commit()
    usn_old = db.get_local_usn()

    # Delete playlist
    pl = db.get_playlist(Name="sub playlist folder").one()
    pid = pl.ID
    db.delete_playlist(pl)
    db.commit()

    # Check if playlist was deleted
    pl = db.get_playlist(ID=pid)
    assert pl is None
    # Check if playlist was deleted from xml
    plxml = db.playlist_xml.get(pid)
    assert plxml is None
    # Check if seq numbers in parent were updated
    pl = db.get_playlist(Name="sub playlist 3").one()
    assert pl.Seq == 2
    # Check USN is correct (+1 for deleting)
    assert db.get_local_usn() == usn_old + 1
    assert pl.rb_local_usn == usn_old + 1

    assert _check_playlist_xml(db)
    assert _check_playlist_xml_delete(db)


def test_delete_playlist_non_empty(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    pl2 = db.create_playlist("sub playlist 2", parent=folder.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    # Add songs to playlists
    sid1 = db.add_to_playlist(pl1, CID1).ID
    sid2 = db.add_to_playlist(pl2, CID2).ID
    sid3 = db.add_to_playlist(pl2, CID3).ID
    sid4 = db.add_to_playlist(pl3, CID4).ID
    db.commit()
    usn_old = db.get_local_usn()

    assert db.query(tables.DjmdSongPlaylist).count() == 4

    # Delete playlist
    pl = db.get_playlist(Name="sub playlist 2").one()
    pid = pl.ID
    db.delete_playlist(pl)
    db.commit()

    # Check if playlist was deleted
    pl = db.get_playlist(ID=pid)
    assert pl is None
    # Check if songs in playlist were deleted
    assert db.query(tables.DjmdSongPlaylist).count() == 2
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid1).count() == 1
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid2).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid3).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid4).count() == 1
    # Check if USN is correct (+1 for deleting with contents)
    assert db.get_local_usn() == usn_old + 1

    assert _check_playlist_xml(db)
    assert _check_playlist_xml_delete(db)


def test_delete_playlist_folder_non_empty(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    folder2 = db.create_playlist_folder("sub playlist folder", parent=folder.ID)
    pl2 = db.create_playlist("sub sub playlist", parent=folder2.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    # Add songs to playlists
    sid1 = db.add_to_playlist(pl1, CID1).ID
    sid2 = db.add_to_playlist(pl2, CID2).ID
    sid3 = db.add_to_playlist(pl2, CID3).ID
    sid4 = db.add_to_playlist(pl3, CID4).ID
    db.commit()
    usn_old = db.get_local_usn()

    assert db.query(tables.DjmdSongPlaylist).count() == 4

    # Delete playlist
    pl = db.get_playlist(Name="sub playlist folder").one()
    pid = pl.ID

    pid2 = db.get_playlist(Name="sub sub playlist").one().ID

    db.delete_playlist(pl)
    db.commit()

    # Check if playlists were deleted
    pl = db.get_playlist(ID=pid)
    assert pl is None
    pl = db.get_playlist(ID=pid2)
    assert pl is None
    # Check if songs in playlist were deleted
    assert db.query(tables.DjmdSongPlaylist).count() == 2
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid1).count() == 1
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid2).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid3).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid4).count() == 1

    # Check if USN is correct (+1 for deleting with Seq update, +1 for children)
    assert db.get_local_usn() == usn_old + 2

    assert _check_playlist_xml(db)
    assert _check_playlist_xml_delete(db)


def test_delete_playlist_folder_chained(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    subfolder1 = db.create_playlist_folder("subfolder", parent=folder.ID)
    subfolder2 = db.create_playlist_folder("subsubfolder", parent=subfolder1.ID)
    subfolder3 = db.create_playlist_folder("subsubsubfolder", parent=subfolder2.ID)
    pl1 = db.create_playlist("sub playlist 1", parent=subfolder2.ID)
    pl2 = db.create_playlist("sub playlist 2", parent=subfolder3.ID)

    pid1 = folder.ID
    pid2 = subfolder1.ID
    pid3 = subfolder2.ID
    pid4 = subfolder3.ID
    pid5 = pl1.ID
    pid6 = pl2.ID

    # Add songs to playlists
    sid1 = db.add_to_playlist(pl1, CID1).ID
    sid2 = db.add_to_playlist(pl1, CID2).ID
    sid3 = db.add_to_playlist(pl2, CID3).ID
    sid4 = db.add_to_playlist(pl2, CID4).ID

    db.commit()
    usn_old = db.get_local_usn()

    db.delete_playlist(folder)
    db.commit()

    # Check if all playlists and songs were deleted
    assert db.get_playlist(ID=pid1) is None
    assert db.get_playlist(ID=pid2) is None
    assert db.get_playlist(ID=pid3) is None
    assert db.get_playlist(ID=pid5) is None
    assert db.get_playlist(ID=pid4) is None
    assert db.get_playlist(ID=pid6) is None
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid1).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid2).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid3).count() == 0
    assert db.query(tables.DjmdSongPlaylist).filter_by(ID=sid4).count() == 0

    # Check all the corresponding xml entries were deleted
    assert db.playlist_xml.get(pid1) is None
    assert db.playlist_xml.get(pid2) is None
    assert db.playlist_xml.get(pid3) is None
    assert db.playlist_xml.get(pid4) is None
    assert db.playlist_xml.get(pid5) is None
    assert db.playlist_xml.get(pid6) is None

    # Check if USN is correct (+1 for deleting with Seq update, +1 for children)
    assert db.get_local_usn() == usn_old + 2

    assert _check_playlist_xml(db)
    assert _check_playlist_xml_delete(db)


def test_move_playlist_seq(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    f1 = db.create_playlist_folder("f 1", parent=folder)
    _ = db.create_playlist_folder("f 2", parent=folder)
    db.create_playlist("pl 1", parent=folder)
    db.create_playlist("pl 2", parent=folder)
    db.create_playlist("pl 3", parent=folder)
    db.create_playlist("pl 4", parent=folder)
    db.create_playlist("sub pl 1", parent=f1)
    db.create_playlist("sub pl 2", parent=f1)
    db.create_playlist("sub pl 3", parent=f1)
    db.create_playlist("sub pl 4", parent=f1)
    db.commit()

    playlists = db.get_playlist(ParentID=folder.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["f 1", "f 2", "pl 1", "pl 2", "pl 3", "pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5, 6]

    playlists = db.get_playlist(ParentID=f1.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["sub pl 1", "sub pl 2", "sub pl 3", "sub pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4]

    usn_old = db.get_local_usn()
    # Move playlist 1 to position 5
    pl = db.get_playlist(Name="pl 1").one()
    mtime_old = pl.updated_at
    db.move_playlist(pl, seq=5)
    db.commit()

    playlists = db.get_playlist(ParentID=folder.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["f 1", "f 2", "pl 2", "pl 3", "pl 1", "pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5, 6]
    # Check that the usn and update time was updated correctly
    # First the moved playlist USN is set, then the other updated playlists
    # in the seq order
    pl1 = db.get_playlist(Name="pl 1").one()
    pl2 = db.get_playlist(Name="pl 2").one()
    pl3 = db.get_playlist(Name="pl 3").one()
    assert db.get_local_usn() == usn_old + 3
    assert pl1.rb_local_usn == usn_old + 1
    assert pl2.rb_local_usn == usn_old + 2
    assert pl3.rb_local_usn == usn_old + 3
    assert pl1.updated_at >= mtime_old
    assert pl2.updated_at >= mtime_old
    assert pl3.updated_at >= mtime_old

    usn_old = db.get_local_usn()
    # Move playlist 3 to position 2
    pl = db.get_playlist(Name="pl 3").one()
    mtime_old = pl.updated_at
    db.move_playlist(pl, seq=2)
    db.commit()

    playlists = db.get_playlist(ParentID=folder.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["f 1", "pl 3", "f 2", "pl 2", "pl 1", "pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5, 6]
    # Check that the usn and update time was updated correctly
    # First the moved playlist USN is set, then the other updated playlists
    # in the seq order
    pl2 = db.get_playlist(Name="pl 2").one()
    pl3 = db.get_playlist(Name="pl 3").one()
    f2 = db.get_playlist(Name="f 2").one()
    assert db.get_local_usn() == usn_old + 3
    assert pl3.rb_local_usn == usn_old + 1
    assert f2.rb_local_usn == usn_old + 2
    assert pl2.rb_local_usn == usn_old + 3
    assert pl2.updated_at >= mtime_old
    assert pl3.updated_at >= mtime_old
    assert f2.updated_at >= mtime_old

    assert _check_playlist_xml(db)


def test_move_playlist_parent(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    f1 = db.create_playlist_folder("f 1", parent=folder)
    _ = db.create_playlist_folder("f 2", parent=folder)
    db.create_playlist("pl 1", parent=folder)
    db.create_playlist("pl 2", parent=folder)
    db.create_playlist("pl 3", parent=folder)
    db.create_playlist("pl 4", parent=folder)
    db.create_playlist("sub pl 1", parent=f1)
    db.create_playlist("sub pl 2", parent=f1)
    db.create_playlist("sub pl 3", parent=f1)
    db.create_playlist("sub pl 4", parent=f1)
    db.commit()

    playlists = db.get_playlist(ParentID=folder.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["f 1", "f 2", "pl 1", "pl 2", "pl 3", "pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5, 6]

    playlists = db.get_playlist(ParentID=f1.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["sub pl 1", "sub pl 2", "sub pl 3", "sub pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4]

    # Move playlist 1 to sub playlist (at the end)
    old_usn = db.get_local_usn()
    pl = db.get_playlist(Name="pl 1").one()
    old_mtime = pl.updated_at
    db.move_playlist(pl, parent=f1)
    db.commit()

    playlists = db.get_playlist(ParentID=folder.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["f 1", "f 2", "pl 2", "pl 3", "pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5]
    playlists = db.get_playlist(ParentID=f1.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["sub pl 1", "sub pl 2", "sub pl 3", "sub pl 4", "pl 1"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5]

    # Check that the usn and update time was updated correctly
    pl = db.get_playlist(Name="pl 1").one()
    assert db.get_local_usn() == old_usn + 1
    assert pl.rb_local_usn == old_usn + 1
    assert pl.updated_at >= old_mtime

    # Move playlist 2 to sub playlist
    old_usn = db.get_local_usn()
    pl = db.get_playlist(Name="pl 2").one()
    old_mtime = pl.updated_at
    db.move_playlist(pl, seq=2, parent=f1)
    db.commit()

    playlists = db.get_playlist(ParentID=folder.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["f 1", "f 2", "pl 3", "pl 4"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4]
    playlists = db.get_playlist(ParentID=f1.ID).order_by(tables.DjmdPlaylist.Seq)
    expected = ["sub pl 1", "pl 2", "sub pl 2", "sub pl 3", "sub pl 4", "pl 1"]
    assert [p.Name for p in playlists] == expected
    assert [pl.Seq for pl in playlists] == [1, 2, 3, 4, 5, 6]
    # Check that the usn and update time was updated correctly
    _ = db.get_playlist(Name="sub pl 1").one()
    subpl2 = db.get_playlist(Name="sub pl 2").one()
    subpl3 = db.get_playlist(Name="sub pl 3").one()
    subpl4 = db.get_playlist(Name="sub pl 4").one()
    pl1 = db.get_playlist(Name="pl 1").one()
    pl = db.get_playlist(Name="pl 2").one()
    assert db.get_local_usn() == old_usn + 5
    assert pl.rb_local_usn == old_usn + 1
    assert pl.updated_at >= old_mtime
    assert subpl2.rb_local_usn == old_usn + 2
    assert subpl3.rb_local_usn == old_usn + 3
    assert subpl4.rb_local_usn == old_usn + 4
    assert pl1.rb_local_usn == old_usn + 5

    assert _check_playlist_xml(db)


def test_rename_playlist(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    db.create_playlist("pl 1", parent=folder)
    db.create_playlist("pl 2", parent=folder)
    db.commit()

    pl = db.get_playlist(Name="pl 1").one()
    pid = pl.ID
    mtime_old = pl.updated_at
    usn_old = db.get_local_usn()

    # Rename playlist
    db.rename_playlist(pl, "pl 1 new")
    db.commit()

    pl = db.get_playlist(ID=pid)
    assert pl.Name == "pl 1 new"
    assert pl.updated_at >= mtime_old
    assert db.get_local_usn() == usn_old + 1
    assert pl.rb_local_usn == usn_old + 1

    assert _check_playlist_xml(db)


def test_get_playlist_contents(db):
    # Create playlist and add content
    pl = db.create_playlist("Test playlist")
    db.add_to_playlist(pl, CID1)
    db.add_to_playlist(pl, CID2)
    db.commit()

    # Get playlist contents
    contents = db.get_playlist_contents(pl).all()
    assert len(contents) == 2
    assert {c.ID for c in contents} == {str(CID1), str(CID2)}


def test_get_playlist_contents_smart(db):
    # Singe condition
    smart = SmartList(LogicalOperator.ALL)
    smart.add_condition(Property.ARTIST, Operator.EQUAL, "Loopmasters")
    pl = db.create_smart_playlist("Smart playlist", smart)
    db.commit()
    contents = db.get_playlist_contents(pl).all()
    assert len(contents) == 2
    assert {c.ID for c in contents} == {str(CID1), str(CID2)}

    # All conditions
    smart = SmartList(LogicalOperator.ALL)
    smart.add_condition(Property.ARTIST, Operator.EQUAL, "Loopmasters")
    smart.add_condition(Property.NAME, Operator.EQUAL, "Demo Track 1")
    pl = db.create_smart_playlist("Smart playlist", smart)
    db.commit()
    contents = db.get_playlist_contents(pl).all()
    assert len(contents) == 1
    assert {c.ID for c in contents} == {str(CID1)}

    # Any conditions
    smart = SmartList(LogicalOperator.ANY)
    smart.add_condition(Property.ARTIST, Operator.EQUAL, "Loopmasters")
    smart.add_condition(Property.NAME, Operator.EQUAL, "HORN")
    pl = db.create_smart_playlist("Smart playlist", smart)
    db.commit()
    contents = db.get_playlist_contents(pl).all()
    assert len(contents) == 3
    assert {c.ID for c in contents} == {str(CID1), str(CID2), str(CID3)}


def test_add_album(db):
    old_usn = db.get_local_usn()
    name = "test"
    db.add_album(name)
    db.commit()

    # Check that album was created and USN is incremented
    instance = db.get_album(Name=name).one()
    assert instance.Name == name
    assert instance.rb_local_usn == old_usn + 1
    assert db.get_local_usn() == old_usn + 1

    # Fail if album with same name is added
    with pytest.raises(ValueError):
        db.add_album(name)

    # Add album with album artist by artist
    artist = db.get_artist().first()
    album = db.add_album("album 2", artist=artist)
    assert album.AlbumArtistID == artist.ID

    # Add album with album artist by ID
    artist = db.get_artist().first()
    album = db.add_album("album 3", artist=artist.ID)
    assert album.AlbumArtistID == artist.ID


def test_add_artist(db):
    old_usn = db.get_local_usn()
    name = "test"
    db.add_artist(name)
    db.commit()

    # Check that album was created and USN is incremented
    instance = db.get_artist(Name=name).one()
    assert instance.Name == name
    assert instance.rb_local_usn == old_usn + 1
    assert db.get_local_usn() == old_usn + 1

    # Fail if album with same name is added
    with pytest.raises(ValueError):
        db.add_artist(name)


def test_add_genre(db):
    old_usn = db.get_local_usn()
    name = "test"
    db.add_genre(name)
    db.commit()

    # Check that album was created and USN is incremented
    instance = db.get_genre(Name=name).one()
    assert instance.Name == name
    assert instance.rb_local_usn == old_usn + 1
    assert db.get_local_usn() == old_usn + 1

    # Fail if album with same name is added
    with pytest.raises(ValueError):
        db.add_genre(name)


def test_add_label(db):
    old_usn = db.get_local_usn()
    name = "test"
    db.add_label(name)
    db.commit()

    # Check that album was created and USN is incremented
    instance = db.get_label(Name=name).one()
    assert instance.Name == name
    assert instance.rb_local_usn == old_usn + 1
    assert db.get_local_usn() == old_usn + 1

    # Fail if album with same name is added
    with pytest.raises(ValueError):
        db.add_label(name)


def test_add_content(db):
    path = os.path.join(TEST_ROOT, "empty.mp3")
    # Add content
    content = db.add_content(path, Title="Test")
    assert content.Title == "Test"
    assert content.FolderPath == path

    # Fail on duplicate content
    with pytest.raises(ValueError):
        db.add_content(path)


def test_get_anlz_paths():
    content = DB.get_content().first()

    anlz_dir = str(DB.get_anlz_dir(content)).replace("\\", "/")
    expected = r"share/PIONEER/USBANLZ/735/e8b81-e69b-41ad-80f8-9c0d7613b96d"
    assert anlz_dir.endswith(expected)


def test_to_json():
    # Check if saving to json works

    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        DB.to_json(tmp.name)
    finally:
        tmp.close()
        os.remove(tmp.name)


def test_copy_unlocked():
    db = Rekordbox6Database(UNLOCKED, unlock=False)
    db.copy_unlocked(UNLOCKED_OUT)

    db2 = Rekordbox6Database(UNLOCKED_OUT, unlock=False)
    # Check everything got copied
    for name in tables.TABLES:
        table = getattr(tables, name)
        for row in db.query(table):
            data = row.to_dict()
            if name == "AgentRegistry":
                query = db2.query(table).filter_by(registry_id=row.registry_id)
            elif name == "DjmdProperty":
                query = db2.query(table).filter_by(DBID=row.DBID)
            else:
                query = db2.query(table).filter_by(ID=row.ID)
            data2 = query.one().to_dict()
            assert data == data2
