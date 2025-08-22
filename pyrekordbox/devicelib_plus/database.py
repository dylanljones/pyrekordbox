# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-08-13

import datetime
import logging
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from sqlalchemy import create_engine, event
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Query, Session

try:
    from sqlcipher3 import dbapi2 as sqlite3  # noqa

    _sqlcipher_available = True
except ImportError:  # pragma: no cover
    import sqlite3  # type: ignore[no-redef]

    _sqlcipher_available = False

from ..masterdb.models import DjmdContent
from ..utils import deobfuscate
from . import models

logger = logging.getLogger(__name__)

BLOB = b"PN_1dH8$oLJY)16j_RvM6qphWw`476>;C1cWmI#se(PG`j}~xAjlufj?`#0i{;=glh(SkW)y0>n?YEiD`l%t("

# Type aliases
PathLike = Union[str, Path]
T = TypeVar("T", bound=models.Base)
ParsedQuery = Union[T, Query[T], None]

# ID column names
ALBUM_ID = "album_id"
ARTIST_ID = "artist_id"
CATEGORY_ID = "category_id"
COLOR_ID = "color_id"
CONTENT_ID = "content_id"
CUE_ID = "cue_id"
GENRE_ID = "genre_id"
HISTORY_ID = "history_id"
HOT_CUE_BANK_LIST_ID = "hotCueBankList_id"
IMAGE_ID = "image_id"
KEY_ID = "key_id"
LABEL_ID = "label_id"
MENU_ITEM_ID = "menuItem_id"
MY_TAG_ID = "myTag_id"
PLAYLIST_ID = "playlist_id"
SORT_ID = "sort_id"


