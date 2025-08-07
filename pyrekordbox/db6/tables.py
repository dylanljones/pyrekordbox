# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-08-07

"""Rekordbox 6 `master.db` SQLAlchemy table declarations."""

import math
import re
import struct
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np
from sqlalchemy import (
    VARCHAR,
    BigInteger,
    Dialect,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    TypeDecorator,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, backref, mapped_column, relationship

from .registry import RekordboxAgentRegistry

__all__ = [
    "TABLES",
    "PlaylistType",
    "StatsTime",
    "StatsFull",
    "AgentRegistry",
    "CloudAgentRegistry",
    "ContentActiveCensor",
    "ContentCue",
    "ContentFile",
    "DjmdActiveCensor",
    "DjmdAlbum",
    "DjmdArtist",
    "DjmdCategory",
    "DjmdColor",
    "DjmdContent",
    "DjmdCue",
    "DjmdDevice",
    "DjmdGenre",
    "DjmdHistory",
    "DjmdHotCueBanklist",
    "DjmdKey",
    "DjmdLabel",
    "DjmdMenuItems",
    "DjmdMixerParam",
    "DjmdMyTag",
    "DjmdPlaylist",
    "DjmdProperty",
    "DjmdRelatedTracks",
    "DjmdSampler",
    "DjmdSongHistory",
    "DjmdSongHotCueBanklist",
    "DjmdSongMyTag",
    "DjmdSongPlaylist",
    "DjmdSongRelatedTracks",
    "DjmdSongSampler",
    "DjmdSongTagList",
    "DjmdSort",
    "HotCueBanklistCue",
    "ImageFile",
    "SettingFile",
    "UuidIDMap",
    "FileType",
]


TABLES = [
    "AgentRegistry",
    "CloudAgentRegistry",
    "ContentActiveCensor",
    "ContentCue",
    "ContentFile",
    "DjmdActiveCensor",
    "DjmdAlbum",
    "DjmdArtist",
    "DjmdCategory",
    "DjmdColor",
    "DjmdContent",
    "DjmdCue",
    "DjmdDevice",
    "DjmdGenre",
    "DjmdHistory",
    "DjmdHotCueBanklist",
    "DjmdKey",
    "DjmdLabel",
    "DjmdMenuItems",
    "DjmdMixerParam",
    "DjmdMyTag",
    "DjmdPlaylist",
    "DjmdProperty",
    "DjmdRelatedTracks",
    "DjmdSampler",
    "DjmdSongHistory",
    "DjmdSongHotCueBanklist",
    "DjmdSongMyTag",
    "DjmdSongPlaylist",
    "DjmdSongRelatedTracks",
    "DjmdSongSampler",
    "DjmdSongTagList",
    "DjmdSort",
    "HotCueBanklistCue",
    "ImageFile",
    "SettingFile",
    "UuidIDMap",
]


def datetime_to_str(value: datetime) -> str:
    # Convert to UTC timezone string
    s = value.astimezone(timezone.utc).isoformat().replace("T", " ")
    # Get the timezone info (last 6 characters of the string)
    tzinfo = s[-6:]
    s = s[:-9] + " " + tzinfo
    return s


def string_to_datetime(value: str) -> datetime:
    try:
        # Normalize 'Z' (Zulu/UTC) to '+00:00' for fromisoformat compatibility
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
    except ValueError:
        if len(value.strip()) > 23:
            # Handles formats like:
            # "2025-04-12 19:11:29.274 -05:00 (Central Daylight Time)"
            datestr, tzinfo = value[:23], value[23:30]
            datestr = datestr.strip()
            tzinfo = tzinfo.strip()
            if tzinfo == "Z":
                tzinfo = "+00:00"
            assert re.match(r"^[+-]?\d{1,2}:\d{2}", tzinfo), f"Invalid tzinfo: {tzinfo}"
            datestr = datestr + tzinfo
        else:
            datestr = value.strip()
        dt = datetime.fromisoformat(datestr)
    return dt.astimezone().replace(tzinfo=None)


class DateTime(TypeDecorator):  # type: ignore[type-arg]
    """Custom datetime column with timezone support.

    The datetime format in the database is `YYYY-MM-DD HH:MM:SS.SSS +00:00`.
    This format is not supported by the `DateTime` column of SQLAlchemy 2.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: datetime, dialect: Dialect) -> str:  # type: ignore[override]
        return datetime_to_str(value)

    def process_result_value(self, value: str, dialect: Dialect) -> Optional[datetime]:  # type: ignore[override]
        if value:
            return string_to_datetime(value)
        return None


class PlaylistType(IntEnum):
    PLAYLIST = 0
    FOLDER = 1
    SMART_PLAYLIST = 4


class FileType(IntEnum):
    MP3 = 1
    M4A = 4
    FLAC = 5
    WAV = 11
    AIFF = 12
    AIF = 12


# -- Base- and Mixin classes -----------------------------------------------------------


class Base(DeclarativeBase):
    """Base class used to initialize the declarative base for all tables."""

    __tablename__: str
    __keys__: List[str] = []

    @classmethod
    def create(cls, **kwargs: Any):  # type: ignore # noqa: ANN206
        with RekordboxAgentRegistry.disabled():
            # noinspection PyArgumentList
            self = cls(**kwargs)
        return self

    @classmethod
    def columns(cls) -> List[str]:
        """Returns a list of all column names without the relationships."""
        return [column.name for column in inspect(cls).c]

    @classmethod
    def relationships(cls) -> List[str]:
        """Returns a list of all relationship names."""
        return [column.key for column in inspect(cls).relationships]  # noqa

    @classmethod
    def __get_keys__(cls) -> List[str]:  # pragma: no cover
        """Get all attributes of the table."""
        items = cls.__dict__.items()
        keys = [k for k, v in items if not callable(v) and not k.startswith("_")]
        return keys

    @classmethod
    def keys(cls) -> List[str]:  # pragma: no cover
        """Returns a list of all column names including the relationships."""
        if not cls.__keys__:  # Cache the keys
            cls.__keys__ = cls.__get_keys__()
        return cls.__keys__

    def __iter__(self) -> Iterator[str]:
        """Iterates over all columns and relationship names."""
        return iter(self.keys())

    def __len__(self) -> int:
        return sum(1 for _ in self.__iter__())

    def __getitem__(self, item: str) -> Any:
        return self.__getattribute__(item)

    # noinspection PyUnresolvedReferences
    def __setattr__(self, key: str, value: Any) -> None:
        if not key.startswith("_"):
            RekordboxAgentRegistry.on_update(self, key, value)
        super().__setattr__(key, value)

    def values(self) -> List[Any]:
        """Returns a list of all column values including the relationships."""
        return [self.__getitem__(key) for key in self.keys()]

    def items(self) -> Iterator[Tuple[str, Any]]:
        for key in self.__iter__():
            yield key, self.__getitem__(key)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary of all column names and values."""
        return {key: self.__getitem__(key) for key in self.columns()}

    def pformat(self, indent: str = "   ") -> str:  # pragma: no cover
        lines = [f"{self.__tablename__}"]
        columns = self.columns()
        w = max(len(col) for col in columns)
        for col in columns:
            lines.append(f"{indent}{col:<{w}} {self.__getitem__(col)}")
        return "\n".join(lines)


class StatsTime:
    """Mixin class for tables that only use time statistics columns."""

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    """The creation date of the table entry (from :class:`StatsTime`)."""
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    """The last update date of the table entry (from :class:`StatsTime`)."""


class StatsFull:
    """Mixin class for tables that use all statistics columns."""

    ID: Mapped[str]
    """The ID (primary key) of the table entry."""

    UUID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The UUID of the table entry (from :class:`StatsFull`)"""
    rb_data_status: Mapped[int] = mapped_column(Integer, default=0)
    """The data status of the table entry (from :class:`StatsFull`)."""
    rb_local_data_status: Mapped[int] = mapped_column(Integer, default=0)
    """The local data status of the table entry (from :class:`StatsFull`)."""
    rb_local_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    """The local deleted status of the table entry (from :class:`StatsFull`)."""
    rb_local_synced: Mapped[int] = mapped_column(SmallInteger, default=0)
    """The local synced status of the table entry (from :class:`StatsFull`)."""
    usn: Mapped[int] = mapped_column(BigInteger, default=None)
    """The USN (unique sequence number) of the table entry (from :class:`StatsFull`)."""
    rb_local_usn: Mapped[int] = mapped_column(BigInteger, default=None)
    """The local USN (unique sequence number) of the table entry
    (from :class:`StatsFull`)."""
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    """The creation date of the table entry (from :class:`StatsFull`)."""
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    """The last update date of the table entry (from :class:`StatsFull`)."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.ID})>"


# -- Table declarations ----------------------------------------------------------------


class AgentRegistry(Base, StatsTime):
    """Table for storing agent registry data.

    Each row represents a single agent registry entry with different attributes.
    For this reason the column names are generic and not specific to the data they
    store.

    See Also
    --------
    :class:`CloudAgentRegistry`: Table for storing the agent registry data in the cloud.
    """

    __tablename__ = "agentRegistry"

    registry_id: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    id_1: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The first ID value of the table entry."""
    id_2: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The second ID value of the table entry."""
    int_1: Mapped[int] = mapped_column(Integer, default=None)
    """The first integer value of the table entry."""
    int_2: Mapped[int] = mapped_column(Integer, default=None)
    """The second integer value of the table entry."""
    str_1: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The first string value of the table entry."""
    str_2: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The second string value of the table entry."""
    date_1: Mapped[datetime] = mapped_column(DateTime, default=None)
    """The first date value of the table entry."""
    date_2: Mapped[datetime] = mapped_column(DateTime, default=None)
    """The second date value of the table entry."""
    text_1: Mapped[str] = mapped_column(Text, default=None)
    """The first text value of the table entry."""
    text_2: Mapped[str] = mapped_column(Text, default=None)
    """The second text value of the table entry."""


class CloudAgentRegistry(Base, StatsFull):
    """Table for storing agent registry data in the Rekordbox cloud.

    Each row represents a single agent registry entry with different attributes.
    For this reason the column names are generic and not specific to the data they
    store.

    See Also
    --------
    :class:`AgentRegistry`: Table for storing the local agent registry data.
    """

    __tablename__ = "cloudAgentRegistry"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    int_1: Mapped[int] = mapped_column(Integer, default=None)
    """The first integer value of the table entry."""
    int_2: Mapped[int] = mapped_column(Integer, default=None)
    """The second integer value of the table entry."""
    str_1: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The first string value of the table entry."""
    str_2: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The second string value of the table entry."""
    date_1: Mapped[datetime] = mapped_column(DateTime, default=None)
    """The first date value of the table entry."""
    date_2: Mapped[datetime] = mapped_column(DateTime, default=None)
    """The second date value of the table entry."""
    text_1: Mapped[str] = mapped_column(Text, default=None)
    """The first text value of the table entry."""
    text_2: Mapped[str] = mapped_column(Text, default=None)
    """The second text value of the table entry."""


class ContentActiveCensor(Base, StatsFull):
    """Table for storing the active censors of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "contentActiveCensor"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this censor belongs to."""
    ActiveCensors: Mapped[str] = mapped_column(Text, default=None)
    """The active censors of the table entry."""
    rb_activecensor_count: Mapped[int] = mapped_column(Integer, default=None)
    """The active censor count of the table entry."""

    Content = relationship("DjmdContent")
    """The content entry this censor belongs to (links to :class:`DjmdContent`)."""


class ContentCue(Base, StatsFull):
    """Table for storing the cues of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "contentCue"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this cue belongs to."""
    Cues: Mapped[str] = mapped_column(Text, default=None)
    """The cues of the table entry."""
    rb_cue_count: Mapped[int] = mapped_column(Integer, default=None)
    """The cue count of the table entry."""

    Content = relationship("DjmdContent")
    """The content entry this cue belongs to (links to :class:`DjmdContent`)."""


class ContentFile(Base, StatsFull):
    """Table for storing the file data of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "contentFile"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this file belongs to."""
    Path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path of the file."""
    Hash: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The hash of the file."""
    Size: Mapped[int] = mapped_column(Integer, default=None)
    """The size of the file."""
    rb_local_path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The local path of the file."""
    rb_insync_hash: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The in-sync hash of the file."""
    rb_insync_local_usn: Mapped[int] = mapped_column(BigInteger, default=None)
    """The in-sync local USN (unique sequence number) of the file."""
    rb_file_hash_dirty: Mapped[int] = mapped_column(Integer, default=0)
    """The file hash dirty flag of the file."""
    rb_local_file_status: Mapped[int] = mapped_column(Integer, default=0)
    """The local file status of the file."""
    rb_in_progress: Mapped[int] = mapped_column(SmallInteger, default=0)
    """The in progress flag of the file."""
    rb_process_type: Mapped[int] = mapped_column(Integer, default=0)
    """The process type of the file."""
    rb_temp_path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The temporary path of the file."""
    rb_priority: Mapped[int] = mapped_column(Integer, default=50)
    """The priority of the file."""
    rb_file_size_dirty: Mapped[int] = mapped_column(Integer, default=0)
    """The file size dirty flag of the file."""

    Content = relationship("DjmdContent")
    """The content entry this file belongs to (links to :class:`DjmdContent`)."""


class DjmdActiveCensor(Base, StatsFull):
    """Table for storing the active censors of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "djmdActiveCensor"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this censor belongs to."""
    InMsec: Mapped[int] = mapped_column(Integer, default=None)
    """The in time of the censor (in milliseconds)."""
    OutMsec: Mapped[int] = mapped_column(Integer, default=None)
    """The out time of the censor (in milliseconds)."""
    Info: Mapped[int] = mapped_column(Integer, default=None)
    """Additional info of the censor."""
    ParameterList: Mapped[str] = mapped_column(Text, default=None)
    """The parameter list of the censor."""
    ContentUUID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The UUID of the :class:`DjmdContent` entry this censor belongs to."""

    Content = relationship("DjmdContent", foreign_keys=ContentID, back_populates="ActiveCensors")
    """The content entry this censor belongs to (links to :class:`DjmdContent`)."""


class DjmdAlbum(Base, StatsFull):
    """Table for storing the album data of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdArtist`: Table for storing the artist data.
    """

    __tablename__ = "djmdAlbum"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the album."""
    AlbumArtistID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None
    )
    """The ID of the :class:`DjmdArtist` entry of the artist of this album."""
    ImagePath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path of the image of the album."""
    Compilation: Mapped[int] = mapped_column(Integer, default=None)
    """The compilation flag of the album."""
    SearchStr: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The search string of the album."""

    AlbumArtist = relationship("DjmdArtist")
    """The artist entry of the artist of this album (links to :class:`DjmdArtist`)."""
    AlbumArtistName = association_proxy("AlbumArtist", "Name")
    """The name of the album artist (:class:`DjmdArtist`) of the track."""

    def __repr__(self) -> str:
        s = f"{self.ID: <10} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdArtist(Base, StatsFull):
    """Table for storing the artist data of the Rekordbox library contents."""

    __tablename__ = "djmdArtist"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the artist."""
    SearchStr: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The search string of the artist."""

    def __repr__(self) -> str:
        s = f"{self.ID: <10} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdCategory(Base, StatsFull):
    """Table for storing the category data of the Rekordbox library.

    See Also
    --------
    :class:`DjmdMenuItems`: Table for storing menu items of Rekordbox.
    """

    __tablename__ = "djmdCategory"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MenuItemID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdMenuItems.ID"), default=None
    )
    """The ID of the :class:`DjmdMenuItems` entry belonging to the category."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the category (for ordering)."""
    Disable: Mapped[int] = mapped_column(Integer, default=None)
    """The disable flag of the category."""
    InfoOrder: Mapped[int] = mapped_column(Integer, default=None)
    """Information for ordering the categories."""

    MenuItem = relationship("DjmdMenuItems", foreign_keys=MenuItemID)
    """The menu item entry of the category (links to :class:`DjmdMenuItems`)."""


class DjmdColor(Base, StatsFull):
    """Table for storing all colors of Rekordbox."""

    __tablename__ = "djmdColor"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ColorCode: Mapped[int] = mapped_column(Integer, default=None)
    """The color code of the color."""
    SortKey: Mapped[int] = mapped_column(Integer, default=None)
    """The sort key of the color."""
    Commnt: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The comment (name) of the color."""

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Comment={self.Commnt}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdContent(Base, StatsFull):
    """Table for storing the content data of the Rekordbox library.

    This table stores the main track data of Rekordbox.
    The table contains most information about each track in the collection.
    Some columns are linked to other tables by the corresponding ID.

    See Also
    --------
    :class:`DjmdAlbum`: Table for storing the album data.
    :class:`DjmdArtist`: Table for storing the artist data.
    :class:`DjmdGenre`: Table for storing the genre data.
    :class:`DjmdKey`: Table for storing the key data.
    :class:`DjmdLabel`: Table for storing the label data.
    :class:`DjmdColor`: Table for storing the color data.
    """

    __tablename__ = "djmdContent"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the track."""
    FolderPath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The full path of the file corresponding to the content entry."""
    FileNameL: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The long file name of the file corresponding to the content entry."""
    FileNameS: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The short file name of the file corresponding to the content entry."""
    Title: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The title of the track."""
    ArtistID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the artist of this track."""
    AlbumID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdAlbum.ID"), default=None)
    """The ID of the :class:`DjmdAlbum` entry of the album of this track."""
    GenreID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdGenre.ID"), default=None)
    """The ID of the :class:`DjmdGenre` entry of the genre of this track."""
    BPM: Mapped[int] = mapped_column(Integer, default=None)
    """The BPM (beats per minute) of the track."""
    Length: Mapped[int] = mapped_column(Integer, default=None)
    """The length of the track."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the track."""
    BitRate: Mapped[int] = mapped_column(Integer, default=None)
    """The bit rate of the track."""
    BitDepth: Mapped[int] = mapped_column(Integer, default=None)
    """The bit depth of the track."""
    Commnt: Mapped[str] = mapped_column(Text, default=None)
    """The comment of the track."""
    FileType: Mapped[int] = mapped_column(Integer, default=None)
    """The file type of the track."""
    Rating: Mapped[int] = mapped_column(Integer, default=None)
    """The rating of the track."""
    ReleaseYear: Mapped[int] = mapped_column(Integer, default=None)
    """The release year of the track."""
    RemixerID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the remixer of this track."""
    LabelID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdLabel.ID"), default=None)
    """The ID of the :class:`DjmdLabel` entry of the label of this track."""
    OrgArtistID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None
    )
    """The ID of the :class:`DjmdArtist` entry of the original artist of this track."""
    KeyID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdKey.ID"), default=None)
    """The ID of the :class:`DjmdKey` entry of the key of this track."""
    StockDate: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The stock date of the track."""
    ColorID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdColor.ID"), default=None)
    """The ID of the :class:`DjmdColor` entry of the color of this track."""
    DJPlayCount: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The play count of the track."""
    ImagePath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path of the image of the track."""
    MasterDBID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The master database ID of the track."""
    MasterSongID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The master song ID of the track."""
    AnalysisDataPath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path of the analysis data (ANLZ) of the track."""
    SearchStr: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The search string of the track."""
    FileSize: Mapped[int] = mapped_column(Integer, default=None)
    """The file size of the track."""
    DiscNo: Mapped[int] = mapped_column(Integer, default=None)
    """The number of the disc of the album of the track."""
    ComposerID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the composer of this track."""
    Subtitle: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The subtitle of the track."""
    SampleRate: Mapped[int] = mapped_column(Integer, default=None)
    """The sample rate of the track in Hz."""
    DisableQuantize: Mapped[int] = mapped_column(Integer, default=None)
    """Individual quantize status of the track."""
    Analysed: Mapped[int] = mapped_column(Integer, default=None)
    """The analysis status of the track."""
    ReleaseDate: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The release date of the track."""
    DateCreated: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The date the track was created."""
    ContentLink: Mapped[int] = mapped_column(Integer, default=None)
    """The content link of the track."""
    Tag: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The tag of the track."""
    ModifiedByRBM: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The modified by RBM status of the track."""
    HotCueAutoLoad: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The hot cue auto load status of the track."""
    DeliveryControl: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The delivery control status of the track."""
    DeliveryComment: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The delivery comment of the track."""
    CueUpdated: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The cue updated status of the track."""
    AnalysisUpdated: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The analysis updated status of the track."""
    TrackInfoUpdated: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The track info updated status of the track."""
    Lyricist: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the lyricist of this track."""
    ISRC: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ISRC of the track."""
    SamplerTrackInfo: Mapped[int] = mapped_column(Integer, default=None)
    """The sampler track info of the track."""
    SamplerPlayOffset: Mapped[int] = mapped_column(Integer, default=None)
    """The sampler play offset of the track."""
    SamplerGain: Mapped[float] = mapped_column(Float, default=None)
    """The sampler gain of the track."""
    VideoAssociate: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The video associate of the track."""
    LyricStatus: Mapped[int] = mapped_column(Integer, default=None)
    """The lyric status of the track."""
    ServiceID: Mapped[int] = mapped_column(Integer, default=None)
    """The service ID of the track."""
    OrgFolderPath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The original folder path of the track."""
    Reserved1: Mapped[str] = mapped_column(Text, default=None)
    """Reserved field 1."""
    Reserved2: Mapped[str] = mapped_column(Text, default=None)
    """Reserved field 2."""
    Reserved3: Mapped[str] = mapped_column(Text, default=None)
    """Reserved field 3."""
    Reserved4: Mapped[str] = mapped_column(Text, default=None)
    """Reserved field 4."""
    ExtInfo: Mapped[str] = mapped_column(Text, default=None)
    """The extended information of the track."""
    rb_file_id: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The file ID used by Rekordbox of the track."""
    DeviceID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The device ID of the track."""
    rb_LocalFolderPath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The local folder path used by Rekordbox of the track."""
    SrcID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the source of the track."""
    SrcTitle: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The title of the source of the track."""
    SrcArtistName: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The artist name of the source of the track."""
    SrcAlbumName: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The album name of the source of the track."""
    SrcLength: Mapped[int] = mapped_column(Integer, default=None)
    """The length of the source of the track."""

    Artist = relationship("DjmdArtist", foreign_keys=ArtistID)
    """The artist entry of the track (links to :class:`DjmdArtists`)."""
    Album = relationship("DjmdAlbum", foreign_keys=AlbumID)
    """The album entry of the track (links to :class:`DjmdAlbum`)."""
    Genre = relationship("DjmdGenre", foreign_keys=GenreID)
    """The genre entry of the track (links to :class:`DjmdGenre`)."""
    Remixer = relationship("DjmdArtist", foreign_keys=RemixerID)
    """The remixer entry of the track (links to :class:`DjmdArtist`)."""
    Label = relationship("DjmdLabel", foreign_keys=LabelID)
    """The label entry of the track (links to :class:`DjmdLabel`)."""
    OrgArtist = relationship("DjmdArtist", foreign_keys=OrgArtistID)
    """The original artist entry of the track (links to :class:`DjmdArtist`)."""
    Key = relationship("DjmdKey", foreign_keys=KeyID)
    """The key entry of the track (links to :class:`DjmdKey`)."""
    Color = relationship("DjmdColor", foreign_keys=ColorID)
    """The color entry of the track (links to :class:`DjmdColor`)."""
    Composer = relationship("DjmdArtist", foreign_keys=ComposerID)
    """The composer entry of the track (links to :class:`DjmdArtist`)."""
    AlbumArtist = association_proxy("Album", "AlbumArtist")
    """The album artist entry of the track (links to :class:`DjmdArtist`)."""
    MyTags = relationship("DjmdSongMyTag", back_populates="Content")
    """The my tags of the track (links to :class:`DjmdSongMyTag`)."""
    Cues = relationship("DjmdCue", foreign_keys="DjmdCue.ContentID", back_populates="Content")
    """The cues of the track (links to :class:`DjmdCue`)."""
    ActiveCensors = relationship("DjmdActiveCensor", back_populates="Content")
    """The active censors of the track (links to :class:`DjmdActiveCensor`)."""
    MixerParams = relationship("DjmdMixerParam", back_populates="Content")
    """The mixer parameters of the track (links to :class:`DjmdMixerParam`)."""

    ArtistName = association_proxy("Artist", "Name")
    """The name of the artist (:class:`DjmdArtist`) of the track."""
    AlbumName = association_proxy("Album", "Name")
    """The name of the album (:class:`DjmdAlbum`) of the track."""
    GenreName = association_proxy("Genre", "Name")
    """The name of the genre (:class:`DjmdArtist`) of the track."""
    RemixerName = association_proxy("Remixer", "Name")
    """The name of the remixer (:class:`DjmdArtist`) of the track."""
    LabelName = association_proxy("Label", "Name")
    """The name of the label (:class:`DjmdLabel`) of the track."""
    OrgArtistName = association_proxy("OrgArtist", "Name")
    """The name of the original artist (:class:`DjmdArtist`) of the track."""
    KeyName = association_proxy("Key", "ScaleName")
    """The name of the key (:class:`DjmdKey`) of the track."""
    ColorName = association_proxy("Color", "Commnt")
    """The name of the color (:class:`DjmdColor`) of the track."""
    ComposerName = association_proxy("Composer", "Name")
    """The name of the composer (:class:`DjmdArtist`) of the track."""
    AlbumArtistName = association_proxy("Album", "AlbumArtistName")
    """The name of the album artist (:class:`DjmdArtist`) of the track."""
    MyTagNames = association_proxy("MyTags", "MyTagName")
    """The names of the my tags (:class:`DjmdSongMyTag`) of the track."""
    MyTagIDs = association_proxy("MyTags", "MyTagID")
    """The IDs of the my tags (:class:`DjmdSongMyTag`) of the track."""

    def __repr__(self) -> str:
        s = f"{self.ID: <10} Title={self.Title}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdCue(Base, StatsFull):
    """Table for storing the cue points of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "djmdCue"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`) containing the cue point."""
    InMsec: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue point in milliseconds."""
    InFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue point in frames."""
    InMpegFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue point in MPEG frames."""
    InMpegAbs: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue point in MPEG absolute."""
    OutMsec: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue point in milliseconds (for loops)."""
    OutFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue point in frames (for loops)."""
    OutMpegFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue point in MPEG frames (for loops)."""
    OutMpegAbs: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue point in MPEG absolute (for loops)."""
    Kind: Mapped[int] = mapped_column(Integer, default=None)
    """The kind of the cue point (Cue=0, Fade-In=0, Fade-Out=0, Load=3, Loop=4)."""
    Color: Mapped[int] = mapped_column(Integer, default=None)
    """The color of the cue point. (-1 if no color)"""
    ColorTableIndex: Mapped[int] = mapped_column(Integer, default=None)
    """The color table index of the cue point."""
    ActiveLoop: Mapped[int] = mapped_column(Integer, default=None)
    """The active loop of the cue point."""
    Comment: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The comment of the cue point."""
    BeatLoopSize: Mapped[int] = mapped_column(Integer, default=None)
    """The beat loop size of the cue point."""
    CueMicrosec: Mapped[int] = mapped_column(Integer, default=None)
    """The cue microsecond of the cue point."""
    InPointSeekInfo: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The in point seek info of the cue point."""
    OutPointSeekInfo: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The out point seek info of the cue point."""
    ContentUUID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdContent.UUID"), default=None
    )
    """The UUID of the content (:class:`DjmdContent`) containing the cue point."""

    Content = relationship("DjmdContent", foreign_keys=ContentID, back_populates="Cues")
    """The content entry of the cue point (links to :class:`DjmdContent`)."""

    @property
    def is_memory_cue(self) -> bool:
        return self.Kind == 0

    @property
    def is_hot_cue(self) -> bool:
        return self.Kind > 0


class DjmdDevice(Base, StatsFull):
    """Table for storing the device data of the Rekordbox library contents."""

    __tablename__ = "djmdDevice"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MasterDBID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the master database."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the device."""

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdGenre(Base, StatsFull):
    """Table for storing the genre data of the Rekordbox library contents."""

    __tablename__ = "djmdGenre"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the genre."""

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdHistory(Base, StatsFull):
    """Table for storing the history data (playlist) of the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongHistory`: Stores the songs in the history playlists.
    """

    __tablename__ = "djmdHistory"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry (:class:`DjmdHistory`)."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the history playlist (for ordering)."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the history playlist."""
    Attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attributes of the history playlist"""
    ParentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdHistory.ID"), default=None)
    """The ID of the parent history playlist (:class:`DjmdHistory`)."""
    DateCreated: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The date the history playlist was created."""

    Songs = relationship("DjmdSongHistory", back_populates="History")
    """The songs in the history playlist (links to :class:`DjmdSongHistory`)."""
    Children = relationship(
        "DjmdHistory",
        foreign_keys=ParentID,
        backref=backref("Parent", remote_side=[ID]),
    )
    """The children of the history playlist (links to :class:`DjmdHistory`).
    Backrefs to the parent history playlist via :attr:`Parent`.
    """

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongHistory(Base, StatsFull):
    """Table for storing the songs in the history of the Rekordbox library.

    See Also
    --------
    :class:`DjmdHistory`: Stores the history playlists.
    """

    __tablename__ = "djmdSongHistory"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)

    HistoryID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdHistory.ID"), default=None)
    """The ID of the history playlist (:class:`DjmdHistory`)."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the song in the history playlist."""

    History = relationship("DjmdHistory", back_populates="Songs")
    """The history playlist this song is in (links to :class:`DjmdHistory`)."""
    Content = relationship("DjmdContent")
    """The content entry of the song (links to :class:`DjmdContent`)."""


