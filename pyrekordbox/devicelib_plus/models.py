# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-08-13

import re
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Dict, Iterator, List, Optional, Tuple

from sqlalchemy import (
    VARCHAR,
    BigInteger,
    Dialect,
    ForeignKey,
    Integer,
    Text,
    TypeDecorator,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, backref, mapped_column, relationship

TABLES = [
    "Album",
    "Artist",
    "Category",
    "Color",
    "Content",
    "Cue",
    "Genre",
    "History",
    "HistoryContent",
    "HotCueBankList",
    "HotCueBankListCue",
    "Image",
    "Key",
    "Label",
    "MenuItem",
    "MyTag",
    "MyTagContent",
    "Playlist",
    "PlaylistContent",
    "Property",
    "RecommendedLike",
    "Sort",
]

__all__ = ["PlaylistType", "FileType", "Base"] + TABLES


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


# -- Base- and Mixin classes -----------------------------------------------------------


class Base(DeclarativeBase):
    """Base class used to initialize the declarative base for all tables."""

    __tablename__: str
    __keys__: List[str] = []

    @classmethod
    def create(cls, **kwargs: Any):  # type: ignore # noqa: ANN206
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


# -- Table declarations ----------------------------------------------------------------


class Album(Base):
    """Table for storing the album data of the Device Library Plus contents.

    See Also
    --------
    :class:`Artist`: Table for storing the artist data.
    """

    __tablename__ = "album"

    album_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the album."""
    artist_id: Mapped[int] = mapped_column(Integer, ForeignKey("artist.artist_id"), default=None)
    """The `artist_id` of the :class:`Artist` entry of the artist of this album."""
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("image.image_id"), default=None)
    """The `image_id` of the :class:`Image` entry of the image of this album."""
    isComplation: Mapped[int] = mapped_column(Integer, default=None)
    """The compilation flag of the album."""
    nameForSearch: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The search string of the album."""

    artist = relationship("Artist")
    """The artist entry of the artist of this album (links to :class:`Artist`)."""
    artist_name = association_proxy("AlbumArtist", "name")
    """The name of the album artist (:class:`Artist`)."""

    image = relationship("Image")
    """The image of this album (links to :class:`Image`)."""
    image_path = association_proxy("Image", "path")
    """The path of the album Image (:class:`Image`)"""

    def __repr__(self) -> str:
        s = f"{self.album_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class Artist(Base):
    """Table for storing the artist data of the Device Library Plus contents."""

    __tablename__ = "artist"

    artist_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the artist."""
    nameForSearch: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The search string of the artist."""

    def __repr__(self) -> str:
        s = f"{self.artist_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class Category(Base):
    """Table for storing the category data of the Device Library Plus contents."""

    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    menuItem_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("menuItem.menuItem_id"), default=None
    )
    """The `menuItem_id` of the :class:`MenuItem` entry of the menu item of the category."""
    sequenceNo: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence number of the category used for sorting."""
    isVisible: Mapped[int] = mapped_column(Integer, default=None)
    """The visibility flag of the category."""

    menuItem = relationship("MenuItem")
    """The menu item of the category. (links to :class:`MenuItem`)."""
    menuItem_name = association_proxy("AlbumArtist", "name")
    """The name of the menu item of the category. (:class:`MenuItem`)."""

    def __repr__(self) -> str:
        s = f"{self.category_id: <10} MenuItem={self.menuItem_id}"
        return f"<{self.__class__.__name__}({s})>"


class Color(Base):
    """Table for storing the color data of the Device Library Plus contents."""

    __tablename__ = "color"

    color_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the color."""

    def __repr__(self) -> str:
        s = f"{self.color_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class Content(Base):
    """Table for storing the content data of the Device Library Plus contents."""

    __tablename__ = "content"

    content_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    title: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The title of the track."""
    titleForSearch: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The search string of the track title."""
    subtitle: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The subtitle of the track."""
    bpmx100: Mapped[int] = mapped_column(Integer, default=None)
    """The BPM of the track multiplied by 100 (e.g. 120 BPM = 12000)."""
    length: Mapped[int] = mapped_column(Integer, default=None)
    """The length of the track in milliseconds."""
    trackNo: Mapped[int] = mapped_column(Integer, default=None)
    """The track number of the track in the album."""
    discNo: Mapped[int] = mapped_column(Integer, default=None)
    """The disc number of the track in the album."""
    artist_id_artist: Mapped[int] = mapped_column(
        Integer, ForeignKey("artist.artist_id"), default=None
    )
    """The `artist_id` of the :class:`Artist` entry of the artist of this track."""
    artist_id_remixer: Mapped[int] = mapped_column(
        Integer, ForeignKey("artist.artist_id"), default=None
    )
    """The `artist_id` of the :class:`Artist` entry of the remixer of this track."""
    artist_id_originalArtist: Mapped[int] = mapped_column(
        Integer, ForeignKey("artist.artist_id"), default=None
    )
    """The `artist_id` of the :class:`Artist` entry of the original artist of this track."""
    artist_id_composer: Mapped[int] = mapped_column(
        Integer, ForeignKey("artist.artist_id"), default=None
    )
    """The `artist_id` of the :class:`Artist` entry of the composer of this track."""
    artist_id_lyricist: Mapped[int] = mapped_column(
        Integer, ForeignKey("artist.artist_id"), default=None
    )
    """The `artist_id` of the :class:`Artist` entry of the lyricist of this track."""
    album_id: Mapped[int] = mapped_column(Integer, ForeignKey("album.album_id"), default=None)
    """The `album_id` of the :class:`Album` entry of the album of this track."""
    genre_id: Mapped[int] = mapped_column(Integer, ForeignKey("genre.genre_id"), default=None)
    """The `genre_id` of the :class:`Genre` entry of the genre of this track."""
    label_id: Mapped[int] = mapped_column(Integer, ForeignKey("label.label_id"), default=None)
    """The `label_id` of the :class:`Label` entry of the label of this track."""
    key_id: Mapped[int] = mapped_column(Integer, ForeignKey("key.key_id"), default=None)
    """The `key_id` of the :class:`Key` entry of the key of this track."""
    color_id: Mapped[int] = mapped_column(Integer, ForeignKey("color.color_id"), default=None)
    """The `color_id` of the :class:`Color` entry of the color of this track."""
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("image.image_id"), default=None)
    """The `image_id` of the :class:`Image` entry of the image of this track."""
    djComment: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The comment of the track."""
    rating: Mapped[int] = mapped_column(Integer, default=None)
    """The rating of the track (0-5)."""
    releaseYear: Mapped[int] = mapped_column(Integer, default=None)
    """The release year of the track."""
    releaseDate: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    """The release date of the track."""
    dateCreated: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    """The date when the track was created."""
    dateAdded: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    """The date when the track was added to the library."""
    path: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False)
    """The file path of the track."""
    fileName: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    """The file name of the track."""
    fileSize: Mapped[int] = mapped_column(BigInteger, nullable=False)
    """The file size of the trackin bytes."""
    fileType: Mapped[int] = mapped_column(Integer, nullable=False)
    """The file type of the track."""
    bitrate: Mapped[int] = mapped_column(Integer, nullable=False)
    """The bitrate of the track in kbps."""
    bitDepth: Mapped[int] = mapped_column(Integer, nullable=False)
    """The bit depth of the track."""
    samplingRate: Mapped[int] = mapped_column(Integer, nullable=False)
    """The sampling rate of the track in Hz."""
    isrc: Mapped[str] = mapped_column(VARCHAR(12), default=None)
    """The ISRC (International Standard Recording Code) of the track."""
    isHotCueAutoLoadOn: Mapped[int] = mapped_column(Integer, default=None)
    """The hot cue auto load flag of the track."""
    isKuvoDeliverStatusOn: Mapped[int] = mapped_column(Integer, default=None)
    """The KUVO deliver status flag of the track."""
    kuvoDeliveryComment: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The KUVO deliver comment of the track."""
    masterDbId: Mapped[int] = mapped_column(Integer, default=None)
    """The ID of the track in the local master database."""
    masterContentId: Mapped[int] = mapped_column(Integer, default=None)
    """The content ID of the track in the local master database."""
    analysisDataFilePath: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The file path of the analysis files (ANLZ) of the track."""
    analysedBits: Mapped[int] = mapped_column(Integer, default=None)
    """The number of bits used for the analysis of the track."""
    contentLink: Mapped[int] = mapped_column(Integer, default=None)
    """The content linked flag of the track."""
    hasModified: Mapped[int] = mapped_column(Integer, default=None)
    """The modified flag of the track."""
    cueUpdateCount: Mapped[int] = mapped_column(Integer, default=None)
    """The number of times the cues of the track were updated."""
    analysisDataUpdateCount: Mapped[int] = mapped_column(Integer, default=None)
    """The number of times the analysis data of the track were updated."""
    informationUpdateCount: Mapped[int] = mapped_column(Integer, default=None)
    """The number of times the information of the track was updated."""

    artist = relationship("Artist", foreign_keys=artist_id_artist)
    """The artist entry of the track (links to :class:`Artist`)."""
    remixer = relationship("Artist", foreign_keys=artist_id_remixer)
    """The remixer entry of the track (links to :class:`Artist`)."""
    originalArtist = relationship("Artist", foreign_keys=artist_id_originalArtist)
    """The original artist entry of the track (links to :class:`Artist`)."""
    composer = relationship("Artist", foreign_keys=artist_id_composer)
    """The composer entry of the track (links to :class:`Artist`)."""
    lyricist = relationship("Artist", foreign_keys=artist_id_lyricist)
    """The lyricist entry of the track (links to :class:`Artist`)."""
    album = relationship("Album")
    """The album entry of the track (links to :class:`Album`)."""
    genre = relationship("Genre")
    """The genre entry of the track (links to :class:`Genre`)."""
    label = relationship("Label")
    """The label entry of the track (links to :class:`Label`)."""
    key = relationship("Key")
    """The key entry of the track (links to :class:`Key`)."""
    color = relationship("Color")
    """The color entry of the track (links to :class:`Color`)."""
    image = relationship("Image")
    """The image entry of the track (links to :class:`Image`)."""
    cues = relationship("Cue", foreign_keys="Cue.content_id", back_populates="content")
    """The cues of the track (links to :class:`Cue`)."""

    artist_name = association_proxy("artist", "name")
    """The name of the artist of the track (:class:`Artist`)."""
    remixer_name = association_proxy("remixer", "name")
    """The name of the remixer of the track (:class:`Artist`)."""
    original_artist_name = association_proxy("originalArtist", "name")
    """The name of the original artist of the track (:class:`Artist`)."""
    composer_name = association_proxy("composer", "name")
    """The name of the composer of the track (:class:`Artist`)."""
    lyricist_name = association_proxy("lyricist", "name")
    """The name of the lyricist of the track (:class:`Artist`)."""
    album_name = association_proxy("album", "name")
    """The name of the album of the track (:class:`Album`)."""
    genre_name = association_proxy("genre", "name")
    """The name of the genre of the track (:class:`Genre`)."""
    label_name = association_proxy("label", "name")
    """The name of the label of the track (:class:`Label`)."""
    image_path = association_proxy("image", "path")
    """The path of the image of the track (:class:`Image`)."""

    def __repr__(self) -> str:
        s = f"{self.content_id: <10} name={self.title}"
        return f"<{self.__class__.__name__}({s})>"


