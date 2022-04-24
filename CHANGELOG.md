# What's New

<a name="0.0.3"></a>
## [0.0.3] - 2022-24-04

### New Features
- add get-methods for `master.db` database tables

### Improvements/Bug Fixes
- fix table name in `get_artist`
- fix typo in settingFile table name

### Documentation
- switch back to rtd theme since furo code blocks don't render properly
- use furo sphinx theme
- add quick-start
- add installation section
- add tutorial sections
- rename file-format headers
- add development section


<a name="0.0.2"></a>
## [0.0.2] - 2022-20-04
### New Features
- use SQLAlchemy for the  Rekordbox6 `master.db` database

### Improvements/Bug Fixes
- fix import error and README.md
- set logging level to warning
- fix loading the Rekordbox setting file twice in config initialization
- add context for Rekordbox 6 database
- inherit AnlzFile from Mapping to implement dict interface
- unify binary file API

### Documentation
- add missing djmd tables to `master.db` database documentation


<a name="0.0.1"></a>
## [0.0.1] - 2022-10-04
### Improvements/Bug Fixes
- fix Python version


<a name="0.0.0"></a>
## 0.0.0 - 2022-10-04

[0.0.3]: https://github.com/dylanljones/pyrekordbox/compare/0.0.2...0.0.3
[0.0.2]: https://github.com/dylanljones/pyrekordbox/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/dylanljones/pyrekordbox/compare/0.0.0...0.0.1