class DjmdHotCueBanklist(Base, StatsFull):
    """Table for storing the hot-cue banklist data of the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongHotCueBanklist`: Stores the hot-cues in the hot cue banklists.
    """

    __tablename__ = "djmdHotCueBanklist"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry (:class:`DjmdHotCueBanklist`)"""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the hot-cue banklist (for ordering)."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the hot-cue banklist."""
    ImagePath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path to the image of the hot-cue banklist."""
    Attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attributes of the hot cue banklist."""
    ParentID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.ID"), default=None
    )
    """The ID of the parent hot-cue banklist (:class:`DjmdHotCueBanklist`)."""

    Children = relationship(
        "DjmdHotCueBanklist",
        foreign_keys=ParentID,
        backref=backref("Parent", remote_side=[ID]),
    )
    """The children of the hot-cue banklist (links to :class:`DjmdHotCueBanklist`).
    Backrefs to the parent hot-cue banklist via :attr:`Parent`.
    """

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongHotCueBanklist(Base, StatsFull):
    """Table for storing the hot-cues in the hot cue banklists of the Rekordbox library.

    See Also
    --------
    :class:`DjmdHotCueBanklist`: Stores the hot cue banklists.
    """

    __tablename__ = "djmdSongHotCueBanklist"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    HotCueBanklistID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.ID"), default=None
    )
    """The ID of the hot cue banklist (:class:`DjmdHotCueBanklist`)."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the hot-cue in the hot cue banklist."""
    CueID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the hot-cue."""
    InMsec: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the hot-cue in milliseconds."""
    InFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the hot-cue in frames."""
    InMpegFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the hot-cue in MPEG frames."""
    InMpegAbs: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the hot-cue in MPEG absolute."""
    OutMsec: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the hot-cue in milliseconds (for loops)."""
    OutFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the hot-cue in frames (for loops)."""
    OutMpegFrame: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the hot-cue in MPEG frames (for loops)."""
    OutMpegAbs: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the hot-cue in MPEG absolute (for loops)."""
    Color: Mapped[int] = mapped_column(Integer, default=None)
    """The color of the hot-cue."""
    ColorTableIndex: Mapped[int] = mapped_column(Integer, default=None)
    """The color table index of the hot-cue."""
    ActiveLoop: Mapped[int] = mapped_column(Integer, default=None)
    """The active loop flag of the hot-cue."""
    Comment: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The comment of the hot-cue."""
    BeatLoopSize: Mapped[int] = mapped_column(Integer, default=None)
    """The beat loop size of the hot-cue."""
    CueMicrosec: Mapped[int] = mapped_column(Integer, default=None)
    """The cue microsecond of the hot-cue."""
    InPointSeekInfo: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The in point seek info of the hot-cue."""
    OutPointSeekInfo: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The out point seek info of the hot-cue."""
    HotCueBanklistUUID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.UUID"), default=None
    )
    """The UUID of the hot-cue banklist (links to :class:`DjmdHotCueBanklist`)."""

    Content = relationship("DjmdContent")
    """The content of the hot-cue (links to :class:`DjmdContent`)."""


