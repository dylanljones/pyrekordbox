# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-08-07

"""Rekordbox 6 `master.db` SQLAlchemy table declarations."""

from sqlalchemy import Column, Integer, VARCHAR, BigInteger, SmallInteger, DateTime
from sqlalchemy import Text, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.inspection import inspect
from .registry import RekordboxAgentRegistry

__all__ = [
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
]


# -- Base- and Mixin classes -----------------------------------------------------------


class _Base(object):
    """Base class used to initialize the declarative base for all tables."""

    __tablename__: str

    @classmethod
    def create(cls, **kwargs):
        RekordboxAgentRegistry.disable_tracking()
        # noinspection PyArgumentList
        self = cls(**kwargs)
        RekordboxAgentRegistry.enable_tracking()

        RekordboxAgentRegistry.on_create(self)
        return self

    @classmethod
    def columns(cls):
        """Returns a list of all column names without the relationships."""
        return [column.name for column in inspect(cls).c]

    @classmethod
    def relationships(cls):
        """Returns a list of all relationship names."""
        return [column.key for column in inspect(cls).relationships]

    def __iter__(self):
        """Iterates over all columns and relationship names."""
        insp = inspect(self.__class__)
        for column in insp.c:
            yield column.name
        for column in insp.relationships:
            yield column.key

    def __len__(self):
        return sum(1 for _ in self.__iter__())

    def __getitem__(self, item):
        return self.__getattribute__(item)

    # noinspection PyUnresolvedReferences
    def __setattr__(self, key, value):
        if not key.startswith("_"):
            RekordboxAgentRegistry.on_update(self, key, value)
        super().__setattr__(key, value)

    def keys(self):
        """Returns a list of all column names including the relationships."""
        return list(self.__iter__())

    def values(self):
        """Returns a list of all column values including the relationships."""
        return [self.__getitem__(key) for key in self.keys()]

    def items(self):
        for key in self.__iter__():
            yield key, self.__getitem__(key)

    def pformat(self, indent="   "):
        lines = [f"{self.__tablename__}"]
        columns = self.columns()
        w = max(len(col) for col in columns)
        for col in columns:
            lines.append(f"{indent}{col:<{w}} {self.__getitem__(col)}")
        return "\n".join(lines)


Base = declarative_base(cls=_Base)


class StatsTime:
    """Mixin class for tables that only use time statistics columns."""

    created_at = Column(DateTime, nullable=False)
    """The creation date of the table entry (from :class:`StatsTime`)."""
    updated_at = Column(DateTime, nullable=False)
    """The last update date of the table entry (from :class:`StatsTime`)."""


class StatsFull:
    """Mixin class for tables that use all statistics columns."""

    ID: Column
    """The ID (primary key) of the table entry."""

    UUID = Column(VARCHAR(255), default=None)
    """The UUID of the table entry (from :class:`StatsFull`)"""
    rb_data_status = Column(Integer, default=0)
    """The data status of the table entry (from :class:`StatsFull`)."""
    rb_local_data_status = Column(Integer, default=0)
    """The local data status of the table entry (from :class:`StatsFull`)."""
    rb_local_deleted = Column(SmallInteger, default=0)
    """The local deleted status of the table entry (from :class:`StatsFull`)."""
    rb_local_synced = Column(SmallInteger, default=0)
    """The local synced status of the table entry (from :class:`StatsFull`)."""
    usn = Column(BigInteger, default=None)
    """The USN (unique sequence number) of the table entry (from :class:`StatsFull`)."""
    rb_local_usn = Column(BigInteger, default=None)
    """The local USN (unique sequence number) of the table entry
    (from :class:`StatsFull`)."""
    created_at = Column(DateTime, nullable=False)
    """The creation date of the table entry (from :class:`StatsFull`)."""
    updated_at = Column(DateTime, nullable=False)
    """The last update date of the table entry (from :class:`StatsFull`)."""

    def __repr__(self):
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

    registry_id = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    id_1 = Column(VARCHAR(255), default=None)
    """The first ID value of the table entry."""
    id_2 = Column(VARCHAR(255), default=None)
    """The second ID value of the table entry."""
    int_1 = Column(Integer, default=None)
    """The first integer value of the table entry."""
    int_2 = Column(Integer, default=None)
    """The second integer value of the table entry."""
    str_1 = Column(VARCHAR(255), default=None)
    """The first string value of the table entry."""
    str_2 = Column(VARCHAR(255), default=None)
    """The second string value of the table entry."""
    date_1 = Column(DateTime, default=None)
    """The first date value of the table entry."""
    date_2 = Column(DateTime, default=None)
    """The second date value of the table entry."""
    text_1 = Column(Text, default=None)
    """The first text value of the table entry."""
    text_2 = Column(Text, default=None)
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

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    int_1 = Column(Integer, default=None)
    """The first integer value of the table entry."""
    int_2 = Column(Integer, default=None)
    """The second integer value of the table entry."""
    str_1 = Column(VARCHAR(255), default=None)
    """The first string value of the table entry."""
    str_2 = Column(VARCHAR(255), default=None)
    """The second string value of the table entry."""
    date_1 = Column(DateTime, default=None)
    """The first date value of the table entry."""
    date_2 = Column(DateTime, default=None)
    """The second date value of the table entry."""
    text_1 = Column(Text, default=None)
    """The first text value of the table entry."""
    text_2 = Column(Text, default=None)
    """The second text value of the table entry."""


