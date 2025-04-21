(db6-format)=
# Rekordbox 6 Database Format

With Rekordbox 6 Pioneer switched from using a DeviceSQL database (`.edb`) to SQLite.
This is an [SQLite3] database encrypted with [SQLCipher4].

## Encryption

The new SQLite database is encrypted which means it can't be used without
the encryption key. Pioneer did this because they prefer that no one outside of
Pioneer touches it (there is a forum post by Pulse).
Since your data is stored and used locally, we know that the key must be present
on our machine. Knowing the key must be local somewhere, gives good hope that you
can find it. It appears that the key is not license or machine dependent and all
databases are encrypted with the same key [^cite_ref6].

## Database structure

The new SQLite database is clearly structured and easy to parse once it is unlocked.
Most tables in the database seem to have a few default columns used by Rekordbox
internally. The last columns of most tables usually are

```{eval-rst}
.. list-table:: Default columns of database tables
   :widths: 25 75
   :header-rows: 1

   * - Table Name
     - Description
   * - `UUID`
     - Universally Unique Identifier
   * - `rb_data_status`
     - Unknown
   * - `rb_local_data_status`
     - Unknown
   * - `rb_local_deleted`
     - Unknown
   * - `rb_local_synced`
     - If the entry is synced with the cloud
   * - `usn`
     - Update sequence number
   * - `rb_local_usn`
     - Local update sequence number
   * - `created_at`
     - Creation time of the entry
   * - `updated_at`
     - Last update time of the entry
```

If a table *does not* use these default columns it is noted in the description of the
table.

### Collection

The main track data of the Rekordbox collection is stored in the `djmdContent` table.
Some tags are linked to other tables in the database via the `ID` column. These include

| Tag      | ID           | Table        |
|----------|--------------|--------------|
| Album    | `AlbumID`    | `djmdAlbum`  |
| Artist   | `ArtistID`   | `djmdArtist` |
| Composer | `ComposerID` | `djmdArtist` |
| Genre    | `GenreID`    | `djmdGenre`  |
| Key      | `KeyID`      | `djmdKey`    |
| Label    | `LabelID`    | `djmdLabel`  |
| Remixer  | `RemixerID`  | `djmdArtist` |

### Playlists and Histories

Playlist-like objects like Playlists and Histories are each stored in two tables,
`djmd<NAME>` and `djmdSong<NAME>`. Regular playlists, for example, are stored in the tables
`djmdPlaylist` and `djmdSongPlaylist`.

The first table contains the information about each playlist or playlist folder, similar
to the nodes of the Rekordbox XML format. Each entry contains a `ID`. The second table
contains the tracks which are contained in all the corresponding playlists. Each entry
contains a `<NAME>ID`, which links it to a playlist in the first table. The track
is linked to the `djmdContent` table via the `ContentID`.

## Tables

### djmdActiveCensor

This table stores the Active Censor data of Rekordbox. It contains information for
actively censoring explicit content of tracks in the Rekordbox collection.
Active Censor items behave like two cue points, between which an effect is applied to
the audio of a track. The table has the following columns:

```{eval-rst}
.. list-table:: djmdActiveCensor columns
   :widths: 25 75
   :header-rows: 1

   * - Table Name
     - Description
   * - `ID`
     - The ID of the Active Censor entry
   * - `ContentID`
     - The ID of the corresponding track
   * - `InMsec`
     - The start time of the section in milli-seconds
   * - `OutMsec`
     - The end time of the section in milli-seconds
   * - `Info`
     -
   * - `ParameterList`
     -
   * - `ContentUUID`
     -

```

### djmdAlbum

This table stores the Album data of Rekordbox. Since multiple tracks can be in the
same album this data is stored in its own table. The table contains all albums found in
the collection.