class DjmdKey(Base, StatsFull):
    """Table for storing the keys of tracks in the Rekordbox library."""

    __tablename__ = "djmdKey"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ScaleName: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The scale (name) of the key."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the key (for ordering)."""

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.ScaleName}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdLabel(Base, StatsFull):
    """Table for storing the labels of tracks in the Rekordbox library."""

    __tablename__ = "djmdLabel"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the label."""

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdMenuItems(Base, StatsFull):
    """Table for storing the menu items in the Rekordbox library."""

    __tablename__ = "djmdMenuItems"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Class: Mapped[int] = mapped_column(Integer, default=None)
    """The class of the menu item."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the menu item."""

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdMixerParam(Base, StatsFull):
    """Table for storing the mixer parameters for tracks in the Rekordbox library.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "djmdMixerParam"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`)."""
    GainHigh: Mapped[int] = mapped_column(Integer, default=None)
    """The high gain of the mixer parameter."""
    GainLow: Mapped[int] = mapped_column(Integer, default=None)
    """The low gain of the mixer parameter."""
    PeakHigh: Mapped[int] = mapped_column(Integer, default=None)
    """The high peak of the mixer parameter."""
    PeakLow: Mapped[int] = mapped_column(Integer, default=None)
    """The low peak of the mixer parameter."""

    Content = relationship("DjmdContent", back_populates="MixerParams")
    """The content this mixer parameters belong to (links to :class:`DjmdContent`)."""

    @staticmethod
    def _get_db(low: int, high: int) -> float:
        integer = (high << 16) | low
        byte_data = integer.to_bytes(4, byteorder="big")
        factor = struct.unpack("!f", byte_data)[0]
        if factor <= 0:
            return -np.inf
        return 20 * math.log10(factor)

    @staticmethod
    def _set_db(value: float) -> Tuple[int, int]:
        if value == -np.inf:
            return 0, 0
        factor = 10 ** (value / 20)
        byte_data = struct.pack("!f", factor)
        integer = int.from_bytes(byte_data, byteorder="big")
        low, high = integer & 0xFFFF, integer >> 16
        return low, high

    @property
    def Gain(self) -> float:
        """The auto-gain value of a track in dB.

        This value is computed from the low and high gain values.
        It is the value of the auto-gain knob in the Grid Edit panel or Rekordbox,
        which is also set by the analysis process.
        """
        return self._get_db(self.GainLow, self.GainHigh)

    @Gain.setter
    def Gain(self, value: float) -> None:
        self.GainLow, self.GainHigh = self._set_db(value)

    @property
    def Peak(self) -> float:
        """The peak amplitude of a track in dB.

        This value is computed from the low and high peak values.
        It is not exposed in Rekordbox.
        """
        return self._get_db(self.PeakLow, self.PeakHigh)

    @Peak.setter
    def Peak(self, value: float) -> None:
        self.PeakLow, self.PeakHigh = self._set_db(value)


