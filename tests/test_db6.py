# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os

import pytest
from pytest import mark
from sqlalchemy.orm.query import Query
from pyrekordbox import Rekordbox6Database, open_rekordbox_database
from pyrekordbox.db6 import tables

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
UNLOCKED = os.path.join(TEST_ROOT, "rekordbox 6", "master_unlocked.db")

DB = Rekordbox6Database(UNLOCKED, unlock=False)


def test_open_rekordbox_database():
    con = open_rekordbox_database(UNLOCKED, unlock=False)
    con.execute("SELECT name FROM sqlite_master WHERE type='table';")


def test_close_open():
    db = Rekordbox6Database(UNLOCKED, unlock=False)
    db.close()
    db.open()
    _ = db.get_content()[0]  # Try to query the database


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
        ("Demo Track 1", [178162577]),  # Title
        ("Demo Track 2", [66382436]),  # Title
        ("Loopmasters", [178162577, 66382436]),  # Label/Artist Name
        ("Noise", [24401986]),  # lowercase
        ("NOIS", [24401986]),  # incomplete
    ],
)
def test_search_content(search, ids):
    results = DB.search_content(search)
    for id_, res in zip(ids, results):
        assert int(res.ID) == id_


def test_increment_local_usn():
    db = Rekordbox6Database(UNLOCKED, unlock=False)

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
