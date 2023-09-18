# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import os
import pytest
from pytest import mark
from pathlib import Path
import shutil
import tempfile
from sqlalchemy.orm.query import Query
from pyrekordbox import Rekordbox6Database, open_rekordbox_database
from pyrekordbox.db6 import tables

TEST_ROOT = Path(__file__).parent.parent / ".testdata"
UNLOCKED = TEST_ROOT / "rekordbox 6" / "master_unlocked.db"
UNLOCKED_COPY = TEST_ROOT / "rekordbox 6" / "master_unlocked_copy.db"
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
    con = open_rekordbox_database(UNLOCKED, unlock=False)
    con.execute("SELECT name FROM sqlite_master WHERE type='table';")
    con.close()


def test_close_open():
    db = Rekordbox6Database(UNLOCKED, unlock=False)
    db.close()
    db.open()
    _ = db.get_content()[0]  # Try to query the database
    db.close()


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
    "parent_name,cls",
    [
        ("get_playlist", tables.DjmdSongHistory),
        ("get_hot_cue_banklist", tables.DjmdSongHotCueBanklist),
        ("get_my_tag", tables.DjmdSongMyTag),
        ("get_playlist", tables.DjmdSongPlaylist),
        ("get_related_tracks", tables.DjmdSongPlaylist),
        ("get_sampler", tables.DjmdSongPlaylist),
    ],
)
def test_songs_getters(parent_name, cls):
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
    query = getter(id_)
    if not query.count():
        return  # No data to check...

    assert isinstance(query.first(), cls)


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


def test_add_song_to_playlist(db):
    # test adding song to playlist
    song = db.add_to_playlist(PID1, CID1)
    db.commit()

    pl = db.get_playlist(ID=PID1)
    assert len(pl.Songs) == 1
    assert pl.Songs[0].ContentID == str(CID1)
    assert song.TrackNo == 1

    # Get xml item
    plxml = db.playlist_xml.get(PID1)
    ts = plxml["Timestamp"]
    assert int(pl.updated_at.timestamp() * 1000) == int(ts.timestamp() * 1000)

    # test raising error when adding song to playlist with wrong TrackNo
    with pytest.raises(ValueError):
        db.add_to_playlist(PID1, CID2, track_no=0)
    with pytest.raises(ValueError):
        db.add_to_playlist(PID1, CID2, track_no=3)


def test_add_song_to_playlist_trackno_end(db):
    song1 = db.add_to_playlist(PID1, CID1)
    song2 = db.add_to_playlist(PID1, CID2)
    song3 = db.add_to_playlist(PID1, CID3)
    assert song1.TrackNo == 1
    assert song2.TrackNo == 2
    assert song3.TrackNo == 3

    db.commit()


def test_add_song_to_playlist_trackno_middle(db):
    song1 = db.add_to_playlist(PID1, CID1)
    song2 = db.add_to_playlist(PID1, CID2)
    assert song1.TrackNo == 1
    assert song2.TrackNo == 2
    db.commit()

    # Insert song in the middle
    song3 = db.add_to_playlist(PID1, CID3, track_no=2)
    assert song3.TrackNo == 2
    db.commit()

    pl = db.get_playlist(ID=PID1)
    songs = sorted(pl.Songs, key=lambda x: int(x.TrackNo))
    assert len(songs) == 3
    assert songs[0].ContentID == str(CID1)
    assert songs[0].TrackNo == 1
    assert songs[1].ContentID == str(CID3)
    assert songs[1].TrackNo == 2
    assert songs[2].ContentID == str(CID2)
    assert songs[2].TrackNo == 3


def test_remove_song_from_playlist(db):
    # Add songs to playlist
    db.add_to_playlist(PID1, CID1, track_no=1)
    song2 = db.add_to_playlist(PID1, CID2, track_no=2)
    db.add_to_playlist(PID1, CID3, track_no=3)
    sid2 = song2.ID
    db.commit()

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


def test_create_playlist(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2

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

    # Try to add song to playlist
    db.add_to_playlist(pl, CID1)
    db.commit()

    pl = db.get_playlist(ID=pid)
    assert len(pl.Songs) == 1

    # Check if playlist was added to xml
    plxml = db.playlist_xml.get(pl.ID)
    assert plxml is not None
    ts = plxml["Timestamp"]
    assert int(pl.updated_at.timestamp() * 1000) == int(ts.timestamp() * 1000)


def test_create_playlist_seq_middle(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2

    # Create playlist
    pl = db.create_playlist("playlist1")
    pid1 = pl.ID
    assert pl.Seq == 3
    db.commit()

    pl = db.create_playlist("playlist2", seq=3)
    pid2 = pl.ID
    db.commit()

    pl1 = db.get_playlist(ID=pid1)
    pl2 = db.get_playlist(ID=pid2)
    assert pl1.Seq == 4
    assert pl2.Seq == 3


def test_create_playlist_folder(db):
    seqs = [pl.Seq for pl in db.get_playlist()]
    assert max(seqs) == 2

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
    # Try to add sub-playlist to playlist folder

    db.create_playlist("Test playlist", parent=pl)
    db.commit()

    pl = db.get_playlist(ID=pid)
    assert len(pl.Children) == 1


def test_playlist_xml_sync(db):
    # Create playlist structure
    folder1 = db.create_playlist_folder("dev folder")
    folder2 = db.create_playlist_folder("sub folder 1", parent=folder1.ID)
    db.create_playlist("sub playlist 1", parent=folder1.ID)
    db.create_playlist("sub playlist 2", parent=folder1.ID)
    db.create_playlist("sub sub playlist 1", parent=folder2.ID)
    db.create_playlist("sub sub playlist 2", parent=folder2.ID)
    db.commit()

    # Check that every playlist is synced in the masterPlaylists xml file
    for pl in db.get_playlist():
        if pl.Name == "Trial playlist - Cloud Library Sync":
            continue
        plxml = db.playlist_xml.get(pl.ID)
        # Check if playlist exists
        assert plxml is not None
        # Check update time
        ts = plxml["Timestamp"]
        assert int(pl.updated_at.timestamp() * 1000) == int(ts.timestamp() * 1000)


def test_delete_playlist_empty(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    pl2 = db.create_playlist("sub playlist 2", parent=folder.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    assert pl1.Seq == 1 and pl2.Seq == 2 and pl3.Seq == 3

    parent_updated_at = folder.updated_at
    db.commit()

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
    # Check if parent was updated
    pl = db.get_playlist(Name="folder").one()
    assert pl.updated_at > parent_updated_at
    # Check if seq numbers in parent were updated
    pl = db.get_playlist(Name="sub playlist 3").one()
    assert pl.Seq == 2


def test_delete_playlist_folder_empty(db):
    # Create playlist structure
    folder = db.create_playlist_folder("folder")
    pl1 = db.create_playlist("sub playlist 1", parent=folder.ID)
    pl2 = db.create_playlist_folder("sub playlist folder", parent=folder.ID)
    pl3 = db.create_playlist("sub playlist 3", parent=folder.ID)
    assert pl1.Seq == 1 and pl2.Seq == 2 and pl3.Seq == 3

    parent_updated_at = folder.updated_at
    db.commit()

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
    # Check if parent was updated
    pl = db.get_playlist(Name="folder").one()
    assert pl.updated_at > parent_updated_at
    # Check if seq numbers in parent were updated
    pl = db.get_playlist(Name="sub playlist 3").one()
    assert pl.Seq == 2


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
