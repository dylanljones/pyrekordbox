# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
import re
import base64
import blowfish
import logging
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from ..config import get_config
from ..utils import read_rekordbox6_asar
from ..anlz import get_anlz_paths, read_anlz_files
from .tables import DjmdContent
from . import tables

try:
    from pysqlcipher3 import dbapi2 as sqlite3  # noqa
except ImportError:
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
    """Opens the Rekordbox v6 master.db SQLite3 database for the use with SQLAlchemy.

    Parameters
    ----------
    path : str, optional
        The path of the database file. Uses the main Rekordbox v6 master.db database
        by default.
    unlock : bool, optional
        Flag if the database is encrypted and needs to be unlocked.
    sql_driver : Callable, optional
        The SQLite driver to used for opening the database. The standard `sqlite3`
        package is used as default driver.
    echo : bool, optional
        Echo flag for SQLAlchemy.

    Returns
    -------
    engine : sqlalchemy.engine.Engine
        The open SQLAlchemy engine instance for the Rekordbox v6 database.
    """
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
    """Opens a connection to the Rekordbox v6 master.db SQLite3 database.

    Parameters
    ----------
    path : str, optional
        The path of the database file. Uses the main Rekordbox v6 master.db database
        by default.
    unlock : bool, optional
        Flag if the database is encrypted and needs to be unlocked.
    sql_driver : Callable, optional
        The SQLite driver to used for opening the database. The standard `sqlite3`
        package is used as default driver.

    Returns
    -------
    con : sql_driver.Connection
        The opened Rekordbox v6 database connection.

    Examples
    --------
    Open the Rekordbox v6 master.db database:
    >>> db = open_rekordbox_database()

    Open a copy of the database:
    >>> db = open_rekordbox_database("path/to/master_copy.db")

    Open a decrypted copy of the database:
    >>> db = open_rekordbox_database("path/to/master_unlocked.db", unlock=False)

    To use the `pysqlcipher3` package as SQLite driver, either import it as
    >>> from pysqlcipher3 import dbapi2 as sqlite3
    >>> db = open_rekordbox_database("path/to/master_copy.db")

    or supply the package as driver:
    >>> from pysqlcipher3 import dbapi2
    >>> db = open_rekordbox_database("path/to/master_copy.db", sql_driver=dbapi2)
    """
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


def _parse_query_result(result, kwargs):
    if "ID" in kwargs:
        result = result.one()
    return result