```{eval-rst}
.. list-table:: djmdAlbum columns
   :widths: 25 100
   :header-rows: 1

   * - Table Name
     - Description
   * - `ID`
     - The ID of the album.
   * - `Name`
     - The name of the album.
   * - `AlbumArtistID`
     - The ID of the album-artist (djmdArtist table)
   * - `ImagePath`
     - The path to the album artwork
   * - `Compilation`
     - Flag if the album is a compilation
   * - `SearchStr`
     - A string somehow used for searching (mostly None)

```

### djmdArtist

This table stores the Artist data of Rekordbox. Since multiple tracks can be made by
the same artist this data is stored in its own table. The table contains all artists
found in the collection.

```{eval-rst}
.. list-table:: djmdArtist columns
   :widths: 25 100
   :header-rows: 1

   * - Column Name
     - Description
   * - `ID`
     - The ID of the artist.
   * - `Name`
     - The name of the artist.
   * - `SearchStr`
     - A string somehow used for searching (mostly None)


```

### djmdCategory

This table stores the Category data of Rekordbox.

```{eval-rst}
.. list-table:: djmdCategory columns
   :widths: 25 100
   :header-rows: 1

   * - Column Name
     - Description
   * - `ID`
     - The ID of the category.
   * - `MenuItemID`
     -
   * - `Seq`
     -
   * - `Disable`
     -
   * - `InfoOrder`
     -

```

### djmdCloudProperty

This table contains no data and consists of reserved columns.

### djmdColor

This table stores the Color data of Rekordbox. The table contains all colors used by
Rekordbox and for tagging tracks:

```{eval-rst}
.. list-table:: djmdCategory columns
   :widths: 25 100
   :header-rows: 1

   * - Column Name
     - Description
   * - `ID`
     - The ID of the color
   * - `ColorCode`
     - Some code for the color
   * - `SortKey`
     - A key used for sorting colors
   * - `Commnt`
     - The name of the color

```

### djmdContent

This table stores the main track data of Rekordbox. The table contains most information
about each track in the collection. Some columns are linked to other tables by the
corresponding ID.

