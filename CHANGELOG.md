# What's New

<a name="unreleased"></a>
## [Unreleased]

### Improvements/Bug Fixes

- **prevent autoflush in ``autoincrement_local_usn`` in the RBv6 database object**  
- **small improvements of the ``Rekordbox6Database``**  
- **fix bug in ``pformat`` of RBv6 database tables**  

<a name="0.1.3"></a>
## [0.1.3] - 2022-28-10

This release mainly consists of improvements on the Rekordbox v6 database
handling.

### New Features

- **support Python3.11**  
- **add auto-increment of USN's for uncommited changes to the RBv6 database**  
  The new ``autoincrement_usn`` method auto-increments the local USN for each uncommited created, changed or deleted row. The ``rb_local_usn`` attribute of added or changed rows are updated according to the update sequence
- **add session-event callbacks to the RBv6 database object**  
- **add update and transaction tracking to the RBv6 database object**  
  This feature is intended for automatic tracking of the USN's.
- **add local USN handlers to RBv6 database object**  
  Methods added:
  - ``get_local_usn``
  - ``set_local_usn``
  - ``increment_local_usn``
- **add process-id getters**  

### Improvements/Bug Fixes

- **make ``columns`` in the RBv6 table classes a class method** 
- **fix small bug in ``read_rekordbox6_asar``**  
- **fix bugs in RBv6 database object**  

### Documentation

- **add missing My-Setting docstrings**  
- **add missing Rekordbox v6 database docstrings**  
- **add missing XML docstrings**  


<a name="0.1.2"></a>
## [0.1.2] - 2022-19-10

This release contains documentation fixes.

### Documentation

- **fix typos and formatting**  
- **fix light theme styling**  


<a name="0.1.1"></a>
## [0.1.1] - 2022-19-10

### New Features

- **`AnlzFile` now stores the path of the parsed file**  
- **add `update_content_path` and `update_content_filename` to RB6 database**  
  These methods update the file path in the entire Rekordbox collection (database and ANLZ files)

### Improvements/Bug Fixes

- **fix bugs in PQTZ/PQT2 tag handler of ANLZ files**  
- **improve ANLZ file path handling**  
- **fix bug when reading the pyrekordbox config files**  
- **remove wrong type hint in ``AbstractAnlzTag``**  
- **Use path instead of extension as key in `read_anlz_files` output**  
  This helps for saving ANLZ files after making changes.

### Documentation

- **update Quick-Start and change reference labels**  
- **add initial version of API Reference**  
- **fix links in ANLZ file documentation**  


<a name="0.1.0"></a>
## [0.1.0] - 2022-16-10

### New Features

- **add `set_content_path` to `Rekordbox6Database` object**  
- **add `set_path` to `AnlzFile` object**  
- **add name properties for linked tables in the ``DjmdContent`` table of the RB6 database**  
  The new properties include:
  - ArtistName
  - AlbumName
  - GenreName
  - RemixerName
  - LabelName
  - OrgArtistName
  - KeyName
  - ColorName
  - ComposerName
- **add relationship for `Content` in the RB6 database tables**  

### Improvements/Bug Fixes

- **return first query result when using ID as argument**  
- **add type annotation to ``read_mysetting_file``**  
- **fix ``items()`` method in MySettings objects**  
- **also try to import ``pysqlcipher3`` on Windows**  

### Documentation

- **add missing ``FolderPath`` in RB6 database documentation**  
- **add MySettings tutorial to documentation**  
- **Add simple XML playlist tutorial**  
- **Add logo to documentation**  
- **Update installation guide for SQLCipher**  


<a name="0.0.8"></a>
## [0.0.8] - 2022-15-10

### New Features