class ContentActiveCensor(Base, StatsFull):
    """Table for storing the active censors of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "contentActiveCensor"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this censor belongs to."""
    ActiveCensors = Column(Text, default=None)
    """The active censors of the table entry."""
    rb_activecensor_count = Column(Integer, default=None)
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

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this cue belongs to."""
    Cues = Column(Text, default=None)
    """The cues of the table entry."""
    rb_cue_count = Column(Integer, default=None)
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

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this file belongs to."""
    Path = Column(VARCHAR(255), default=None)
    """The path of the file."""
    Hash = Column(VARCHAR(255), default=None)
    """The hash of the file."""
    Size = Column(Integer, default=None)
    """The size of the file."""
    rb_local_path = Column(VARCHAR(255), default=None)
    """The local path of the file."""
    rb_insync_hash = Column(VARCHAR(255), default=None)
    """The in-sync hash of the file."""
    rb_insync_local_usn = Column(BigInteger, default=None)
    """The in-sync local USN (unique sequence number) of the file."""
    rb_file_hash_dirty = Column(Integer, default=0)
    """The file hash dirty flag of the file."""
    rb_local_file_status = Column(Integer, default=0)
    """The local file status of the file."""
    rb_in_progress = Column(SmallInteger, default=0)
    """The in progress flag of the file."""
    rb_process_type = Column(Integer, default=0)
    """The process type of the file."""
    rb_temp_path = Column(VARCHAR(255), default=None)
    """The temporary path of the file."""
    rb_priority = Column(Integer, default=50)
    """The priority of the file."""
    rb_file_size_dirty = Column(Integer, default=0)
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

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the :class:`DjmdContent` entry this censor belongs to."""
    InMsec = Column(Integer, default=None)
    """The in time of the censor (in milliseconds)."""
    OutMsec = Column(Integer, default=None)
    """The out time of the censor (in milliseconds)."""
    Info = Column(Integer, default=None)
    """Additional info of the censor."""
    ParameterList = Column(Text, default=None)
    """The parameter list of the censor."""
    ContentUUID = Column(VARCHAR(255), default=None)
    """The UUID of the :class:`DjmdContent` entry this censor belongs to."""

    Content = relationship("DjmdContent")
    """The content entry this censor belongs to (links to :class:`DjmdContent`)."""


class DjmdAlbum(Base, StatsFull):
    """Table for storing the album data of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdArtist`: Table for storing the artist data.
    """

    __tablename__ = "djmdAlbum"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the album."""
    AlbumArtistID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the artist of this album."""
    ImagePath = Column(VARCHAR(255), default=None)
    """The path of the image of the album."""
    Compilation = Column(Integer, default=None)
    """The compilation flag of the album."""
    SearchStr = Column(VARCHAR(255), default=None)
    """The search string of the album."""

    AlbumArtist = relationship("DjmdArtist")
    """The artist entry of the artist of this album (links to :class:`DjmdArtist`)."""

    def __repr__(self):
        s = f"{self.ID: <10} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdArtist(Base, StatsFull):
    """Table for storing the artist data of the Rekordbox library contents."""

    __tablename__ = "djmdArtist"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the artist."""
    SearchStr = Column(VARCHAR(255), default=None)
    """The search string of the artist."""

    def __repr__(self):
        s = f"{self.ID: <10} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdCategory(Base, StatsFull):
    """Table for storing the category data of the Rekordbox library.

    See Also
    --------
    :class:`DjmdMenuItems`: Table for storing menu items of Rekordbox.
    """

    __tablename__ = "djmdCategory"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MenuItemID = Column(VARCHAR(255), ForeignKey("djmdMenuItems.ID"), default=None)
    """The ID of the :class:`DjmdMenuItems` entry belonging to the category."""
    Seq = Column(Integer, default=None)
    """The sequence of the category (for ordering)."""
    Disable = Column(Integer, default=None)
    """The disable flag of the category."""
    InfoOrder = Column(Integer, default=None)
    """Information for ordering the categories."""

    MenuItem = relationship("DjmdMenuItems", foreign_keys=[MenuItemID])
    """The menu item entry of the category (links to :class:`DjmdMenuItems`)."""


class DjmdColor(Base, StatsFull):
    """Table for storing all colors of Rekordbox."""

    __tablename__ = "djmdColor"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ColorCode = Column(Integer, default=None)
    """The color code of the color."""
    SortKey = Column(Integer, default=None)
    """The sort key of the color."""
    Commnt = Column(VARCHAR(255), default=None)
    """The comment (name) of the color."""

    def __repr__(self):
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

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the track."""
    FolderPath = Column(VARCHAR(255), default=None)
    """The full path of the file corresponding to the content entry."""
    FileNameL = Column(VARCHAR(255), default=None)
    """The long file name of the file corresponding to the content entry."""
    FileNameS = Column(VARCHAR(255), default=None)
    """The short file name of the file corresponding to the content entry."""
    Title = Column(VARCHAR(255), default=None)
    """The title of the track."""
    ArtistID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the artist of this track."""
    AlbumID = Column(VARCHAR(255), ForeignKey("djmdAlbum.ID"), default=None)
    """The ID of the :class:`DjmdAlbum` entry of the album of this track."""
    GenreID = Column(VARCHAR(255), ForeignKey("djmdGenre.ID"), default=None)
    """The ID of the :class:`DjmdGenre` entry of the genre of this track."""
    BPM = Column(Integer, default=None)
    """The BPM (beats per minute) of the track."""
    Length = Column(Integer, default=None)
    """The length of the track."""
    TrackNo = Column(Integer, default=None)
    """The track number of the track."""
    BitRate = Column(Integer, default=None)
    """The bit rate of the track."""
    BitDepth = Column(Integer, default=None)
    """The bit depth of the track."""
    Commnt = Column(Text, default=None)
    """The comment of the track."""
    FileType = Column(Integer, default=None)
    """The file type of the track."""
    Rating = Column(Integer, default=None)
    """The rating of the track."""
    ReleaseYear = Column(Integer, default=None)
    """The release year of the track."""
    RemixerID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the remixer of this track."""
    LabelID = Column(VARCHAR(255), ForeignKey("djmdLabel.ID"), default=None)
    """The ID of the :class:`DjmdLabel` entry of the label of this track."""
    OrgArtistID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the original artist of this track."""
    KeyID = Column(VARCHAR(255), ForeignKey("djmdKey.ID"), default=None)
    """The ID of the :class:`DjmdKey` entry of the key of this track."""
    StockDate = Column(VARCHAR(255), default=None)
    """The stock date of the track."""
    ColorID = Column(VARCHAR(255), ForeignKey("djmdColor.ID"), default=None)
    """The ID of the :class:`DjmdColor` entry of the color of this track."""
    DJPlayCount = Column(VARCHAR(255), default=None)
    """The play count of the track."""
    ImagePath = Column(VARCHAR(255), default=None)
    """The path of the image of the track."""
    MasterDBID = Column(VARCHAR(255), default=None)
    """The master database ID of the track."""
    MasterSongID = Column(VARCHAR(255), default=None)
    """The master song ID of the track."""
    AnalysisDataPath = Column(VARCHAR(255), default=None)
    """The path of the analysis data (ANLZ) of the track."""
    SearchStr = Column(VARCHAR(255), default=None)
    """The search string of the track."""
    FileSize = Column(Integer, default=None)
    """The file size of the track."""
    DiscNo = Column(Integer, default=None)
    """The number of the disc of the album of the track."""
    ComposerID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the composer of this track."""
    Subtitle = Column(VARCHAR(255), default=None)
    """The subtitle of the track."""
    SampleRate = Column(Integer, default=None)
    """The sample rate of the track in Hz."""
    DisableQuantize = Column(Integer, default=None)
    """Individual quantize status of the track."""
    Analysed = Column(Integer, default=None)
    """The analysis status of the track."""
    ReleaseDate = Column(VARCHAR(255), default=None)
    """The release date of the track."""
    DateCreated = Column(VARCHAR(255), default=None)
    """The date the track was created."""
    ContentLink = Column(Integer, default=None)
    """The content link of the track."""
    Tag = Column(VARCHAR(255), default=None)
    """The tag of the track."""
    ModifiedByRBM = Column(VARCHAR(255), default=None)
    """The modified by RBM status of the track."""
    HotCueAutoLoad = Column(VARCHAR(255), default=None)
    """The hot cue auto load status of the track."""
    DeliveryControl = Column(VARCHAR(255), default=None)
    """The delivery control status of the track."""
    DeliveryComment = Column(VARCHAR(255), default=None)
    """The delivery comment of the track."""
    CueUpdated = Column(VARCHAR(255), default=None)
    """The cue updated status of the track."""
    AnalysisUpdated = Column(VARCHAR(255), default=None)
    """The analysis updated status of the track."""
    TrackInfoUpdated = Column(VARCHAR(255), default=None)
    """The track info updated status of the track."""
    Lyricist = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    """The ID of the :class:`DjmdArtist` entry of the lyricist of this track."""
    ISRC = Column(VARCHAR(255), default=None)
    """The ISRC of the track."""
    SamplerTrackInfo = Column(Integer, default=None)
    """The sampler track info of the track."""
    SamplerPlayOffset = Column(Integer, default=None)
    """The sampler play offset of the track."""
    SamplerGain = Column(Float, default=None)
    """The sampler gain of the track."""
    VideoAssociate = Column(VARCHAR(255), default=None)
    """The video associate of the track."""
    LyricStatus = Column(Integer, default=None)
    """The lyric status of the track."""
    ServiceID = Column(Integer, default=None)
    """The service ID of the track."""
    OrgFolderPath = Column(VARCHAR(255), default=None)
    """The original folder path of the track."""
    Reserved1 = Column(Text, default=None)
    """Reserved field 1."""
    Reserved2 = Column(Text, default=None)
    """Reserved field 2."""
    Reserved3 = Column(Text, default=None)
    """Reserved field 3."""
    Reserved4 = Column(Text, default=None)
    """Reserved field 4."""
    ExtInfo = Column(Text, default=None)
    """The extended information of the track."""
    rb_file_id = Column(VARCHAR(255), default=None)
    """The file ID used by Rekordbox of the track."""
    DeviceID = Column(VARCHAR(255), default=None)
    """The device ID of the track."""
    rb_LocalFolderPath = Column(VARCHAR(255), default=None)
    """The local folder path used by Rekordbox of the track."""
    SrcID = Column(VARCHAR(255), default=None)
    """The ID of the source of the track."""
    SrcTitle = Column(VARCHAR(255), default=None)
    """The title of the source of the track."""
    SrcArtistName = Column(VARCHAR(255), default=None)
    """The artist name of the source of the track."""
    SrcAlbumName = Column(VARCHAR(255), default=None)
    """The album name of the source of the track."""
    SrcLength = Column(Integer, default=None)
    """The length of the source of the track."""

    Artist = relationship("DjmdArtist", foreign_keys=[ArtistID])
    """The artist entry of the track (links to :class:`DjmdArtists`)."""
    Album = relationship("DjmdAlbum", foreign_keys=[AlbumID])
    """The album entry of the track (links to :class:`DjmdAlbum`)."""
    Genre = relationship("DjmdGenre", foreign_keys=[GenreID])
    """The genre entry of the track (links to :class:`DjmdGenre`)."""
    Remixer = relationship("DjmdArtist", foreign_keys=[RemixerID])
    """The remixer entry of the track (links to :class:`DjmdArtist`)."""
    Label = relationship("DjmdLabel", foreign_keys=[LabelID])
    """The label entry of the track (links to :class:`DjmdLabel`)."""
    OrgArtist = relationship("DjmdArtist", foreign_keys=[OrgArtistID])
    """The original artist entry of the track (links to :class:`DjmdArtist`)."""
    Key = relationship("DjmdKey", foreign_keys=[KeyID])
    """The key entry of the track (links to :class:`DjmdKey`)."""
    Color = relationship("DjmdColor", foreign_keys=[ColorID])
    """The color entry of the track (links to :class:`DjmdColor`)."""
    Composer = relationship("DjmdArtist", foreign_keys=[ComposerID])
    """The composer entry of the track (links to :class:`DjmdArtist`)."""

    def __repr__(self):
        s = f"{self.ID: <10} Title={self.Title}"
        return f"<{self.__class__.__name__}({s})>"

    @property
    def ArtistName(self) -> str:
        """The name of the artist (:class:`DjmdArtist`) of the track."""
        try:
            return self.Artist.Name
        except AttributeError:
            return ""

    @property
    def AlbumName(self) -> str:
        """The name of the album (:class:`DjmdAlbum`) of the track."""
        try:
            return self.Album.Name
        except AttributeError:
            return ""

    @property
    def GenreName(self) -> str:
        """The name of the genre (:class:`DjmdArtist`) of the track."""
        try:
            return self.Genre.Name
        except AttributeError:
            return ""

    @property
    def RemixerName(self) -> str:
        """The name of the remixer (:class:`DjmdArtist`) of the track."""
        try:
            return self.Remixer.Name
        except AttributeError:
            return ""

    @property
    def LabelName(self) -> str:
        """The name of the label (:class:`DjmdLabel`) of the track."""
        try:
            return self.Label.Name
        except AttributeError:
            return ""

    @property
    def OrgArtistName(self) -> str:
        """The name of the original artist (:class:`DjmdArtist`) of the track."""
        try:
            return self.OrgArtist.Name
        except AttributeError:
            return ""

    @property
    def KeyName(self) -> str:
        """The name of the key (:class:`DjmdKey`) of the track."""
        try:
            return self.Key.ScaleName
        except AttributeError:
            return ""

    @property
    def ColorName(self) -> str:
        """The name of the color (:class:`DjmdColor`) of the track."""
        try:
            return self.Color.Commnt
        except AttributeError:
            return ""

    @property
    def ComposerName(self) -> str:
        """The name of the composer (:class:`DjmdArtist`) of the track."""
        try:
            return self.Composer.Name
        except AttributeError:
            return ""


class DjmdCue(Base, StatsFull):
    """Table for storing the cue points of the Rekordbox library contents.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "djmdCue"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`) containing the cue point."""
    InMsec = Column(Integer, default=None)
    """The in point of the cue point in milliseconds."""
    InFrame = Column(Integer, default=None)
    """The in point of the cue point in frames."""
    InMpegFrame = Column(Integer, default=None)
    """The in point of the cue point in MPEG frames."""
    InMpegAbs = Column(Integer, default=None)
    """The in point of the cue point in MPEG absolute."""
    OutMsec = Column(Integer, default=None)
    """The out point of the cue point in milliseconds (for loops)."""
    OutFrame = Column(Integer, default=None)
    """The out point of the cue point in frames (for loops)."""
    OutMpegFrame = Column(Integer, default=None)
    """The out point of the cue point in MPEG frames (for loops)."""
    OutMpegAbs = Column(Integer, default=None)
    """The out point of the cue point in MPEG absolute (for loops)."""
    Kind = Column(Integer, default=None)
    """The kind of the cue point (Cue=0, Fade-In=0, Fade-Out=0, Load=3, Loop=4)."""
    Color = Column(Integer, default=None)
    """The color of the cue point. (-1 if no color)"""
    ColorTableIndex = Column(Integer, default=None)
    """The color table index of the cue point."""
    ActiveLoop = Column(Integer, default=None)
    """The active loop of the cue point."""
    Comment = Column(VARCHAR(255), default=None)
    """The comment of the cue point."""
    BeatLoopSize = Column(Integer, default=None)
    """The beat loop size of the cue point."""
    CueMicrosec = Column(Integer, default=None)
    """The cue microsecond of the cue point."""
    InPointSeekInfo = Column(VARCHAR(255), default=None)
    """The in point seek info of the cue point."""
    OutPointSeekInfo = Column(VARCHAR(255), default=None)
    """The out point seek info of the cue point."""
    ContentUUID = Column(VARCHAR(255), ForeignKey("djmdContent.UUID"), default=None)
    """The UUID of the content (:class:`DjmdContent`) containing the cue point."""

    Content = relationship("DjmdContent", foreign_keys=[ContentID])
    """The content entry of the cue point (links to :class:`DjmdContent`)."""


class DjmdDevice(Base, StatsFull):
    """Table for storing the device data of the Rekordbox library contents."""

    __tablename__ = "djmdDevice"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MasterDBID = Column(VARCHAR(255), default=None)
    """The ID of the master database."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the device."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdGenre(Base, StatsFull):
    """Table for storing the genre data of the Rekordbox library contents."""

    __tablename__ = "djmdGenre"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the genre."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdHistory(Base, StatsFull):
    """Table for storing the history data (playlist) of the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongHistory`: Stores the songs in the history playlists.
    """

    __tablename__ = "djmdHistory"

    ID = Column(VARCHAR(255), ForeignKey("djmdHistory.ParentID"), primary_key=True)
    """The ID (primary key) of the table entry (:class:`DjmdHistory`)."""
    Seq = Column(Integer, default=None)
    """The sequence of the history playlist (for ordering)."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the history playlist."""
    Attribute = Column(Integer, default=None)
    """The attributes of the history playlist"""
    ParentID = Column(VARCHAR(255), ForeignKey("djmdHistory.ID"), default=None)
    """The ID of the parent history playlist (:class:`DjmdHistory`)."""
    DateCreated = Column(VARCHAR(255), default=None)
    """The date the history playlist was created."""

    Songs = relationship("DjmdSongHistory", back_populates="History")
    """The songs in the history playlist (links to :class:`DjmdSongHistory`)."""
    Children = relationship("DjmdHistory", foreign_keys=ParentID)
    """The children of the history playlist (links to :class:`DjmdHistory`)."""
    Parent = relationship("DjmdHistory", foreign_keys=ID)
    """The parent of the history playlist (links to :class:`DjmdHistory`)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongHistory(Base, StatsFull):
    """Table for storing the songs in the history of the Rekordbox library.

    See Also
    --------
    :class:`DjmdHistory`: Stores the history playlists.
    """

    __tablename__ = "djmdSongHistory"

    ID = Column(VARCHAR(255), primary_key=True)

    HistoryID = Column(VARCHAR(255), ForeignKey("djmdHistory.ID"), default=None)
    """The ID of the history playlist (:class:`DjmdHistory`)."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
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

    ID = Column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.ParentID"), primary_key=True
    )
    """The ID (primary key) of the table entry (:class:`DjmdHotCueBanklist`)"""
    Seq = Column(Integer, default=None)
    """The sequence of the hot-cue banklist (for ordering)."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the hot-cue banklist."""
    ImagePath = Column(VARCHAR(255), default=None)
    """The path to the image of the hot-cue banklist."""
    Attribute = Column(Integer, default=None)
    """The attributes of the hot cue banklist."""
    ParentID = Column(VARCHAR(255), ForeignKey("djmdHotCueBanklist.ID"), default=None)
    """The ID of the parent hot-cue banklist (:class:`DjmdHotCueBanklist`)."""

    Children = relationship("DjmdHotCueBanklist", foreign_keys=ParentID)
    """The children of the hot-cue banklist (links to :class:`DjmdHotCueBanklist`)."""
    Parent = relationship("DjmdHotCueBanklist", foreign_keys=ID)
    """The parent of the hot-cue banklist (links to :class:`DjmdHotCueBanklist`)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongHotCueBanklist(Base, StatsFull):
    """Table for storing the hot-cues in the hot cue banklists of the Rekordbox library.

    See Also
    --------
    :class:`DjmdHotCueBanklist`: Stores the hot cue banklists.
    """

    __tablename__ = "djmdSongHotCueBanklist"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    HotCueBanklistID = Column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.ID"), default=None
    )
    """The ID of the hot cue banklist (:class:`DjmdHotCueBanklist`)."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
    """The track number of the hot-cue in the hot cue banklist."""
    CueID = Column(VARCHAR(255), default=None)
    """The ID of the hot-cue."""
    InMsec = Column(Integer, default=None)
    """The in point of the hot-cue in milliseconds."""
    InFrame = Column(Integer, default=None)
    """The in point of the hot-cue in frames."""
    InMpegFrame = Column(Integer, default=None)
    """The in point of the hot-cue in MPEG frames."""
    InMpegAbs = Column(Integer, default=None)
    """The in point of the hot-cue in MPEG absolute."""
    OutMsec = Column(Integer, default=None)
    """The out point of the hot-cue in milliseconds (for loops)."""
    OutFrame = Column(Integer, default=None)
    """The out point of the hot-cue in frames (for loops)."""
    OutMpegFrame = Column(Integer, default=None)
    """The out point of the hot-cue in MPEG frames (for loops)."""
    OutMpegAbs = Column(Integer, default=None)
    """The out point of the hot-cue in MPEG absolute (for loops)."""
    Color = Column(Integer, default=None)
    """The color of the hot-cue."""
    ColorTableIndex = Column(Integer, default=None)
    """The color table index of the hot-cue."""
    ActiveLoop = Column(Integer, default=None)
    """The active loop flag of the hot-cue."""
    Comment = Column(VARCHAR(255), default=None)
    """The comment of the hot-cue."""
    BeatLoopSize = Column(Integer, default=None)
    """The beat loop size of the hot-cue."""
    CueMicrosec = Column(Integer, default=None)
    """The cue microsecond of the hot-cue."""
    InPointSeekInfo = Column(VARCHAR(255), default=None)
    """The in point seek info of the hot-cue."""
    OutPointSeekInfo = Column(VARCHAR(255), default=None)
    """The out point seek info of the hot-cue."""
    HotCueBanklistUUID = Column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.UUID"), default=None
    )
    """The UUID of the hot-cue banklist (links to :class:`DjmdHotCueBanklist`)."""

    Content = relationship("DjmdContent")
    """The content of the hot-cue (links to :class:`DjmdContent`)."""