```{eval-rst}
.. list-table:: djmdContent columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the content
     - referenced as `ContentID` in other tables
   * - `FolderPath`
     - The full path of the file
     -
   * - `FileNameL`
     - The long file name
     - This is the normal file name
   * - `FileNameS`
     - The short file name
     - mostly empty
   * - `Title`
     - The title of the track
     -
   * - `ArtistID`
     - The ID of the artist of the track
     - Links to `ID` in the `djmdArtist` table
   * - `AlbumID`
     - The album of the track
     - Links to `ID` in the `djmdAlbum` table
   * - `GenreID`
     - The genre of the track
     - Links to `ID` in the `djmdGenre` table
   * - `BPM`
     - The average BPM of the track
     - Unit: Second
   * - `Length`
     - The length of the track
     - Unit: seconds
   * - `TrackNo`
     - Number of the track of the album
     -
   * - `BitRate`
     - Encoding bit rate
     - Unit: Kbps
   * - `BitDepth`
     - Encoding bit depth
     - Unit: Bits
   * - `Commnt`
     - The comments of the track
     -
   * - `FileType`
     - Type of audio file
     - mp3= `0` / `1` , m4a= `4` , flac= `5` , wav= `11` , aiff= `12`
   * - `Rating`
     - Rating of the track
     -
   * - `ReleaseYear`
     - Year of release
     -
   * - `RemixerID`
     - The remixer of the track
     - Links to `ID` in the `djmdArtist` table
   * - `LabelID`
     - The record label
     - Links to `ID` in the `djmdLabel` table
   * - `OrgArtistID`
     - The original artist (for remixes)
     - Links to `ID` in the `djmdArtist` table
   * - `KeyID`
     - Tonality (Kind of musical key)
     - Links to `ID` in the `djmdKey` table
   * - `StockDate`
     - ?
     -
   * - `ColorID`
     - Colour for track grouping
     - Links to `ID` in the `djmdColor` table
   * - `DJPlayCount`
     - Play count of the track
     - Not sure if plays in Rekordbox count
   * - `ImagePath`
     - Path to the tracks album artwork
     - The path is relative to the Rekordbox database root
   * - `MasterDBID`
     - The database where the track is stored
     - Links to `DBID` in the `DjmdProperty` table
   * - `MasterSongID`
     - The master-song-ID of the track
     - Not sure whats the difference to `ID` and `MasterDBID`
   * - `AnalysisDataPath`
     - Path to the tracks analysis files (ANLZ)
     - The path is relative to the Rekordbox database root
   * - `SearchStr`
     - Some string used for searching?
     -
   * - `FileSize`
     - The file size of the track
     - Unit: Octet
   * - `DiscNo`
     - Number of the disc of the album
     -
   * - `ComposerID`
     - The composer (or producer) of the track
     - Links to `ID` in the `djmdArtist` table
   * - `Subtitle`
     - The track subtitles
     -
   * - `SampleRate`
     - Frequency of sampling
     - Unit: Hertz
   * - `DisableQuantize`
     - Individual quantize setting fro track
     - If None the global setting is used
   * - `Analysed`
     - Some code how the trck is analyzed
     - Guessing not analyzed= `0` , standard= `105` , advanced= `121`, locked = `233`
   * - `ReleaseDate`
     - Date of track release
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - `DateCreated`
     - Date of file creation
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - `ContentLink`
     - Link to the `rb_local_usn` of `TRACK` in `DjmdMenuItems`?
     -
   * - `Tag`
     - My tag value
     -
   * - `ModifiedByRBM`
     - ?
     -
   * - `HotCueAutoLoad`
     - Individual hot cue auto-load settin
     - Either `'on'` or `'off'`
   * - `DeliveryControl`
     - ?
     -
   * - `DeliveryComment`
     - ?
     -
   * - `CueUpdated`
     - Maybe number of times cues where changed?
     -
   * - `AnalysisUpdated`
     - Flag if track is analyzed in advanced mode
     - advanced= `1`, normal= `0`
   * - `TrackInfoUpdated`
     - Maybe number of times cues where changed?
     -
   * - `Lyricist`
     - The lyricist of the track
     -
   * - `ISRC`
     - The ISRC code of the track
     -
   * - `SamplerTrackInfo`
     - ?
     -
   * - `SamplerPlayOffset`
     - ?
     -
   * - `SamplerGain`
     - ?
     -
   * - `VideoAssociate`
     - ?
     -
   * - `LyricStatus`
     - ?
     -
   * - `ServiceID`
     - ?
     -
   * - `OrgFolderPath`
     - ?
     - Mostly same as `FolderPath`
   * - `Reserved1`
     -
     -
   * - `Reserved2`
     -
     -
   * - `Reserved3`
     -
     -
   * - `Reserved4`
     -
     -
   * - `ExtInfo`
     - ?
     -
   * - `rb_file_id`
     - The Rekordbox ID of the file
     -
   * - `DeviceID`
     - The ID of the DjmdDevice this track is stored on.
     -
   * - `rb_LocalFolderPath`
     - ?
     -
   * - `SrcID`
     - ?
     -
   * - `SrcTitle`
     - ?
     -
   * - `SrcArtistName`
     - ?
     -
   * - `SrcAlbumName`
     - ?
     -
   * - `SrcLength`
     - ?
     -

```

### djmdCue

This table stores the cue points (memory and hotcues) of the tracks in Rekordbox.

```{note}
Rekordbox internally represents time in "frames", each being 1/150th of a second (6.666ms).
The `InFrame` and `OutFrame` values use this unit of time. However, when a track is encoded with
variable bit-rate (VBR) or average bit-rate (ABR), the `InMpegFrame` and `OutMpegFrame` values
are filled out to assist with correctly seeking. Despite the names, these values are **not** the
frame indices within the MPEG file, but instead use an alternative timing scheme that is typically
around 1/75th of a second (13.333ms) per frame, i.e. about half the granularity of normal frames.
```

