# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
import re
import base64
import warnings
import blowfish
import logging
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import get_config
from ..utils import read_rekordbox6_asar
from ..anlz import get_anlz_paths, read_anlz_files
from . import tables

if sys.platform.lower() == "darwin":
    try:
        from pysqlcipher3 import dbapi2 as sqlite3
    except ImportError:
        import sqlite3
else:
    import sqlite3

logger = logging.getLogger(__name__)

rb6_config = get_config("rekordbox6")


def _get_masterdb_key():
    # See https://www.reddit.com/r/Rekordbox/comments/qou6nm/key_to_open_masterdb_file/

    # Read password key from app.asar file
    asar_data = read_rekordbox6_asar(rb6_config["install_dir"])
    match = re.search('pass: ".(.*?)"', asar_data).group(0)
    password = match.replace("pass: ", "").strip('"')
    password_bytes = password.encode()

    # Decode database key data
    encoded_key_data = rb6_config["dp"]  # from 'options.json'
    decoded_key_data = base64.standard_b64decode(encoded_key_data)

    # Decrypt database key
    cipher = blowfish.Cipher(password_bytes)
    decrypted_bytes = b"".join(cipher.decrypt_ecb(decoded_key_data))
    database_key = decrypted_bytes.decode()

    return database_key


def create_rekordbox_engine(path="", unlock=True, sql_driver=None, echo=None):
    if not path:
        path = rb6_config["db_path"]

    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' does not exist!")
    logger.info("Opening %s", path)

    # Open database
    if unlock:
        key = _get_masterdb_key()
        logger.info("Key: %s", key)
        if sql_driver is None:
            # Use default sqlite3 package
            # This requires that the 'sqlite3.dll' was replaced by
            # the 'sqlcipher.dll' (renamed to 'sqlite3.dll')
            sql_driver = sqlite3
        url = f"sqlite+pysqlcipher://:{key}@/{path}?"
        engine = create_engine(url, module=sql_driver, echo=echo)
    else:
        engine = create_engine(f"sqlite:///{path}", echo=echo)

    return engine


def open_rekordbox_database(path="", unlock=True, sql_driver=None):
    warnings.warn(
        "This method is deprecated and will be removed in a future version!"
        "Use the `Rekordbox6Database` class instead!",
        DeprecationWarning,
    )
    if not path:
        path = rb6_config["db_path"]

    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' does not exist!")
    logger.info("Opening %s", path)

    # Open database
    if sql_driver is None:
        # Use default sqlite3 package
        # This requires that the 'sqlite3.dll' was replaced by
        # the 'sqlcipher.dll' (renamed to 'sqlite3.dll')
        sql_driver = sqlite3
    con = sql_driver.connect(path)

    if unlock:
        # Read and decode master.db key
        key = _get_masterdb_key()
        logger.info("Key: %s", key)
        # Unlock database
        con.execute(f"PRAGMA key='{key}'")

    # Check connection
    try:
        con.execute("SELECT name FROM sqlite_master WHERE type='table';")
    except sqlite3.DatabaseError as e:
        msg = f"Opening database failed: '{e}'. Check if the database key is correct!"
        raise sqlite3.DatabaseError(msg)
    else:
        logger.info("Database unlocked!")

    return con


