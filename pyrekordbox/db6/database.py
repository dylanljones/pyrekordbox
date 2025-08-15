# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-08-13

import datetime
import logging
import secrets
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from uuid import uuid4

from sqlalchemy import MetaData, create_engine, event, or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.sqltypes import DateTime, String

from ..anlz import AnlzFile, get_anlz_paths, read_anlz_files  # type: ignore[attr-defined]
from ..config import get_config
from ..utils import deobfuscate, get_rekordbox_pid
from . import tables
from .aux_files import MasterPlaylistXml
from .registry import RekordboxAgentRegistry
from .smartlist import SmartList
from .tables import DjmdContent, DjmdPlaylist, DjmdSongPlaylist, FileType, PlaylistType

try:
    from sqlcipher3 import dbapi2 as sqlite3  # noqa

    _sqlcipher_available = True
except ImportError:  # pragma: no cover
    import sqlite3  # type: ignore[no-redef]

    _sqlcipher_available = False

SPECIAL_PLAYLIST_IDS = [
    "100000",  # Cloud Library Sync
    "200000",  # CUE Analysis Playlist
]

BLOB = b"PN_Pq^*N>(JYe*u^8;Yg76HuZ<mR13S?=>)b9;DpoTXV(6ItkU`}8*m6tx_I{Solh_N#dfe{v="

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]
ContentLike = Union[DjmdContent, int, str]
PlaylistLike = Union[DjmdPlaylist, int, str]
T = TypeVar("T", bound=tables.Base)


def _parse_query_result(query: Query[T], kwargs: Dict[str, Any]) -> Any:
    if "ID" in kwargs or "registry_id" in kwargs:
        try:
            result: T = query.one()
            return result
        except NoResultFound:
            return None
    return query


class SessionNotInitializedError(Exception):
    def __init__(self) -> None:
        super().__init__("Sqlite-session not intialized!")