```{eval-rst}
.. list-table:: djmdCue columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the cue point
     -
   * - `ContentID`
     - The corresponding track of the cue
     - Links to `ID` in the `djmdContent` table
   * - `InMsec`
     - Start time of the cue point
     - Unit: Millisecond
   * - `InFrame`
     - The frame number of the start time
     - One frame is 1/150th of a second
   * - `InMpegFrame`
     - The MPEG frame number of the start time
     - See note above. `0` if not a VBR/ABR MPEG file.
   * - `InMpegAbs`
     - The offset (bytes) in the file where the starting frame appears.
     - `0` if not a VBR/ABR MPEG file.
   * - `OutMsec`
     - End time of the cue point (for loops)
     - Unit: Millisecond, `-1` if not a loop
   * - `OutFrame`
     - The frame number of the end time (for loops)
     - One frame is 1/150th of a second. `0` if not a loop
   * - `OutMpegFrame`
     - The MPEG frame number of the end time (for loops)
     - See note above. `0` if not a loop or VBR/ABR MPEG file
   * - `OutMpegAbs`
     - The offset (bytes) in the file where the ending frame appears.
     - `0` if not a loop or VBR/ABR MPEG file
   * - `Kind`
     - Type and/or number of cue point
     - `0` if memory cue, otherwise the number of Hot Cue
   * - `Color`
     - The color ID of the cue point
     - `-1` if no color
   * - `ColorTableIndex`
     - ?
     -
   * - `ActiveLoop`
     - Should the loop start active when reaching the point in playback
     -
   * - `Comment`
     - Name of comment of cue point
     -
   * - `BeatLoopSize`
     - ?
     -
   * - `CueMicrosec`
     - ?
     -
   * - `InPointSeekInfo`
     - ?
     -
   * - `OutPointSeekInfo`
     - ?
     -
   * - `ContentUUID`
     - The UUID of the track
     - Links to `UUID` in `djmdContent` table

```

### djmdDevice

This table stores information about the device(s) where Rekordbox is installed.

```{eval-rst}
.. list-table:: djmdDevice columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the device
     -
   * - `MasterDBID`
     - The ID of the `master.db` database
     -
   * - `Name`
     - The name of the device
     -

```

### djmdGenre

This table stores the genre data of Rekordbox. Since multiple tracks can be the same
genre data is stored in its own table. The table contains all genres found in the
collection.

```{eval-rst}
.. list-table:: djmdDevice columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the genre
     -
   * - `Name`
     - The name of the genre
     -

```

### djmdHistory

This table stores the history playlist data of Rekordbox. It does *not* store the
tracks in the history playlists. These are stored in the `djmdSongHistory` table.
The items in the table can either be a playlist folder or an actual playlist containing
tracks.

```{eval-rst}
.. list-table:: djmdHistory columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the history playlist
     -
   * - `Seq`
     - The number of the the history playlist in the parent folder
     -
   * - `Name`
     - The name of the history playlist
     -
   * - `Attribute`
     - The attributes of the history playlist
     -
   * - `ParentID`
     - The `ID` of the parent history playlist folder
     -
   * - `DateCreated`
     - The date of creation
     -

```

### djmdHotCueBanklist

This table stores the history the hot-cue bank list. It does *not* store the
actual hot-cues. These are stored in the `djmdSongHotCueBanklist` table.

```{eval-rst}
.. list-table:: djmdHistory columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the hot-cue bank list
     -
   * - `Seq`
     - The number of the the hot-cue bank list in the parent folder
     -
   * - `Name`
     - The name of the hot-cue bank list
     -
   * - `ImagePath`
     - The path of the image of the hot-cue bank list
     -
   * - `Attribute`
     - The attributes of the hot-cue bank list
     -
   * - `ParentID`
     - The `ID` of the parent hot-cue bank list folder
     -

```

### djmdKey

This table stores the musical key data of Rekordbox. Since multiple tracks can be
written in the same key the data is stored in its own table. The table contains all
keys found in the collection.

