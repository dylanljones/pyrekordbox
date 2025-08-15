# Rekordbox 6 Database

Pyrekordbox uses [SQLALchemy](https://www.sqlalchemy.org/) as ORM-Framework to handle the
Rekordbox database file (``master.db``). The table declarations can be found in
``pyrekordbox.db6.tables``.

```{seealso}
See the {ref}`Rekordbox 6 Database Format <Rekordbox 6 Database Format>` documentation for more information.
```

Since the Rekordbox database handler automatically finds the ``master.db`` database file
(see configuration), it can be initialized without any arguments:
````python
from pyrekordbox import Rekordbox6Database

db = Rekordbox6Database()
````

## Querying the database

A query can be executed on any table by calling the ``query()`` method. The result is
a SQLAlchemy query object, which can be used to filter and sort the results.
````python
from pyrekordbox.db6 import tables

query = db.query(tables.DjmdContent)
results = query.filter(tables.DjmdContent.Title == "My Song").all()
````

To simplify querying the database, the ``Rekordbox6Database`` class provides simple
getters for executing queries on all the tables. The parameters of the getters are
passed to the ``query.filter_by()`` method. If the query is filtered by a *unique* key
(e.g. ``ID``), the query will be executed using the ``query.one()`` method, returning the
table instance directly:
````python
# Return specific entry in DjmDContent table
content = db.get_content(ID=0)
````

In all other cases the query is returned, allowing to further filter and sort the results:
````python
# Query and sort entries in DjmdHistory table
for history in db.get_history().order_by(tables.DjmdHistory.DateCreated):
    print(history)
````

This allows the user to make use of the full power of SQLAlchemy queries.

### Relationships

Some values of table entries are linked to other tables and can not be updated
directly. For example, the [djmdContent table][djmdContent-table] contains an
``ArtistID`` column, which links to the [djmdArtist table][djmdArtist-table].
The table declarations provide relationships to access the linked values.
The artist of a song can be accessed as follows:
````python
content = db.get_content(ID=0)
artist = content.Artist
````
A full list of linked tables can be found in the [](db6-format) documentation.


## Updating the database

Many values in the Rekordbox database can be updated by simply changing the corresponding
attribute of the table instance and calling the ``db.commit()`` method:
````python
content = db.get_content().first()
content.Title = "New title"
db.commit()
````

Since some values of table entries are linked to other tables these values can not
be updated directly. Also, many values depend on other values on the table and have to
be updated accordingly to ensure consistency of the database, for example the ``TrackNo``
of songs in playlists.

To simplify updating the database, the ``Rekordbox6Database`` class provides a set of
high level methods for updating the database. These methods take care of updating all
linked values and metadata.

### Playlists

A new playlist can be created by calling the ``db.create_playlist()`` method:
````python
playlist = db.create_playlist("My Playlist")
````
It creates a new [DjmdPlaylist] instance and adds it to the [djmdPlaylist table][djmdPlaylist-table].
By default, the playlist is inserted as last element of the parent playlist folder.
Alternatively, the sequence number of the new playlist can be specified:
````python
playlist = db.create_playlist("My Playlist", seq=2)
````
To add the playlist to a specific playlist folder, the ``parent`` parameter can be used
to pass a playlist folder instance or ID:
````python
folder = db.get_playlist(Name="My Folder").one()  # Query for unique playlist folder
playlist = db.create_playlist("My Playlist", parent=folder)
````

Playlist folders can also be created , which are also stored in the [djmdPlaylist table][djmdPlaylist-table].
The method accepts the same parameters as the ``db.create_playlist()`` method:
````python
folder = db.create_playlist_folder("My Folder")
````

Playlists and playlist folders can also be deleted:
````python
playlist = db.get_playlist(Name="My Playlist").one()
db.delete_playlist(playlist)

folder = db.get_playlist(Name="My Folder").one()
db.delete_playlist(folder)
````

```{caution}
When deleting a playlist or playlist folder, all children are deleted as well.
Deleting a playlist removes all songs from the playlist before deleting it. Similarly,
deleting a playlist folder removes all playlists and playlist folders in the folder,
including all songs in the sub-playlists.
```

Adding tracks to a playlist is done by calling the ``db.add_to_playlist()`` method.
It accepts a [DjmdContent] instance or corresponding ID and creates a new entry in
the [djmdSongPlaylist table][djmdSongPlaylist-table], which stores the contents of playlists:
````python
content = db.get_content(ID=0)
playlist = db.get_playlist(Name="My Playlist").one()
song = db.add_to_playlist(playlist, content)
````

To delete a song from a playlist, the [DjmdSongPlaylist] instance or ID has to be passed,
since a track can be contained in a plalyist more than once:
````python
playlist = db.get_playlist(Name="My Playlist").one()
song = playlist.Songs[0]

db.remove_from_playlist(playlist, song)
````

### Tracks

New tracks can be added to your rekordbox collection by calling the `db.add_content()` method:

```python
track = db.add_content("/Users/deadmau5/Downloads/Banger.mp3")
```

This creates a new [DjmdContent] instance and adds it to the [djmdContent-table]. This
track will appear in your rekordbox collection, but the track metadata (title, artist,
etc.) will be blank. To load this data, simply right click the track and select the
`Reload Tag` menu option. rekordbox will correctly populate the metadata, including
creating any related table data for things like artist and album.

The `db.add_content()` method accepts `**kwargs` which are passed on to the [DjmdContent]
instance. You can use these keyword arguments if you want to populate some of the track
metadata right away. However, things like [DjmdArtist] and [DjmdAlbum] are foreign keys to
other tables, so make sure you create these objects first and pass the objects via kwargs,
rather than passing plain strings. A plain string will work for `Title`, however.

```python
db.add_content("/Users/deadmau5/Downloads/Banger.mp3", Title="Banger")
```

Populating the [DjmdContent] metadata directly from the track file is not currently
supported, but it will hopefully be included in a future release.


```{note}
More coming soon!
```



[db-format]: #db6-format
[djmdArtist-table]: #djmdArtist
[DjmdArtist]: pyrekordbox.db6.tables.DjmdArtist
[djmdContent-table]: #djmdContent
[DjmdContent]: pyrekordbox.db6.tables.DjmdContent
[djmdPlaylist-table]: #djmdPlaylist
[DjmdPlaylist]: pyrekordbox.db6.tables.DjmdPlaylist
[djmdSongPlaylist-table]: #djmdSongPlaylist
[DjmdSongPlaylist]: pyrekordbox.db6.tables.DjmdSongPlaylist
