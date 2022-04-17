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
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import get_config
from ..utils import read_rekordbox6_asar
from ..anlz import get_anlz_paths, read_anlz_files
from .tables import DjmdContent, DjmdArtist, DjmdAlbum, DjmdCue, DjmdGenre, DjmdKey

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

        anlz_root = os.path.join(rb6_config["db_dir"], "share")
        self._anlz_root = os.path.normpath(anlz_root)

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

    def get_content(self, **kwargs):
        query = self.query(DjmdContent).filter_by(**kwargs)
        return query

    def search_content(self, search):

        columns = ["Title", "Commnt", "SearchStr"]

        results = list()
        for col in columns:
            obj = getattr(DjmdContent, col)
            res = self.query(DjmdContent).filter(obj.contains(search))
            results.extend(res.all())

        rel_columns = {
            "Album": (DjmdAlbum, "Name"),
            "Artist": (DjmdArtist, "Name"),
            "Composer": (DjmdArtist, "Name"),
            "Remixer": (DjmdArtist, "Name"),
            "Genre": (DjmdGenre, "Name"),
            "Key": (DjmdKey, "ScaleName"),
        }
        for col, (table, attr) in rel_columns.items():
            obj = getattr(DjmdContent, col)
            item = getattr(table, attr)
            res = self.query(DjmdContent).join(obj).filter(item.contains(search))
            results.extend(res.all())

        return results

    def get_cue(self, **kwargs):
        query = self.query(DjmdCue).filter_by(**kwargs)
        return query

    def get_anlz_dir(self, content_id):
        item = self.get_content(ID=content_id)
        dat_path = os.path.normpath(item["AnalysisDataPath"]).strip("\\/")
        return os.path.join(self._anlz_root, os.path.dirname(dat_path))

    def get_anlz_paths(self, content_id):
        root = self.get_anlz_dir(content_id)
        return get_anlz_paths(root)

    def read_anlz_files(self, content_id):
        root = self.get_anlz_dir(content_id)
        return read_anlz_files(root)
