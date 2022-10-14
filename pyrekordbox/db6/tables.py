# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

"""Rekordbox 6 `master.db` SQLAlchemy tabel declarations."""

from sqlalchemy import Column, Integer, VARCHAR, BigInteger, SmallInteger, DateTime
from sqlalchemy import Text, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship

__all__ = [
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


Base = declarative_base()


class StatsTime:

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class StatsFull:

    ID: Column

    UUID = Column(VARCHAR(255), default=None)
    rb_data_status = Column(Integer, default=0)
    rb_local_data_status = Column(Integer, default=0)
    rb_local_deleted = Column(SmallInteger, default=0)
    rb_local_synced = Column(SmallInteger, default=0)
    usn = Column(BigInteger, default=None)
    rb_local_usn = Column(BigInteger, default=None)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.ID})>"


# -- Table declarations ----------------------------------------------------------------


class AgentRegistry(Base, StatsTime):

    __tablename__ = "agentRegistry"

    registry_id = Column(VARCHAR(255), primary_key=True)
    id_1 = Column(VARCHAR(255), default=None)
    id_2 = Column(VARCHAR(255), default=None)
    int_1 = Column(Integer, default=None)
    int_2 = Column(Integer, default=None)
    str_1 = Column(VARCHAR(255), default=None)
    str_2 = Column(VARCHAR(255), default=None)
    date_1 = Column(DateTime, default=None)
    date_2 = Column(DateTime, default=None)
    text_1 = Column(Text, default=None)
    text_2 = Column(Text, default=None)


class CloudAgentRegistry(Base, StatsFull):

    __tablename__ = "cloudAgentRegistry"

    ID = Column(VARCHAR(255), primary_key=True)
    int_1 = Column(Integer, default=None)
    int_2 = Column(Integer, default=None)
    str_1 = Column(VARCHAR(255), default=None)
    str_2 = Column(VARCHAR(255), default=None)
    date_1 = Column(DateTime, default=None)
    date_2 = Column(DateTime, default=None)
    text_1 = Column(Text, default=None)
    text_2 = Column(Text, default=None)


class ContentActiveCensor(Base, StatsFull):

    __tablename__ = "contentActiveCensor"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    ActiveCensors = Column(Text, default=None)
    rb_activecensor_count = Column(Integer, default=None)


class ContentCue(Base, StatsFull):

    __tablename__ = "contentCue"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    Cues = Column(Text, default=None)
    rb_cue_count = Column(Integer, default=None)


class ContentFile(Base, StatsFull):

    __tablename__ = "contentFile"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    Path = Column(VARCHAR(255), default=None)
    Hash = Column(VARCHAR(255), default=None)
    Size = Column(Integer, default=None)
    rb_local_path = Column(VARCHAR(255), default=None)
    rb_insync_hash = Column(VARCHAR(255), default=None)
    rb_insync_local_usn = Column(BigInteger, default=None)
    rb_file_hash_dirty = Column(Integer, default=0)
    rb_local_file_status = Column(Integer, default=0)
    rb_in_progress = Column(SmallInteger, default=0)
    rb_process_type = Column(Integer, default=0)
    rb_temp_path = Column(VARCHAR(255), default=None)
    rb_priority = Column(Integer, default=50)
    rb_file_size_dirty = Column(Integer, default=0)


class DjmdActiveCensor(Base, StatsFull):

    __tablename__ = "djmdActiveCensor"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), default=None)
    InMsec = Column(Integer, default=None)
    OutMsec = Column(Integer, default=None)
    Info = Column(Integer, default=None)
    ParameterList = Column(Text, default=None)
    ContentUUID = Column(VARCHAR(255), default=None)


class DjmdAlbum(Base, StatsFull):

    __tablename__ = "djmdAlbum"

    ID = Column(VARCHAR(255), primary_key=True)
    Name = Column(VARCHAR(255), default=None)
    AlbumArtistID = Column(VARCHAR(255), default=None)
    ImagePath = Column(VARCHAR(255), default=None)
    Compilation = Column(Integer, default=None)
    SearchStr = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <10} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdArtist(Base, StatsFull):

    __tablename__ = "djmdArtist"

    ID = Column(VARCHAR(255), primary_key=True)
    Name = Column(VARCHAR(255), default=None)
    SearchStr = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <10} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdCategory(Base, StatsFull):

    __tablename__ = "djmdCategory"

    ID = Column(VARCHAR(255), primary_key=True)
    MenuItemID = Column(VARCHAR(255), default=None)
    Seq = Column(Integer, default=None)
    Disable = Column(Integer, default=None)
    InfoOrder = Column(Integer, default=None)