class DjmdMyTag(Base, StatsFull):
    """Table for storing My-Tags lists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongMyTag`: Table for storing the My-Tag items.
    """

    __tablename__ = "djmdMyTag"

    ID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdMyTag.ParentID"), primary_key=True
    )
    """The ID (primary key) of the table entry."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the My-Tag list (for ordering)."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the My-Tag list."""
    Attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the My-Tag list."""
    ParentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)
    """The ID of the parent My-Tag list (:class:`DjmdMyTag`)."""

    MyTags = relationship("DjmdSongMyTag", back_populates="MyTag")
    """The My-Tag items (links to :class:`DjmdSongMyTag`)."""
    Children = relationship(
        "DjmdMyTag", foreign_keys=ParentID, backref=backref("Parent", remote_side=[ID])
    )
    """The child lists of the My-Tag list (links to :class:`DjmdMyTag`).
    Backrefs to the parent list via :attr:`Parent`.
    """

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongMyTag(Base, StatsFull):
    """Table for storing My-Tag items in the Rekordbox library.

    See Also
    --------
    :class:`DjmdMyTag`: Table for storing My-Tag lists.
    """

    __tablename__ = "djmdSongMyTag"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MyTagID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)
    """The ID of the My-Tag list (links to :class:`DjmdMyTag`)."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the My-Tag item (for ordering)."""

    MyTag = relationship("DjmdMyTag", back_populates="MyTags")
    """The My-Tag list this item belongs to (links to :class:`DjmdMyTag`)."""
    Content = relationship("DjmdContent", back_populates="MyTags")
    """The content this item belongs to (links to :class:`DjmdContent`)."""

    MyTagName = association_proxy("MyTag", "Name")
    """The name of the My-Tag item (:class:`DjmdMyTag`)."""


