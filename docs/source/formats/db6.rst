Rekordbox 6 Database
====================

With Rekordbox 6 Pioneer switched from using a DeviceSQL database (`.edb`) to SQLite.
This is an `SQLite3`_ database encrypted with `SQLCipher4`_.



.. _SQLCipher4: https://www.sqlite.org/index.html
.. _SQLite3: https://www.zetetic.net/sqlcipher

Encryption
----------

The new SQLite database is encrypted which means it can't be used without
the encryption key. Pioneer did this because they prefer that no one outside of
Pioneer touches it (there is a forum post by Pulse).
Since your data is stored and used locally, we know that the key must be present
on our machine. Knowing the key must be local somewhere, gives good hope that you
can find it. It appears that the key is not license or machine dependent and all
databases are encrypted with the same key [ref6]_.


Database structure
------------------

The new SQLite database is clearly structured and easy to parse once it is unlocked.
Each table in the database seems to have a few default columns used by Rekordbox
internally. The last columns of each tables are

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


Collection
~~~~~~~~~~

The main track data of the Rekordbox collection is stored in the `djmdContent` table.
Some tags are linked to other tables in the database via the `ID` column. These include

+----------+---------------+--------------+
| Tag      |      ID       |    Table     |
+==========+===============+==============+
| Album    |   `AlbumID`   | `djmdAlbum`  |
+----------+---------------+--------------+
| Artist   |  `ArtistID`   | `djmdArtist` |
+----------+---------------+--------------+
| Composer | `ComposerID`  | `djmdArtist` |
+----------+---------------+--------------+
| Genre    |   `GenreID`   | `djmdGenre`  |
+----------+---------------+--------------+
| Key      |    `KeyID`    |  `djmdKey`   |
+----------+---------------+--------------+
| Label    |   `LabelID`   | `djmdLabel`  |
+----------+---------------+--------------+
| Remixer  |  `RemixerID`  | `djmdArtist` |
+----------+---------------+--------------+


Playlists and Histories
~~~~~~~~~~~~~~~~~~~~~~~

Playlist-like objects like Playlists and Histories are each stored in two tables,
`djmd<NAME>` and `djmdSong<NAME>`. Regular playlists, for example, are stored in the tables
`djmdPlaylist` and `djmdSongPlaylist`.

The first table contains the information about each playlist or playlist folder, similar
to the nodes of the Rekordbox XML format. Each entry contains a `ID`. The second table
contains the tracks which are contained in all the corresponding playlists. Each entry
contains a `<NAME>ID`, which links it to a playlist in the first table. The track
is linked to the `djmdContent` table via the `ContentID`.


Tables
------

djmdActiveCensor
~~~~~~~~~~~~~~~~

This table stores the Active Censor data of Rekordbox. It contains information for
actively censoring explicit content of tracks in the Rekordbox collection.
Active Censor items behave like two cue points, between which a effect is applied to
the audio of a track.


djmdActiveCensor
~~~~~~~~~~~~~~~~

This table stores the Active Censor data of Rekordbox. It contains information for
actively censoring explicit content of tracks in the Rekordbox collection.
Active Censor items behave like two cue points, between which an effect is applied to
the audio of a track. The table has the following columns:

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


djmdAlbum
~~~~~~~~~

This table stores the Album data of Rekordbox. Since multiple tracks can be in the
same album this data is stored in its own table. The table contains all albums found in
the collection.

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


djmdArtist
~~~~~~~~~~

This table stores the Artist data of Rekordbox. Since multiple tracks can be made by
the same artist this data is stored in its own table. The table contains all artists
found in the collection.

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



djmdCategory
~~~~~~~~~~~~

This table stores the Category data of Rekordbox.

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


djmdCloudProperty
~~~~~~~~~~~~~~~~~

This table contains no data and consists of reserved columns.



djmdColor
~~~~~~~~~

This table stores the Color data of Rekordbox. The table contains all colors used by
Rekordbox and for tagging tracks:

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


djmdContent
~~~~~~~~~~~

This table stores the main track data of Rekordbox. The table contains most information
about each track in the collection. Some columns are linked to other tables by the
corresponding ID.

.. list-table:: djmdContent columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `ID`
     - The ID of the content
     - referenced as `ContentID` in other tables
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
     - mp3= `0` / `1` , m4a= `4` , wav= `11` , aiff= `12`
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
     - The master-ID of the track
     - Not sure whats the difference to `ID`
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
     - Guessing not analyzed= `0` , standard= `105` , advanced= `121`
   * - `ReleaseDate`
     - Date of track release
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - `DateCreated`
     - Date of file creation
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - `ContentLink`
     - ?
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
     - ?
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


djmdCue
~~~~~~~

This table stores the cue points (memory and hotcues) of the tracks in Rekordbox.


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
     -
   * - `InMpegFrame`
     - The Mpeg frame number of the start time
     - `0` if not a mpeg file
   * - `InMpegAbs`
     - ?
     - `0` if not a mpeg file
   * - `OutMsec`
     - End time of the cue point (for loops)
     - Unit: Millisecond, `-1` if not a loop
   * - `OutFrame`
     - The frame number of the end time (for loops)
     - `0` if not a loop
   * - `OutMpegFrame`
     - The Mpeg frame number of the end time (for loops)
     - `0` if not a loop or mpeg file
   * - `OutMpegAbs`
     - ?
     - `0` if not a loop or mpeg file
   * - `Kind`
     - Type of cue point
     - Cue= `0` , Fade-In= `0` , Fade-Out= `0` , Load= `3` , Loop= `4`
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
   * - `ContentUUID`
     - The UUID of the track
     - Links to `UUID` in `djmdContent` table


References
----------

.. [ref6] Technical inspection of Rekordbox 6 and its new internals.  Christiaan Maks. 2020.
   https://rekord.cloud/blog/technical-inspection-of-rekordbox-6-and-its-new-internals.