class DjmdColor(Base, StatsFull):

    __tablename__ = "djmdColor"

    ID = Column(VARCHAR(255), primary_key=True)
    ColorCode = Column(Integer, default=None)
    SortKey = Column(Integer, default=None)
    Commnt = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Comment={self.Commnt}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdContent(Base, StatsFull):

    __tablename__ = "djmdContent"

    ID = Column(VARCHAR(255), primary_key=True)
    FolderPath = Column(VARCHAR(255), default=None)
    FileNameL = Column(VARCHAR(255), default=None)
    FileNameS = Column(VARCHAR(255), default=None)
    Title = Column(VARCHAR(255), default=None)
    ArtistID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    AlbumID = Column(VARCHAR(255), ForeignKey("djmdAlbum.ID"), default=None)
    GenreID = Column(VARCHAR(255), ForeignKey("djmdGenre.ID"), default=None)
    BPM = Column(Integer, default=None)
    Length = Column(Integer, default=None)
    TrackNo = Column(Integer, default=None)
    BitRate = Column(Integer, default=None)
    BitDepth = Column(Integer, default=None)
    Commnt = Column(Text, default=None)
    FileType = Column(Integer, default=None)
    Rating = Column(Integer, default=None)
    ReleaseYear = Column(Integer, default=None)
    RemixerID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    LabelID = Column(VARCHAR(255), ForeignKey("djmdLabel.ID"), default=None)
    OrgArtistID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    KeyID = Column(VARCHAR(255), ForeignKey("djmdKey.ID"), default=None)
    StockDate = Column(VARCHAR(255), default=None)
    ColorID = Column(VARCHAR(255), ForeignKey("djmdColor.ID"), default=None)
    DJPlayCount = Column(VARCHAR(255), default=None)
    ImagePath = Column(VARCHAR(255), default=None)
    MasterDBID = Column(VARCHAR(255), default=None)
    MasterSongID = Column(VARCHAR(255), default=None)
    AnalysisDataPath = Column(VARCHAR(255), default=None)
    SearchStr = Column(VARCHAR(255), default=None)
    FileSize = Column(Integer, default=None)
    DiscNo = Column(Integer, default=None)
    ComposerID = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    Subtitle = Column(VARCHAR(255), default=None)
    SampleRate = Column(Integer, default=None)
    DisableQuantize = Column(Integer, default=None)
    Analysed = Column(Integer, default=None)
    ReleaseDate = Column(VARCHAR(255), default=None)
    DateCreated = Column(VARCHAR(255), default=None)
    ContentLink = Column(Integer, default=None)
    Tag = Column(VARCHAR(255), default=None)
    ModifiedByRBM = Column(VARCHAR(255), default=None)
    HotCueAutoLoad = Column(VARCHAR(255), default=None)
    DeliveryControl = Column(VARCHAR(255), default=None)
    DeliveryComment = Column(VARCHAR(255), default=None)
    CueUpdated = Column(VARCHAR(255), default=None)
    AnalysisUpdated = Column(VARCHAR(255), default=None)
    TrackInfoUpdated = Column(VARCHAR(255), default=None)
    Lyricist = Column(VARCHAR(255), ForeignKey("djmdArtist.ID"), default=None)
    ISRC = Column(VARCHAR(255), default=None)
    SamplerTrackInfo = Column(Integer, default=None)
    SamplerPlayOffset = Column(Integer, default=None)
    SamplerGain = Column(Float, default=None)
    VideoAssociate = Column(VARCHAR(255), default=None)
    LyricStatus = Column(Integer, default=None)
    ServiceID = Column(Integer, default=None)
    OrgFolderPath = Column(VARCHAR(255), default=None)
    Reserved1 = Column(Text, default=None)
    Reserved2 = Column(Text, default=None)
    Reserved3 = Column(Text, default=None)
    Reserved4 = Column(Text, default=None)
    ExtInfo = Column(Text, default=None)
    rb_file_id = Column(VARCHAR(255), default=None)
    DeviceID = Column(VARCHAR(255), default=None)
    rb_LocalFolderPath = Column(VARCHAR(255), default=None)
    SrcID = Column(VARCHAR(255), default=None)
    SrcTitle = Column(VARCHAR(255), default=None)
    SrcArtistName = Column(VARCHAR(255), default=None)
    SrcAlbumName = Column(VARCHAR(255), default=None)
    SrcLength = Column(Integer, default=None)

    Artist = relationship("DjmdArtist", foreign_keys=[ArtistID])
    Album = relationship("DjmdAlbum", foreign_keys=[AlbumID])
    Genre = relationship("DjmdGenre", foreign_keys=[GenreID])
    Remixer = relationship("DjmdArtist", foreign_keys=[RemixerID])
    Label = relationship("DjmdLabel", foreign_keys=[LabelID])
    OrgArtist = relationship("DjmdArtist", foreign_keys=[OrgArtistID])
    Key = relationship("DjmdKey", foreign_keys=[KeyID])
    Color = relationship("DjmdColor", foreign_keys=[ColorID])
    Composer = relationship("DjmdArtist", foreign_keys=[ComposerID])

    def __repr__(self):
        s = f"{self.ID: <10} Title={self.Title}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdCue(Base, StatsFull):

    __tablename__ = "djmdCue"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    InMsec = Column(Integer, default=None)
    InFrame = Column(Integer, default=None)
    InMpegFrame = Column(Integer, default=None)
    InMpegAbs = Column(Integer, default=None)
    OutMsec = Column(Integer, default=None)
    OutFrame = Column(Integer, default=None)
    OutMpegFrame = Column(Integer, default=None)
    OutMpegAbs = Column(Integer, default=None)
    Kind = Column(Integer, default=None)
    Color = Column(Integer, default=None)
    ColorTableIndex = Column(Integer, default=None)
    ActiveLoop = Column(Integer, default=None)
    Comment = Column(VARCHAR(255), default=None)
    BeatLoopSize = Column(Integer, default=None)
    CueMicrosec = Column(Integer, default=None)
    InPointSeekInfo = Column(VARCHAR(255), default=None)
    OutPointSeekInfo = Column(VARCHAR(255), default=None)
    ContentUUID = Column(VARCHAR(255), ForeignKey("djmdContent.UUID"), default=None)