class DjmdPlaylist(Base, StatsFull):
    """Table for storing playlists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongPlaylist`: Table for storing the playlist contents.
    """

    __tablename__ = "djmdPlaylist"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the playlist (for ordering)."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the playlist."""
    ImagePath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path to the image of the playlist."""
    Attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the playlist."""
    ParentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdPlaylist.ID"), default=None)
    """The ID of the parent playlist (:class:`DjmdPlaylist`)."""
    SmartList: Mapped[str] = mapped_column(Text, default=None)
    """The smart list settings of the playlist."""

    Songs = relationship("DjmdSongPlaylist", back_populates="Playlist", cascade="all, delete")
    """The contents of the playlist (links to :class:`DjmdSongPlaylist`)."""
    Children = relationship(
        "DjmdPlaylist",
        foreign_keys=ParentID,
        backref=backref("Parent", remote_side=[ID]),
        cascade="all, delete",
    )
    """The child playlists of the playlist (links to :class:`DjmdPlaylist`).
    Backrefs to the parent playlist via :attr:`Parent`.
    """

    @property
    def is_playlist(self) -> bool:
        return self.Attribute == PlaylistType.PLAYLIST

    @property
    def is_folder(self) -> bool:
        return self.Attribute == PlaylistType.FOLDER

    @property
    def is_smart_playlist(self) -> bool:
        return self.Attribute == PlaylistType.SMART_PLAYLIST

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongPlaylist(Base, StatsFull):
    """Table for storing playlist contents in the Rekordbox library.

    See Also
    --------
    :class:`DjmdPlaylist`: Table for storing playlists.
    """

    __tablename__ = "djmdSongPlaylist"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    PlaylistID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdPlaylist.ID"), default=None
    )
    """The ID of the playlist this item is in (:class:`DjmdPlaylist`)."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the playlist item (for ordering)."""

    Playlist = relationship("DjmdPlaylist", back_populates="Songs")
    """The playlist this item is in (links to :class:`DjmdPlaylist`)."""
    Content = relationship("DjmdContent")
    """The content this item belongs to (links to :class:`DjmdContent`)."""