```{eval-rst}
.. list-table:: djmdKey columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the key
     -
   * - `ScaleName`
     - The name of the key
     -
   * - `Seq`
     - The number of the key when sorted
     -

```

### djmdLabel

This table stores the label data of Rekordbox. Since multiple tracks can be
realeased on the same key the data is stored in its own table. The table contains all
labels found in the collection.

```{eval-rst}
.. list-table:: djmdLabel columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the label
     -
   * - `Name`
     - The name of the label
     -

```

### djmdMenuItems

This table stores the configurable menu items shown in the Rekordbox application.

```{eval-rst}
.. list-table:: djmdDevice columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the menu item
     -
   * - `Class`
     - The class of the menu item
     -
   * - `Name`
     - The name of the menu item
     -


```

### djmdMixerParam

This table stores the mixer parameters of tracks in the Rekordbox collection.

Each of the two gain values are represented by a 32-bit floating point number that is packed into a
pair of 16-bit integers. The floating point value represents the linear gain factor, which can be
converted into decibels (dB) by calculating `20.0 * math.log10(f)` where `f` is the gain factor.

The auto-gain value is the one shown in the grid edit panel. The peak value does not appear to be
displayed anywhere in the program, and is most likely used internally for limiting and/or waveform
scaling.

```{eval-rst}
.. list-table:: djmdMixerParam columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the mixer parameters
     -
   * - `ContentID`
     - The `ID` of the corrsponding track
     -
   * - `GainHigh`
     - The upper 16 bits of an IEEE754 single-precision floating point number representing the gain.
     - Auto-gain for the track. See note above.
   * - `GainLow`
     - The lower 16 bits of an IEEE754 single-precision floating point number representing the gain.
     - Auto-gain for the track. See note above.
   * - `PeakHigh`
     - The upper 16 bits of an IEEE754 single-precision floating point number representing the peak.
     - Unknown functionality. Maybe some sort of limiter setting. See note above.
   * - `PeakLow`
     - The lower 16 bits of an IEEE754 single-precision floating point number representing the peak.
     - Unknown functionality. Maybe some sort of limiter setting. See note above.

```

### djmdMyTag

This table stores the My-Tag data of Rekordbox. It does *not* store the
tracks for which the My-Tag values are set. These are stored in the `djmdSongMyTag`
table. The items in the table can either be a My-Tag section or an actual My-Tag value.

```{eval-rst}
.. list-table:: djmdMyTag columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the My-Tag
     -
   * - `Seq`
     - The number of the My-Tag entry
     - Used for sorting
   * - `Name`
     - The name of the My-Tag
     -
   * - `Attribute`
     - The attributes of the My-Tag
     -
   * - `ParentID`
     - The `ID` of the parent My-Tag section
     -

```

### djmdPlaylist

This table stores the playlist data of Rekordbox. It does *not* store the tracks in the
playlists. These are stored in the `djmdSongPlaylist` table. The items in the table can
either be a playlist folder or an actual playlist containing tracks.

```{eval-rst}
.. list-table:: djmdPlaylist columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the playlist
     -
   * - `Seq`
     - The number of the the playlist in the parent folder
     -
   * - `Name`
     - The name of the playlist
     -
   * - `ImagePath`
     - The path to the image file of the playlist
     -
   * - `Attribute`
     - The type of playlist
     - 0: playlist, 1: folder, 4: smart playlist
   * - `ParentID`
     - The `ID` of the parent playlist folder
     -
   * - `SmartList`
     - The conditions for a smart list (if used)
     - Saved as a XML string

```

### djmdProperty

This table stores internal properties of the Rekordbox application. Most columns of it
are reserved.

```{important}
This table does not use the default columns the other tables use. Therefore *all*
columns in the table are shown below
```