- **add relationships between lists and contents ([#37](https://github.com/dylanljones/pyrekordbox/issues/37))**  
  Affected tables:
  - DjmdHistory
  - DjmdMyTag
  - DjmdPlaylist
  - DjmdRelatedTracks
  - DjmdSampler

### Improvements/Bug Fixes

- **fix incorrect table in `get_related_tracks`**  
- **fix incorrect foreign key in `DjmdHotCueBanklist`**  

### Documentation

- **remove duplicate entry in the Rekordbox v6 database format documentation**  


<a name="0.0.7"></a>
## [0.0.7] - 2022-12-06

### New Features

- **add SQLCipher support for macOS (see [#27](https://github.com/dylanljones/pyrekordbox/issues/27))**  

### Documentation

- **add installation instructions for SQLCipher on macOS**  


<a name="0.0.6"></a>
## [0.0.6] - 2022-27-05

### Improvements/Bug Fixes

- **fix encoding errors on MacOS**  
- **improve ANLZ getters**  


<a name="0.0.5"></a>
## [0.0.5] - 2022-06-05

### Improvements/Bug Fixes

- **improve XML playlist handling and fix refactoring bugs**  
- **raise ValueError if duplicate track is added**  
  Checks for
  - Location
  - TrackID
- **improve XML key errors**  
- **add implementation of crc16xmodem to support Python 3.10 ([#21](https://github.com/dylanljones/pyrekordbox/issues/21))**  


<a name="0.0.4"></a>
## [0.0.4] - 2022-06-05

### New Features

- **add auto-increment of XML TrackID when adding new tracks**  

### Improvements/Bug Fixes

- **fix wrong MySetting default values**  
- **simplify names of playlist (folder) creation methods**  
- **add method to remove tracks in XML database and fix bug in track count update**  
- **fix position argument of XPath in XML file (starts at 1)**  
- **file paths in the XML file are now encoded and decoded as URI's**  
- **fix XML tests with new API**  
- **Improve Rekordbox XML handling and API**  
  The attributes of track can now be accessed with a dict interface. Additionally, the object attributes now correspond to the keys in the XML file


<a name="0.0.3"></a>
## [0.0.3] - 2022-24-04

### New Features

- **add get-methods for `master.db` database tables**  

### Improvements/Bug Fixes

- **fix table name in `get_artist`**  
- **fix typo in settingFile table name**  

### Documentation

- **switch back to rtd theme since furo code blocks don't render properly**  
- **use furo sphinx theme**  
- **add quick-start**  
- **add installation section**  
- **add tutorial sections**  
- **rename file-format headers**  
- **add development section**  
  contains the change-log and contributing information


<a name="0.0.2"></a>
## [0.0.2] - 2022-20-04

### New Features

- **use SQLAlchemy for the  Rekordbox6 `master.db` database**  

### Improvements/Bug Fixes

- **fix import error and README.md**  
- **set logging level to warning**  
- **fix loading the Rekordbox setting file twice in config initialization**  
- **add context for Rekordbox 6 database**  
- **inherit AnlzFile from Mapping to implement dict interface**  
- **unify binary file API**  
  The Settings files now also use the `parse` and `parse_file` class-methods

### Documentation

- **add missing djmd tables to `master.db` database documentation**


<a name="0.0.1"></a>
## [0.0.1] - 2022-10-04

### Improvements/Bug Fixes

- **fix Python version**  


<a name="0.0.0"></a>
## 0.0.0 - 2022-10-04



[Unreleased]: https://github.com/dylanljones/pyrekordbox/compare/0.1.3...HEAD
[0.1.3]: https://github.com/dylanljones/pyrekordbox/compare/0.1.2...0.1.3
[0.1.2]: https://github.com/dylanljones/pyrekordbox/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/dylanljones/pyrekordbox/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/dylanljones/pyrekordbox/compare/0.0.8...0.1.0
[0.0.8]: https://github.com/dylanljones/pyrekordbox/compare/0.0.7...0.0.8
[0.0.7]: https://github.com/dylanljones/pyrekordbox/compare/0.0.6...0.0.7
[0.0.6]: https://github.com/dylanljones/pyrekordbox/compare/0.0.5...0.0.6
[0.0.5]: https://github.com/dylanljones/pyrekordbox/compare/0.0.4...0.0.5
[0.0.4]: https://github.com/dylanljones/pyrekordbox/compare/0.0.3...0.0.4
[0.0.3]: https://github.com/dylanljones/pyrekordbox/compare/0.0.2...0.0.3
[0.0.2]: https://github.com/dylanljones/pyrekordbox/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/dylanljones/pyrekordbox/compare/0.0.0...0.0.1
