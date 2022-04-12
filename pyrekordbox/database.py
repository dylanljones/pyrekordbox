# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

"""Rekordbox 6 `master.db` database interface."""

import os
import re
import base64
import blowfish
import logging
import sqlite3
from .config import get_config
from .utils import read_rekordbox6_asar
from .anlz import get_anlz_paths, read_anlz_files

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


def open_rekordbox_database(path="", unlock=True, sql_driver=None):
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
    """Rekordbox SQLite database handler."""

    def __init__(self, path="", unlock=True, sql_driver=None):
        self.con = open_rekordbox_database(path, unlock, sql_driver)
        self.cur = self.con.cursor()

        anlz_root = os.path.join(rb6_config["db_dir"], "share")
        self._anlz_root = os.path.normpath(anlz_root)

    def close(self):
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute(self, sql, params=None):
        if params is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, params)

    def fetchall(self):
        return self.cur.fetchall()

    def fetchone(self):
        return self.cur.fetchone()

    def table_names(self):
        """Gets the table names in the RekordBox database.

        Returns
        -------
        names : list of str
            The names of the tables in the database.
        """
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [x[0] for x in self.cur.fetchall()]

    def column_names(self, table):
        """Gets the column names for a table in the RekordBox database.

        Parameters
        ----------
        table : str
            The name of the table.

        Returns
        -------
        names : list of str
            The names of the columns in the database.
        """
        self.cur.execute(f"SELECT * FROM {table}")
        return list(map(lambda x: x[0], self.cur.description))

    def fetchall_json(self) -> list:
        """Fetches all results from the SQLite cursor and returns them as JSON data.

        Notes
        -----
        Only works for select-statements where *all* columns are selected,
        i.e. SELECT * FROM ...
        """
        keys = list(map(lambda x: x[0], self.cur.description))
        return [dict(zip(keys, vals)) for vals in self.cur.fetchall()]

    def fetchone_json(self) -> dict:
        """Fetches one result from the SQLite cursor and returns them as JSON data.

        Notes
        -----
        Only works for select-statements where *all* columns are selected,
        i.e. SELECT * FROM ...
        """
        column_names = list(map(lambda x: x[0], self.cur.description))
        return dict(zip(column_names, self.cur.fetchone()))

    # -- Tracks ------------------------------------------------------------------------

    def find_content(self, column, value):
        sql = f"SELECT ID FROM djmdContent WHERE {column} LIKE ?"
        self.cur.execute(sql, (f"%{value}%",))
        return [int(x[0]) for x in self.cur.fetchall()]

    def get_content(self, id_=None, uuid=None):
        """Gets the main DJDM content from the RekordBox database.

        This table contains the data for the tracks contained in the RekordBox database.

        Parameters
        ----------
        id_ : int or str, optional
            The ID of a track. If None tracks with any ID are fetched.
        uuid : str, optional
            The UUID of a track. If None tracks with any UUID are fetched.

        Returns
        -------
        tracks : list or dict
            The data of the specified tracks(s) in JSON format.
        """
        if id_ is not None:
            self.cur.execute("SELECT * FROM djmdContent WHERE ID=?", (id_,))
            return self.fetchone_json()
        elif uuid is not None:
            self.cur.execute("SELECT * FROM djmdContent WHERE UUID=?", (uuid,))
            return self.fetchone_json()
        else:
            self.cur.execute("SELECT * FROM djmdContent")
            return self.fetchall_json()

    def get_album_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT AlbumID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT Name FROM djmdAlbum WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    def get_artist_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT ArtistID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT Name FROM djmdArtist WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    def get_composer_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT ComposerID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT Name FROM djmdArtist WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    def get_genre_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT GenreID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT Name FROM djmdGenre WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    def get_key_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT KeyID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT ScaleName FROM djmdKey WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    def get_label_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT LabelID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT Name FROM djmdLabel WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    def get_remixer_name(self, id_=None, content_id=None):
        if id_ is not None:
            cond, args = "?", (id_,)
        else:
            cond, args = "SELECT RemixerID FROM djmdContent WHERE ID=?", (content_id,)
        self.cur.execute(f"SELECT Name FROM djmdArtist WHERE ID = ({cond})", args)
        res = self.fetchone()
        return res[0] if res is not None else None

    # -- Playlists ---------------------------------------------------------------------

    def get_playlists(self, id_=None, uuid=None):
        """Gets the data of one or multiple playlists in the RekordBox database.

        Parameters
        ----------
        id_ : int or str, optional
            The ID of a playlist. If None playlists with any ID are fetched.
        uuid : str, optional
            The UUID of a playlist. If None playlists with any UUID are fetched.

        Returns
        -------
        playlists : list
            The data of the specified playlist(s) in JSON format.
        """
        if id_ is not None:
            self.cur.execute("SELECT * FROM djmdPlaylist WHERE ID=?", (id_,))
            return self.fetchone_json()
        elif uuid is not None:
            self.cur.execute("SELECT * FROM djmdPlaylist WHERE UUID=?", (uuid,))
            return self.fetchone_json()
        else:
            self.cur.execute("SELECT * FROM djmdPlaylist")
            return self.fetchall_json()

    def get_playlist_songs(self, playlist_id=None):
        """Gets the data of the songs contained in playlists in the RekordBox database.

        Parameters
        ----------
        playlist_id : int or str, optional
            The ID of a playlist for which the song information is returned.
            If None all songs contained in playlists are fetched from the database.

        Returns
        -------
        playlist_songs : list of dict
            The data of the songs contained in the specified playlist(s) in JSON format.
        """
        if playlist_id is not None:
            sql = "SELECT * FROM djmdSongPlaylist WHERE PlaylistID=?"
            self.cur.execute(sql, (playlist_id,))
            return self.fetchall_json()
        else:
            self.cur.execute("SELECT * FROM djmdSongPlaylist")
            return self.fetchall_json()

    def get_playlist_contents(self, playlist_id):
        """Gets the track contents of the songs contained in playlist.

        Fetches the track IDs from the songs in the playlist and fetches the
        djmdContent items.

        Parameters
        ----------
        playlist_id : int or str
            The ID of a playlist for which the song information is returned.

        Returns
        -------
        playlist_tracks : list of dict
            The data of the tracks contained in the specified playlist in JSON format.
        """
        sql = (
            "SELECT * FROM djmdContent WHERE id IN "
            "(SELECT ContentID FROM djmdSongPlaylist WHERE PlaylistID=?)"
        )
        self.cur.execute(sql, (playlist_id,))
        return self.fetchall_json()

    # -- Histories ---------------------------------------------------------------------

    def get_history(self, id_=None, uuid=None):
        """Gets the data of one or multiple histories in the RekordBox database.

        Parameters
        ----------
        id_ : int or str, optional
            The ID of a history. If None histories with any ID are fetched.
        uuid : str, optional
            The UUID of a history. If None histories with any UUID are fetched.

        Returns
        -------
        histories : dict or list
            The data of the specified histories in JSON format.
        """
        if id_ is not None:
            self.cur.execute("SELECT * FROM djmdHistory WHERE ID=?", (id_,))
            return self.fetchone_json()
        elif uuid is not None:
            self.cur.execute("SELECT * FROM djmdHistory WHERE UUID=?", (uuid,))
            return self.fetchone_json()
        else:
            self.cur.execute("SELECT * FROM djmdHistory")
            return self.fetchall_json()

    def get_history_songs(self, history_id=None):
        """Gets the data of the songs contained in histories in the RekordBox database.

        Parameters
        ----------
        history_id : int or str, optional
            The ID of a history for which the song information is returned.
            If None all songs contained in histories are fetched from the database.

        Returns
        -------
        history_songs : list of dict
            The data of the songs contained in the specified histories in JSON format.
        """
        if history_id is not None:
            sql = "SELECT * FROM djmdSongHistory WHERE HistoryID=?"
            self.cur.execute(sql, (history_id,))
            return self.fetchall_json()
        else:
            self.cur.execute("SELECT * FROM djmdSongHistory")
            return self.fetchall_json()

    # -- My Tags -----------------------------------------------------------------------

    def get_mytag(self, id_=None, uuid=None):
        """Gets the data of one or multiple tags in the RekordBox database.

        Parameters
        ----------
        id_ : int or str, optional
            The ID of a tag. If None tags with any ID are fetched.
        uuid : str, optional
            The UUID of a tag. If None tags with any UUID are fetched.

        Returns
        -------
        tags : dict or list
            The data of the specified tags in JSON format.
        """
        if id_ is not None:
            self.cur.execute("SELECT * FROM djmdMyTag WHERE ID=?", (id_,))
            return self.fetchone_json()
        elif uuid is not None:
            self.cur.execute("SELECT * FROM djmdMyTag WHERE UUID=?", (uuid,))
            return self.fetchone_json()
        else:
            self.cur.execute("SELECT * FROM djmdMyTag")
            return self.fetchall_json()

    def get_mytag_songs(self, tag_id=None, cid=None):
        """Gets the data of the songs contained in tags in the RekordBox database.

        Parameters
        ----------
        tag_id : int or str, optional
            The ID of a tags for which the song information is returned.
            If None all songs contained in tags are fetched from the database.
        cid : int or str, optional
            The content ID of a track for which the tags are returned.
            If None all songs contained in tags are fetched from the database.

        Returns
        -------
        tags_songs : list of dict
            The data of the songs contained in the specified tags in JSON format.
        """
        if tag_id is not None:
            sql = "SELECT * FROM djmdSongMyTag WHERE MyTagID=?"
            self.cur.execute(sql, (tag_id,))
            return self.fetchall_json()
        elif cid is not None:
            sql = "SELECT * FROM djmdSongMyTag WHERE ContentID=?"
            self.cur.execute(sql, (cid,))
            return self.fetchall_json()
        else:
            self.cur.execute("SELECT * FROM djmdSongMyTag")
            return self.fetchall_json()

    def get_content_mytag(self, cid):
        sql = (
            "SELECT * FROM djmdMyTag WHERE ID IN ("
            "SELECT MyTagID FROM djmdSongMyTag WHERE ContentID=?)"
        )
        self.cur.execute(sql, (cid,))
        return self.fetchall_json()

    def get_content_mytag_names(self, cid):
        sql = (
            "SELECT Name FROM djmdMyTag WHERE ID IN ("
            "SELECT MyTagID FROM djmdSongMyTag WHERE ContentID=?)"
        )
        self.cur.execute(sql, (cid,))
        return [x[0] for x in self.fetchall()]

    # -- Other -------------------------------------------------------------------------

    def get_anlz_dir(self, content_id):
        item = self.get_content(content_id)
        dat_path = os.path.normpath(item["AnalysisDataPath"]).strip("\\/")
        return os.path.join(self._anlz_root, os.path.dirname(dat_path))

    def get_anlz_paths(self, content_id):
        root = self.get_anlz_dir(content_id)
        return get_anlz_paths(root)

    def read_anlz_files(self, content_id):
        root = self.get_anlz_dir(content_id)
        return read_anlz_files(root)