class DjmdRelatedTracks(Base, StatsFull):
    """Table for storing related tracks lists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongRelatedTracks`: Table for storing the related tracks contents.
    """

    __tablename__ = "djmdRelatedTracks"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the related tracks list (for ordering)."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the related tracks list."""
    Attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the related tracks list."""
    ParentID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdRelatedTracks.ID"), default=None
    )
    """The ID of the parent related tracks list (:class:`DjmdRelatedTracks`)."""
    Criteria: Mapped[str] = mapped_column(Text, default=None)
    """The criteria used to determine the items in the related tracks list."""

    Songs = relationship("DjmdSongRelatedTracks", back_populates="RelatedTracks")
    """The contents of the related tracks list
    (links to :class:`DjmdSongRelatedTracks`)."""
    Children = relationship(
        "DjmdRelatedTracks",
        foreign_keys=ParentID,
        backref=backref("Parent", remote_side=[ID]),
    )
    """The child related tracks lists of the related tracks list
    (links to :class:`DjmdSongRelatedTracks`).
    Backrefs to the parent related tracks list via :attr:`Parent`.
    """

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongRelatedTracks(Base, StatsFull):
    """Table for storing related tracks list contents in the Rekordbox library.

    See Also
    --------
    :class:`DjmdRelatedTracks`: Table for storing related tracks lists.
    """

    __tablename__ = "djmdSongRelatedTracks"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    RelatedTracksID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdRelatedTracks.ID"), default=None
    )
    """The ID of the related tracks list this item is in
    (:class:`DjmdRelatedTracks`)."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the related tracks list item (for ordering)."""

    RelatedTracks = relationship("DjmdRelatedTracks", back_populates="Songs")
    """The related tracks list this item is in (links to :class:`DjmdRelatedTracks`)."""
    Content = relationship("DjmdContent")
    """The content this item belongs to (links to :class:`DjmdContent`)."""