```{eval-rst}
.. list-table:: djmdProperty columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `DBID`
     - The ID of the `master.db` database
     -
   * - `DBVersion`
     - The version of the `master.db` database
     -
   * - `BaseDBDrive`
     - The default drive where the `master.db` database is located
     -
   * - `CurrentDBDrive`
     - The current drive where the `master.db` database is located
     -
   * - `Reserved1`
     -
     -
   * - `Reserved2`
     -
     -
   * - `Reserved3`
     -
     -
   * - `Reserved4`
     -
     -
   * - `Reserved5`
     -
     -
   * - `created_at`
     - Creation time of the entry
     -
   * - `updated_at`
     - Last update time of the entry
     -

```

### djmdRelatedTracks

This table stores the related tracks of the tracks in Rekordbox. It does *not* store
the actual related tracks, but rather behaves like a playlist.
The related tracks are stored in the `djmdSongRelatedTracks` table. The items in the table can
either be a folder or an actual list containing the related tracks.

```{eval-rst}
.. list-table:: djmdRelatedTracks columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the related tracks list
     -
   * - `Seq`
     - The number of the related tracks list in the parent folder
     -
   * - `Name`
     - The name of the related tracks list
     -
   * - `Attribute`
     - The attributes of the related tracks list
     -
   * - `ParentID`
     - The `ID` of the parent related tracks list
     -
   * - `Criteria`
     - The criteria used for finding the lated tracks in the list
     -

```

### djmdSampler

This table stores the sampler items of Rekordbox. It does *not* store the actual
samples, but rather behaves like a playlist of samples. The samples are stored in the
`djmdSongSampler` table. The items in the table can either be a folder or an actual list
containing the samples.

```{eval-rst}
.. list-table:: djmdSampler columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the sample list
     -
   * - `Seq`
     - The number of the sample list in the parent folder
     -
   * - `Name`
     - The name of the sample list
     -
   * - `Attribute`
     - The attributes of the sample list
     -
   * - `ParentID`
     - The `ID` of the parent sample list
     -

```

### djmdSongHistory

This table stores tracks contained in the history lists in the `djmdHistory` table.

```{eval-rst}
.. list-table:: djmdSongHistory columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the track in a history
     -
   * - `HistoryID`
     - The ID of the history containing the track
     - Links to `ID` in the `djmdHistory` table
   * - `ContentID`
     - The corresponding track
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the track in the history list
     -

```

### djmdSongHotCueBanklist

This table stores the hot cue entries contained in the hot-cue bank lists in the
`djmdHotCueBanklist` table.

```{note}
Rekordbox internally represents time in "frames", each being 1/150th of a second (6.666ms).
The `InFrame` and `OutFrame` values use this unit of time. However, when a track is encoded with
variable bit-rate (VBR) or average bit-rate (ABR), the `InMpegFrame` and `OutMpegFrame` values
are filled out to assist with correctly seeking. Despite the names, these values are **not** the
frame indices within the MPEG file, but instead use an alternative timing scheme that is typically
around 1/75th of a second (13.333ms) per frame, i.e. about half the granularity of normal frames.
```