class DjmdKey(Base, StatsFull):
    """Table for storing the keys of tracks in the Rekordbox library."""

    __tablename__ = "djmdKey"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ScaleName = Column(VARCHAR(255), default=None)
    """The scale (name) of the key."""
    Seq = Column(Integer, default=None)
    """The sequence of the key (for ordering)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.ScaleName}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdLabel(Base, StatsFull):
    """Table for storing the labels of tracks in the Rekordbox library."""

    __tablename__ = "djmdLabel"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the label."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdMenuItems(Base, StatsFull):
    """Table for storing the menu items in the Rekordbox library."""

    __tablename__ = "djmdMenuItems"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Class = Column(Integer, default=None)
    """The class of the menu item."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the menu item."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdMixerParam(Base, StatsFull):
    """Table for storing the mixer parameters for tracks in the Rekordbox library.

    See Also
    --------
    :class:`DjmdContent`: Table for storing the content data.
    """

    __tablename__ = "djmdMixerParam"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content (:class:`DjmdContent`)."""
    GainHigh = Column(Integer, default=None)
    """The high gain of the mixer parameter."""
    GainLow = Column(Integer, default=None)
    """The low gain of the mixer parameter."""
    PeakHigh = Column(Integer, default=None)
    """The high peak of the mixer parameter."""
    PeakLow = Column(Integer, default=None)
    """The low peak of the mixer parameter."""

    Content = relationship("DjmdContent")
    """The content this mixer parameters belong to (links to :class:`DjmdContent`)."""


class DjmdMyTag(Base, StatsFull):
    """Table for storing My-Tags lists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongMyTag`: Table for storing the My-Tag items.
    """

    __tablename__ = "djmdMyTag"

    ID = Column(VARCHAR(255), ForeignKey("djmdMyTag.ParentID"), primary_key=True)
    """The ID (primary key) of the table entry."""
    Seq = Column(Integer, default=None)
    """The sequence of the My-Tag list (for ordering)."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the My-Tag list."""
    Attribute = Column(Integer, default=None)
    """The attribute of the My-Tag list."""
    ParentID = Column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)
    """The ID of the parent My-Tag list (:class:`DjmdMyTag`)."""

    MyTags = relationship("DjmdSongMyTag", back_populates="MyTag")
    """The My-Tag items (links to :class:`DjmdSongMyTag`)."""
    Children = relationship("DjmdMyTag", foreign_keys=ParentID)
    """The child lists of the My-Tag list (links to :class:`DjmdMyTag`)."""
    Parent = relationship("DjmdMyTag", foreign_keys=ID)
    """The parent list of the My-Tag list (links to :class:`DjmdMyTag`)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongMyTag(Base, StatsFull):
    """Table for storing My-Tag items in the Rekordbox library.

    See Also
    --------
    :class:`DjmdMyTag`: Table for storing My-Tag lists.
    """

    __tablename__ = "djmdSongMyTag"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MyTagID = Column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)
    """The ID of the My-Tag list (links to :class:`DjmdMyTag`)."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
    """The track number of the My-Tag item (for ordering)."""

    MyTag = relationship("DjmdMyTag", back_populates="MyTags")
    """The My-Tag list this item belongs to (links to :class:`DjmdMyTag`)."""
    Content = relationship("DjmdContent")
    """The content this item belongs to (links to :class:`DjmdContent`)."""


class DjmdPlaylist(Base, StatsFull):
    """Table for storing playlists in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSongPlaylist`: Table for storing the playlist contents.
    """

    __tablename__ = "djmdPlaylist"

    ID = Column(VARCHAR(255), ForeignKey("djmdPlaylist.ParentID"), primary_key=True)
    """The ID (primary key) of the table entry."""
    Seq = Column(Integer, default=None)
    """The sequence of the playlist (for ordering)."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the playlist."""
    ImagePath = Column(VARCHAR(255), default=None)
    """The path to the image of the playlist."""
    Attribute = Column(Integer, default=None)
    """The attribute of the playlist."""
    ParentID = Column(VARCHAR(255), ForeignKey("djmdPlaylist.ID"), default=None)
    """The ID of the parent playlist (:class:`DjmdPlaylist`)."""
    SmartList = Column(Text, default=None)
    """The smart list settings of the playlist."""

    Songs = relationship("DjmdSongPlaylist", back_populates="Playlist")
    """The contents of the playlist (links to :class:`DjmdSongPlaylist`)."""
    Children = relationship("DjmdPlaylist", foreign_keys=ParentID)
    """The child playlists of the playlist (links to :class:`DjmdPlaylist`)."""
    Parent = relationship("DjmdPlaylist", foreign_keys=ID)
    """The parent playlist of the playlist (links to :class:`DjmdPlaylist`)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongPlaylist(Base, StatsFull):
    """Table for storing playlist contents in the Rekordbox library.

    See Also
    --------
    :class:`DjmdPlaylist`: Table for storing playlists.
    """

    __tablename__ = "djmdSongPlaylist"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    PlaylistID = Column(VARCHAR(255), ForeignKey("djmdPlaylist.ID"), default=None)
    """The ID of the playlist this item is in (:class:`DjmdPlaylist`)."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
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

    ID = Column(
        VARCHAR(255), ForeignKey("djmdRelatedTracks.ParentID"), primary_key=True
    )
    """The ID (primary key) of the table entry."""
    Seq = Column(Integer, default=None)
    """The sequence of the related tracks list (for ordering)."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the related tracks list."""
    Attribute = Column(Integer, default=None)
    """The attribute of the related tracks list."""
    ParentID = Column(VARCHAR(255), ForeignKey("djmdRelatedTracks.ID"), default=None)
    """The ID of the parent related tracks list (:class:`DjmdRelatedTracks`)."""
    Criteria = Column(Text, default=None)
    """The criteria used to determine the items in the related tracks list."""

    Songs = relationship("DjmdSongRelatedTracks", back_populates="RelatedTracks")
    """The contents of the related tracks list
    (links to :class:`DjmdSongRelatedTracks`)."""
    Children = relationship("DjmdRelatedTracks", foreign_keys=ParentID)
    """The child related tracks lists of the related tracks list
    (links to :class:`DjmdSongRelatedTracks`)."""
    Parent = relationship("DjmdRelatedTracks", foreign_keys=ID)
    """The parent related tracks list of the related tracks list
    (links to :class:`DjmdSongRelatedTracks`)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongRelatedTracks(Base, StatsFull):
    """Table for storing related tracks list contents in the Rekordbox library.

    See Also
    --------
    :class:`DjmdRelatedTracks`: Table for storing related tracks lists.
    """

    __tablename__ = "djmdSongRelatedTracks"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    RelatedTracksID = Column(
        VARCHAR(255), ForeignKey("djmdRelatedTracks.ID"), default=None
    )
    """The ID of the related tracks list this item is in
    (:class:`DjmdRelatedTracks`)."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
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

    ID = Column(VARCHAR(255), ForeignKey("djmdSampler.ID"), primary_key=True)
    """The ID (primary key) of the table entry."""
    Seq = Column(Integer, default=None)
    """The sequence of the sampler list (for ordering)."""
    Name = Column(VARCHAR(255), default=None)
    """The name of the sampler list."""
    Attribute = Column(Integer, default=None)
    """The attribute of the sampler list."""
    ParentID = Column(VARCHAR(255), ForeignKey("djmdSampler.ID"), default=None)
    """The ID of the parent sampler list (:class:`DjmdSampler`)."""

    Songs = relationship("DjmdSongSampler", back_populates="Sampler")
    """The contents of the sampler list (links to :class:`DjmdSongSampler`)."""
    Children = relationship("DjmdSampler", foreign_keys=ParentID)
    """The child sampler lists of the sampler list (links to :class:`DjmdSampler`)."""
    Parent = relationship("DjmdSampler", foreign_keys=ID)
    """The parent sampler list of the sampler list (links to :class:`DjmdSampler`)."""

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongSampler(Base, StatsFull):
    """Table for storing sampler list contents in the Rekordbox library.

    See Also
    --------
    :class:`DjmdSampler`: Table for storing sampler lists.
    """

    __tablename__ = "djmdSongSampler"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    SamplerID = Column(VARCHAR(255), ForeignKey("djmdSampler.ID"), default=None)
    """The ID of the sampler list this item is in (:class:`DjmdSampler`)."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
    """The track number of the sampler list item (for ordering)."""

    Sampler = relationship("DjmdSampler", back_populates="Songs")
    """The sampler list this item is in (links to :class:`DjmdSampler`)."""
    Content = relationship("DjmdContent")
    """The content this item belongs to (links to :class:`DjmdContent`)."""


class DjmdSongTagList(Base, StatsFull):
    """Table for storing tag list contents in the Rekordbox library."""

    __tablename__ = "djmdSongTagList"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    """The ID of the content this item belongs to (:class:`DjmdContent`)."""
    TrackNo = Column(Integer, default=None)
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

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    MenuItemID = Column(VARCHAR(255), ForeignKey("djmdMenuItems.ID"), default=None)
    """The ID of the menu item this sort list is in (:class:`DjmdMenuItems`)."""
    Seq = Column(Integer, default=None)
    """The sequence of the sort list (for ordering)."""
    Disable = Column(Integer, default=None)
    """Whether the sort list is disabled."""

    MenuItem = relationship("DjmdMenuItems", foreign_keys=[MenuItemID])
    """The menu item this sort list is in (links to :class:`DjmdMenuItems`)."""


class HotCueBanklistCue(Base, StatsFull):
    """Table for storing hot cue bank list contents in the Rekordbox library."""

    __tablename__ = "hotCueBanklistCue"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    HotCueBanklistID = Column(VARCHAR(255), default=None)
    """The ID of the hot cue bank list."""
    Cues = Column(Text, default=None)
    """The hot cue bank list contents."""
    rb_cue_count = Column(Integer, default=None)
    """The number of hot cues in the bank list."""


class DjmdProperty(Base, StatsTime):
    """Table for storing properties in the Rekordbox library."""

    __tablename__ = "djmdProperty"

    DBID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    DBVersion = Column(VARCHAR(255), default=None)
    """The version of the database."""
    BaseDBDrive = Column(VARCHAR(255), default=None)
    """The drive the database is stored on."""
    CurrentDBDrive = Column(VARCHAR(255), default=None)
    """The drive the database is currently stored on."""
    DeviceID = Column(VARCHAR(255), default=None)
    """The ID of the device the database is stored on."""
    Reserved1 = Column(Text, default=None)
    """Reserved column."""
    Reserved2 = Column(Text, default=None)
    """Reserved column."""
    Reserved3 = Column(Text, default=None)
    """Reserved column."""
    Reserved4 = Column(Text, default=None)
    """Reserved column."""
    Reserved5 = Column(Text, default=None)
    """Reserved column."""


class ImageFile(Base, StatsFull):
    """Table for storing image files in the Rekordbox library.""" ""

    __tablename__ = "imageFile"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    TableName = Column(VARCHAR(255), default=None)
    """The name of the table the image file is in."""
    TargetUUID = Column(VARCHAR(255), default=None)
    """The UUID of the target the image file is for."""
    TargetID = Column(VARCHAR(255), default=None)
    """The ID of the target the image file is for."""
    Path = Column(VARCHAR(255), default=None)
    """The path to the image file."""
    Hash = Column(VARCHAR(255), default=None)
    """The hash of the image file."""
    Size = Column(Integer, default=None)
    """The size of the image file."""
    rb_local_path = Column(VARCHAR(255), default=None)
    """The local path to the image file."""
    rb_insync_hash = Column(VARCHAR(255), default=None)
    """The hash of the image file."""
    rb_insync_local_usn = Column(BigInteger, default=None)
    """The local USN of the in-sync image file."""
    rb_file_hash_dirty = Column(Integer, default=0)
    """Whether the hash of the image file is dirty."""
    rb_local_file_status = Column(Integer, default=0)
    """The status of the image file."""
    rb_in_progress = Column(SmallInteger, default=0)
    """Whether the image file is in progress."""
    rb_process_type = Column(Integer, default=0)
    """The type of process the image file is in."""
    rb_temp_path = Column(VARCHAR(255), default=None)
    """The temporary path of the image file."""
    rb_priority = Column(Integer, default=50)
    """The priority of the image file."""
    rb_file_size_dirty = Column(Integer, default=0)
    """Whether the size of the image file is dirty."""


class SettingFile(Base, StatsFull):
    """Table for storing setting files in the Rekordbox library."""

    __tablename__ = "settingFile"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    Path = Column(VARCHAR(255), default=None)
    """The path to the setting file."""
    Hash = Column(VARCHAR(255), default=None)
    """The hash of the setting file."""
    Size = Column(Integer, default=None)
    """The size of the setting file."""
    rb_local_path = Column(VARCHAR(255), default=None)
    """The local path to the setting file."""
    rb_insync_hash = Column(VARCHAR(255), default=None)
    """The hash of the in-sync setting file."""
    rb_insync_local_usn = Column(BigInteger, default=None)
    """The local USN of the setting file."""
    rb_file_hash_dirty = Column(Integer, default=0)
    """Whether the hash of the setting file is dirty."""
    rb_file_size_dirty = Column(Integer, default=0)
    """Whether the size of the setting file is dirty."""


class UuidIDMap(Base, StatsFull):
    """Table for storing UUID to ID mappings in the Rekordbox library."""

    __tablename__ = "uuidIDMap"

    ID = Column(VARCHAR(255), primary_key=True)
    """The ID (primary key) of the table entry."""
    TableName = Column(VARCHAR(255), default=None)
    """The name of the table the mapping is used for."""
    TargetUUID = Column(VARCHAR(255), default=None)
    """The UUID of the mapping."""
    CurrentID = Column(VARCHAR(255), default=None)
    """The ID of the mapping."""