class DjmdDevice(Base, StatsFull):

    __tablename__ = "djmdDevice"

    ID = Column(VARCHAR(255), primary_key=True)
    MasterDBID = Column(VARCHAR(255), default=None)
    Name = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdGenre(Base, StatsFull):

    __tablename__ = "djmdGenre"

    ID = Column(VARCHAR(255), primary_key=True)
    Name = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdHistory(Base, StatsFull):

    __tablename__ = "djmdHistory"

    ID = Column(VARCHAR(255), primary_key=True)
    Seq = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)
    Attribute = Column(Integer, default=None)
    ParentID = Column(VARCHAR(255), ForeignKey("djmdHistory.ID"), default=None)
    DateCreated = Column(VARCHAR(255), default=None)

    Songs = relationship("DjmdSongHistory", back_populates="History")

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongHistory(Base, StatsFull):

    __tablename__ = "djmdSongHistory"

    ID = Column(VARCHAR(255), primary_key=True)
    HistoryID = Column(VARCHAR(255), ForeignKey("djmdHistory.ID"), default=None)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)

    History = relationship("DjmdHistory", back_populates="Songs")


class DjmdHotCueBanklist(Base, StatsFull):

    __tablename__ = "djmdHotCueBanklist"

    ID = Column(VARCHAR(255), primary_key=True)
    Seq = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)
    ImagePath = Column(VARCHAR(255), default=None)
    Attribute = Column(Integer, default=None)
    ParentID = Column(VARCHAR(255), ForeignKey("djmdHotCueBanklist.ID"), default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongHotCueBanklist(Base, StatsFull):

    __tablename__ = "djmdSongHotCueBanklist"

    ID = Column(VARCHAR(255), primary_key=True)
    HotCueBanklistID = Column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.ID"), default=None
    )
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)
    CueID = Column(VARCHAR(255), default=None)
    InMsec = Column(Integer, default=None)
    InFrame = Column(Integer, default=None)
    InMpegFrame = Column(Integer, default=None)
    InMpegAbs = Column(Integer, default=None)
    OutMsec = Column(Integer, default=None)
    OutFrame = Column(Integer, default=None)
    OutMpegFrame = Column(Integer, default=None)
    OutMpegAbs = Column(Integer, default=None)
    Color = Column(Integer, default=None)
    ColorTableIndex = Column(Integer, default=None)
    ActiveLoop = Column(Integer, default=None)
    Comment = Column(VARCHAR(255), default=None)
    BeatLoopSize = Column(Integer, default=None)
    CueMicrosec = Column(Integer, default=None)
    InPointSeekInfo = Column(VARCHAR(255), default=None)
    OutPointSeekInfo = Column(VARCHAR(255), default=None)
    HotCueBanklistUUID = Column(
        VARCHAR(255), ForeignKey("djmdHotCueBanklist.UUID"), default=None
    )