```{eval-rst}
.. list-table:: djmdSongHotCueBanklist columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the hot-cue bank list entry
     -
   * - `HotCueBanklistID`
     - The ID of the hot-cue bank list containing the entry
     - Links to `ID` in the `djmdHotCueBanklist` table
   * - `ContentID`
     - The corresponding track
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the hot-cue bank list entry
     -
   * - `CueID`
     - The ID of the corresponding cue item
     - Links to `ID` in the `djmdCues` table
   * - `InMsec`
     - Start time of the cue point
     - Unit: Millisecond
   * - `InFrame`
     - The frame number of the start time
     - One frame is 1/150th of a second.
   * - `InMpegFrame`
     - The MPEG frame number of the start time
     - See note above. `0` if not a VBR/ABR MPEG file
   * - `InMpegAbs`
     - ?
     - `0` if not a VBR/ABR MPEG file
   * - `OutMsec`
     - End time of the cue point (for loops)
     - Unit: Millisecond, `-1` if not a loop
   * - `OutFrame`
     - The frame number of the end time (for loops)
     - One frame is 1/150th of a second. `0` if not a loop
   * - `OutMpegFrame`
     - The MPEG frame number of the end time (for loops)
     - See note above. `0` if not a VBR/ABR MPEG file or if not a loop.
   * - `OutMpegAbs`
     - ?
     - `0` if not a loop or VBR/ABR MPEG file
   * - `Color`
     - The color ID of the cue point
     - `-1` if no color
   * - `ColorTableIndex`
     - ?
     -
   * - `ActiveLoop`
     - ?
     -
   * - `Comment`
     - Name of comment of cue point
     -
   * - `BeatLoopSize`
     - ?
     -
   * - `CueMicrosec`
     - ?
     -
   * - `InPointSeekInfo`
     - ?
     -
   * - `OutPointSeekInfo`
     - ?
     -
   * - `HotCueBanklistUUID`
     - The UUID of the hot-cue bank list
     - Links to `UUID` in `djmdHotCueBanklist` table

```

### djmdSongMyTag

This table stores the My-tag values of tracks linked to in the `djmdMyTag` table.

```{eval-rst}
.. list-table:: djmdSongMyTag columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the My-Tag value
     -
   * - `MyTagID`
     - The ID of the My-Tag group containing the item
     - Links to `ID` in the `djmdMyTag` table
   * - `ContentID`
     - The corresponding track
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the My-Tag for a track
     -

```

### djmdSongPlaylist

This table stores tracks contained in the playlists in the `djmdPlaylist` table.

```{eval-rst}
.. list-table:: djmdSongPlaylist columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the track entry in a playlist
     -
   * - `PlaylistID`
     - The ID of the playlist containing the track
     - Links to `ID` in the `djmdHistory` table
   * - `ContentID`
     - The corresponding track
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the track in the playlist
     -

```

### djmdSongRelatedTracks

This table stores tracks contained in the related tracks lists in the `djmdRelatedTracks`
table.

```{eval-rst}
.. list-table:: djmdSongRelatedTracks columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the related track entry
     -
   * - `SongRelatedTracksID`
     - The ID of the related tracks list containing the entry
     - Links to `ID` in the `djmdRelatedTracks` table
   * - `ContentID`
     - The corresponding track
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the track in the related tracks list
     -

```

### djmdSongSampler

This table stores samples contained in the samples lists in the `djmdSampler` table.

```{eval-rst}
.. list-table:: djmdSongSampler columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the sample entry
     -
   * - `SamplerID`
     - The ID of the samples list containing the entry
     - Links to `ID` in the `djmdSampler` table
   * - `ContentID`
     - The corresponding track (or sample)
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the sample in the sample list
     -

```

### djmdSongTagList

This table is not well understood.

```{eval-rst}
.. list-table:: djmdSongTagList columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the entries in the tag list
     -
   * - `ContentID`
     - The corresponding track
     - Links to `ID` in the `djmdContent` table
   * - `TrackNo`
     - The number of the entry in the tag list
     -

```

### djmdSort

This table stores information for sorting menu items contained in the `djmdMenuItems`
table in Rekordbox.

```{eval-rst}
.. list-table:: djmdSort columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the sorting entry
     -
   * - `MenuItemID`
     - The ID of the corresponding menu item
     - Links to `ID` in the `djmdMenuItems` table
   * - `Seq`
     - The number of the entry in the list
     -
   * - `Disable`
     - Flag if the menu item is disabled or not
     -

```

## References

[^cite_ref6]: Technical inspection of Rekordbox 6 and its new internals.  Christiaan Maks. 2020.
    <https://rekord.cloud/blog/technical-inspection-of-rekordbox-6-and-its-new-internals>.

[sqlcipher4]: https://www.zetetic.net/sqlcipher
[sqlite3]: https://www.sqlite.org/index.html
