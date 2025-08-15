<!--
pyrekordbox documentation master file, created by
sphinx-quickstart on Thu Apr  7 15:06:50 2022.
-->

# Pyrekordbox documentation

[![Tests][tests-badge]][tests-link]
[![Codecov][codecov-badge]][codecov-link]
[![Version][pypi-badge]][pypi-link]
[![Python][python-badge+]][pypi-link]
[![Platform][platform-badge]][pypi-link]
[![license: MIT][license-badge]][license-link]

```{admonition} Disclaimer
This project is not affiliated with Pioneer Corp. or its related companies
in any way or form and has been written independently! Pyrekordbox is licensed
under the [MIT license][license-link].
The maintainers of the project are not liable for any damages to your Rekordbox library.
```

Pyrekordbox is a Python package for interacting with the library and export data of
Pioneer's Rekordbox DJ Software. It currently supports

- Rekordbox 6 `master.db` database
- Rekordbox XML database
- Analysis files (ANLZ)
- My-Settings files

Tested Rekordbox versions: `5.8.6 | 6.5.3 | 6.7.7`

```{warning}
This project is still under development and might contain bugs or
have breaking API changes in the future.
```

## Contents

```{toctree}
---
maxdepth: 2
caption: User Guide
---

quickstart
installation
tutorial/index
api
```

```{toctree}
---
maxdepth: 2
caption: File formats
---

formats/db6
formats/xml
formats/anlz
formats/mysetting
```

```{toctree}
---
maxdepth: 1
caption: Development
---

development/contributing
development/changes
```

```{toctree}
---
hidden:
caption: Project Links
---

GitHub <https://github.com/dylanljones/pyrekordbox>
PyPI <https://pypi.org/project/pyrekordbox/>
```

# Indices and tables

- {ref}`genindex`
- {ref}`search`


[tests-badge]: https://img.shields.io/github/actions/workflow/status/dylanljones/pyrekordbox/tests.yml?branch=master&label=tests&logo=github&style=flat
[codecov-badge]: https://codecov.io/gh/dylanljones/pyrekordbox/branch/master/graph/badge.svg?token=5Z2KVGL7N3
[python-badge]: https://img.shields.io/pypi/pyversions/pyrekordbox?style=flat
[python-badge+]: https://img.shields.io/badge/python-3.8+-blue.svg
[platform-badge]: https://img.shields.io/badge/platform-win%20%7C%20osx-blue?style=flat
[pypi-badge]: https://img.shields.io/pypi/v/pyrekordbox?style=flat
[license-badge]: https://img.shields.io/pypi/l/pyrekordbox?color=lightgrey

[pypi-link]: https://pypi.org/project/pyrekordbox/
[license-link]: https://github.com/dylanljones/pyrekordbox/blob/master/LICENSE
[tests-link]: https://github.com/dylanljones/pyrekordbox/actions/workflows/tests.yml
[codecov-link]: https://app.codecov.io/gh/dylanljones/pyrekordbox/tree/master

[issue]: https://github.com/dylanljones/pyrekordbox/issues/64