class DjmdKey(Base, StatsFull):

    __tablename__ = "djmdKey"

    ID = Column(VARCHAR(255), primary_key=True)
    ScaleName = Column(VARCHAR(255), default=None)
    Seq = Column(Integer, default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.ScaleName}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdLabel(Base, StatsFull):

    __tablename__ = "djmdLabel"

    ID = Column(VARCHAR(255), primary_key=True)
    Name = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdMenuItems(Base, StatsFull):

    __tablename__ = "djmdMenuItems"

    ID = Column(VARCHAR(255), primary_key=True)
    Class = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdMixerParam(Base, StatsFull):

    __tablename__ = "djmdMixerParam"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    GainHigh = Column(Integer, default=None)
    GainLow = Column(Integer, default=None)
    PeakHigh = Column(Integer, default=None)
    PeakLow = Column(Integer, default=None)


class DjmdMyTag(Base, StatsFull):

    __tablename__ = "djmdMyTag"

    ID = Column(VARCHAR(255), primary_key=True)
    Seq = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)
    Attribute = Column(Integer, default=None)
    ParentID = Column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)

    MyTags = relationship("DjmdSongMyTag", back_populates="MyTag")

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongMyTag(Base, StatsFull):

    __tablename__ = "djmdSongMyTag"

    ID = Column(VARCHAR(255), primary_key=True)
    MyTagID = Column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)

    MyTag = relationship("DjmdMyTag", back_populates="MyTags")


class DjmdPlaylist(Base, StatsFull):

    __tablename__ = "djmdPlaylist"

    ID = Column(VARCHAR(255), primary_key=True)
    Seq = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)
    ImagePath = Column(VARCHAR(255), default=None)
    Attribute = Column(Integer, default=None)
    ParentID = Column(VARCHAR(255), ForeignKey("djmdMyTag.ID"), default=None)
    SmartList = Column(Text, default=None)

    Songs = relationship("DjmdSongPlaylist", back_populates="Playlist")

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongPlaylist(Base, StatsFull):

    __tablename__ = "djmdSongPlaylist"

    ID = Column(VARCHAR(255), primary_key=True)
    PlaylistID = Column(VARCHAR(255), ForeignKey("djmdPlaylist.ID"), default=None)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)

    Playlist = relationship("DjmdPlaylist", back_populates="Songs")


class DjmdRelatedTracks(Base, StatsFull):

    __tablename__ = "djmdRelatedTracks"

    ID = Column(VARCHAR(255), primary_key=True)
    Seq = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)
    Attribute = Column(Integer, default=None)
    ParentID = Column(VARCHAR(255), ForeignKey("djmdRelatedTracks.ID"), default=None)
    Criteria = Column(Text, default=None)

    Songs = relationship("DjmdSongRelatedTracks", back_populates="RelatedTracks")

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongRelatedTracks(Base, StatsFull):

    __tablename__ = "djmdSongRelatedTracks"

    ID = Column(VARCHAR(255), primary_key=True)
    RelatedTracksID = Column(
        VARCHAR(255), ForeignKey("djmdRelatedTracks.ID"), default=None
    )
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)

    RelatedTracks = relationship("DjmdRelatedTracks", back_populates="Songs")