class Rekordbox6Database:
    """Rekordbox v6 master.db database handler.

    Parameters
    ----------
    path : str or Path, optional
        The path of the Rekordbox v6 database file. By default, pyrekordbox
        automatically finds the Rekordbox v6 master.db database file.
        This parameter is only required for opening other databases or if the
        configuration fails.
    db_dir: str, optional
        The path of the Rekordbox v6 database directory. By default, pyrekordbox
        automatically finds the Rekordbox v6 database directory. Usually this is also
        the root directory of the analysis files. This parameter is only required for
        finding the analysis root directory if you are opening a database, that is
        stored somewhere else.
    key : str, optional
        The database key. By default, pyrekordbox automatically reads the database
        key from the Rekordbox v6 configuration file. This parameter is only required
        if the key extraction fails.
    unlock: bool, optional
        Flag if the database needs to be decrypted. Set to False if you are opening
        an unencrypted test database.

    Attributes
    ----------
    engine : sqlalchemy.engine.Engine
        The SQLAlchemy engine instance for the Rekordbox v6 database.
    session : sqlalchemy.orm.Session
        The SQLAlchemy session instance bound to the engine.

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

    def __init__(
        self, path: PathLike = None, db_dir: PathLike = "", key: str = "", unlock: bool = True
    ):
        # get config of latest supported version
        rb_config = get_config("rekordbox7")
        if not rb_config:
            rb_config = get_config("rekordbox6")

        pid = get_rekordbox_pid()
        if pid:
            logger.warning("Rekordbox is running!")

        if not path:
            # Get path from the RB config
            path = rb_config.get("db_path", "")
            if not path:
                pdir = get_config("pioneer", "install_dir")
                raise FileNotFoundError(f"No Rekordbox v6/v7 directory found in '{pdir}'")
        db_path: Path = Path(path)
        # make sure file exists
        if not db_path.exists():
            raise FileNotFoundError(f"File '{db_path}' does not exist!")
        # Open database
        if unlock:
            if not _sqlcipher_available:  # pragma: no cover
                raise ImportError("Could not unlock database: 'sqlcipher3' package not found")

            if not key:  # pragma: no cover
                key = deobfuscate(BLOB)
            elif not key.startswith("402fd"):
                # Check if key looks like a valid key
                raise ValueError("The provided database key doesn't look valid!")

            # Unlock database and create engine
            logger.debug("Key: %s", key)
            url = f"sqlite+pysqlcipher://:{key}@/{db_path}?"
            engine = create_engine(url, module=sqlite3)
        else:
            engine = create_engine(f"sqlite:///{db_path}")

        if not db_dir:
            db_dir = db_path.parent
        db_directory: Path = Path(db_dir)
        if not db_directory.exists():
            raise FileNotFoundError(f"Database directory '{db_directory}' does not exist!")

        self.engine = engine
        self.session: Optional[Session] = None

        self.registry = RekordboxAgentRegistry(self)
        self._events: Dict[str, Callable[[Any], None]] = dict()
        self.playlist_xml: Optional[MasterPlaylistXml]
        try:
            self.playlist_xml = MasterPlaylistXml(db_dir=db_directory)
        except FileNotFoundError:
            logger.warning(f"No masterPlaylists6.xml found in {db_directory}")
            self.playlist_xml = None

        self._db_dir = db_directory
        self._share_dir: Path = db_directory / "share"

        self.open()

    @property
    def no_autoflush(self) -> Any:
        """Creates a no-autoflush context."""
        if self.session is None:
            raise SessionNotInitializedError()
        return self.session.no_autoflush

    @property
    def db_directory(self) -> Path:
        return self._db_dir

    @property
    def share_directory(self) -> Path:
        return self._share_dir

    def open(self) -> None:
        """Open the database by instantiating a new session using the SQLAchemy engine.

        A new session instance is only created if the session was closed previously.

        Examples
        --------
        >>> db = Rekordbox6Database()
        >>> db.close()
        >>> db.open()
        """
        if self.session is None:
            self.session = Session(bind=self.engine)
            self.registry.clear_buffer()

    def close(self) -> None:
        """Close the currently active session."""
        if self.session is None:
            raise SessionNotInitializedError()
        for key in self._events:
            self.unregister_event(key)
        self.registry.clear_buffer()
        self.session.close()
        self.session = None

    def __enter__(self) -> "Rekordbox6Database":
        return self

    def __exit__(
        self,
        type_: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()

    def register_event(self, identifier: str, fn: Callable[[Any], None]) -> None:
        """Registers a session event callback.

        Parameters
        ----------
        identifier : str
            The identifier of the event, for example 'before_flush', 'after_commit', ...
            See the SQLAlchemy documentation for a list of valid event identifiers.
        fn : callable
            The event callback method.
        """
        if self.session is None:
            raise SessionNotInitializedError()
        event.listen(self.session, identifier, fn)
        self._events[identifier] = fn

    def unregister_event(self, identifier: str) -> None:
        """Removes an existing session event callback.

        Parameters
        ----------
        identifier : str
            The identifier of the event
        """
        if self.session is None:
            raise SessionNotInitializedError()
        fn = self._events[identifier]
        event.remove(self.session, identifier, fn)

    def query(self, *entities: Any, **kwargs: Any) -> Any:
        """Creates a new SQL query for the given entities.

        Parameters
        ----------
        *entities : Base
            The table objects for which the query is created.
        **kwargs
            Arbitrary keyword arguments used for creating the query.

        Returns
        -------
        query : sqlalchemy.orm.query.Query
            The SQLAlchemy ``Query`` object.

        Examples
        --------
        Query the ``DjmdContent`` table

        >>> db = Rekordbox6Database()
        >>> query = db.query(DjmdContent)

        Query the `Title` attribute of the ``DjmdContent`` table

        >>> db = Rekordbox6Database()
        >>> query = db.query(DjmdContent.Title)
        """
        if self.session is None:
            raise SessionNotInitializedError()
        return self.session.query(*entities, **kwargs)

    def add(self, instance: tables.Base) -> None:
        """Add an element to the Rekordbox database.

        Parameters
        ----------
        instance : tables.Base
            The table entry to add.
        """
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.add(instance)
        self.registry.on_create(instance)

    def delete(self, instance: tables.Base) -> None:
        """Delete an element from the Rekordbox database.

        Parameters
        ----------
        instance : tables.Base
            The table entry to delte.
        """
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.delete(instance)
        self.registry.on_delete(instance)

    def get_local_usn(self) -> int:
        """Returns the local sequence number (update count) of Rekordbox.

        Any changes made to the `Djmd...` tables increments the local update count of
        Rekordbox. The ``usn`` entry of the changed row is set to the corresponding
        update count.

        Returns
        -------
        usn : int
            The value of the local update count.
        """
        return self.registry.get_local_update_count()

    def set_local_usn(self, usn: int) -> None:
        """Sets the local sequence number (update count) of Rekordbox.

        Parameters
        ----------
        usn : int or str
            The new update sequence number.
        """
        self.registry.set_local_update_count(usn)

    def increment_local_usn(self, num: int = 1) -> int:
        """Increments the local update sequence number (update count) of Rekordbox.

        Parameters
        ----------
        num : int, optional
            The number of times to increment the update counter. By default, the counter
            is incremented by 1.

        Returns
        -------
        usn : int
            The value of the incremented local update count.

        Examples
        --------
        >>> db = Rekordbox6Database()
        >>> db.get_local_usn()
        70500

        >>> db.increment_local_usn()
        70501

        >>> db.get_local_usn()
        70501
        """
        return self.registry.increment_local_update_count(num)

    def autoincrement_usn(self, set_row_usn: bool = True) -> int:
        """Auto-increments the local USN for all uncommited changes.

        Parameters
        ----------
        set_row_usn : bool, optional
            If True, set the ``rb_local_usn`` value of updated or added rows according
            to the uncommited update sequence.

        Returns
        -------
        new_usn : int
            The new local update sequence number after applying all updates.

        Examples
        --------
        >>> db = Rekordbox6Database()
        >>> db.get_local_usn()
        70500

        >>> content = db.get_content().first()
        >>> playlist = db.get_playlist().first()
        >>> content.Title = "New Title"
        >>> playlist.Name = "New Name"
        >>> db.autoincrement_usn(set_row_usn=True)
        >>> db.get_local_usn()
        70502
        """
        return self.registry.autoincrement_local_update_count(set_row_usn)

    def flush(self) -> None:
        """Flushes the buffer of the SQLAlchemy session instance."""
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.flush()

    def commit(self, autoinc: bool = True) -> None:
        """Commit the changes made to the database.

        Parameters
        ----------
        autoinc : bool, optional
            If True, auto-increment the local and row USN's before commiting the
            changes made to the database.

        See Also
        --------
        autoincrement_usn : Auto-increments the local Rekordbox USN's.
        """
        if self.session is None:
            raise SessionNotInitializedError()
        pid = get_rekordbox_pid()
        if pid:
            raise RuntimeError(
                "Rekordbox is running. Please close Rekordbox before commiting changes."
            )
        if autoinc:
            self.registry.autoincrement_local_update_count(set_row_usn=True)
        self.session.commit()
        self.registry.clear_buffer()

        # Update the masterPlaylists6.xml file
        if self.playlist_xml is not None:
            # Sync the updated_at values of the playlists in the DB and the XML file
            for pl in self.get_playlist():
                plxml = self.playlist_xml.get(pl.ID)
                if plxml is not None:
                    ts = plxml["Timestamp"]
                    diff = pl.updated_at - ts
                    if abs(diff.total_seconds()) > 1:
                        logger.debug("Updating updated_at of playlist %s in XML", pl.ID)
                        self.playlist_xml.update(pl.ID, updated_at=pl.updated_at)
                else:
                    # Dont warn for special playlists
                    if pl.ID not in SPECIAL_PLAYLIST_IDS:
                        logger.warning(
                            f"Playlist {pl.ID} not found in masterPlaylists6.xml! "
                            "Did you add it manually? "
                            "Use the create_playlist method instead."
                        )

            # Save the XML file if it was modified
            if self.playlist_xml.modified:
                self.playlist_xml.save()

    def rollback(self) -> None:
        """Rolls back the uncommited changes to the database."""
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.rollback()
        self.registry.clear_buffer()

    # -- Table queries -----------------------------------------------------------------

    def get_active_censor(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdActiveCensor`` table."""
        query = self.query(tables.DjmdActiveCensor).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_album(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdAlbum`` table."""
        query = self.query(tables.DjmdAlbum).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_artist(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdArtist`` table."""
        query = self.query(tables.DjmdArtist).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_category(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdCategory`` table."""
        query = self.query(tables.DjmdCategory).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_color(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdColor`` table."""
        query = self.query(tables.DjmdColor).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_content(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdContent`` table."""
        query = self.query(tables.DjmdContent).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    # noinspection PyUnresolvedReferences
    def search_content(self, text: str) -> List[DjmdContent]:
        """Searches the contents of the ``DjmdContent`` table.

        The search is case-insensitive and includes the following collumns of the
        ``DjmdContent`` table:

        - `Album`
        - `Artist`
        - `Commnt`
        - `Composer`
        - `Genre`
        - `Key`
        - `OrgArtist`
        - `Remixer`

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
        results = set(query.all())

        # Search artist (Artist, OrgArtist, Composer and Remixer)
        artist_attrs = ["Artist", "OrgArtist", "Composer", "Remixer"]
        for attr in artist_attrs:
            query = self.query(DjmdContent).join(getattr(DjmdContent, attr))
            results.update(query.filter(tables.DjmdArtist.Name.contains(text)).all())

        # Search album
        query = self.query(DjmdContent).join(DjmdContent.Album)
        results.update(query.filter(tables.DjmdAlbum.Name.contains(text)).all())

        # Search Genre
        query = self.query(DjmdContent).join(DjmdContent.Genre)
        results.update(query.filter(tables.DjmdGenre.Name.contains(text)).all())

        # Search Key
        query = self.query(DjmdContent).join(DjmdContent.Key)
        results.update(query.filter(tables.DjmdKey.ScaleName.contains(text)).all())

        result_list: List[DjmdContent] = list(results)
        result_list.sort(key=lambda x: x.ID)
        return result_list

    def get_cue(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdCue`` table."""
        query = self.query(tables.DjmdCue).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_device(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdDevice`` table."""
        query = self.query(tables.DjmdDevice).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_genre(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdGenre`` table."""
        query = self.query(tables.DjmdGenre).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_history(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdHistory`` table."""
        query = self.query(tables.DjmdHistory).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_history_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongHistory`` table."""
        query = self.query(tables.DjmdSongHistory).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_hot_cue_banklist(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdHotCueBanklist`` table."""
        query = self.query(tables.DjmdHotCueBanklist).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_hot_cue_banklist_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongHotCueBanklist`` table."""
        query = self.query(tables.DjmdSongHotCueBanklist).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_key(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdKey`` table."""
        query = self.query(tables.DjmdKey).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_label(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdLabel`` table."""
        query = self.query(tables.DjmdLabel).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_menu_items(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdMenuItems`` table."""
        query = self.query(tables.DjmdMenuItems).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_mixer_param(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdMixerParam`` table."""
        query = self.query(tables.DjmdMixerParam).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_my_tag(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdMyTag`` table."""
        query = self.query(tables.DjmdMyTag).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_my_tag_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongMyTag`` table."""
        query = self.query(tables.DjmdSongMyTag).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_playlist(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdPlaylist`` table."""
        query = self.query(tables.DjmdPlaylist).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_playlist_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongPlaylist`` table."""
        query = self.query(tables.DjmdSongPlaylist).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_playlist_contents(self, playlist: PlaylistLike, *entities: tables.Base) -> Any:
        """Return the contents of a regular or smart playlist.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist instance. Can either be a :class:`DjmdPlaylist`
            object or a playlist ID.
        *entities : Base
            The table objects for which the query is created. If no entities
            are given, the query will return the :class:`DjmdContent` objects.

        Returns
        -------
        query : sqlalchemy.orm.query.Query
            The SQLAlchemy ``Query`` object. The query contains the content instances
            or the selected columns if ``entities`` are given.

        Examples
        --------
        Return the content instances in the playlist

        >>> db = Rekordbox6Database()
        >>> pl = db.get_playlist(Name="My Playlist").one()
        >>> db.get_playlist_contents(pl).all()
        [<DjmdContent(12345678   Title=Title1)>, <DjmdContent(23456789   Title=Title2)>]

        Return only the content IDs

        >>> db.get_playlist_contents(pl, DjmdContent.ID).all()
        [('12345678',), ('23456789',)]
        """
        plist: DjmdPlaylist
        if isinstance(playlist, (int, str)):
            plist = self.get_playlist(ID=playlist)
        else:
            plist = playlist

        if plist.is_folder:
            raise ValueError(f"Playlist {plist} is a playlist folder.")

        if not entities:
            entities = [
                DjmdContent,
            ]  # type: ignore[assignment]

        if plist.is_smart_playlist:
            smartlist = SmartList()
            smartlist.parse(plist.SmartList)
            filter_clause = smartlist.filter_clause()
        else:
            sub_query = self.query(tables.DjmdSongPlaylist.ContentID).filter(
                tables.DjmdSongPlaylist.PlaylistID == plist.ID
            )
            filter_clause = DjmdContent.ID.in_(select(sub_query.subquery()))

        return self.query(*entities).filter(filter_clause)

    def get_property(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdProperty`` table."""
        query = self.query(tables.DjmdProperty).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_related_tracks(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdRelatedTracks`` table."""
        query = self.query(tables.DjmdRelatedTracks).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_related_tracks_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongRelatedTracks`` table."""
        query = self.query(tables.DjmdSongRelatedTracks).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_sampler(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSampler`` table."""
        query = self.query(tables.DjmdSampler).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_sampler_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongSampler`` table."""
        query = self.query(tables.DjmdSongSampler).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_tag_list_songs(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSongTagList`` table."""
        query = self.query(tables.DjmdSongTagList).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_sort(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``DjmdSort`` table."""
        query = self.query(tables.DjmdSort).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_agent_registry(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``AgentRegistry`` table."""
        query = self.query(tables.AgentRegistry).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_cloud_agent_registry(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``CloudAgentRegistry`` table."""
        query = self.query(tables.CloudAgentRegistry).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_content_active_censor(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``ContentActiveCensor`` table."""
        query = self.query(tables.ContentActiveCensor).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_content_cue(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``ContentCue`` table."""
        query = self.query(tables.ContentCue).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_content_file(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``ContentFile`` table."""
        query = self.query(tables.ContentFile).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_hot_cue_banklist_cue(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``HotCueBanklistCue`` table."""
        query = self.query(tables.HotCueBanklistCue).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_image_file(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``ImageFile`` table."""
        query = self.query(tables.ImageFile).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_setting_file(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``SettingFile`` table."""
        query = self.query(tables.SettingFile).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    def get_uuid_map(self, **kwargs: Any) -> Any:
        """Creates a filtered query for the ``UuidIDMap`` table."""
        query = self.query(tables.UuidIDMap).filter_by(**kwargs)
        return _parse_query_result(query, kwargs)

    # -- Database updates --------------------------------------------------------------

    def generate_unused_id(
        self, table: Type[tables.Base], is_28_bit: bool = True, id_field_name: str = "ID"
    ) -> int:
        """Generates an unused ID for the given table."""
        max_tries = 1000000
        for _ in range(max_tries):
            # Generate random ID
            buf = secrets.token_bytes(4)
            id_ = (buf[0] << 24) + (buf[1] << 16) + (buf[2] << 8) + buf[3] >> 0
            if is_28_bit:
                id_ = id_ >> 4
            if id_ < 100:
                continue
            # Check if ID is already used
            id_field = getattr(table, id_field_name)
            query = self.query(id_field).filter(id_field == id_)
            used = self.query(query.exists()).scalar()
            if not used:
                return id_

        raise ValueError("Could not generate unused ID")

    def add_to_playlist(
        self, playlist: PlaylistLike, content: ContentLike, track_no: int = None
    ) -> tables.DjmdSongPlaylist:
        """Adds a track to a playlist.

        Creates a new :class:`DjmdSongPlaylist` object corresponding to the given
        content and adds it to the playlist.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist to add the track to. Can either be a :class:`DjmdPlaylist`
            object or a playlist ID.
        content : DjmdContent or int or str
            The content to add to the playlist. Can either be a :class:`DjmdContent`
            object or a content ID.
        track_no : int, optional
            The track number to add the content to. If not specified, the track
            will be added to the end of the playlist.

        Returns
        -------
        song: DjmdSongPlaylist
            The song playlist object that was created from the content.

        Raises
        ------
        ValueError : If the playlist is a folder or smart playlist.
        ValueError : If the track number is less than 1 or to large.

        Examples
        --------
        Add a track to the end of a playlist:

        >>> db = Rekordbox6Database()
        >>> cid = 12345  # Content ID
        >>> pid = 56789  # Playlist ID
        >>> db.add_to_playlist(pid, cid)
        <DjmdSongPlaylist(c803dfde-2236-4659-b3d7-e57221663375)>

        Add a track to the beginning of a playlist:

        >>> new_song = db.add_to_playlist(pid, cid, track_no=1)
        >>> new_song.TrackNo
        1
        """
        plist: DjmdPlaylist
        cont: DjmdContent
        if isinstance(playlist, (int, str)):
            plist = self.get_playlist(ID=playlist)
        else:
            plist = playlist

        if isinstance(content, (int, str)):
            cont = self.get_content(ID=content)
        else:
            cont = content

        # Check playlist attribute (can't be folder or smart playlist)
        if plist.Attribute != 0:
            raise ValueError("Playlist must be a normal playlist")

        uuid = str(uuid4())
        id_ = str(uuid4())
        now = datetime.datetime.now()
        nsongs = self.query(tables.DjmdSongPlaylist).filter_by(PlaylistID=plist.ID).count()
        if track_no is not None:
            insert_at_end = False
            track_no = int(track_no)
            if track_no < 1:
                raise ValueError("Track number must be greater than 0")
            if track_no > nsongs + 1:
                raise ValueError(f"Track number too high, parent contains {nsongs} items")
        else:
            insert_at_end = True
            track_no = nsongs + 1

        cid = cont.ID
        pid = plist.ID

        logger.info("Adding content with ID=%s to playlist with ID=%s:", cid, pid)
        logger.debug("Content ID:  %s", cid)
        logger.debug("Playlist ID: %s", pid)
        logger.debug("ID:          %s", id_)
        logger.debug("UUID:        %s", uuid)
        logger.debug("TrackNo:     %s", track_no)

        moved = list()
        if not insert_at_end:
            self.registry.disable_tracking()
            # Update track numbers higher than the removed track
            query = (
                self.query(tables.DjmdSongPlaylist)
                .filter(
                    tables.DjmdSongPlaylist.PlaylistID == plist.ID,
                    tables.DjmdSongPlaylist.TrackNo >= track_no,
                )
                .order_by(tables.DjmdSongPlaylist.TrackNo)
            )
            for other_song in query:
                other_song.TrackNo += 1
                other_song.updated_at = now
                moved.append(other_song)
            self.registry.enable_tracking()

        # Add song to playlist
        song: tables.DjmdSongPlaylist = tables.DjmdSongPlaylist.create(
            ID=id_,
            PlaylistID=str(pid),
            ContentID=str(cid),
            TrackNo=track_no,
            UUID=uuid,
            created_at=now,
            updated_at=now,
        )
        self.add(song)
        if not insert_at_end:
            moved.append(song)
            self.registry.on_move(moved)

        return song

    def remove_from_playlist(
        self,
        playlist: PlaylistLike,
        song: Union[tables.DjmdSongPlaylist, int, str],
    ) -> None:
        """Removes a track from a playlist.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist to remove the track from. Can either be a :class:`DjmdPlaylist`
            object or a playlist ID.
        song : DjmdSongPlaylist or int or str
            The song to remove from the playlist. Can either be a
            :class:`DjmdSongPlaylist` object or a song ID.

        Examples
        --------
        Remove a track from a playlist:

        >>> db = Rekordbox6Database()
        >>> pid = 56789
        >>> pl = db.get_playlist(ID=pid)
        >>> song = pl.Songs[0]
        >>> db.remove_from_playlist(pl, song)
        """
        plist: DjmdPlaylist
        plist_song: DjmdSongPlaylist
        if isinstance(playlist, (int, str)):
            plist = self.get_playlist(ID=playlist)
        else:
            plist = playlist

        if isinstance(song, (int, str)):
            plist_song = self.query(tables.DjmdSongPlaylist).filter_by(ID=song).one()
        else:
            plist_song = song

        if not isinstance(plist_song, tables.DjmdSongPlaylist):
            raise ValueError(
                "Playlist must be a DjmdSongPlaylist or corresponding playlist song ID!"
            )

        logger.info("Removing song with ID=%s from playlist with ID=%s", plist_song.ID, plist.ID)
        now = datetime.datetime.now()
        # Remove track from playlist
        track_no = plist_song.TrackNo
        self.delete(plist_song)
        self.commit()
        # Update track numbers higher than the removed track
        query = (
            self.query(tables.DjmdSongPlaylist)
            .filter(
                tables.DjmdSongPlaylist.PlaylistID == plist.ID,
                tables.DjmdSongPlaylist.TrackNo > track_no,
            )
            .order_by(tables.DjmdSongPlaylist.TrackNo)
        )
        moved = list()
        with self.registry.disabled():
            for other_song in query:
                other_song.TrackNo -= 1
                other_song.updated_at = now
                moved.append(other_song)

        if moved:
            self.registry.on_move(moved)

    def move_song_in_playlist(
        self,
        playlist: PlaylistLike,
        song: Union[tables.DjmdSongPlaylist, int, str],
        new_track_no: int,
    ) -> None:
        """Sets a new track number of a song.

        Also updates the track numbers of the other songs in the playlist.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist the track is in. Can either be a :class:`DjmdPlaylist`
            object or a playlist ID.
        song : DjmdSongPlaylist or int or str
            The song to move inside the playlist. Can either be a
            :class:`DjmdSongPlaylist` object or a song ID.
        new_track_no : int
            The new track number of the song. Must be greater than 0 and less than
            the number of songs in the playlist.

        Examples
        --------
        Take a playlist containing a few tracks:

        >>> db = Rekordbox6Database()
        >>> pid = 56789
        >>> pl = db.get_playlist(ID=pid)
        >>> songs = sorted(pl.Songs, key=lambda x: x.TrackNo)
        >>> [s.Content.Title for s in songs]  # noqa
        ['Demo Track 1', 'Demo Track 2', 'HORN', 'NOISE']

        Move a track forward in a playlist:

        >>> song = songs[2]
        >>> db.move_song_in_playlist(pl, song, new_track_no=1)
        >>> [s.Content.Title for s in sorted(pl.Songs, key=lambda x: x.TrackNo)]  # noqa
        ['HORN', 'Demo Track 1', 'Demo Track 2', 'NOISE']

        Move a track backward in a playlist:

        >>> song = songs[1]
        >>> db.move_song_in_playlist(pl, song, new_track_no=4)
        >>> [s.Content.Title for s in sorted(pl.Songs, key=lambda x: x.TrackNo)]  # noqa
        ['Demo Track 1', 'HORN', 'NOISE', 'Demo Track 2']
        """
        plist: DjmdPlaylist
        plist_song: DjmdSongPlaylist
        if isinstance(playlist, (int, str)):
            plist = self.get_playlist(ID=playlist)
        else:
            plist = playlist

        if isinstance(song, (int, str)):
            plist_song = self.query(tables.DjmdSongPlaylist).filter_by(ID=song).one()
        else:
            plist_song = song

        nsongs = self.query(tables.DjmdSongPlaylist).filter_by(PlaylistID=plist.ID).count()
        if new_track_no < 1:
            raise ValueError("Track number must be greater than 0")
        if new_track_no > nsongs + 1:
            raise ValueError(f"Track number too high, parent contains {nsongs} items")
        logger.info(
            "Moving song with ID=%s in playlist with ID=%s to %s",
            plist_song.ID,
            plist.ID,
            new_track_no,
        )
        now = datetime.datetime.now()
        old_track_no = plist_song.TrackNo

        self.registry.disable_tracking()
        moved = list()
        if new_track_no > old_track_no:
            query = (
                self.query(tables.DjmdSongPlaylist)
                .filter(
                    tables.DjmdSongPlaylist.PlaylistID == plist.ID,
                    old_track_no < tables.DjmdSongPlaylist.TrackNo,
                    tables.DjmdSongPlaylist.TrackNo <= new_track_no,
                )
                .order_by(tables.DjmdSongPlaylist.TrackNo)
            )
            for other_song in query:
                other_song.TrackNo -= 1
                other_song.updated_at = now
                moved.append(other_song)
        elif new_track_no < old_track_no:
            query = self.query(tables.DjmdSongPlaylist).filter(
                tables.DjmdSongPlaylist.PlaylistID == plist.ID,
                new_track_no <= tables.DjmdSongPlaylist.TrackNo,
                tables.DjmdSongPlaylist.TrackNo < old_track_no,
            )
            for other_song in query:
                other_song.TrackNo += 1
                other_song.updated_at = now
                moved.append(other_song)
        else:
            return

        plist_song.TrackNo = new_track_no
        plist_song.updated_at = now
        moved.append(song)

        self.registry.enable_tracking()
        self.registry.on_move(moved)

    def _create_playlist(
        self,
        name: str,
        seq: Optional[int],
        image_path: Optional[str],
        parent: Optional[PlaylistLike],
        smart_list: Optional[SmartList] = None,
        attribute: int = None,
    ) -> DjmdPlaylist:
        """Creates a new playlist object."""
        table = tables.DjmdPlaylist
        id_ = str(self.generate_unused_id(table, is_28_bit=True))
        uuid = str(uuid4())
        attrib = int(attribute) if attribute is not None else 0
        now = datetime.datetime.now()
        if smart_list is not None:
            # Set the playlist ID in the smart list and generate XML
            smart_list.playlist_id = id_
            smart_list_xml = smart_list.to_xml()
        else:
            smart_list_xml = None

        if parent is None:
            # If no parent is given, use root playlist
            parent_id = "root"
        elif isinstance(parent, tables.DjmdPlaylist):
            # Check if parent is a folder
            parent_id = parent.ID
            if parent.Attribute != 1:
                raise ValueError("Parent is not a folder")
        else:
            # Check if parent exists and is a folder
            parent_id = str(parent)
            query = self.query(table.ID).filter(table.ID == parent_id, table.Attribute == 1)
            if not self.query(query.exists()).scalar():
                raise ValueError("Parent does not exist or is not a folder")

        n = self.get_playlist(ParentID=parent_id).count()
        logger.debug("Parent playlist with ID=%s contains %s items", parent_id, n)

        if seq is None:
            # New playlist is last in parents
            seq = n + 1
            insert_at_end = True
        else:
            # Check if sequence number is valid
            insert_at_end = False
            if seq < 1:
                raise ValueError("Sequence number must be greater than 0")
            elif seq > n + 1:
                raise ValueError(f"Sequence number too high, parent contains {n} items")

        logger.debug("ID:          %s", id_)
        logger.debug("UUID:        %s", uuid)
        logger.debug("Name:        %s", name)
        logger.debug("Parent ID:   %s", parent_id)
        logger.debug("Seq:         %s", seq)
        logger.debug("Attribute:   %s", attrib)
        logger.debug("Smart List:  %s", smart_list_xml)
        logger.debug("Image Path:  %s", image_path)

        # Update seq numbers higher than the new seq number
        if not insert_at_end:
            query = self.query(tables.DjmdPlaylist).filter(
                tables.DjmdPlaylist.ParentID == parent_id,
                tables.DjmdPlaylist.Seq >= seq,
            )
            for pl in query:
                pl.Seq += 1
                with self.registry.disabled():
                    pl.updated_at = now

        # Add new playlist to database
        # First create with name 'New playlist'
        playlist: DjmdPlaylist = table.create(
            ID=id_,
            Seq=seq,
            Name="New playlist",
            ImagePath=image_path,
            Attribute=attrib,
            ParentID=parent_id,
            SmartList=smart_list_xml,
            UUID=uuid,
            created_at=now,
            updated_at=now,
        )
        self.add(playlist)
        # Then update with correct name for correct USN
        playlist.Name = name

        # Update masterPlaylists6.xml
        if self.playlist_xml is not None:
            self.playlist_xml.add(id_, parent_id, attrib, now, lib_type=0, check_type=0)

        return playlist

    def create_playlist(
        self, name: str, parent: PlaylistLike = None, seq: int = None, image_path: str = None
    ) -> DjmdPlaylist:
        """Creates a new playlist in the database.

        Parameters
        ----------
        name : str
            The name of the new playlist.
        parent : DjmdPlaylist or int or str, optional
            The parent playlist of the new playlist. If not given, the playlist will be
            added to the root playlist. Can either be a :class:`DjmdPlaylist` object or
            a playlist ID.
        seq : int, optional
            The sequence number of the new playlist. If not given, the playlist will be
            added at the end of the parent playlist.
        image_path : str, optional
            The path to the image file of the new playlist.

        Returns
        -------
        playlist : DjmdPlaylist
            The newly created playlist.

        Raises
        ------
        ValueError : If the parent playlist is not a folder.
        ValueError : If the sequence number is less than 1 or to large.

        Examples
        --------
        Create a new playlist in the root playlist:

        >>> db = Rekordbox6Database()
        >>> pl = db.create_playlist("My Playlist")
        >>> pl.ParentID
        'root'

        Create a new playlist in a folder:

        >>> folder = db.get_playlist(Name="My Folder").one()
        >>> pl = db.create_playlist("My Playlist", parent=folder)
        >>> pl.ParentID
        '123456'
        """
        logger.info("Creating playlist %s", name)
        return self._create_playlist(name, seq, image_path, parent, attribute=PlaylistType.PLAYLIST)

    def create_playlist_folder(
        self, name: str, parent: PlaylistLike = None, seq: int = None, image_path: str = None
    ) -> DjmdPlaylist:
        """Creates a new playlist folder in the database.

        Parameters
        ----------
        name : str
            The name of the new playlist folder.
        parent : DjmdPlaylist or int or str, optional
            The parent playlist of the new folder. If not given, the playlist will be
            added to the root playlist. Can either be a :class:`DjmdPlaylist` object or
            a playlist ID.
        seq : int, optional
            The sequence number of the new folder. If not given, the playlist will be
            added at the end of the parent playlist.
        image_path : str, optional
            The path to the image file of the new playlist.

        Returns
        -------
        playlist_folder : DjmdPlaylist
            The newly created playlist folder.

        Examples
        --------
        Create a new playlist folder in the root playlist:

        >>> db = Rekordbox6Database()
        >>> folder1 = db.create_playlist_folder("My Playlist Folder")
        >>> folder1.ParentID
        'root'

        Create a new playlist folder in the other folder:

        >>> folder2 = db.create_playlist("My Playlist Folder2", parent=folder1)
        >>> folder2.ParentID
        '123456'
        """
        logger.info("Creating playlist folder %s", name)
        return self._create_playlist(name, seq, image_path, parent, attribute=PlaylistType.FOLDER)

    def create_smart_playlist(
        self,
        name: str,
        smart_list: SmartList,
        parent: PlaylistLike = None,
        seq: int = None,
        image_path: str = None,
    ) -> DjmdPlaylist:
        """Creates a new smart playlist in the database.

        Parameters
        ----------
        name : str
            The name of the new smart playlist.
        smart_list : SmartList
            The smart list conditions to use for the new playlist.
        parent : DjmdPlaylist or int or str, optional
            The parent playlist of the new playlist. If not given, the playlist will be
            added to the root playlist. Can either be a :class:`DjmdPlaylist` object or
            a playlist ID.
        seq : int, optional
            The sequence number of the new playlist. If not given, the playlist will be
            added at the end of the parent playlist.
        image_path : str, optional
            The path to the image file of the new playlist.

        Returns
        -------
        playlist : DjmdPlaylist
            The newly created playlist.

        Examples
        --------
        Create a new smart list which we will use for the new smart playlist:

        >>> smart = SmartList(logical_operator=1)  # ALL conditions must be met
        >>> smart.add_condition("genre", operator=1, value_left="House")  # is House

        Create a new smart playlist in the root playlist:
        >>> db = Rekordbox6Database()
        >>> pl = db.create_smart_playlist("My Smart Playlist", smart)
        >>> pl.ID
        '123456789'

        >>> pl.SmartList[:72]
        '<NODE Id="123456789" LogicalOperator="1" AutomaticUpdate="1"><CONDITION '
        """
        logger.info("Creating smart playlist %s", name)
        return self._create_playlist(
            name, seq, image_path, parent, smart_list, PlaylistType.SMART_PLAYLIST
        )

    def delete_playlist(self, playlist: PlaylistLike) -> None:
        """Deletes a playlist or playlist folder from the database.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist or playlist folder to delete. Can either be a
            :class:`DjmdPlaylist` object or a playlist ID.

        Examples
        --------
        Delete a playlist:

        >>> db = Rekordbox6Database()
        >>> pl = db.get_playlist(Name="My Playlist").one()
        >>> db.delete_playlist(pl)

        Delete a playlist folder:

        >>> folder = db.get_playlist(Name="My Folder").one()
        >>> db.delete_playlist(folder)
        """
        plist: DjmdPlaylist
        if isinstance(playlist, (int, str)):
            plist = self.get_playlist(ID=playlist)
        else:
            plist = playlist
        if not isinstance(plist, DjmdPlaylist):
            raise ValueError("Playlist must be a DjmdPlaylist or corresponding playlist ID!")

        if plist.Attribute == 1:
            logger.info("Deleting playlist folder '%s' with ID=%s", plist.Name, plist.ID)
        else:
            logger.info("Deleting playlist '%s' with ID=%s", plist.Name, plist.ID)

        now = datetime.datetime.now()
        seq = plist.Seq
        parent_id = plist.ParentID

        self.registry.disable_tracking()
        # Update seq numbers higher than the deleted seq number
        query = (
            self.query(tables.DjmdPlaylist)
            .filter(
                tables.DjmdPlaylist.ParentID == parent_id,
                tables.DjmdPlaylist.Seq > seq,
            )
            .order_by(tables.DjmdPlaylist.Seq)
        )
        moved = list()
        for pl in query:
            pl.Seq -= 1
            pl.updated_at = now
            moved.append(pl)
        moved.append(plist)

        children = [plist]
        # Get all child playlist IDs
        child_ids = list()
        while len(children):
            new_children = list()
            for child in children:
                child_ids.append(child.ID)
                new_children.extend(list(child.Children))
            children = new_children

        # First ID in 'child_ids' is always the deleted playlist, others are children

        # Remove playlist from masterPlaylists6.xml
        if self.playlist_xml is not None:
            for pid in child_ids:
                self.playlist_xml.remove(pid)

        # Remove playlist from database
        self.delete(plist)
        self.registry.enable_tracking()
        if len(child_ids) > 1:
            # The playlist folder had children: one extra USN increment
            self.registry.on_delete(child_ids[1:])
        self.registry.on_delete(moved)

    def move_playlist(
        self, playlist: PlaylistLike, parent: PlaylistLike = None, seq: int = None
    ) -> None:
        """Moves a playlist (folder) in the current parent folder or to a new one.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist or playlist folder to move. Can either be a
            :class:`DjmdPlaylist` object or a playlist ID.
        parent : DjmdPlaylist or int or str, optional
            The new parent playlist of the playlist. If not given, the playlist will
            be moved to `seq` in the current parent playlist. Can either be a
            :class:`DjmdPlaylist` object or a playlist ID.
        seq : int, optional
            The new sequence number of the playlist. If the `parent` argument is given,
            the playlist will be moved to `seq` in the new parent playlist or to
            the end of the new parent folder if `seq=None`. If the `parent` argument is
            not given, the playlist will be moved to `seq` in the current parent.

        Examples
        --------
        Take the following playlist tree:

        >>> db = Rekordbox6Database()
        >>> playlists = db.get_playlist().order_by(tables.DjmdPlaylist.Seq)
        >>> [pl.Name for pl in playlists]  # noqa
        ['Folder 1', 'Folder 2', 'Playlist 1', 'Playlist 2', 'Playlist 3']

        The playlists and folders above are all in the `root` plalyist folder.
        Move a playlist in the current parent folder:

        >>> pl = db.get_playlist(Name="Playlist 2").one()  # noqa
        >>> db.move_playlist(pl, seq=2)
        >>> playlists = db.get_playlist().order_by(tables.DjmdPlaylist.Seq)
        >>> [pl.Name for pl in playlists]  # noqa
        ['Folder 1', 'Playlist 2', 'Folder 2', 'Playlist 1', 'Playlist 3']

        Move a playlist to a new parent folder:

        >>> pl = db.get_playlist(Name="Playlist 1").one()  # noqa
        >>> parent = db.get_playlist(Name="Folder 1").one()  # noqa
        >>> db.move_playlist(pl, parent=parent)
        >>> db.get_playlist(ParentID=parent.ID).all()
        ['Playlist 1']
        """
        if parent is None and seq is None:
            raise ValueError("Either parent or seq must be given")
        plist: DjmdPlaylist
        seqence: int

        if isinstance(playlist, (int, str)):
            plist = self.get_playlist(ID=playlist)
        else:
            plist = playlist
        now = datetime.datetime.now()
        table = tables.DjmdPlaylist

        if parent is None:
            # If no parent is given, keep the current parent
            parent_id = plist.ParentID
        elif isinstance(parent, tables.DjmdPlaylist):
            # Check if parent is a folder
            parent_id = parent.ID
            if parent.Attribute != 1:
                raise ValueError("Parent is not a folder")
        else:
            # Check if parent exists and is a folder
            parent_id = str(parent)
            query = self.query(table.ID).filter(table.ID == parent_id, table.Attribute == 1)
            if not self.query(query.exists()).scalar():
                raise ValueError("Parent does not exist or is not a folder")

        n = self.get_playlist(ParentID=parent_id).count()
        old_seq = plist.Seq

        if parent_id != plist.ParentID:
            # Move to new parent

            old_parent_id = plist.ParentID
            if seq is None:
                # New playlist is last in parents
                seqence = n + 1
                insert_at_end = True
            else:
                seqence = seq
                # Check if sequence number is valid
                insert_at_end = False
                if seqence < 1:
                    raise ValueError("Sequence number must be greater than 0")
                elif seqence > n + 1:
                    raise ValueError(f"Sequence number too high, parent contains {n} items")

            if not insert_at_end:
                # Get all playlists with seq between old_seq and seq
                query = (
                    self.query(tables.DjmdPlaylist)
                    .filter(
                        tables.DjmdPlaylist.ParentID == parent_id,
                        tables.DjmdPlaylist.Seq >= seq,
                    )
                    .order_by(tables.DjmdPlaylist.Seq)
                )
                other_playlists = query.all()
            # Set seq number and update time *before* other playlists to ensure
            # right USN increment order
            plist.ParentID = parent_id
            with self.registry.disabled():
                plist.Seq = seqence
                plist.updated_at = now

            if not insert_at_end:
                # Update seq numbers higher than the new seq number in *new* parent
                # noinspection PyUnboundLocalVariable
                for pl in other_playlists:
                    # Update time of other playlists are left unchanged
                    pl.Seq += 1
                    # Each move counts as one USN increment, so disable for update time
                    with self.registry.disabled():
                        pl.updated_at = now

            # Update seq numbers higher than the old seq number in *old* parent
            # USN is not updated here
            self.registry.disable_tracking()
            query = (
                self.query(tables.DjmdPlaylist)
                .filter(
                    tables.DjmdPlaylist.ParentID == old_parent_id,
                    tables.DjmdPlaylist.Seq > old_seq,
                )
                .order_by(tables.DjmdPlaylist.Seq)
            )
            for pl in query:
                # Update time of other playlists are left unchanged
                pl.Seq -= 1
                pl.updated_at = now
            self.registry.enable_tracking()

        else:
            # Keep parent, only change seq number
            if seq is None:
                raise ValueError("Sequence number must be given")
            seqence = seq
            if seqence < 1:
                raise ValueError("Sequence number must be greater than 0")
            elif seqence > n + 1:
                raise ValueError(f"Sequence number too high, parent contains {n} items")

            if seqence > old_seq:
                # Get all playlists with seq between old_seq and seq
                query = (
                    self.query(tables.DjmdPlaylist)
                    .filter(
                        tables.DjmdPlaylist.ParentID == plist.ParentID,
                        old_seq < tables.DjmdPlaylist.Seq,
                        tables.DjmdPlaylist.Seq <= seqence,
                    )
                    .order_by(tables.DjmdPlaylist.Seq)
                )
                other_playlists = query.all()
                delta_seq = -1
            elif seqence < old_seq:
                query = (
                    self.query(tables.DjmdPlaylist)
                    .filter(
                        tables.DjmdPlaylist.ParentID == plist.ParentID,
                        seqence <= tables.DjmdPlaylist.Seq,
                        tables.DjmdPlaylist.Seq < old_seq,
                    )
                    .order_by(tables.DjmdPlaylist.Seq)
                )
                other_playlists = query.all()
                delta_seq = +1
            else:
                return

            # Set seq number and update time *before* other playlists to ensure
            # right USN increment order
            plist.Seq = seqence
            # Each move counts as one USN increment, so disable for update time
            with self.registry.disabled():
                plist.updated_at = now

            # Set seq number and update time for playlists between old_seq and seq
            for pl in other_playlists:
                pl.Seq += delta_seq
                # Each move counts as one USN increment, so disable for update time
                with self.registry.disabled():
                    pl.updated_at = now

    def rename_playlist(self, playlist: PlaylistLike, name: str) -> None:
        """Renames a playlist or playlist folder.

        Parameters
        ----------
        playlist : DjmdPlaylist or int or str
            The playlist or playlist folder to move. Can either be a
            :class:`DjmdPlaylist` object or a playlist ID.
        name : str
            The new name of the playlist or playlist folder.

        Examples
        --------
        Take the following playlist tree:

        >>> db = Rekordbox6Database()
        >>> playlists = db.get_playlist().order_by(tables.DjmdPlaylist.Seq)
        >>> [pl.Name for pl in playlists]  # noqa
        ['Playlist 1', 'Playlist 2']

        Rename a playlist:

        >>> pl = db.get_playlist(Name="Playlist 1").one()  # noqa
        >>> db.rename_playlist(pl, name="Playlist new")
        >>> playlists = db.get_playlist().order_by(tables.DjmdPlaylist.Seq)
        >>> [pl.Name for pl in playlists]  # noqa
        ['Playlist new', 'Playlist 2']
        """
        pl: DjmdPlaylist
        if isinstance(playlist, (int, str)):
            pl = self.get_playlist(ID=playlist)
        else:
            pl = playlist

        now = datetime.datetime.now()
        # Update name of playlist
        pl.Name = name
        # Update update time: USN not incremented
        with self.registry.disabled():
            pl.updated_at = now

    def add_album(
        self,
        name: str,
        artist: Union[tables.DjmdArtist, int, str] = None,
        image_path: PathLike = None,
        compilation: bool = None,
        search_str: str = None,
    ) -> tables.DjmdAlbum:
        """Adds a new album to the database.

        Parameters
        ----------
        name : str
            The name of the album. Must be a unique name (case-sensitive).
            If an album with the same name already exists in the database,
            use the `ID` of the existing album instead.
        artist : str or int or DjmdArtist, optional
            The artist of the album. Can either be a :class:`DjmdArtist` object
            or an artist ID.
        image_path : str, optional
            The path to the album cover image.
        compilation : bool, optional
            Whether the album is a compilation album. If not given, the
            default value of `False` is used.
        search_str : str, optional
            The search string of the album.

        Returns
        -------
        album : DjmdAlbum
            The newly created album.

        Raises
        ------
        ValueError : If an album with the same name already exists in the database.

        Examples
        --------
        Add a new album to the database:

        >>> db = Rekordbox6Database()
        >>> db.add_album(name="Album 1")
        <DjmdAlbum(148754249  Name=Album 1)>

        Add a new album to the database with an album artist:

        >>> artist = db.get_artist(Name="Artist 1").one()  # noqa
        >>> db.add_album(name="Album 2", artist=artist)
        <DjmdAlbum(148754249  Name=Album 2)>

        For setting the album of a track, the usual procedure is to first
        check if an entry with the same album name already exists in the database,
        and if not, add a new album:

        >>> name = "Album name"
        >>> content = db.get_content().one()
        >>> album = db.get_album(Name=name).one_or_none()
        >>> if album is None:
        ...     album = db.add_album(name=name)
        >>> content.AlbumID = album.ID
        """
        # Check if album already exists
        query = self.query(tables.DjmdAlbum).filter_by(Name=name)
        if query.count() > 0:
            raise ValueError(f"Album '{name}' already exists in database")

        # Get artist ID
        artist_id: Optional[str] = None
        if artist is not None:
            art: tables.DjmdArtist
            if isinstance(artist, (int, str)):
                art = self.get_artist(ID=artist)
            else:
                art = artist
            artist_id = art.ID

        id_ = self.generate_unused_id(tables.DjmdAlbum)
        uuid = str(uuid4())
        album: tables.DjmdAlbum = tables.DjmdAlbum.create(
            ID=id_,
            Name=name,
            AlbumArtistID=artist_id,
            ImagePath=str(image_path) if image_path is not None else None,
            Compilation=compilation,
            SearchStr=search_str,
            UUID=str(uuid),
        )
        self.add(album)
        self.flush()
        return album

    def add_artist(self, name: str, search_str: str = None) -> tables.DjmdArtist:
        """Adds a new artist to the database.

        Parameters
        ----------
        name : str
            The name of the artist. Must be a unique name (case-sensitive).
            If an artist with the same name already exists in the database,
            use the `ID` of the existing artist instead.
        search_str : str, optional
            The search string of the artist.

        Returns
        -------
        artist : DjmdArtist
            The newly created artist.

        Raises
        ------
        ValueError : If an artist with the same name already exists in the database.

        Examples
        --------
        Add a new artist to the database:

        >>> db = Rekordbox6Database()
        >>> db.add_artist(name="Artist 1")
        <DjmdArtist(123456789, Name='Artist 1')>

        Add a new artist to the database with a custom search string:

        >>> db.add_artist(name="Artist 2", search_str="artist 2")
        <DjmdArtist(123456789, Name='Artist 2')>

        For setting the artist of a track, the usual procedure is to first
        check if an entry with the same artist name already exists in the database,
        and if not, add a new artist:

        >>> name = "Artist name"
        >>> content = db.get_content().one()
        >>> artist = db.get_artist(Name=name).one_or_none()
        >>> if artist is None:
        ...     artist = db.add_artist(name=name)
        >>> content.ArtistID = artist.ID
        """
        # Check if artist already exists
        query = self.query(tables.DjmdArtist).filter_by(Name=name)
        if query.count() > 0:
            raise ValueError(f"Artist '{name}' already exists in database")

        id_ = self.generate_unused_id(tables.DjmdArtist)
        uuid = str(uuid4())
        artist: tables.DjmdArtist = tables.DjmdArtist.create(
            ID=id_, Name=name, SearchStr=search_str, UUID=uuid
        )
        self.add(artist)
        self.flush()
        return artist

    def add_genre(self, name: str) -> tables.DjmdGenre:
        """Adds a new genre to the database.

        Parameters
        ----------
        name : str
            The name of the genre. Must be a unique name (case-sensitive).
            If a genre with the same name already exists in the database,
            use the `ID` of the existing genre instead.

        Returns
        -------
        genre : DjmdGenre
            The newly created genre.

        Raises
        ------
        ValueError : If a genre with the same name already exists in the database.

        Examples
        --------
        Add a new genre to the database:

        >>> db = Rekordbox6Database()
        >>> db.add_genre(name="Genre 1")
        <DjmdGenre(123456789 Name=Genre 1)>

        For setting the genre of a track, the usual procedure is to first
        check if an entry with the same genre name already exists in the database,
        and if not, add a new genre:

        >>> name = "Genre name"
        >>> content = db.get_content().one()
        >>> genre = db.get_genre(Name=name).one_or_none()
        >>> if genre is None:
        ...     genre = db.add_genre(name=name)
        >>> content.GenreID = genre.ID
        """
        # Check if genre already exists
        query = self.query(tables.DjmdGenre).filter_by(Name=name)
        if query.count() > 0:
            raise ValueError(f"Genre '{name}' already exists in database")

        id_ = self.generate_unused_id(tables.DjmdGenre)
        uuid = str(uuid4())
        genre: tables.DjmdGenre = tables.DjmdGenre.create(ID=id_, Name=name, UUID=uuid)
        self.add(genre)
        self.flush()
        return genre

    def add_label(self, name: str) -> tables.DjmdLabel:
        """Adds a new label to the database.

        Parameters
        ----------
        name : str
            The name of the label. Must be a unique name (case-sensitive).
            If a label with the same name already exists in the database,
            use the `ID` of the existing label instead.

        Returns
        -------
        label : DjmdLabel
            The newly created label.

        Raises
        ------
        ValueError : If a label with the same name already exists in the database.

        Examples
        --------
        Add a new label to the database:

        >>> db = Rekordbox6Database()
        >>> db.add_label(name="Label 1")
        <DjmdLabel(123456789 Name=Label 1)>

        For setting the label of a track, the usual procedure is to first
        check if an entry with the same label name already exists in the database,
        and if not, add a new label:

        >>> name = "Label name"
        >>> content = db.get_content().one()
        >>> label = db.get_label(Name=name).one_or_none()
        >>> if label is None:
        ...     label = db.add_label(name=name)
        >>> content.LabelID = label.ID
        """
        # Check if label already exists
        query = self.query(tables.DjmdLabel).filter_by(Name=name)
        if query.count() > 0:
            raise ValueError(f"Label '{name}' already exists in database")

        id_ = self.generate_unused_id(tables.DjmdLabel)
        uuid = str(uuid4())
        label: tables.DjmdLabel = tables.DjmdLabel.create(ID=id_, Name=name, UUID=uuid)
        self.add(label)
        self.flush()
        return label

    def add_content(self, path: PathLike, **kwargs: Any) -> DjmdContent:
        """Adds a new track to the database.

        Parameters
        ----------
        path : str
            Absolute path to the music file to be added.

        **kwargs:
            Keyword arguments passed to DjmdContent on creation. These arguments
            should be a valid DjmdContent field.

        Returns
        -------
        content : DjmdContent
            The newly created track.

        Raises
        ------
        ValueError : If a track with the same path already exists in the database.
        ValueError : If the file type is invalid.

        Examples
        --------
        Add a new track to the database:

        >>> db = Rekordbox6Database()
        >>> db.add_content("/Users/foo/Downloads/banger.mp3", Title="Banger")
        <DjmdContent(123456789 Title=Banger)>
        """
        path = Path(path)
        path_string = str(path)
        query = self.query(tables.DjmdContent).filter_by(FolderPath=path_string)
        if query.count() > 0:
            raise ValueError(f"Track with path '{path}' already exists in database")

        id_ = self.generate_unused_id(tables.DjmdContent)
        file_id = self.generate_unused_id(tables.DjmdContent, id_field_name="rb_file_id")
        uuid = str(uuid4())
        content_link = self.get_menu_items(Name="TRACK").one()
        date_created = datetime.date.today()
        device = self.get_device().first()
        file_name_l = path.name
        file_size = path.stat().st_size

        file_type_string = path.suffix.lstrip(".").upper()
        try:
            file_type = getattr(FileType, file_type_string)
        except ValueError:
            raise ValueError(f"Invalid file type: {path.suffix}")

        content: DjmdContent = tables.DjmdContent.create(
            ID=id_,
            UUID=uuid,
            ContentLink=content_link.rb_local_usn,
            DateCreated=date_created,
            DeviceID=device.ID,
            FileNameL=file_name_l,
            FileSize=file_size,
            FileType=file_type.value,
            FolderPath=path_string,
            HotCueAutoLoad="on",
            MasterDBID=device.MasterDBID,
            MasterSongID=id_,
            StockDate=date_created,
            rb_file_id=file_id,
            **kwargs,
        )
        self.add(content)
        self.flush()
        return content

    # ----------------------------------------------------------------------------------

    def get_mysetting_paths(self) -> List[Path]:
        """Returns the file paths of the local Rekordbox MySetting files.

        Returns
        -------
        paths : list[str]
            the file paths of the local MySetting files.
        """
        paths: List[Path] = list()
        for item in self.get_setting_file():
            paths.append(self._db_dir / item.Path.lstrip("/\\"))
        return paths

    def get_anlz_dir(self, content: ContentLike) -> Path:
        """Returns the directory path containing the ANLZ analysis files of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the ``DjmdContent``
            entry.

        Returns
        -------
        anlz_dir : Path
            The path of the directory containing the analysis files for the content.
        """
        cont: DjmdContent
        if isinstance(content, (int, str)):
            cont = self.get_content(ID=content)
        else:
            cont = content

        dat_path = Path(cont.AnalysisDataPath.strip("\\/"))
        path: Path = self._share_dir / dat_path.parent
        return path

    def get_anlz_paths(self, content: ContentLike) -> Dict[str, Optional[Path]]:
        """Returns all existing ANLZ analysis file paths of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the ``DjmdContent``
            entry.

        Returns
        -------
        anlz_paths : dict[str, Path]
            The analysis file paths for the content as dictionary. The keys of the
            dictionary are the file types ("DAT", "EXT" or "EX2").
        """
        root = self.get_anlz_dir(content)
        return get_anlz_paths(root)

    def read_anlz_files(self, content: ContentLike) -> Dict[Path, AnlzFile]:
        """Reads all existing ANLZ analysis files of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the ``DjmdContent``
            entry.

        Returns
        -------
        anlz_files : dict[str, AnlzFile]
            The analysis files for the content as dictionary. The keys of the
            dictionary are the file paths.
        """
        root = self.get_anlz_dir(content)
        return read_anlz_files(root)

    def get_anlz_path(self, content: ContentLike, type_: str) -> Optional[PathLike]:
        """Returns the file path of an ANLZ analysis file of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the ``DjmdContent``
            entry.
        type_ : str, optional
            The type of the analysis file to return. Must be one of "DAT", "EXT" or
            "EX2". "DAT" by default.

        Returns
        -------
        anlz_path : Path or None
            The file path of the analysis file for the content. If the file does not
            exist, None is returned.
        """
        root = self.get_anlz_dir(content)
        paths = get_anlz_paths(root)
        return paths.get(type_.upper(), "")

    def read_anlz_file(self, content: ContentLike, type_: str) -> Optional[AnlzFile]:
        """Reads an ANLZ analysis file of a track.

        Parameters
        ----------
        content : DjmdContent or int or str
            The content corresponding to a track in the Rekordbox v6 database.
            If an integer is passed the database is queried for the ``DjmdContent``
            entry.
        type_ : str, optional
            The type of the analysis file to return. Must be one of "DAT", "EXT" or
            "EX2". "DAT" by default.

        Returns
        -------
        anlz_file : AnlzFile or None
            The analysis file for the content. If the file does not exist, None is
            returned.
        """
        path = self.get_anlz_path(content, type_)
        if path:
            return AnlzFile.parse_file(path)
        return None

    def update_content_path(
        self,
        content: ContentLike,
        path: PathLike,
        save: bool = True,
        check_path: bool = True,
        commit: bool = True,
    ) -> None:
        """Update the file path of a track in the Rekordbox v6 database.

        This changes the `FolderPath` entry in the ``DjmdContent`` table and the
        path tag (PPTH) of the corresponding ANLZ analysis files.

        Parameters
        ----------
        content : DjmdContent or int or str
            The ``DjmdContent`` element to change. If an integer is passed the database
            is queried for the content.
        path : str or Path
            The new file path of the database entry.
        save : bool, optional
            If True, the changes made are written to disc.
        check_path : bool, optional
            If True, raise an assertion error if the given file path does not exist.
        commit : bool, optional
            If True, the changes are committed to the database. True by default.

        Examples
        --------
        If, for example, the file `NOISE.wav` was moved up a few directories
        (from `.../Sampler/OSC_SAMPLER/PRESET ONESHOT/` to `.../Sampler/`) the file
        could no longer be opened in Rekordbox, since the database still contains the
        old file path:

        >>> db = Rekordbox6Database()
        >>> cont = db.get_content()[0]
        >>> cont.FolderPath
        C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/NOISE.wav

        Updating the path changes the database entry

        >>> new_path = "C:/Music/PioneerDJ/Sampler/PRESET ONESHOT/NOISE.wav"
        >>> db.update_content_path(cont, path)
        >>> cont.FolderPath
        C:/Music/PioneerDJ/Sampler/PRESET ONESHOT/NOISE.wav

        and updates the file path in the corresponding ANLZ analysis files:

        >>> files = self.read_anlz_files(cont.ID)
        >>> file = list(files.values())[0]
        >>> file.get("path")
        C:/Music/PioneerDJ/Sampler/PRESET ONESHOT/NOISE.wav

        """
        cont: DjmdContent
        if isinstance(content, (int, str)):
            cont = self.get_content(ID=content)
        else:
            cont = content

        cid = cont.ID

        path = Path(path)
        # Check and format path (the database and ANLZ files use "/" as path delimiter)
        if check_path:
            assert path.exists()
        path = str(path).replace("\\", "/")
        old_path = cont.FolderPath
        logger.info("Replacing '%s' with '%s' of content [%s]", old_path, path, cid)

        # Update path in ANLZ files
        anlz_files = self.read_anlz_files(cid)
        for anlz_path, anlz in anlz_files.items():
            logger.debug("Updating path of %s: %s", anlz_path, path)
            anlz.set_path(path)

        # Update path in database (DjmdContent)
        logger.debug("Updating database file path: %s", path)
        cont.FolderPath = path

        # Update the OrgFolderPath column with the new path
        # if the column matches the old_path variable
        org_folder_path = cont.OrgFolderPath
        if org_folder_path == old_path:
            cont.OrgFolderPath = path

        # Update the FileNameL column with the new filename if it changed
        new_name = path.split("/")[-1]
        if cont.FileNameL != new_name:
            cont.FileNameL = new_name

        if save:
            logger.debug("Saving ANLZ files")
            # Save ANLZ files
            for anlz_path, anlz in anlz_files.items():
                anlz.save(anlz_path)

        if commit:
            # Commit database changes
            logger.debug("Committing changes to the database")
            self.commit()

    def update_content_filename(
        self,
        content: ContentLike,
        name: str,
        save: bool = True,
        check_path: bool = True,
        commit: bool = True,
    ) -> None:
        """Update the file name of a track in the Rekordbox v6 database.

        This changes the `FolderPath` entry in the ``DjmdContent`` table and the
        path tag (PPTH) of the corresponding ANLZ analysis files.

        Parameters
        ----------
        content : DjmdContent or int or str
            The ``DjmdContent`` element to change. If an integer is passed the database
            is queried for the content.
        name : str
            The new file name of the database entry.
        save : bool, optional
            If True, the changes made are written to disc.
        check_path : bool, optional
            If True, raise an assertion error if the new file path does not exist.
        commit : bool, optional
            If True, the changes are committed to the database. True by default.

        See Also
        --------
        update_content_path: Update the file path of a track in the Rekordbox database.

        Examples
        --------
        Updating the file name changes the database entry

        >>> db = Rekordbox6Database()
        >>> cont = db.get_content()[0]
        >>> cont.FolderPath
        C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/NOISE.wav

        >>> new_name = "noise"
        >>> db.update_content_filename(cont, new_name)
        >>> cont.FolderPath
        C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET ONESHOT/noise.wav

        and updates the file path in the corresponding ANLZ analysis files:

        >>> files = self.read_anlz_files(cont.ID)
        >>> file = list(files.values())[0]
        >>> cont.FolderPath == file.get("path")
        True
        """
        cont: DjmdContent
        if isinstance(content, (int, str)):
            cont = self.get_content(ID=content)
        else:
            cont = content

        old_path = Path(cont.FolderPath)
        ext = old_path.suffix
        new_path = old_path.parent / name
        new_path = new_path.with_suffix(ext)
        self.update_content_path(cont, new_path, save, check_path, commit=commit)

    def to_dict(self, verbose: bool = False) -> Dict[str, Any]:
        """Convert the database to a dictionary.

        Parameters
        ----------
        verbose: bool, optional
            If True, print the name of the table that is currently converted.

        Returns
        -------
        dict
            A dictionary containing the database tables as keys and the table data as
            a list of dicts.
        """
        data = dict()
        for table_name in tables.TABLES:
            if table_name.startswith("Stats") or table_name == "Base":
                continue
            if verbose:
                print(f"Converting table: {table_name}")
            table = getattr(tables, table_name)
            columns = table.columns()
            table_data = list()
            for row in self.query(table).all():
                table_data.append({column: row[column] for column in columns})
            data[table_name] = table_data
        return data

    def to_json(
        self, file: PathLike, indent: int = 4, sort_keys: bool = True, verbose: bool = False
    ) -> None:
        """Convert the database to a JSON file."""
        import json

        def json_serial(obj: Any) -> Any:
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        data = self.to_dict(verbose=verbose)
        with open(file, "w") as fp:
            json.dump(data, fp, indent=indent, sort_keys=sort_keys, default=json_serial)

    def copy_unlocked(self, output_file: PathLike) -> None:
        src_engine = self.engine
        src_metadata = MetaData()
        exclude_tables = ("sqlite_master", "sqlite_sequence", "sqlite_temp_master")

        dst_engine = create_engine(f"sqlite:///{output_file}")
        dst_metadata = MetaData()

        @event.listens_for(src_metadata, "column_reflect")
        def genericize_datatypes(inspector, tablename, column_dict):  # type: ignore # noqa: ANN202
            type_ = column_dict["type"].as_generic(allow_nulltype=True)
            if isinstance(type_, DateTime):
                type_ = String
            column_dict["type"] = type_

        src_conn = src_engine.connect()
        dst_conn = dst_engine.connect()
        dst_metadata.reflect(bind=dst_engine)
        # drop all tables in target database
        for table in reversed(dst_metadata.sorted_tables):
            if table.name not in exclude_tables:
                print("dropping table =", table.name)
                table.drop(bind=dst_engine)
        # Delete all data in target database
        for table in reversed(dst_metadata.sorted_tables):
            table.delete()
        dst_metadata.clear()
        dst_metadata.reflect(bind=dst_engine)
        src_metadata.reflect(bind=src_engine)
        # create all tables in target database
        for table in src_metadata.sorted_tables:
            if table.name not in exclude_tables:
                table.create(bind=dst_engine)
        # refresh metadata before you can copy data
        dst_metadata.clear()
        dst_metadata.reflect(bind=dst_engine)
        # Copy all data from src to target
        print("Copying data...")
        string = "\rCopying table {name}: Inserting row {row}"
        index = 0
        for table in dst_metadata.sorted_tables:
            src_table = src_metadata.tables[table.name]
            stmt = table.insert()
            for index, row in enumerate(src_conn.execute(src_table.select())):
                print(string.format(name=table.name, row=index), end="", flush=True)
                dst_conn.execute(stmt.values(row))
            print(f"\rCopying table {table.name}: Inserted {index} rows", flush=True)

        dst_conn.commit()
