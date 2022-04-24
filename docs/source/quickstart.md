Quick-Start
===========

Pyrekordbox can be installed via:
````shell
$ pip install pyrekordbox
````

See the {doc}`Installation</installation>` section for more details.

## Rekordbox XML

The Rekordbox XML database is used for importing (and exporting) Rekordbox collections
including track metadata and playlists. They can also be used to share playlists
between two databases. Exporting XML databases was removed in Rekordbox 6.
*Update*: In newer Rekordbox 6 versions the XML export feature returned!

pyrekordbox can read and write Rekordbox XML databases.

````python
from pyrekordbox.xml import RekordboxXml

xml = RekordboxXml("database.xml")
track = xml.get_track(0)
````


## Rekordbox ANLZ files

Rekordbox stores analysis information of the tracks in the collection in specific files,
which also get exported to decives used by Pioneer professional DJ equipment. The files
have names like `ANLZ0000` and come with the extensions `.DAT`, `.EXT` or `.2EX`.
They include waveforms, beat grids (information about the precise time at which
each beat occurs), time indices to allow efficient seeking to specific positions
inside variable bit-rate audio streams, and lists of memory cues and loop points.

pyrekordbox can parse all three analysis files, although not all the information of
the tracks can be extracted yet.

````python
from pyrekordbox.anlz import AnlzFile

anlz = AnlzFile.parse_file("ANLZ0000.DAT")
beat_grid = anlz.getone("beat_grid")
````

Changing and creating the Rekordbox analysis files is planned as well, but for that the
full structure of the analysis files has to be understood.


## Rekordbox MySettings

Rekordbox stores the user settings in `*SETTING.DAT` files, which get exported to USB
devices. These files are either in the `PIONEER`directory of a USB drive
(device exports), but are also present for on local installations of Rekordbox 6.
The setting files store the settings found on the "DJ System" > "My Settings" page of
the Rekordbox preferences. These include language, LCD brightness, tempo fader range,
crossfader curve and other settings for Pioneer professional DJ equipment.

pyrekordbox supports both parsing and writing MySetting files.

````python
from pyrekordbox.mysettings import read_mysetting_file

mysett = read_mysetting_file("MYSETTINGS.DAT")
sync = mysett.get("sync")
quant = mysett.get("quantize")
````


## Rekordbox 6 database

Rekordbox 6 now uses a SQLite database for storing the collection content. The old
DeviceSQL of Rekordbox 5 was probably too old for Pioneer  to keep using adequately,
especially with the Rekordbox Agent. Unfortunatly, the new `master.db` SQLite database
is encrypted using [SQLCipher][sqlcipher], which means it can't be used without the encryption key.
Pioneer did this because they prefer that no one outside of Pioneer touches it.
However, since your data is stored and used locally, the key must be present on the
machine running Rekordbox.

pyrekordbox can unlock the new Rekordbox `master.db` SQLite database and provides
an easy interface for accessing the data stored in it:

````python
from pyrekordbox import Rekordbox6Database

db = Rekordbox6Database()
for item in db.get_content():
    print(item.Title, item.Artist.Name)
````
Changing entries of the database is not supported yet since it is not guaranteed that
the database could be corrupted from writing to it. However, this feature will by
added after some testing.
