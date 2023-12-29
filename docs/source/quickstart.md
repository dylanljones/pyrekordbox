# Quick-Start


Pyrekordbox can be installed via:
````shell
$ pip install pyrekordbox
````

See the {doc}`Installation</installation>` section for more details.

```{attention}
Please make sure to back up your Rekordbox collection before making
any changes with pyrekordbox or developing/testing new features.

The backup dialog can be found under "File" > "Library" > "Backup Library"
```


## Configuration

Pyrekordbox looks for installed Rekordbox versions and sets up the configuration
automatically. The configuration can be checked by calling:
````python
from pyrekordbox import show_config

show_config()
````
If for some reason the configuration fails the values can be updated by providing the
paths to the directory where Pioneer applications are installed (`pioneer_install_dir`)
and to the directory where Pioneer stores the application data  (`pioneer_app_dir`)
````python
from pyrekordbox.config import update_config

update_config("<pioneer_install_dir>", "<pioneer_app_dir>")
````
Alternatively the two paths can be specified in a configuration file under the section
`rekordbox`. Supported configuration files are pyproject.toml, setup.cfg, pyrekordbox.toml,
pyrekordbox.cfg and pyrekordbox.yaml.


## Rekordbox 6 database

Rekordbox 6 now uses a SQLite database for storing the collection content.
Unfortunatly, the new `master.db` SQLite database is encrypted using
[SQLCipher][sqlcipher], which means it can't be used without the encryption key.
However, since your data is stored and used locally, the key must be present on the
machine running Rekordbox.

Pyrekordbox can unlock the new Rekordbox `master.db` SQLite database and provides
an easy interface for accessing the data stored in it:

````python
from pyrekordbox import Rekordbox6Database

db = Rekordbox6Database()

for content in db.get_content():
    print(content.Title, content.Artist.Name)

playlist = db.get_playlist()[0]
for song in playlist.Songs:
    content = song.Content
    print(content.Title, content.Artist.Name)
````
Fields in the Rekordbox database that are stored without linking to other tables
can be changed via the corresponding property of the object:
````python
content = db.get_content()[0]
content.Title = "New Title"
````
Some fields are stored as references to other tables, for example the artist of a track.
Check the [documentation](#db6-format) of the corresponding object for more information.
So far only a few tables support adding or deleting entries:
- ``DjmdPlaylist``: Playlists/Playlist Folders
- ``DjmdSongPlaylist``: Songs in a playlist
- ``DjmdAlbum``: Albums
- ``DjmdArtist``: Artists
- ``DjmdGenre``: Genres
- ``DjmdLabel``: Labels

````{important}
Starting from Rekordbox version ``6.6.5`` Pioneer obfuscated the ``app.asar`` file
contents, breaking the key extraction (see [this discussion](https://github.com/dylanljones/pyrekordbox/discussions/97) for more details).
If you are using a later version of Rekorbox and have no cached key from a previous
version, the database can not be unlocked automatically.
The command line interface of ``pyrekordbox`` provides a command for downloading
the key from known sources and writing it to the cache file:
```shell
python -m pyrekordbox download-key
```
Once the key is cached the database can be opened without providing the key.
The key can also be provided manually:
```python
db = Rekordbox6Database(key="<insert key here>")
```
````


## Rekordbox XML

The Rekordbox XML database is used for importing (and exporting) Rekordbox collections
including track metadata and playlists. They can also be used to share playlists
between two databases.

Pyrekordbox can read and write Rekordbox XML databases.

````python
from pyrekordbox.rbxml import RekordboxXml

xml = RekordboxXml("database.xml")

track = xml.get_track(0)    # Get track by index (or TrackID)
track_id = track.TrackID    # Access via attribute
name = track["Name"]        # or dictionary syntax

path = "/path/to/file.mp3"
track = xml.add_track(path) # Add new track
track["Name"] = "Title"     # Add attributes to new track
track["TrackID"] = 10       # Types are handled automatically

# Get playlist (folder) by path
pl = xml.get_playlist("Folder", "Sub Playlist")
keys = pl.get_tracks()  # Get keys of tracks in playlist
ktype = pl.key_type     # Key can either be TrackID or Location

# Add tracks and sub-playlists (folders)
pl.add_track(track.TrackID)
pl.add_playlist("Sub Sub Playlist")
````

## Rekordbox ANLZ files

Rekordbox stores analysis information of the tracks in the collection in specific files,
which also get exported to decives used by Pioneer professional DJ equipment. The files
have names like `ANLZ0000` and come with the extensions `.DAT`, `.EXT` or `.2EX`.
They include waveforms, beat grids (information about the precise time at which
each beat occurs), time indices to allow efficient seeking to specific positions
inside variable bit-rate audio streams, and lists of memory cues and loop points.

Pyrekordbox can parse all three analysis files, although not all the information of
the tracks can be extracted yet.

````python
from pyrekordbox.anlz import AnlzFile

anlz = AnlzFile.parse_file("ANLZ0000.DAT")
beat_grid = anlz.get("beat_grid")
path_tags = anlz.getall_tags("path")
````

Changing and creating the Rekordbox analysis files is planned as well, but for that the
full structure of the analysis files has to be understood.


```{note}
Some ANLZ tags are still unsupported:
  - PCOB
  - PCO2
  - PSSI
  - PWV6
  - PWV7
  - PWVC
```


## Rekordbox My-Settings

Rekordbox stores the user settings in `*SETTING.DAT` files, which get exported to USB
devices. These files are either in the `PIONEER`directory of a USB drive
(device exports), but are also present for on local installations of Rekordbox 6.
The setting files store the settings found on the "DJ System" > "My Settings" page of
the Rekordbox preferences. These include language, LCD brightness, tempo fader range,
crossfader curve and other settings for Pioneer professional DJ equipment.

Pyrekordbox supports both parsing and writing My-Setting files.

````python
from pyrekordbox.mysettings import read_mysetting_file

mysett = read_mysetting_file("MYSETTINGS.DAT")
sync = mysett.get("sync")
quant = mysett.get("quantize")
````

```{note}
The `DEVSETTING.DAT` file is still not supported
```

[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
