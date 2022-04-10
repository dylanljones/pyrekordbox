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

   * - Table Name
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

   * - Table Name
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

   * - Table Name
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


References
----------

.. [ref6] Technical inspection of Rekordbox 6 and its new internals.  Christiaan Maks. 2020.
   https://rekord.cloud/blog/technical-inspection-of-rekordbox-6-and-its-new-internals.