class DjmdSampler(Base, StatsFull):
    """Table for storing sampler lists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongSampler`: Table for storing the sampler contents.
    """

    __tablename__ = "djmdSampler"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the sampler list (for ordering)."""
    Name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the sampler list."""
    Attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the sampler list."""
    ParentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdSampler.ID"), default=None)
    """The ID of the parent sampler list (:class:`DjmdSampler`)."""

    Songs = relationship("DjmdSongSampler", back_populates="Sampler")
    """The contents of the sampler list (links to :class:`DjmdSongSampler`)."""
    Children = relationship(
        "DjmdSampler",
        foreign_keys=ParentID,
        backref=backref("Parent", remote_side=[ID]),
    )
    """The child sampler lists of the sampler list (links to :class:`DjmdSampler`).
    Backrefs to the parent sampler list via :attr:`Parent`.
    """

    def __repr__(self) -> str:
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongSampler(Base, StatsFull):
    """Table for storing sampler list contents in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSampler`: Table for storing sampler lists.
    """

    __tablename__ = "djmdSongSampler"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    SamplerID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdSampler.ID"), default=None)
    """The ID of the sampler list this item is in (:class:`DjmdSampler`)."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the sampler list item (for ordering)."""

    Sampler = relationship("DjmdSampler", back_populates="Songs")
    """The sampler list this item is in (links to :class:`DjmdSampler`)."""
    Content = relationship("DjmdContent")
    """The content this item belongs to (links to :class:`DjmdContent`)."""


class DjmdSongTagList(Base, StatsFull):
    """Table for storing tag list contents in the Rekordbox library."""

    __tablename__ = "djmdSongTagList"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID: Mapped[str] = mapped_column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the tag list item (for ordering)."""

    Content = relationship("DjmdContent")
    """The content this item belongs to (links to :class:`DjmdContent`)."""


class DjmdSort(Base, StatsFull):
    """Table for storing sort lists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongSort`: Table for storing the sort list contents.
    """

    __tablename__ = "djmdSort"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MenuItemID: Mapped[str] = mapped_column(
        VARCHAR(255), ForeignKey("djmdMenuItems.ID"), default=None
    )
    """The ID of the menu item this sort list is in (:class:`DjmdMenuItems`)."""
    Seq: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence of the sort list (for ordering)."""
    Disable: Mapped[int] = mapped_column(Integer, default=None)
    """Whether the sort list is disabled."""

    MenuItem = relationship("DjmdMenuItems", foreign_keys=MenuItemID)
    """The menu item this sort list is in (links to :class:`DjmdMenuItems`)."""