def _rename_id(kwargs: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Renames the 'id' key to the corresponding id column name."""
    if "id" in kwargs:
        kwargs[name] = kwargs.pop("id")
    return kwargs


def _parse_query_result(query: Query[T], id_column: str, kwargs: Dict[str, Any]) -> ParsedQuery[T]:
    if id_column in kwargs:
        try:
            result: T = query.one()
            return result
        except NoResultFound:
            return None
    return query


class SessionNotInitializedError(Exception):
    def __init__(self) -> None:
        super().__init__("Sqlite-session not intialized!")


class DeviceLibraryPlus:
    """Rekordbox Device Library Plus database handler.

    Parameters
    ----------
    path : str or Path
        The path of the `exportLibrary.db` database file.
    key : str, optional
        The database key. By default, pyrekordbox automatically uses a known key.
        This parameter is only required if the key fails.
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
    pyrekordbox.device_lib_plus.models: Device Library Plus table definitions
    """

    def __init__(self, path: PathLike = None, key: str = "", unlock: bool = True):
        db_path: Path = Path(str(path))
        # make sure file exists
        if not db_path.exists():
            raise FileNotFoundError(f"File '{db_path}' does not exist!")
        # Open database
        if unlock:
            if not _sqlcipher_available:  # pragma: no cover
                raise ImportError("Could not unlock database: 'sqlcipher3' package not found")

            if not key:  # pragma: no cover
                key = deobfuscate(BLOB)
            elif not key.startswith("r8gd"):
                # Check if key looks like a valid key
                raise ValueError("The provided database key doesn't look valid!")

            # Unlock database and create engine
            logger.debug("Key: %s", key)
            url = f"sqlite+pysqlcipher://:{key}@/{db_path}?"
            engine = create_engine(url, module=sqlite3)
        else:
            engine = create_engine(f"sqlite:///{db_path}")

        self.engine = engine
        self.session: Optional[Session] = None
        self._events: Dict[str, Callable[[Any], None]] = dict()

        self.open()

    @property
    def no_autoflush(self) -> Any:
        """Creates a no-autoflush context."""
        if self.session is None:
            raise SessionNotInitializedError()
        return self.session.no_autoflush

    def open(self) -> None:
        """Open the database by instantiating a new session using the SQLAchemy engine.

        A new session instance is only created if the session was closed previously.

        Examples
        --------
        >>> db = DeviceLibraryPlus()
        >>> db.close()
        >>> db.open()
        """
        if self.session is None:
            self.session = Session(bind=self.engine)

    def close(self) -> None:
        """Close the currently active session."""
        if self.session is None:
            raise SessionNotInitializedError()
        for key in self._events:
            self.unregister_event(key)

        self.session.close()
        self.session = None

    def __enter__(self) -> "DeviceLibraryPlus":
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
        Query the ``Content`` table

        >>> db = DeviceLibraryPlus()
        >>> query = db.query(Content)

        Query the `title` attribute of the ``Content`` table

        >>> db = DeviceLibraryPlus()
        >>> query = db.query(Content.title)
        """
        if self.session is None:
            raise SessionNotInitializedError()
        return self.session.query(*entities, **kwargs)

    def add(self, instance: models.Base) -> None:
        """Add an element to the Rekordbox database.

        Parameters
        ----------
        instance : tables.Base
            The table entry to add.
        """
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.add(instance)

    def delete(self, instance: models.Base) -> None:
        """Delete an element from the Rekordbox database.

        Parameters
        ----------
        instance : tables.Base
            The table entry to delte.
        """
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.delete(instance)

    def flush(self) -> None:
        """Flushes the buffer of the SQLAlchemy session instance."""
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.flush()

    def commit(self) -> None:
        """Commit the changes made to the database."""
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.commit()

    def rollback(self) -> None:
        """Rolls back the uncommited changes to the database."""
        if self.session is None:
            raise SessionNotInitializedError()
        self.session.rollback()

    # -- Table queries -----------------------------------------------------------------

    def get_album(self, **kwargs: Any) -> ParsedQuery[models.Album]:
        """Creates a filtered query for the ``Album`` table."""
        _rename_id(kwargs, ALBUM_ID)
        query = self.query(models.Album).filter_by(**kwargs)
        return _parse_query_result(query, ALBUM_ID, kwargs)

    def get_artist(self, **kwargs: Any) -> ParsedQuery[models.Artist]:
        """Creates a filtered query for the ``Artist`` table."""
        _rename_id(kwargs, ARTIST_ID)
        query = self.query(models.Artist).filter_by(**kwargs)
        return _parse_query_result(query, ARTIST_ID, kwargs)

    def get_category(self, **kwargs: Any) -> ParsedQuery[models.Category]:
        """Creates a filtered query for the ``Category`` table."""
        _rename_id(kwargs, CATEGORY_ID)
        query = self.query(models.Category).filter_by(**kwargs)
        return _parse_query_result(query, CATEGORY_ID, kwargs)

    def get_color(self, **kwargs: Any) -> ParsedQuery[models.Color]:
        """Creates a filtered query for the ``Color`` table."""
        _rename_id(kwargs, COLOR_ID)
        query = self.query(models.Color).filter_by(**kwargs)
        return _parse_query_result(query, COLOR_ID, kwargs)

    def get_content(self, **kwargs: Any) -> ParsedQuery[models.Content]:
        """Creates a filtered query for the ``Content`` table."""
        _rename_id(kwargs, CONTENT_ID)
        query = self.query(models.Content).filter_by(**kwargs)
        return _parse_query_result(query, CONTENT_ID, kwargs)

    def get_cue(self, **kwargs: Any) -> ParsedQuery[models.Cue]:
        """Creates a filtered query for the ``Cue`` table."""
        _rename_id(kwargs, CUE_ID)
        query = self.query(models.Cue).filter_by(**kwargs)
        return _parse_query_result(query, CUE_ID, kwargs)

    def get_genre(self, **kwargs: Any) -> ParsedQuery[models.Genre]:
        """Creates a filtered query for the ``Genre`` table."""
        _rename_id(kwargs, GENRE_ID)
        query = self.query(models.Genre).filter_by(**kwargs)
        return _parse_query_result(query, GENRE_ID, kwargs)

    def get_history(self, **kwargs: Any) -> ParsedQuery[models.History]:
        """Creates a filtered query for the ``History`` table."""
        _rename_id(kwargs, HISTORY_ID)
        query = self.query(models.History).filter_by(**kwargs)
        return _parse_query_result(query, HISTORY_ID, kwargs)

    def get_history_content(self, **kwargs: Any) -> Query[models.HistoryContent]:
        """Creates a filtered query for the ``HistoryContent`` table."""
        query: Query[models.HistoryContent] = self.query(models.HistoryContent).filter_by(**kwargs)
        return query

    def get_hot_cue_banklist(self, **kwargs: Any) -> ParsedQuery[models.HotCueBankList]:
        """Creates a filtered query for the ``HotCueBankList`` table."""
        _rename_id(kwargs, HOT_CUE_BANK_LIST_ID)
        query = self.query(models.HotCueBankList).filter_by(**kwargs)
        return _parse_query_result(query, HOT_CUE_BANK_LIST_ID, kwargs)

    def get_hot_cue_banklist_cue(self, **kwargs: Any) -> Query[models.HotCueBankListCue]:
        """Creates a filtered query for the ``HotCueBankListCue`` table."""
        query: Query[models.HotCueBankListCue] = self.query(models.HotCueBankListCue).filter_by(
            **kwargs
        )
        return query

    def get_image(self, **kwargs: Any) -> ParsedQuery[models.Image]:
        """Creates a filtered query for the ``Image`` table."""
        _rename_id(kwargs, IMAGE_ID)
        query = self.query(models.Image).filter_by(**kwargs)
        return _parse_query_result(query, IMAGE_ID, kwargs)

    def get_key(self, **kwargs: Any) -> ParsedQuery[models.Key]:
        """Creates a filtered query for the ``Key`` table."""
        _rename_id(kwargs, KEY_ID)
        query = self.query(models.Key).filter_by(**kwargs)
        return _parse_query_result(query, KEY_ID, kwargs)

    def get_label(self, **kwargs: Any) -> ParsedQuery[models.Label]:
        """Creates a filtered query for the ``Label`` table."""
        _rename_id(kwargs, LABEL_ID)
        query = self.query(models.Label).filter_by(**kwargs)
        return _parse_query_result(query, LABEL_ID, kwargs)

    def get_menu_item(self, **kwargs: Any) -> ParsedQuery[models.MenuItem]:
        """Creates a filtered query for the ``MenuItem`` table."""
        _rename_id(kwargs, MENU_ITEM_ID)
        query = self.query(models.MenuItem).filter_by(**kwargs)
        return _parse_query_result(query, MENU_ITEM_ID, kwargs)

    def get_my_tag(self, **kwargs: Any) -> ParsedQuery[models.MyTag]:
        """Creates a filtered query for the ``MyTag`` table."""
        _rename_id(kwargs, MY_TAG_ID)
        query = self.query(models.MyTag).filter_by(**kwargs)
        return _parse_query_result(query, MY_TAG_ID, kwargs)

    def get_my_tag_content(self, **kwargs: Any) -> Query[models.MyTagContent]:
        """Creates a filtered query for the ``MyTagContent`` table."""
        query: Query[models.MyTagContent] = self.query(models.MyTagContent).filter_by(**kwargs)
        return query

    def get_playlist(self, **kwargs: Any) -> ParsedQuery[models.Playlist]:
        """Creates a filtered query for the ``Playlist`` table."""
        _rename_id(kwargs, PLAYLIST_ID)
        query = self.query(models.Playlist).filter_by(**kwargs)
        return _parse_query_result(query, PLAYLIST_ID, kwargs)

    def get_playlist_content(self, **kwargs: Any) -> Query[models.PlaylistContent]:
        """Creates a filtered query for the ``PlaylistContent`` table."""
        query: Query[models.PlaylistContent] = self.query(models.PlaylistContent).filter_by(
            **kwargs
        )
        return query

    def get_property(self, **kwargs: Any) -> Query[models.Property]:
        """Creates a filtered query for the ``Property`` table."""
        query: Query[models.Property] = self.query(models.Property).filter_by(**kwargs)
        return query

    def get_recommended_like(self) -> Query[models.RecommendedLike]:
        """Creates a query for the ``RecommendedLike`` table."""
        query: Query[models.RecommendedLike] = self.query(models.RecommendedLike)
        return query

    def get_sort(self, **kwargs: Any) -> ParsedQuery[models.Sort]:
        """Creates a filtered query for the ``Sort`` table."""
        _rename_id(kwargs, SORT_ID)
        query = self.query(models.Sort).filter_by(**kwargs)
        return _parse_query_result(query, SORT_ID, kwargs)

    # -- Database updates --------------------------------------------------------------

    def add_album(
        self,
        name: str,
        artist_id: Optional[int] = None,
        image_id: Optional[int] = None,
        is_compilation: bool = False,
        search_string: Optional[str] = None,
    ) -> models.Album:
        """Create a new album entry in the database.

        Parameters
        ----------
        name : str
            The name of the album.
        artist_id : int, optional
            The ID of the artist associated with the album. If None, no artist is set.
        image_id : int, optional
            The ID of the album image. If None, no image is set.
        is_compilation : bool, optional
            Flag indicating if the album is a compilation. Defaults to False.
        search_string : str, optional
            A search string for the album. Defaults to None.

        Returns
        -------
        models.Album
            The newly created album object.
        """
        album = models.Album(
            name=name,
            artist_id=artist_id,
            image_id=image_id,
            isComplation=int(is_compilation),
            nameForSearch=search_string or "",
        )
        self.add(album)
        self.flush()
        return album

    def add_artist(
        self,
        name: str,
        search_string: Optional[str] = None,
    ) -> models.Artist:
        """Create a new artist entry in the database.

        Parameters
        ----------
        name : str
            The name of the artist.
        search_string : str, optional
            A search string for the artist. Defaults to None.

        Returns
        -------
        models.Artist
            The newly created artist object.
        """
        artist = models.Artist(
            name=name,
            nameForSearch=search_string or "",
        )
        self.add(artist)
        self.flush()
        return artist

    def add_category(
        self,
        menu_item_id: int,
        seq: int,
        is_visible: bool = True,
    ) -> models.Category:
        """Create a new category entry in the database.

        Parameters
        ----------
        menu_item_id : int
            The ID of the menu item associated with the category.
        seq : int
            The sequence number of the category.
        is_visible : bool, optional
            Flag indicating if the category is visible. Defaults to True.

        Returns
        -------
        models.Category
            The newly created category object.
        """
        category = models.Category(
            menuItem_id=menu_item_id,
            sequenceNo=seq,
            isVisible=int(is_visible),
        )
        self.add(category)
        self.flush()
        return category

    def add_color(self, name: str) -> models.Color:
        """Create a new color entry in the database.

        Parameters
        ----------
        name : str
            The name of the color.

        Returns
        -------
        models.Color
            The newly created color object.
        """
        color = models.Color(name=name)
        self.add(color)
        self.flush()
        return color

    def add_content(
        self,
        path: PathLike,
        file_type: int,
        bitrate: int = 0,
        bit_depth: int = 0,
        sampling_rate: int = 0,
        analysis_path: PathLike = None,
        **kwargs: Any,
    ) -> models.Content:
        """Create a new content entry in the database.

        Parameters
        ----------
        path : PathLike
            The path to the content file.
        file_type : int
            The type of the content file.
        bitrate : int, optional
            The bitrate of the content file. Defaults to 0.
        bit_depth : int, optional
            The bit depth of the content file. Defaults to 0.
        sampling_rate : int, optional
            The sampling rate of the content file. Defaults to 0.
        analysis_path : PathLike, optional
            The path to the analysis data file on the device. Defaults to None.
        **kwargs : Any
            Arbitrary keyword arguments used to set additional attributes of the content.

        Returns
        -------
        models.Content
            The newly created content object.
        """
        path = Path(path)
        path_string = str(path)
        query = self.query(models.Content).filter_by(path=path_string)
        if query.count() > 0:
            raise ValueError(f"Track with path '{path}' already exists in database")

        file_name = path.name
        file_size = path.stat().st_size

        content = models.Content(
            path=path_string,
            fileName=file_name,
            fileSize=file_size,
            fileType=file_type,
            bitrate=bitrate,
            bitDepth=bit_depth,
            samplingRate=sampling_rate,
            hasModified=0,
            cueUpdateCount=0,
            analysisDataUpdateCount=0,
            informationUpdateCount=0,
            analysisDataFilePath=str(analysis_path) if analysis_path else None,
            **kwargs,
        )
        self.add(content)
        self.flush()
        return content

    def add_content_from_db(self, path: PathLike, djmd_content: DjmdContent) -> models.Content:
        """Create a new content entry in the database from a DjmdContent object.

        Parameters
        ----------
        path : PathLike
            The path to the content file.
        djmd_content : DjmdContent
            The DjmdContent object containing the content data.

        Returns
        -------
        models.Content
            The newly created content object.
        """
        return self.add_content(
            path=path,
            file_type=djmd_content.FileType,
            bitrate=djmd_content.BitRate,
            bit_depth=djmd_content.BitDepth,
            sampling_rate=djmd_content.SampleRate,
            title=djmd_content.Title,
            subtitle=djmd_content.Subtitle,
            bpmx100=djmd_content.BPM,
            length=djmd_content.Length,
            trackNo=djmd_content.TrackNo,
            discNo=djmd_content.DiscNo,
            artist_id_artist=None,
            artist_id_remixer=None,
            artist_id_originalArtist=None,
            artist_id_composer=None,
            artist_id_lyricist=None,
            album_id=None,
            genre_id=None,
            label_id=None,
            key_id=None,
            color_id=None,
            image_id=None,
            djComment=djmd_content.Commnt,
            rating=djmd_content.Rating,
            releaseYear=djmd_content.ReleaseYear,
            releaseDate=djmd_content.ReleaseDate,
            dateAdded=djmd_content.created_at,
            isrc=djmd_content.ISRC,
            isHotCueAutoLoadOn=djmd_content.HotCueAutoLoad,
            isKuvoDeliverStatusOn=None,
            kuvoDeliveryComment=None,
            masterDbId=int(djmd_content.ID),
            masterContentId=None,
            analysedBits=None,
            contentLink=djmd_content.ContentLink,
        )

    # TODO: Add cue

    def add_genre(self, name: str) -> models.Genre:
        """Create a new genre entry in the database.

        Parameters
        ----------
        name : str
            The name of the genre.

        Returns
        -------
        models.Genre
            The newly created genre object.
        """
        genre = models.Genre(name=name)
        self.add(genre)
        self.flush()
        return genre

    # TODO: Add hotCueBankList
    # TODO: Add hotCueBankListCue

    def add_image(self, path: Path) -> models.Image:
        """Create a new image entry in the database.

        Parameters
        ----------
        path : Path
            The path to the image file.

        Returns
        -------
        models.Image
            The newly created image object.
        """
        image = models.Image(path=str(path))
        self.add(image)
        self.flush()
        return image

    def add_key(self, name: str) -> models.Key:
        """Create a new key entry in the database.

        Parameters
        ----------
        name : str
            The name of the key.

        Returns
        -------
        models.Key
            The newly created key object.
        """
        key = models.Key(name=name)
        self.add(key)
        self.flush()
        return key

    def add_label(self, name: str) -> models.Label:
        """Create a new label entry in the database.

        Parameters
        ----------
        name : str
            The name of the label.

        Returns
        -------
        models.Label
            The newly created label object.
        """
        label = models.Label(name=name)
        self.add(label)
        self.flush()
        return label

    def add_menu_item(self, kind: int, name: str) -> models.MenuItem:
        """Create a new menu item entry in the database.

        Parameters
        ----------
        kind : int
            The kind of the menu item.
        name : str
            The name of the menu item.

        Returns
        -------
        models.MenuItem
            The newly created menu item object.
        """
        menu_item = models.MenuItem(kind=kind, name=name)
        self.add(menu_item)
        self.flush()
        return menu_item

    def add_my_tag(
        self,
        name: str,
        seq: int = None,
        attribute: int = 0,
        parent_id: int = 0,
    ) -> models.MyTag:
        """Create a new MyTag entry in the database.

        Parameters
        ----------
        name : str
            The name of the MyTag.
        seq : int, optional
            The sequence number of the MyTag. If None, the new myTag entry will be added to the
            end of the parent myTag. Defaults to None.
        attribute : int, optional
            The attribute of the MyTag. Defaults to 0.
        parent_id : int, optional
            The ID of the parent MyTag. Defaults to 0, which means the MyTag is a top-level tag.

        Returns
        -------
        models.MyTag
            The newly created MyTag object.
        """
        if seq is None:
            # If no sequence is provided, set it to the next available sequence number
            seq = self.get_my_tag(parent_id=parent_id).count() + 1

        my_tag = models.MyTag(
            name=name,
            sequenceNo=seq,
            attribute=attribute,
            myTag_id_parent=parent_id,
        )
        self.add(my_tag)
        self.flush()
        return my_tag

    def add_my_tag_content(self, my_tag_id: int, content_id: int) -> models.MyTagContent:
        """Create a new MyTagContent entry in the database.

        Parameters
        ----------
        my_tag_id : int
            The ID of the MyTag associated with the content.
        content_id : int
            The ID of the content associated with the MyTag.

        Returns
        -------
        models.MyTagContent
            The newly created MyTagContent object.
        """
        my_tag_content = models.MyTagContent(
            myTag_id=my_tag_id,
            content_id=content_id,
        )
        self.add(my_tag_content)
        self.flush()
        return my_tag_content

    def _add_playlist(
        self,
        name: str,
        attribute: int,
        seq: int = None,
        parent_id: int = 0,
        image_id: int = None,
    ) -> models.Playlist:
        """Create a new playlist entry in the database.

        Parameters
        ----------
        name : str
            The name of the playlist.
        attribute : int
            The attribute of the playlist.
        seq : int, optional
            The sequence number of the playlist. If None, the new playlist entry will be added to
            the end of the parent playlist. Defaults to None.
        parent_id : int, optional
            The ID of the parent playlist. Defaults to 0, which means the playlist is a top-level
             playlist.
        image_id : int, optional
            The ID of the playlist image. Defaults to None, which means no image is set.

        Returns
        -------
        models.Playlist
            The newly created playlist object.
        """
        if seq is None:
            # If no sequence is provided, set it to the next available sequence number
            seq = self.get_playlist(playlist_id_parent=parent_id).count() + 1

        playlist = models.Playlist(
            sequenceNo=seq,
            name=name,
            image_id=image_id,
            attribute=attribute,
            playlist_id_parent=parent_id,
        )
        self.add(playlist)
        self.flush()
        return playlist

    def add_playlist(
        self,
        name: str,
        seq: int = None,
        parent_id: int = 0,
        image_id: int = None,
    ) -> models.Playlist:
        """Create a new playlist entry in the database.

        Parameters
        ----------
        name : str
            The name of the playlist.
        seq : int, optional
            The sequence number of the playlist. If None, the new playlist entry will be added to
            the end of the parent playlist. Defaults to None.
        parent_id : int, optional
            The ID of the parent playlist. Defaults to 0, which means the playlist is a top-level
            playlist.
        image_id : int, optional
            The ID of the playlist image. Defaults to None, which means no image is set.

        Returns
        -------
        models.Playlist
            The newly created playlist object.
        """
        return self._add_playlist(
            name, attribute=0, seq=seq, image_id=image_id, parent_id=parent_id
        )

    def add_playlist_folder(
        self,
        name: str,
        seq: int = None,
        parent_id: int = 0,
    ) -> models.Playlist:
        """Create a new playlist folder entry in the database.

        Parameters
        ----------
        name : str
            The name of the playlist.
        seq : int, optional
            The sequence number of the playlist. If None, the new playlist entry will be added to
            the end of the parent playlist. Defaults to None.
        parent_id : int, optional
            The ID of the parent playlist. Defaults to 0, which means the playlist is a top-level
            playlist.

        Returns
        -------
        models.Playlist
            The newly created playlist object.
        """
        return self._add_playlist(name, attribute=1, seq=seq, image_id=None, parent_id=parent_id)

    def add_playlist_content(
        self, playlist_id: int, content_id: int, seq: int = None
    ) -> models.PlaylistContent:
        """Create a new playlist content entry in the database.

        Parameters
        ----------
        playlist_id : int
            The ID of the playlist associated with the content.
        content_id : int
            The ID of the content associated with the playlist.
        seq : int, optional
            The sequence number of the content in the playlist.
            If None, it will be set to the next available sequence number.

        Returns
        -------
        models.PlaylistContent
            The newly created playlist content object.
        """
        if seq is None:
            seq = self.get_playlist_content(playlist_id=playlist_id).count() + 1

        playlist_content = models.PlaylistContent(
            playlist_id=playlist_id,
            content_id=content_id,
            sequenceNo=seq,
        )
        self.add(playlist_content)
        self.flush()
        return playlist_content

    def add_property(
        self,
        my_tag_master_dbid: int,
        device_name: str = "",
        db_version: int = 1000,
        background_color_type: int = 0,
    ) -> models.Property:
        """Create a new property entry in the database.

        Parameters
        ----------
        my_tag_master_dbid : int
            The MyTag master database ID.
        device_name : str, optional
            The device name of the property. Defaults to an empty string.
        db_version : int, optional
            The database version. Defaults to 1000.
        background_color_type : int, optional
            The background color type. Defaults to 0.

        Returns
        -------
        models.Property
            The newly created property object.
        """
        now = datetime.datetime.today()
        prop = models.Property(
            deviceName=device_name,
            dbVersion=db_version,
            numberOfContents=0,
            createdDate=now,
            backGroundColorType=background_color_type,
            myTagMasterDBID=my_tag_master_dbid,
        )
        self.add(prop)
        self.flush()
        return prop

    def update_content_count(self) -> None:
        """Update the content count in the property table."""
        prop = self.get_property().one_or_none()
        if prop is None:
            raise ValueError("No property entry found in the database.")
        num_contents = self.get_content().count()
        prop.numberOfContents = num_contents

    def add_recommended_like(
        self, content_id_1: int, content_id_2: int, rating: int
    ) -> models.RecommendedLike:
        """Create a new recommended like entry in the database.

        Parameters
        ----------
        content_id_1 : int
            The ID of the first content.
        content_id_2 : int
            The ID of the second content.
        rating : int
            The rating of the recommendation.

        Returns
        -------
        models.RecommendedLike
            The newly created recommended like object.
        """
        recommended_like = models.RecommendedLike(
            content_id_1=content_id_1,
            content_id_2=content_id_2,
            rating=rating,
        )
        self.add(recommended_like)
        self.flush()
        return recommended_like

    def add_sort(
        self,
        menu_item_id: int,
        seq: int,
        is_visible: bool = True,
        is_selected_as_column: bool = False,
    ) -> models.Sort:
        """Create a new sort entry in the database.

        Parameters
        ----------
        menu_item_id : int
            The ID of the menu item associated with the sort.
        seq : int
            The sequence number of the sort.
        is_visible : bool, optional
            Flag indicating if the sort is visible. Defaults to True.
        is_selected_as_column : bool, optional
            The selected as sub-column flag of the sort entry. Defaults to False.

        Returns
        -------
        models.Sort
            The newly created sort object.
        """
        sort = models.Sort(
            menuItem_id=menu_item_id,
            sequenceNo=seq,
            isVisible=int(is_visible),
            isSelectedAsSubColumn=int(is_selected_as_column),
        )
        self.add(sort)
        self.flush()
        return sort

    # ----------------------------------------------------------------------------------

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
        for table_name in models.TABLES:
            if table_name == "Base":
                continue
            if verbose:
                print(f"Converting table: {table_name}")
            table = getattr(models, table_name)
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