class Rekordbox6Database:
    """Rekordbox v6 master.db database handler.

    Parameters
    ----------
    path : str, optional
        The path of the Rekordbox v6 database file. By default, pyrekordbox
        automatically finds the Rekordbox v6 master.db database file.
        This parameter is only required for opening other databases or if the
        configuration fails.
    unlock: bool, optional
        Flag if the database needs to be decrypted. Set to False if you are opening
        an unencrypted test database.

    See Also
    --------
    pyrekordbox.db6.tables: Rekordbox v6 database table definitions
    create_rekordbox_engine: Creates the SQLAlchemy engine for the Rekordbox v6 database

    Examples
    --------
    Pyrekordbox automatically finds the Rekordbox v6 master.db database file and
    opens it when initializing the object:

    >>> db = Rekordbox6Database()

    Use the included getters for querying the database:

    >>> db.get_content()[0]
    <DjmdContent(40110712   Title=NOISE)>
    """

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

    def commit(self):
        self.session.commit()

    # -- Table queries -----------------------------------------------------------------

    def get_active_censor(self, **kwargs):
        res = self.query(tables.DjmdActiveCensor).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_album(self, **kwargs):
        res = self.query(tables.DjmdAlbum).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_artist(self, **kwargs):
        res = self.query(tables.DjmdArtist).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_category(self, **kwargs):
        res = self.query(tables.DjmdCategory).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_color(self, **kwargs):
        res = self.query(tables.DjmdColor).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_content(self, **kwargs):
        res = self.query(tables.DjmdContent).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_cue(self, **kwargs):
        res = self.query(tables.DjmdCue).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_device(self, **kwargs):
        res = self.query(tables.DjmdDevice).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_genre(self, **kwargs):
        res = self.query(tables.DjmdGenre).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_history(self, **kwargs):
        res = self.query(tables.DjmdHistory).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_history_songs(self, id_):
        res = self.query(tables.DjmdSongHistory).filter_by(HistoryID=id_)
        return res

    def get_hot_cue_banklist(self, **kwargs):
        res = self.query(tables.DjmdHotCueBanklist).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_hot_cue_banklist_songs(self, id_):
        res = self.query(tables.DjmdSongHotCueBanklist).filter_by(HotCueBanklistID=id_)
        return res

    def get_key(self, **kwargs):
        res = self.query(tables.DjmdKey).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_label(self, **kwargs):
        res = self.query(tables.DjmdLabel).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_menu_items(self, **kwargs):
        res = self.query(tables.DjmdMenuItems).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_mixer_param(self, **kwargs):
        res = self.query(tables.DjmdMixerParam).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_my_tag(self, **kwargs):
        res = self.query(tables.DjmdMyTag).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_my_tag_songs(self, id_):
        res = self.query(tables.DjmdSongMyTag).filter_by(MyTagID=id_)
        return res

    def get_playlist(self, **kwargs):
        res = self.query(tables.DjmdPlaylist).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_playlist_songs(self, id_):
        res = self.query(tables.DjmdSongPlaylist).filter_by(PlaylistID=id_)
        return res

    def get_property(self, **kwargs):
        res = self.query(tables.DjmdProperty).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_related_tracks(self, **kwargs):
        res = self.query(tables.DjmdRelatedTracks).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_related_tracks_songs(self, id_):
        res = self.query(tables.DjmdSongRelatedTracks).filter_by(RelatedTracksID=id_)
        return res

    def get_sampler(self, **kwargs):
        res = self.query(tables.DjmdSampler).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_sampler_songs(self, id_):
        res = self.query(tables.DjmdSongSampler).filter_by(SamplerID=id_)
        return res

    def get_tag_list_songs(self, id_):
        res = self.query(tables.DjmdSongTagList).filter_by(ID=id_)
        return res

    def get_sort(self, **kwargs):
        res = self.query(tables.DjmdSort).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_agent_registry(self, **kwargs):
        res = self.query(tables.AgentRegistry).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_cloud_agent_registry(self, **kwargs):
        res = self.query(tables.CloudAgentRegistry).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_content_active_censor(self, **kwargs):
        res = self.query(tables.ContentActiveCensor).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_content_cue(self, **kwargs):
        res = self.query(tables.ContentCue).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_content_file(self, **kwargs):
        res = self.query(tables.ContentFile).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_hot_cue_banklist_cue(self, **kwargs):
        res = self.query(tables.HotCueBanklistCue).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_image_file(self, **kwargs):
        res = self.query(tables.ImageFile).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_setting_file(self, **kwargs):
        res = self.query(tables.SettingFile).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    def get_uuid_map(self, **kwargs):
        res = self.query(tables.UuidIDMap).filter_by(**kwargs)
        return _parse_query_result(res, kwargs)

    # ==================================================================================

    # noinspection PyUnresolvedReferences
    def search_content(self, text):
        """Searches the contents of the `DjmdContents` table.

        Parameters
        ----------
        text : str
            The search text.

        Returns
        -------
        results : list[DjmdContent]
            The resulting content elements.
        """
        # Search standard columns
        query = self.query(tables.DjmdContent).filter(
            or_(
                DjmdContent.Title.contains(text),
                DjmdContent.Commnt.contains(text),
                DjmdContent.SearchStr.contains(text),
            )
        )
        results = query.all()

        # Search artist (Artist, OrgArtist, Composer and Remixer)
        artist_attrs = ["Artist", "OrgArtist", "Composer", "Remixer"]
        for attr in artist_attrs:
            query = self.query(DjmdContent).join(getattr(DjmdContent, attr))
            results += query.filter(tables.DjmdArtist.Name.contains(text)).all()

        # Search album
        query = self.query(DjmdContent).join(DjmdContent.Album)
        results += query.filter(tables.DjmdAlbum.Name.contains(text)).all()

        # Search Genre
        query = self.query(DjmdContent).join(DjmdContent.Genre)
        results += query.filter(tables.DjmdGenre.Name.contains(text)).all()

        # Search Key
        query = self.query(DjmdContent).join(DjmdContent.Key)
        results += query.filter(tables.DjmdKey.ScaleName.contains(text)).all()

        return results

    def get_mysetting_paths(self):
        """Returns the file paths of the local Rekordbox MySetting files.

        Returns
        -------
        paths : list[str]
            the file paths of the local MySetting files.
        """
        paths = list()
        for item in self.get_setting_file():
            paths.append(os.path.join(self._db_dir, item.Path.lstrip("/\\")))
        return paths

    def get_anlz_dir(self, content):
        """Returns the directory path containing the ANLZ analysis files of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the `DjmdContent` entry.

        Returns
        -------
        anlz_dir : str
            The path of the directory containing the analysis files for the content.
        """
        if isinstance(content, (int, str)):
            content = self.get_content(ID=content)

        dat_path = os.path.normpath(content.AnalysisDataPath).strip("\\/")
        path = os.path.join(self._anlz_root, os.path.dirname(dat_path))
        assert os.path.exists(path)
        return path

    def get_anlz_paths(self, content):
        """Returns all existing ANLZ analysis file paths of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the `DjmdContent` entry.

        Returns
        -------
        anlz_paths : dict[str, str]
            The analysis file paths for the content as dictionary. The keys of the
            dictionary are the file types ("DAT", "EXT" or "EX2").
        """
        root = self.get_anlz_dir(content)
        return get_anlz_paths(root)

    def read_anlz_files(self, content):
        """Reads all existing ANLZ analysis files of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the `DjmdContent` entry.

        Returns
        -------
        anlz_files : dict[str, AnlzFile]
            The analysis files for the content as dictionary. The keys of the
            dictionary are the file paths.
        """
        root = self.get_anlz_dir(content)
        return read_anlz_files(root)

    def set_content_path(self, content_id, path):
        content = self.get_content(ID=content_id)
        path = path.replace("\\", "/")
        content.FolderPath = path.replace("\\", "/")
