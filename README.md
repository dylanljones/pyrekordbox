
# pyrekordbox

[![Tests][tests-badge]][tests-link]
[![Docs][docs-badge]][documentation]
[![Version][pypi-badge]][pypi-link]
[![Python][python-badge]][pypi-link]
[![Platform][platform-badge]][pypi-link]
[![license: MIT][license-badge]][license-link]
[![style: black][black-badge]][black-link]

Pyrekordbox is a Python package for interacting with the library and export data of
Pioneer's Rekordbox DJ Software. It currently supports
- Rekordbox XML database
- Analysis files (ANLZ)
- My-settings files
- Rekordbox 6 `master.db` database

*Note*: This project is **not** affiliated with Pioneer Corp. or its related companies
in any way and has been written independently!

|⚠️|  This project is still under heavy development and might contain bugs or have breaking API changes in the future. |
|----|:------------------------------------------------------------------------------------------------------------------|



## Installation

pyrekordbox is available on [PyPI][pypi-link]:
````commandline
pip install pyrekordbox
````

Alternatively, it can be installed via [GitHub][repo]
```commandline
pip install git+https://github.com/dylanljones/pyrekordbox.git@VERSION
```
where `VERSION` is a release, tag or branch name.
The project can also be cloned/forked and installed via
````commandline
python setup.py install
````

Some features need additional dependencies (see the [Rekordbox 6 database](#rekordbox-6-database) section).



## Usage

[Read the documentation on ReadTheDocs!][documentation]


### Configuration

pyrekordbox looks for installed Rekordbox versions and sets up the configuration
automatically. The configuration can be checked by calling:
````python
from pyrekordbox import show_config

show_config()
````

which, for example, will print
````
Pioneer:
   app_dir =      C:\Users\user\AppData\Roaming\Pioneer
   install_dir =  C:\Program Files\Pioneer
Rekordbox 5:
   app_dir =      C:\Users\user\AppData\Roaming\Pioneer\rekordbox
   db_dir =       C:\Users\user\AppData\Roaming\Pioneer\rekordbox
   db_path =      C:\Users\user\AppData\Roaming\Pioneer\rekordbox\datafile.edb
   install_dir =  C:\Program Files\Pioneer\rekordbox 5.8.6
   version =      5.8.6
````

If for some reason the configuration fails the values can be updated by providing the
paths to the directory where Pioneer applications are installed (`pioneer_install_dir`)
and to the directory where Pioneer stores the application data  (`pioneer_app_dir`)
````python
from pyrekordbox.config import update_config

update_config(pioneer_install_dir, pioneer_app_dir)
````

Alternatively the two paths can be specified in a configuration file under the section
`rekordbox`. Supported configuration files are pyproject.toml, setup.cfg, rekordbox.toml,
rekordbox.cfg and rekordbox.yml.


### Rekordbox XML

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


### Rekordbox ANLZ files

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


### Rekordbox MySettings

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


### Rekordbox 6 database

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
track_items = db.get_content()
cid = track_items[0]["ID"]
artist = db.get_artist_name(content_id=cid)
````
Changing entries of the database is not supported yet since it is not guaranteed that
the database could be corrupted from writing to it. However, this feature will by
added after some testing.


#### Dependencies

Unlocking the new Rekordbox 6 `master.db` database file requires [SQLCipher][sqlcipher].

So far I did not find a reliable dependency for using SQLCipher
with Python on Windows. For now, SQLCipher can be used with the included DLL's by replacing
the Python SQLite DLL's (see [this](https://stackoverflow.com/questions/58964763/using-sqlcipher-in-python-the-easy-way)
StackOverflow discussion):

1) rename `sqlcipher.dll` to `sqlite3.dll` and replace the existing file in the Python DLLs folder with it
2) copy `libcrypto-1_1.dll` into the Python DLLs folder (optional, should work without)
3) copy `libssl-1_1.dll` into the Python DLLs folder (optional, should work without)

After that SQLCipher-databases can be unlocked via the normal `sqlite3` package by
providing the key via the `PRAGMA key='db-key'` SQL statement.