class Cue(Base):
    """Table for storing the cue data of the Device Library Plus contents."""

    __tablename__ = "cue"

    cue_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey("content.content_id"), default=None)
    """The `content_id` of the :class:`Content` entry of the content this cue belongs to."""
    kind: Mapped[int] = mapped_column(Integer, default=None)
    """The kind of the cue point (Cue=0, Fade-In=0, Fade-Out=0, Load=3, Loop=4)."""
    colorTableIndex: Mapped[int] = mapped_column(Integer, default=None)
    """The index of the color in the color table."""
    cueComment: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The comment of the cue."""
    isActiveLoop: Mapped[int] = mapped_column(Integer, default=None)
    """The active loop flag of the cue."""
    beatLoopNumerator: Mapped[int] = mapped_column(Integer, default=None)
    """The numerator of the beat loop of the cue."""
    beatLoopDenominator: Mapped[int] = mapped_column(Integer, default=None)
    """The denominator of the beat loop of the cue."""
    inUsec: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue in microseconds."""
    outUsec: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue in microseconds."""
    in150FramePerSec: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue in 150 frames per second."""
    out150FramePerSec: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue in 150 frames per second."""
    inMpegFrameNumber: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue in MPEG frame number."""
    outMpegFrameNumber: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue in MPEG frame number."""
    inMpegAbs: Mapped[int] = mapped_column(Integer, default=None)
    """The absolute in point of the cue in MPEG frame number."""
    outMpegAbs: Mapped[int] = mapped_column(Integer, default=None)
    """The absolute out point of the cue in MPEG frame number."""
    inDecodingStartFramePosition: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue in decoding start frame position."""
    outDecodingStartFramePosition: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue in decoding start frame position."""
    inFileOffsetInBlock: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue in file offset in block."""
    outFileOffsetInBlock: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue in file offset in block."""
    inNumberOfSampleInBlock: Mapped[int] = mapped_column(Integer, default=None)
    """The in point of the cue in number of samples in block."""
    outNumberOfSampleInBlock: Mapped[int] = mapped_column(Integer, default=None)
    """The out point of the cue in number of samples in block."""

    content = relationship("Content")
    """The content this cue belongs to (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"{self.cue_id: <10} id={self.cue_id} kind={self.kind}"
        return f"<{self.__class__.__name__}({s})>"


class Genre(Base):
    """Table for storing the genre data of the Device Library Plus contents."""

    __tablename__ = "genre"

    genre_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the genre."""

    def __repr__(self) -> str:
        s = f"{self.genre_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class History(Base):
    """Table for storing the history data of the Device Library Plus contents."""

    __tablename__ = "history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    sequenceNo: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence number of the history entry used for sorting."""
    name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the history entry."""
    attribute: Mapped[str] = mapped_column(Text, default=None)
    """The attribute of the history playlist."""
    history_id_parent: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("history.history_id"), default=None
    )
    """The `history_id` of the parent :class:`History` entry of this history entry."""

    children = relationship(
        "History",
        foreign_keys=history_id_parent,
        backref=backref("parent", remote_side=[history_id]),
    )
    """The children of the history playlist (links to :class:`DjmdHistory`).
    Backrefs to the parent history playlist via :attr:`Parent`.
    """
    songs = relationship("HistoryContent", back_populates="history")
    """The songs in the history playlist (links to :class:`HistoryContent`)."""
    contents = association_proxy("songs", "content")
    """The contents in the history playlist (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"{self.history_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class HistoryContent(Base):
    """Table for storing the history content data of the Device Library Plus contents."""

    __tablename__ = "history_content"

    history_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("history.history_id"), default=None, primary_key=True
    )
    """The `history_id` of the :class:`History` entry of the history this content belongs to."""
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content.content_id"), default=None, primary_key=True
    )
    """The `content_id` of the :class:`Content` entry of the content in this history."""
    sequenceNo: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence number of the history content entry used for sorting."""

    history = relationship("History", back_populates="songs")
    """The history playlist this entry is in (links to :class:`History`)."""
    content = relationship("Content")
    """The content entry of the song (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"history={self.history_id} content={self.content_id}"
        return f"<{self.__class__.__name__}({s})>"


class HotCueBankList(Base):
    """Table for storing the hot cue bank list data of the Device Library Plus contents."""

    __tablename__ = "hotCueBankList"

    hotCueBankList_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    sequenceNo: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence number of the hot cue bank list entry used for sorting."""
    name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the hot cue bank list."""
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("image.image_id"), default=None)
    """The `image_id` of the :class:`Image` entry of the image of this hot cue bank list."""
    attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the hot cue bank list."""
    hotCueBankList_id_parent: Mapped[int] = mapped_column(
        Integer, ForeignKey("hotCueBankList.hotCueBankList_id"), default=None
    )
    """The `hotCueBankList_id` of the parent :class:`HotCueBankList` entry."""

    image = relationship("Image")
    """The image of this hot cue bank list (links to :class:`Image`)."""
    children = relationship(
        "HotCueBankList",
        foreign_keys=hotCueBankList_id_parent,
        backref=backref("parent", remote_side=[hotCueBankList_id]),
    )
    """The children of the hot cue bank list (links to :class:`HotCueBankList`).
    Backrefs to the parent hot cue bank list via :attr:`parent`.
    """
    hotCueBankList_cues = relationship("HotCueBankListCue", back_populates="hotCueBankList")
    """The cues in the hot cue bank list (links to :class:`HotCueBankListCue`)."""

    def __repr__(self) -> str:
        s = f"{self.hotCueBankList_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class HotCueBankListCue(Base):
    """Table for storing the hot cue bank list cue data of the Device Library Plus contents."""

    __tablename__ = "hotCueBankList_cue"

    hotCueBankList_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hotCueBankList.hotCueBankList_id"), default=None, primary_key=True
    )
    """The `hotCueBankList_id` of the :class:`HotCueBankList` entry this cue belongs to."""
    cue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cue.cue_id"), default=None, primary_key=True
    )
    """The `cue_id` of the :class:`Cue` entry of the cue in this hot cue bank list."""
    sequenceNo: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence number of the hot cue bank list cue entry used for sorting."""

    hotCueBankList = relationship("HotCueBankList")
    """The hot cue bank list this entry is in (links to :class:`HotCueBankList`)."""
    cue = relationship("Cue")
    """The cue entry of the hot cue bank list (links to :class:`Cue`)."""

    def __repr__(self) -> str:
        s = f"hotCueBankList={self.hotCueBankList_id} cue={self.cue_id}"
        return f"<{self.__class__.__name__}({s})>"