class Rekordbox6Database:
    def __init__(self, path="", unlock=True):
        self.engine = create_rekordbox_engine(path, unlock=unlock)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self._db_dir = os.path.normpath(rb6_config["db_dir"])
        self._anlz_root = os.path.join(self._db_dir, "share")

    def open(self):
        self.session = self.Session()

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def query(self, *entities, **kwargs):
        return self.session.query(*entities, **kwargs)

    # -- Djmd Tables -------------------------------------------------------------------

    def get_active_censor(self, **kwargs):
        return self.query(tables.DjmdActiveCensor).filter_by(**kwargs)

    def get_album(self, **kwargs):
        return self.query(tables.DjmdAlbum).filter_by(**kwargs)

    def get_artist(self, **kwargs):
        return self.query(tables.DjmdArtist).filter_by(**kwargs)

    def get_category(self, **kwargs):
        return self.query(tables.DjmdCategory).filter_by(**kwargs)

    def get_color(self, **kwargs):
        return self.query(tables.DjmdColor).filter_by(**kwargs)

    def get_content(self, **kwargs):
        query = self.query(tables.DjmdContent).filter_by(**kwargs)
        return query

    def search_content(self, search):

        columns = ["Title", "Commnt", "SearchStr"]

        results = list()
        for col in columns:
            obj = getattr(tables.DjmdContent, col)
            res = self.query(tables.DjmdContent).filter(obj.contains(search))
            results.extend(res.all())

        rel_columns = {
            "Album": (tables.DjmdAlbum, "Name"),
            "Artist": (tables.DjmdArtist, "Name"),
            "Composer": (tables.DjmdArtist, "Name"),
            "Remixer": (tables.DjmdArtist, "Name"),
            "Genre": (tables.DjmdGenre, "Name"),
            "Key": (tables.DjmdKey, "ScaleName"),
        }
        for col, (table, attr) in rel_columns.items():
            obj = getattr(tables.DjmdContent, col)
            item = getattr(table, attr)
            res = self.query(tables.DjmdContent).join(obj).filter(item.contains(search))
            results.extend(res.all())

        return results

    def get_cue(self, **kwargs):
        query = self.query(tables.DjmdCue).filter_by(**kwargs)
        return query

    def get_device(self, **kwargs):
        return self.query(tables.DjmdDevice).filter_by(**kwargs)

    def get_genre(self, **kwargs):
        return self.query(tables.DjmdGenre).filter_by(**kwargs)

    def get_history(self, **kwargs):
        return self.query(tables.DjmdHistory).filter_by(**kwargs)

    def get_history_songs(self, id_):
        return self.query(tables.DjmdSongHistory).filter_by(HistoryID=id_)

    def get_hot_cue_banklist(self, **kwargs):
        return self.query(tables.DjmdHotCueBanklist).filter_by(**kwargs)

    def get_hot_cue_banklist_songs(self, id_):
        return self.query(tables.DjmdSongHotCueBanklist).filter_by(HotCueBanklistID=id_)

    def get_key(self, **kwargs):
        return self.query(tables.DjmdKey).filter_by(**kwargs)

    def get_label(self, **kwargs):
        return self.query(tables.DjmdLabel).filter_by(**kwargs)

    def get_menu_items(self, **kwargs):
        return self.query(tables.DjmdMenuItems).filter_by(**kwargs)

    def get_mixer_param(self, **kwargs):
        return self.query(tables.DjmdMixerParam).filter_by(**kwargs)

    def get_my_tag(self, **kwargs):
        return self.query(tables.DjmdMyTag).filter_by(**kwargs)

    def get_my_tag_songs(self, id_):
        return self.query(tables.DjmdSongMyTag).filter_by(MyTagID=id_)

    def get_playlist(self, **kwargs):
        return self.query(tables.DjmdPlaylist).filter_by(**kwargs)

    def get_playlist_songs(self, id_):
        return self.query(tables.DjmdSongPlaylist).filter_by(PlaylistID=id_)

    def get_property(self, **kwargs):
        return self.query(tables.DjmdProperty).filter_by(**kwargs)

    def get_related_tracks(self, **kwargs):
        return self.query(tables.DjmdRelatedTracks).filter_by(**kwargs)

    def get_related_tracks_songs(self, id_):
        return self.query(tables.DjmdSongRelatedTracks).filter_by(RelatedTracksID=id_)

    def get_sampler(self, **kwargs):
        return self.query(tables.DjmdSampler).filter_by(**kwargs)

    def get_sampler_songs(self, id_):
        return self.query(tables.DjmdSongSampler).filter_by(SamplerID=id_)

    def get_tag_list_songs(self, id_):
        return self.query(tables.DjmdSongTagList).filter_by(ID=id_)

    def get_sort(self, **kwargs):
        return self.query(tables.DjmdSort).filter_by(**kwargs)

    # -- Other tables ------------------------------------------------------------------

    def get_agent_registry(self, **kwargs):
        return self.query(tables.AgentRegistry).filter_by(**kwargs)

    def get_cloud_agent_registry(self, **kwargs):
        return self.query(tables.CloudAgentRegistry).filter_by(**kwargs)

    def get_content_active_censor(self, **kwargs):
        return self.query(tables.ContentActiveCensor).filter_by(**kwargs)

    def get_content_cue(self, **kwargs):
        return self.query(tables.ContentCue).filter_by(**kwargs)

    def get_content_file(self, **kwargs):
        return self.query(tables.ContentFile).filter_by(**kwargs)

    def get_hot_cue_banklist_cue(self, **kwargs):
        return self.query(tables.HotCueBanklistCue).filter_by(**kwargs)

    def get_image_file(self, **kwargs):
        return self.query(tables.ImageFile).filter_by(**kwargs)

    def get_setting_file(self, **kwargs):
        return self.query(tables.SettingFile).filter_by(**kwargs)

    def get_uuid_map(self, **kwargs):
        return self.query(tables.UuidIDMap).filter_by(**kwargs)

    # ==================================================================================

    def get_mysetting_paths(self):
        paths = list()
        for item in self.get_setting_file():
            paths.append(os.path.join(self._db_dir, item.Path.lstrip("/\\")))
        return paths

    def get_anlz_dir(self, content_id):
        item = self.get_content(ID=content_id).one()
        dat_path = os.path.normpath(item.AnalysisDataPath).strip("\\/")
        path = os.path.join(self._anlz_root, os.path.dirname(dat_path))
        assert os.path.exists(path)
        return path

    def get_anlz_paths(self, content_id):
        root = self.get_anlz_dir(content_id)
        return get_anlz_paths(root)

    def read_anlz_files(self, content_id):
        root = self.get_anlz_dir(content_id)
        return read_anlz_files(root)
