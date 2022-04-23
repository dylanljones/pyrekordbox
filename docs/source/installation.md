# Installation

Pyrekordbox is available on [PyPI]:

```sh
$ pip install pyrekordbox
```

Alternatively, it can be installed via [GitHub]:
```sh
$ pip install git+https://github.com/dylanljones/pyrekordbox.git@VERSION
```

where `VERSION` is a branch, tag or release. The project can also be cloned/forked
and installed via
```sh
$ python setup.py install
```

## Dependencies

Unlocking the new Rekordbox 6 `master.db` database file requires [SQLCipher][sqlcipher].

So far I did not find a reliable dependency for using SQLCipher
with Python on Windows. For now, SQLCipher can be used with the [included DLL's][dlls]
by replacing the Python SQLite DLL's (see [this](https://stackoverflow.com/questions/58964763/using-sqlcipher-in-python-the-easy-way)
StackOverflow discussion):

1) rename `sqlcipher.dll` to `sqlite3.dll` and replace the existing file in the Python DLLs folder with it
2) copy `libcrypto-1_1.dll` into the Python DLLs folder (optional, should work without)
3) copy `libssl-1_1.dll` into the Python DLLs folder (optional, should work without)

After that SQLCipher-databases can be unlocked via the normal `sqlite3` package by
providing the key via the `PRAGMA key='db-key'` SQL statement.

```{attention}
The included DLL's only work with *Python 3.8*! For other platforms and Python versions
(specifically the version of the included SQLite3 libary) the DLL's have to be built
from source.
```

[Pypi]: https://pypi.org/project/pyrekordbox/
[GitHub]: https://github.com/dylanljones/pyrekordbox
[dlls]: https://github.com/dylanljones/pyrekordbox/tree/master/Libs
[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
