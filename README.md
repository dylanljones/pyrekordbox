
<p align="center">
<img src="https://raw.githubusercontent.com/dylanljones/pyrekordbox/master/docs/source/_static/logos/light/logo_primary.svg" alt="logo" height="70"/>
</p>

[![Tests][tests-badge]][tests-link]
[![Codecov][codecov-badge]][codecov-link]
[![Version][pypi-badge]][pypi-link]
[![Python][python-badge+]][pypi-link]
[![Platform][platform-badge]][pypi-link]
[![license: MIT][license-badge]][license-link]
[![style: ruff][ruff-badge]][ruff-link]

> **Disclaimer**: This project is **not** affiliated with Pioneer Corp. or its related companies
in any way and has been written independently! Pyrekordbox is licensed under the
[MIT license][license-link]. The maintainers of the project are not liable for any damages to your Rekordbox library.

Pyrekordbox is a Python package for interacting with the library and export data of
Pioneers Rekordbox DJ Software. It currently supports
- Rekordbox v6 master.db database
- Rekordbox XML database
- Analysis files (ANLZ)
- My-Setting files

Check the [changelog][CHANGELOG] for recent changes!

Tested Rekordbox versions: ``5.8.6 | 6.7.7 | 7.0.9``


## 🔧 Installation

Pyrekordbox is available on [PyPI][pypi-link]:
````commandline
pip install pyrekordbox
````

Alternatively, it can be installed via [GitHub][repo]
```commandline
pip install git+https://github.com/dylanljones/pyrekordbox.git@VERSION
```
where `VERSION` is a release, tag or branch name.

### Dependencies


Unlocking the new Rekordbox 6 `master.db` database file requires [SQLCipher][sqlcipher].
Pyrekordbox tries to install pre-built wheels with included sqlcipher binaries via the [sqlcipher3-wheels] package.
If this fails, it can be installed manually following the [installation guide][installation].


## 🚀 Quick-Start

[Read the full documentation on ReadTheDocs!][documentation]

> [!CAUTION]
> Please make sure to back up your Rekordbox collection before making changes with pyrekordbox
> or developing/testing new features.
> The backup dialog can be found under "File" > "Library" > "Backup Library"


### Configuration

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


### Rekordbox 6/7 database

Rekordbox 6 and 7 use a SQLite database for storing the collection content.
Unfortunatly, the `master.db` SQLite database is encrypted using
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
db.commit()
````

> [!NOTE]
> Some fields are stored as references to other tables, for example the artist of a track.
> Check the [documentation][db6-doc] of the corresponding object for more information.

So far only a few tables support adding or deleting entries:
- ``DjmdContent``: Tracks
- ``DjmdPlaylist``: Playlists/Playlist Folders
- ``DjmdSongPlaylist``: Songs in a playlist
- ``DjmdAlbum``: Albums
- ``DjmdArtist``: Artists
- ``DjmdGenre``: Genres
- ``DjmdLabel``: Labels

### Rekordbox XML

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


### Rekordbox ANLZ files

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

Unsupported ANLZ tags:
  - PWV6
  - PWV7
  - PWVC


### Rekordbox My-Settings

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

The `DEVSETTING.DAT` file is still not supported


## 💡 File formats

A summary of the Rekordbox file formats can be found in the [documentation]:

- [Rekordbox XML format][xml-doc]
- [ANLZ file format][anlz-doc]
- [My-Setting file format][mysettings-doc]
- [Rekordbox 6 database][db6-doc]



## 💻 Development

If you encounter an issue or want to contribute to pyrekordbox, please feel free to get in touch,
[open an issue][new-issue] or create a new pull request! A guide for contributing to
`pyrekordbox` and the commit-message style can be found in
[CONTRIBUTING].

For general questions or discussions about Rekordbox, please use [GitHub Discussions][discussions]
instead of opening an issue.

Pyrekordbox is tested on Windows and MacOS, however some features can't be tested in
the CI setup since it requires a working Rekordbox installation.

## ♡ Sponsor

If pyrekordbox has helped you or saved you time, consider supporting its development - every coffee makes a difference!