class HotCueBanklistCue(Base, StatsFull):
    """Table for storing hot cue bank list contents in the Rekordbox library."""

    __tablename__ = "hotCueBanklistCue"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    HotCueBanklistID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the hot cue bank list."""
    Cues: Mapped[str] = mapped_column(Text, default=None)
    """The hot cue bank list contents."""
    rb_cue_count: Mapped[int] = mapped_column(Integer, default=None)
    """The number of hot cues in the bank list."""


class DjmdProperty(Base, StatsTime):
    """Table for storing properties in the Rekordbox library."""

    __tablename__ = "djmdProperty"

    DBID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    DBVersion: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The version of the database."""
    BaseDBDrive: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The drive the database is stored on."""
    CurrentDBDrive: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The drive the database is currently stored on."""
    DeviceID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the device the database is stored on."""
    Reserved1: Mapped[str] = mapped_column(Text, default=None)
    """Reserved column."""
    Reserved2: Mapped[str] = mapped_column(Text, default=None)
    """Reserved column."""
    Reserved3: Mapped[str] = mapped_column(Text, default=None)
    """Reserved column."""
    Reserved4: Mapped[str] = mapped_column(Text, default=None)
    """Reserved column."""
    Reserved5: Mapped[str] = mapped_column(Text, default=None)
    """Reserved column."""


class ImageFile(Base, StatsFull):
    """Table for storing image files in the Rekordbox library.""" ""

    __tablename__ = "imageFile"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    TableName: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the table the image file is in."""
    TargetUUID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The UUID of the target the image file is for."""
    TargetID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the target the image file is for."""
    Path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path to the image file."""
    Hash: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The hash of the image file."""
    Size: Mapped[int] = mapped_column(Integer, default=None)
    """The size of the image file."""
    rb_local_path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The local path to the image file."""
    rb_insync_hash: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The hash of the image file."""
    rb_insync_local_usn: Mapped[int] = mapped_column(BigInteger, default=None)
    """The local USN of the in-sync image file."""
    rb_file_hash_dirty: Mapped[int] = mapped_column(Integer, default=0)
    """Whether the hash of the image file is dirty."""
    rb_local_file_status: Mapped[int] = mapped_column(Integer, default=0)
    """The status of the image file."""
    rb_in_progress: Mapped[int] = mapped_column(SmallInteger, default=0)
    """Whether the image file is in progress."""
    rb_process_type: Mapped[int] = mapped_column(Integer, default=0)
    """The type of process the image file is in."""
    rb_temp_path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The temporary path of the image file."""
    rb_priority: Mapped[int] = mapped_column(Integer, default=50)
    """The priority of the image file."""
    rb_file_size_dirty: Mapped[int] = mapped_column(Integer, default=0)
    """Whether the size of the image file is dirty."""


class SettingFile(Base, StatsFull):
    """Table for storing setting files in the Rekordbox library."""

    __tablename__ = "settingFile"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The path to the setting file."""
    Hash: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The hash of the setting file."""
    Size: Mapped[int] = mapped_column(Integer, default=None)
    """The size of the setting file."""
    rb_local_path: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The local path to the setting file."""
    rb_insync_hash: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The hash of the in-sync setting file."""
    rb_insync_local_usn: Mapped[int] = mapped_column(BigInteger, default=None)
    """The local USN of the setting file."""
    rb_file_hash_dirty: Mapped[int] = mapped_column(Integer, default=0)
    """Whether the hash of the setting file is dirty."""
    rb_file_size_dirty: Mapped[int] = mapped_column(Integer, default=0)
    """Whether the size of the setting file is dirty."""


class UuidIDMap(Base, StatsFull):
    """Table for storing UUID to ID mappings in the Rekordbox library."""

    __tablename__ = "uuidIDMap"

    ID: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    TableName: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the table the mapping is used for."""
    TargetUUID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The UUID of the mapping."""
    CurrentID: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The ID of the mapping."""