class Image(Base):
    """Table for storing the image data of the Device Library Plus contents."""

    __tablename__ = "image"

    image_id: Mapped[str] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    path: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The path of the image file."""

    def __repr__(self) -> str:
        s = f"{self.image_id: <10} path={self.path}"
        return f"<{self.__class__.__name__}({s})>"


class Key(Base):
    """Table for storing the key data of the Device Library Plus contents."""

    __tablename__ = "key"

    key_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the key."""

    def __repr__(self) -> str:
        s = f"{self.key_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class Label(Base):
    """Table for storing the label data of the Device Library Plus contents."""

    __tablename__ = "label"

    label_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the label."""

    def __repr__(self) -> str:
        s = f"{self.label_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class MenuItem(Base):
    """Table for storing the menu item data of the Device Library Plus contents."""

    __tablename__ = "menuItem"

    menuItem_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    kind: Mapped[int] = mapped_column(Integer, default=None)
    """The kind of the menu item."""
    name: Mapped[str] = mapped_column(VARCHAR(255), default=None)
    """The name of the menu item."""

    def __repr__(self) -> str:
        s = f"{self.menuItem_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class MyTag(Base):
    """Table for storing the custom tag data of the Device Library Plus contents."""

    __tablename__ = "myTag"

    myTag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    sequenceNo: Mapped[int] = mapped_column(Integer, nullable=False)
    """The sequence number of the custom tag entry used for sorting."""
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    """The name of the custom tag."""
    attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the custom tag."""
    myTag_id_parent: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("myTag.myTag_id"), default=None
    )

    children = relationship(
        "MyTag",
        foreign_keys=myTag_id_parent,
        backref=backref("parent", remote_side=[myTag_id]),
    )
    """The children of the custom tag (links to :class:`MyTag`).
    Backrefs to the parent custom tag via :attr:`parent`.
    """
    myTags = relationship("MyTagContent", back_populates="myTag")
    """The my tag content in the custom tag (links to :class:`MyTagContent`)."""

    def __repr__(self) -> str:
        s = f"{self.myTag_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class MyTagContent(Base):
    """Table for storing the custom tag content data of the Device Library Plus contents."""

    __tablename__ = "myTag_content"

    myTag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("myTag.myTag_id"), default=None, primary_key=True
    )
    """The `myTag_id` of the :class:`MyTag` entry this content belongs to."""
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content.content_id"), default=None, primary_key=True
    )
    """The `content_id` of the :class:`Content` entry of the content in this custom tag."""

    myTag = relationship("MyTag", back_populates="myTags")
    """The custom tag this entry is in (links to :class:`MyTag`)."""
    content = relationship("Content")
    """The content entry of the custom tag (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"myTag={self.myTag_id} content={self.content_id}"
        return f"<{self.__class__.__name__}({s})>"


class Playlist(Base):
    """Table for storing the playlist data of the Device Library Plus contents."""

    __tablename__ = "playlist"

    playlist_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    sequenceNo: Mapped[int] = mapped_column(Integer, nullable=False)
    """The sequence number of the playlist used for sorting."""
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    """The name of the playlist."""
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("image.image_id"), default=None)
    """The `image_id` of the :class:`Image` entry of the image of this playlist."""
    attribute: Mapped[int] = mapped_column(Integer, default=None)
    """The attribute of the playlist."""
    playlist_id_parent: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("playlist.playlist_id"), default=None
    )
    """The `playlist_id` of the parent :class:`Playlist` entry of this playlist."""

    children = relationship(
        "Playlist",
        foreign_keys=playlist_id_parent,
        backref=backref("parent", remote_side=[playlist_id]),
    )
    """The children of the playlist (links to :class:`Playlist`).
    Backrefs to the parent playlist via :attr:`parent`.
    """
    songs = relationship("PlaylistContent", back_populates="playlist")
    """The songs in the playlist (links to :class:`PlaylistContent`)."""
    contents = association_proxy("songs", "content")
    """The contents in the playlist (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"{self.playlist_id: <10} name={self.name}"
        return f"<{self.__class__.__name__}({s})>"


class PlaylistContent(Base):
    """Table for storing the playlist content data of the Device Library Plus contents."""

    __tablename__ = "playlist_content"

    playlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("playlist.playlist_id"), primary_key=True
    )
    """The `playlist_id` of the :class:`Playlist` entry this content belongs to."""
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content.content_id"), primary_key=True
    )
    """The `content_id` of the :class:`Content` entry of the content in this playlist."""
    sequenceNo: Mapped[int] = mapped_column(Integer, nullable=False)
    """The sequence number of the playlist content entry used for sorting."""

    playlist = relationship("Playlist")
    """The playlist this entry is in (links to :class:`Playlist`)."""
    content = relationship("Content")
    """The content entry of the playlist (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"playlist={self.playlist_id} content={self.content_id}"
        return f"<{self.__class__.__name__}({s})>"


class Property(Base):
    """Table for storing the property data of the Device Library Plus contents."""

    __tablename__ = "property"

    deviceName: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, primary_key=True)
    """The name of the device."""
    dbVersion: Mapped[int] = mapped_column(Integer, default=None)
    """The version of the database."""
    numberOfContents: Mapped[int] = mapped_column(Integer, default=None)
    """The number of contents in the database."""
    createdDate: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    """The date when the property was created."""
    backGroundColorType: Mapped[int] = mapped_column(Integer, default=None)
    """The background color type of the device."""
    myTagMasterDBID: Mapped[int] = mapped_column(Integer, default=None)
    """The master database ID of the custom tags."""

    def __repr__(self) -> str:
        s = f"deviceName={self.deviceName} dbVersion={self.dbVersion}"
        return f"<{self.__class__.__name__}({s})>"


class RecommendedLike(Base):
    """Table for storing the recommended like data of the Device Library Plus contents."""

    __tablename__ = "recommendedLike"

    content_id_1: Mapped[int] = mapped_column(
        Integer, ForeignKey("content.content_id"), primary_key=True
    )
    """The `content_id` of the first :class:`Content` entry of the recommended like."""
    content_id_2: Mapped[int] = mapped_column(
        Integer, ForeignKey("content.content_id"), primary_key=True
    )
    """The `content_id` of the second :class:`Content` entry of the recommended like."""
    rating: Mapped[int] = mapped_column(Integer, default=None)
    """The rating of the recommended like (0-5)."""
    createdDate: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    """The date when the recommended like was created."""

    content_1 = relationship("Content", foreign_keys=content_id_1)
    """The first content of the recommended like (links to :class:`Content`)."""
    content_2 = relationship("Content", foreign_keys=content_id_2)
    """The second content of the recommended like (links to :class:`Content`)."""

    def __repr__(self) -> str:
        s = f"content1={self.content_id_1} content2={self.content_id_2} rating={self.rating}"
        return f"<{self.__class__.__name__}({s})>"


class Sort(Base):
    """Table for storing the sort data for menu items of the Device Library Plus contents."""

    __tablename__ = "sort"

    sort_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """The ID (primary key) of the table entry."""
    menuItem_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("menuItem.menuItem_id"), nullable=False
    )
    """The `menuItem_id` of the :class:`MenuItem` entry of the menu item this sort belongs to."""
    sequenceNo: Mapped[int] = mapped_column(Integer, default=None)
    """The sequence number of the sort entry used for sorting."""
    isVisible: Mapped[int] = mapped_column(Integer, default=None)
    """The visibility flag of the sort entry."""
    isSelectedAsSubColumn: Mapped[int] = mapped_column(Integer, default=None)
    """The selected as sub-column flag of the sort entry."""

    menuItem = relationship("MenuItem")
    """The menu item of the sort entry (links to :class:`MenuItem`)."""

    def __repr__(self) -> str:
        s = f"{self.sort_id: <10} menuItem={self.menuItem_id} sequenceNo={self.sequenceNo}"
        return f"<{self.__class__.__name__}({s})>"