class DjmdSampler(Base, StatsFull):

    __tablename__ = "djmdSampler"

    ID = Column(VARCHAR(255), primary_key=True)
    Seq = Column(Integer, default=None)
    Name = Column(VARCHAR(255), default=None)
    Attribute = Column(Integer, default=None)
    ParentID = Column(VARCHAR(255), ForeignKey("djmdSampler.ID"), default=None)

    Songs = relationship("DjmdSongSampler", back_populates="Sampler")

    def __repr__(self):
        s = f"{self.ID: <2} Name={self.Name}"
        return f"<{self.__class__.__name__}({s})>"


class DjmdSongSampler(Base, StatsFull):

    __tablename__ = "djmdSongSampler"

    ID = Column(VARCHAR(255), primary_key=True)
    SamplerID = Column(VARCHAR(255), ForeignKey("djmdSampler.ID"), default=None)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)

    Sampler = relationship("DjmdSampler", back_populates="Songs")


class DjmdSongTagList(Base, StatsFull):

    __tablename__ = "djmdSongTagList"

    ID = Column(VARCHAR(255), primary_key=True)
    ContentID = Column(VARCHAR(255), ForeignKey("djmdContent.ID"), default=None)
    TrackNo = Column(Integer, default=None)


class DjmdSort(Base, StatsFull):

    __tablename__ = "djmdSort"

    ID = Column(VARCHAR(255), primary_key=True)
    MenuItemID = Column(VARCHAR(255), default=None)
    Seq = Column(Integer, default=None)
    Disable = Column(Integer, default=None)


class HotCueBanklistCue(Base, StatsFull):

    __tablename__ = "hotCueBanklistCue"

    ID = Column(VARCHAR(255), primary_key=True)
    HotCueBanklistID = Column(VARCHAR(255), default=None)
    Cues = Column(Text, default=None)
    rb_cue_count = Column(Integer, default=None)


class DjmdProperty(Base, StatsTime):

    __tablename__ = "djmdProperty"

    DBID = Column(VARCHAR(255), primary_key=True)
    DBVersion = Column(VARCHAR(255), default=None)
    BaseDBDrive = Column(VARCHAR(255), default=None)
    CurrentDBDrive = Column(VARCHAR(255), default=None)
    DeviceID = Column(VARCHAR(255), default=None)
    Reserved1 = Column(Text, default=None)
    Reserved2 = Column(Text, default=None)
    Reserved3 = Column(Text, default=None)
    Reserved4 = Column(Text, default=None)
    Reserved5 = Column(Text, default=None)


class ImageFile(Base, StatsFull):

    __tablename__ = "imageFile"

    ID = Column(VARCHAR(255), primary_key=True)
    TableName = Column(VARCHAR(255), default=None)
    TargetUUID = Column(VARCHAR(255), default=None)
    TargetID = Column(VARCHAR(255), default=None)
    Path = Column(VARCHAR(255), default=None)
    Hash = Column(VARCHAR(255), default=None)
    Size = Column(Integer, default=None)
    rb_local_path = Column(VARCHAR(255), default=None)
    rb_insync_hash = Column(VARCHAR(255), default=None)
    rb_insync_local_usn = Column(BigInteger, default=None)
    rb_file_hash_dirty = Column(Integer, default=0)
    rb_local_file_status = Column(Integer, default=0)
    rb_in_progress = Column(SmallInteger, default=0)
    rb_process_type = Column(Integer, default=0)
    rb_temp_path = Column(VARCHAR(255), default=None)
    rb_priority = Column(Integer, default=50)
    rb_file_size_dirty = Column(Integer, default=0)


class SettingFile(Base, StatsFull):

    __tablename__ = "settingFile"

    ID = Column(VARCHAR(255), primary_key=True)
    Path = Column(VARCHAR(255), default=None)
    Hash = Column(VARCHAR(255), default=None)
    Size = Column(Integer, default=None)
    rb_local_path = Column(VARCHAR(255), default=None)
    rb_insync_hash = Column(VARCHAR(255), default=None)
    rb_insync_local_usn = Column(BigInteger, default=None)
    rb_file_hash_dirty = Column(Integer, default=0)
    rb_file_size_dirty = Column(Integer, default=0)


class UuidIDMap(Base, StatsFull):

    __tablename__ = "uuidIDMap"

    ID = Column(VARCHAR(255), primary_key=True)
    TableName = Column(VARCHAR(255), default=None)
    TargetUUID = Column(VARCHAR(255), default=None)
    CurrentID = Column(VARCHAR(255), default=None)
