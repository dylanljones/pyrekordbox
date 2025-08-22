(devicelib-plus-format)=
# Rekordbox Device Library Plus Format

For newer generation Pioneer DJ devices, Rekordbox exports a new library format to the USB storage
device (or SD card), called ``Device Library Plus``.
As of 2025, this format is only supported by the [OPUS-QUAD], [OMNIS-DUO], and [XDJ-AZ] devices.

Similar to the main database of Rekordbox (``master.db``), the Device Library Plus is a SQLite database
encrypted via the [SQLCipher](https://www.zetetic.net/sqlcipher/) library.
Luckily, it appears that the key of the database is not license or machine dependent and all
Device Libraries are encrypted with the same key.

The database schema is similar to the main Rekordbox database. It contains a selection of tables
from the main database, with similar columns and data types.


## Tables

### album

This table stores the album data of the export library.

```{eval-rst}
.. list-table:: album columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `album_id`
     - ID of the album
     - Primary key
   * - `name`
     - Name of the album
     -
   * - `artist_id
     - The ID of the artist of the album
     - FK to `artist`
   * - `isComplation`
     - Indicates if the album is a compilation
     - Boolean value stored as integer (0 or 1)
   * - `nameForSearch`
     - String used for searching
     -
```

### artist

This table stores the artist data of the export library.

```{eval-rst}
.. list-table:: album columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `artist_id`
     - ID of the artist
     - Primary key
   * - `name`
     - Name of the artist
     -
   * - `nameForSearch`
     - String used for searching
     -
```

### category

This table stores the category data of the export library.

```{eval-rst}
.. list-table:: album columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `category_id`
     - ID of the category
     - Primary key
   * - `menuItem_id`
     - ID of the menu item
     - FK to `menuItem`
   * - `sequenceNo`
     - The sequence number used for sorting
     -
   * - `isVisible`
     - Indicates if the category is visible
     - Boolean value stored as integer (0 or 1)
```

### color

This table stores the color data of the export library.

```{eval-rst}
.. list-table:: color columns
   :widths: 1 1 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `color_id`
     - ID of the color
     - Primary key
   * - `name`
     - Name of the color
     -
```

### content

This table stores the content (track) data of the export library.

```{eval-rst}
.. list-table:: content columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `content_id`
     - ID of the content (track)
     - Primary key
   * - `title`
     - Title of the track
     -
   * - `titleForSearch`
     - Search string for the title
     -
   * - `subtitle`
     - Subtitle of the track
     -
   * - `bpmx100`
     - BPM multiplied by 100
     -
   * - `length`
     - Length in milliseconds
     -
   * - `trackNo`
     - Track number in album
     -
   * - `discNo`
     - Disc number in album
     -
   * - `artist_id_artist`
     - Artist ID
     - FK to `artist`
   * - `artist_id_remixer`
     - Remixer ID
     - FK to `artist`
   * - `artist_id_originalArtist`
     - Original artist ID
     - FK to `artist`
   * - `artist_id_composer`
     - Composer ID
     - FK to `artist`
   * - `artist_id_lyricist`
     - Lyricist ID
     - FK to `artist`
   * - `album_id`
     - Album ID
     - FK to `album`
   * - `genre_id`
     - Genre ID
     - FK to `genre`
   * - `label_id`
     - Label ID
     - FK to `label`
   * - `key_id`
     - Key ID
     - FK to `key`
   * - `color_id`
     - Color ID
     - FK to `color`
   * - `image_id`
     - Image ID
     - FK to `image`
   * - `djComment`
     - DJ comment
     -
   * - `rating`
     - Rating (0-5)
     -
   * - `releaseYear`
     - Release year
     -
   * - `releaseDate`
     - Release date
     -
   * - `dateCreated`
     - Date created
     -
   * - `dateAdded`
     - Date added to library
     -
   * - `path`
     - File path
     -
   * - `fileName`
     - File name
     -
   * - `fileSize`
     - File size in bytes
     -
   * - `fileType`
     - File type
     -
   * - `bitrate`
     - Bitrate in kbps
     -
   * - `bitDepth`
     - Bit depth
     -
   * - `samplingRate`
     - Sampling rate in Hz
     -
   * - `isrc`
     - ISRC code
     -
   * - `isHotCueAutoLoadOn`
     - Hot cue auto load flag
     -
   * - `isKuvoDeliverStatusOn`
     - KUVO deliver status flag
     -
   * - `kuvoDeliveryComment`
     - KUVO delivery comment
     -
   * - `masterDbId`
     - Master DB ID
     -
   * - `masterContentId`
     - Master content ID
     -
   * - `analysisDataFilePath`
     - Analysis file path
     -
   * - `analysedBits`
     - Bits used for analysis
     -
   * - `contentLink`
     - Content linked flag
     -
   * - `hasModified`
     - Modified flag
     -
   * - `cueUpdateCount`
     - Cue update count
     -
   * - `analysisDataUpdateCount`
     - Analysis data update count
     -
   * - `informationUpdateCount`
     - Information update count
     -
```

### cue

This table stores the cue point data.

```{eval-rst}
.. list-table:: cue columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `cue_id`
     - ID of the cue
     - Primary key
   * - `content_id`
     - Content ID
     - FK to `content`
   * - `kind`
     - Kind of cue point
     -
   * - `colorTableIndex`
     - Color table index
     -
   * - `cueComment`
     - Cue comment
     -
   * - `isActiveLoop`
     - Active loop flag
     -
   * - `beatLoopNumerator`
     - Beat loop numerator
     -
   * - `beatLoopDenominator`
     - Beat loop denominator
     -
   * - `inUsec`
     - In point (microseconds)
     -
   * - `outUsec`
     - Out point (microseconds)
     -
   * - `in150FramePerSec`
     - In point (150 fps)
     -
   * - `out150FramePerSec`
     - Out point (150 fps)
     -
   * - `inMpegFrameNumber`
     - In MPEG frame number
     -
   * - `outMpegFrameNumber`
     - Out MPEG frame number
     -
   * - `inMpegAbs`
     - Absolute in MPEG frame
     -
   * - `outMpegAbs`
     - Absolute out MPEG frame
     -
   * - `inDecodingStartFramePosition`
     - In decoding start frame
     -
   * - `outDecodingStartFramePosition`
     - Out decoding start frame
     -
   * - `inFileOffsetInBlock`
     - In file offset in block
     -
   * - `outFileOffsetInBlock`
     - Out file offset in block
     -
   * - `inNumberOfSampleInBlock`
     - In number of samples in block
     -
   * - `outNumberOfSampleInBlock`
     - Out number of samples in block
     -
```

### genre

This table stores the genre data.

```{eval-rst}
.. list-table:: genre columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `genre_id`
     - ID of the genre
     - Primary key
   * - `name`
     - Name of the genre
     -
```

### history

This table stores the history playlist data.

```{eval-rst}
.. list-table:: history columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `history_id`
     - ID of the history entry
     - Primary key
   * - `sequenceNo`
     - Sequence number for sorting
     -
   * - `name`
     - Name of the history entry
     -
   * - `attribute`
     - Attribute of the history playlist
     -
   * - `history_id_parent`
     - Parent history ID
     - FK to `history`
```

### history_content

This table stores the mapping between history playlists and their contents.

```{eval-rst}
.. list-table:: history_content columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `history_id`
     - History playlist ID
     - FK to `history`, part of PK
   * - `content_id`
     - Content ID
     - FK to `content`, part of PK
   * - `sequenceNo`
     - Sequence number for sorting
     -
```

### hotCueBankList

This table stores hot cue bank list data.

```{eval-rst}
.. list-table:: hotCueBankList columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `hotCueBankList_id`
     - ID of the hot cue bank list
     - Primary key
   * - `sequenceNo`
     - Sequence number for sorting
     -
   * - `name`
     - Name of the hot cue bank list
     -
   * - `image_id`
     - Image ID
     - FK to `image`
   * - `attribute`
     - Attribute
     -
   * - `hotCueBankList_id_parent`
     - Parent hot cue bank list ID
     - FK to `hotCueBankList`
```

### hotCueBankList_cue

This table stores the mapping between hot cue bank lists and cues.

```{eval-rst}
.. list-table:: hotCueBankList_cue columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `hotCueBankList_id`
     - Hot cue bank list ID
     - FK to `hotCueBankList`, part of PK
   * - `cue_id`
     - Cue ID
     - FK to `cue`, part of PK
   * - `sequenceNo`
     - Sequence number for sorting
     -
```

### image

This table stores image data.

```{eval-rst}
.. list-table:: image columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `image_id`
     - ID of the image
     - Primary key
   * - `path`
     - Path to the image file
     -
```

### key

This table stores musical key data.

```{eval-rst}
.. list-table:: key columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `key_id`
     - ID of the key
     - Primary key
   * - `name`
     - Name of the key
     -
```

### label

This table stores label data.

```{eval-rst}
.. list-table:: label columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `label_id`
     - ID of the label
     - Primary key
   * - `name`
     - Name of the label
     -
```

### menuItem

This table stores menu item data.

```{eval-rst}
.. list-table:: menuItem columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `menuItem_id`
     - ID of the menu item
     - Primary key
   * - `kind`
     - Kind of menu item
     -
   * - `name`
     - Name of the menu item
     -
```

### myTag

This table stores custom tag data.

```{eval-rst}
.. list-table:: myTag columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `myTag_id`
     - ID of the custom tag
     - Primary key
   * - `sequenceNo`
     - Sequence number for sorting
     -
   * - `name`
     - Name of the custom tag
     -
   * - `attribute`
     - Attribute
     -
   * - `myTag_id_parent`
     - Parent custom tag ID
     - FK to `myTag`
```

### myTag_content

This table stores the mapping between custom tags and contents.

```{eval-rst}
.. list-table:: myTag_content columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `myTag_id`
     - Custom tag ID
     - FK to `myTag`, part of PK
   * - `content_id`
     - Content ID
     - FK to `content`, part of PK
```

### playlist

This table stores playlist data.

```{eval-rst}
.. list-table:: playlist columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `playlist_id`
     - ID of the playlist
     - Primary key
   * - `sequenceNo`
     - Sequence number for sorting
     -
   * - `name`
     - Name of the playlist
     -
   * - `image_id`
     - Image ID
     - FK to `image`
   * - `attribute`
     - Attribute
     -
   * - `playlist_id_parent`
     - Parent playlist ID
     - FK to `playlist`
```

### playlist_content

This table stores the mapping between playlists and contents.

```{eval-rst}
.. list-table:: playlist_content columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `playlist_id`
     - Playlist ID
     - FK to `playlist`, part of PK
   * - `content_id`
     - Content ID
     - FK to `content`, part of PK
   * - `sequenceNo`
     - Sequence number for sorting
     -
```

### property

This table stores device property data.

```{eval-rst}
.. list-table:: property columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `deviceName`
     - Name of the device
     - Primary key
   * - `dbVersion`
     - Database version
     -
   * - `numberOfContents`
     - Number of contents
     -
   * - `createdDate`
     - Date created
     -
   * - `backGroundColorType`
     - Background color type
     -
   * - `myTagMasterDBID`
     - Master DB ID for custom tags
     -
```

### recommendedLike

This table stores recommended like data.

```{eval-rst}
.. list-table:: recommendedLike columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `content_id_1`
     - First content ID
     - FK to `content`, part of PK
   * - `content_id_2`
     - Second content ID
     - FK to `content`, part of PK
   * - `rating`
     - Rating (0-5)
     -
   * - `createdDate`
     - Date created
     -
```

### sort

This table stores sort data for menu items.

```{eval-rst}
.. list-table:: sort columns
   :widths: 1 2 1
   :header-rows: 1

   * - Column Name
     - Description
     - Notes
   * - `sort_id`
     - ID of the sort entry
     - Primary key
   * - `menuItem_id`
     - Menu item ID
     - FK to `menuItem`
   * - `sequenceNo`
     - Sequence number for sorting
     -
   * - `isVisible`
     - Visibility flag
     -
   * - `isSelectedAsSubColumn`
     - Selected as sub-column flag
     -
```

[OPUS-QUAD]: https://www.pioneerdj.com/en/product/all-in-one-system/opus-quad/black/overview/
[OMNIS-DUO]: https://alphatheta.com/en/product/all-in-one-dj-system/omnis-duo/indigo/
[XDJ-AZ]: https://alphatheta.com/en/product/all-in-one-dj-system/xdj-az/black/