[![BuyMeACoffee](https://raw.githubusercontent.com/pachadotdev/buymeacoffee-badges/main/bmc-white.svg)](https://www.buymeacoffee.com/dylanljones)


## 🔗 Related Projects and References

- [crate-digger]: Java library for fetching and parsing rekordbox exports and track analysis files.
- [rekordcrate]: Library for parsing Pioneer Rekordbox device exports
- [supbox]: Get the currently playing track from Rekordbox v6 as Audio Hijack Shoutcast/Icecast metadata, display in your OBS video broadcast or export as JSON.
- [Deep Symmetry] has an extensive analysis of Rekordbox's ANLZ and .edb export file formats
  https://djl-analysis.deepsymmetry.org/djl-analysis


[tests-badge]: https://img.shields.io/github/actions/workflow/status/dylanljones/pyrekordbox/tests.yml?branch=master&label=tests&logo=github&style=flat
[docs-badge]: https://img.shields.io/readthedocs/pyrekordbox/stable?style=flat
[python-badge]: https://img.shields.io/pypi/pyversions/pyrekordbox?style=flat
[python-badge+]: https://img.shields.io/badge/python-3.8+-blue.svg
[platform-badge]: https://img.shields.io/badge/platform-win%20%7C%20osx-blue?style=flat
[pypi-badge]: https://img.shields.io/pypi/v/pyrekordbox?style=flat
[license-badge]: https://img.shields.io/pypi/l/pyrekordbox?color=lightgrey
[black-badge]: https://img.shields.io/badge/code%20style-black-000000?style=flat
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[codecov-badge]: https://codecov.io/gh/dylanljones/pyrekordbox/branch/master/graph/badge.svg?token=5Z2KVGL7N3


[pypi-link]: https://pypi.org/project/pyrekordbox/
[license-link]: https://github.com/dylanljones/pyrekordbox/blob/master/LICENSE
[tests-link]: https://github.com/dylanljones/pyrekordbox/actions/workflows/tests.yml
[black-link]: https://github.com/psf/black
[ruff-link]: https://github.com/astral-sh/ruff
[lgtm-link]: https://lgtm.com/projects/g/dylanljones/pyrekordbox/context:python
[codecov-link]: https://app.codecov.io/gh/dylanljones/pyrekordbox/tree/master
[codecov-dev-link]: https://app.codecov.io/gh/dylanljones/pyrekordbox/tree/dev
[docs-latest-badge]: https://img.shields.io/readthedocs/pyrekordbox/latest?logo=readthedocs&style=flat
[docs-dev-badge]: https://img.shields.io/readthedocs/pyrekordbox/dev?logo=readthedocs&style=flat

[documentation]: https://pyrekordbox.readthedocs.io/en/stable/
[documentation-latest]: https://pyrekordbox.readthedocs.io/en/latest/
[documentation-dev]: https://pyrekordbox.readthedocs.io/en/dev/
[tutorial]: https://pyrekordbox.readthedocs.io/en/stable/tutorial/index.html
[db6-doc]: https://pyrekordbox.readthedocs.io/en/stable/formats/db6.html
[anlz-doc]: https://pyrekordbox.readthedocs.io/en/stable/formats/anlz.html
[xml-doc]: https://pyrekordbox.readthedocs.io/en/stable/formats/xml.html
[mysettings-doc]: https://pyrekordbox.readthedocs.io/en/stable/formats/mysetting.html

[new-issue]: https://github.com/dylanljones/pyrekordbox/issues/new/choose
[discussions]: https://github.com/dylanljones/pyrekordbox/discussions
[CONTRIBUTING]: https://github.com/dylanljones/pyrekordbox/blob/master/CONTRIBUTING.md
[CHANGELOG]: https://github.com/dylanljones/pyrekordbox/blob/master/CHANGELOG.md
[installation]: https://pyrekordbox.readthedocs.io/en/latest/installation.html

[repo]: https://github.com/dylanljones/pyrekordbox
[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
[sqlcipher3-wheels]: https://github.com/laggykiller/sqlcipher3
[rekordcrate]: https://github.com/Holzhaus/rekordcrate
[crate-digger]: https://github.com/Deep-Symmetry/crate-digger
[supbox]: https://github.com/gabek/supbox
[Deep Symmetry]: https://deepsymmetry.org/