| ❗  | The included DLL's only work with *Python 3.8*! For other platforms and Python versions (specificly the version of the included SQLite3 libary) the DLL's have to be built from source. |
|----|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|


## File formats

A summary of the Rekordbox file formats can be cound in the [documentation]:

- [Rekordbox XML format][xml-doc]
- [ANLZ file format][anlz-doc]
- [MySetting file format][mysettings-doc]
- [Rekordbox 6 database][db6-doc]



## Contributing

If you encounter an issue or want to contribute to pyrekordbox, please feel free to get in touch,
open an issue or open a pull request!

pyrekordbox is tested on Windows and MacOS, however some features can't be tested in
the CI setup since it requires a working Rekordbox installation. The auto-configuration
(discovering Rekordbox file locations) is tested on Windows, but help would be
appreciated on MacOS.

### To Do

- [ ] Complete ANLZ file support
     - PCOB
     - PCO2
     - PSSI
     - PWV6
     - PWV7
     - PWVC
- [ ] ANLZ tests
- [ ] Improve Rekordbox 6 `master.db` database parsing
- [ ] Rekordbox 6 `master.db` database tests
- [ ] Add Rekordbox 5 `.edb` database suppport
- [ ] Add USB export database support (`.pdb`)
- [x] Add MySettings support
- [x] MySetting tests



## Related Projects

- [crate-digger]: Java library for fetching and parsing rekordbox exports and track analysis files.
- [rekordcrate]: Library for parsing Pioneer Rekordbox device exports
- [supbox]: Get the currently playing track from Rekordbox v6 as Audio Hijack Shoutcast/Icecast metadata, display in your OBS video broadcast or export as JSON.



## Thank Yous

- Deep Symmetry has an extensive analysis of Rekordbox's ANLZ and .edb export file formats
  https://djl-analysis.deepsymmetry.org/djl-analysis
- rekordcrate reverse engineered the format of the Rekordbox MySetting files
  https://holzhaus.github.io/rekordcrate/rekordcrate/setting/index.html
- rekordcloud went into detail about the internals of Rekordbox 6
  https://rekord.cloud/blog/technical-inspection-of-rekordbox-6-and-its-new-internals.
- supbox has a nice implementation on finding the Rekordbox 6 database key
  https://github.com/gabek/supbox


[tests-badge]: https://img.shields.io/github/workflow/status/dylanljones/pyrekordbox/Test/master?label=test&logo=github&style=flat
[docs-badge]: https://img.shields.io/readthedocs/pyrekordbox/latest?style=flat
[python-badge]: https://img.shields.io/pypi/pyversions/pyrekordbox?style=flat
[platform-badge]: https://img.shields.io/badge/platform-win%20%7C%20osx-blue?style=flat
[pypi-badge]: https://img.shields.io/pypi/v/pyrekordbox?style=flat
[license-badge]: https://img.shields.io/pypi/l/pyrekordbox?color=lightgrey
[black-badge]: https://img.shields.io/badge/code%20style-black-000000?style=flat
[pypi-link]: https://pypi.org/project/pyrekordbox/
[license-link]: https://github.com/dylanljones/pyrekordbox/blob/master/LICENSE
[tests-link]: https://github.com/dylanljones/pyrekordbox/actions/workflows/tests.yml
[black-link]: https://github.com/psf/black

[documentation]: https://pyrekordbox.readthedocs.io/en/latest/
[db6-doc]: https://pyrekordbox.readthedocs.io/en/latest/formats/db6.html
[anlz-doc]: https://pyrekordbox.readthedocs.io/en/latest/formats/anlz.html
[xml-doc]: https://pyrekordbox.readthedocs.io/en/latest/formats/xml.html
[mysettings-doc]: https://pyrekordbox.readthedocs.io/en/latest/formats/mysetting.html

[repo]: https://github.com/dylanljones/pyrekordbox
[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
[pysqlcipher3]: https://github.com/rigglemania/pysqlcipher3
[deep-symmetry]: https://github.com/Deep-Symmetry
[rekordcrate]: https://github.com/Holzhaus/rekordcrate
[crate-digger]: https://github.com/Deep-Symmetry/crate-digger
[supbox]: https://github.com/gabek/supbox
