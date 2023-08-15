# Installation

Pyrekordbox is available on [PyPI]:

```sh
$ pip install pyrekordbox
```

Alternatively, it can be installed via [GitHub]:

```shell
$ pip install git+https://github.com/dylanljones/pyrekordbox.git@VERSION
```

where `VERSION` is a branch, tag or release. The project can also be cloned/forked
and installed via

```shell
$ python setup.py install
```

## Installing SQLCipher

Unlocking the new Rekordbox 6 `master.db` database file requires [SQLCipher][sqlcipher].

### Windows

#### Building SQLCipher and installing pysqlcipher3 (recommended)


1. **Install [Visual Studio Community Edition][VS]**

   Make sure to select all the GCC options (VC++, C++, etc) in the installation process.


2. **Install a prebuilt [OpenSSL binary][OpenSSL]**

   Choose the latest Win32/Win64 version.


3. **Confirm that the `OPENSSL_CONF` environment variable is set properly in environment variables**

   This should not be root openssl path (ex: `C:/Program Files/openssl-Win64`),
   but instead should be the path to the config file, for example:
   - 32-bit: ``C:/Program Files (x86)/openssl-Win32/bin/openssl.cfg``
   - 64-bit: ``C:/Program Files/openssl-Win64/bin/openssl.cfg``


4. **Copy the openssl folder to the VC include directory (ex: `C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include`)**

   The openssl folder is
   - 32-bit: `C:/Program Files (x86)/OpenSSL-Win32/include/openssl`
   - 64-bit: `C:/Program Files/OpenSSL-Win64/include/openssl`

   Confirm the following path exists `../../VC/include/openssl/aes.h`


5. **Download / compile the SQLCipher 3 amalgamation files**

   Pre-built SQLCipher 3 amalgamation files can be downloaded from [this repo](https://github.com/geekbrother/sqlcipher-amalgamation).
   To compile the amalgamation files, follow [this tutorial](http://www.jerryrw.com/howtocompile.php).


6. **Clone [pysqlcipher3] into any directory**

   ````shell
   git clone https://github.com/rigglemania/pysqlcipher3
   ````


7. **Create directory ``...\pysqlcipher3\amalgamation``**

   Copy files ``sqlite3.c`` and ``sqlite3.h`` from the amalgamation directory from step 5 to the new `amalgamation` directory.


8. **Create directory ``...\pysqlcipher3\src\python3\sqlcipher``**

   Copy files ``sqlite3.c``, ``sqlite3.h`` and ``sqlite3ext.h`` from the amalgamation directory from step 5 to the new `sqlcipher` directory.


9. **Modify the ``...\pysqlcipher3\setup.py`` script (optional, see [this](https://stackoverflow.com/questions/65345077/unable-to-build-sqlcipher3-on-windows) discussion)**

   If building the amalgamation fails, modify the ``setup.py`` script:
   - Change
      ````python
      def quote_argument(arg):
          quote = '"' if sys.platform != 'win32' else '\\"'
          return quote + arg + quote
      ````
      to
      ````python
      def quote_argument(arg):
          quote = '"'
          return quote + arg + quote
      ````

   - The library names of OpenSSL have changed in version 1.1.0. If you are using a newer version, you might have to change the library name from
     ````python
     ext.extra_link_args.append("libeay32.lib")
     ````
     to
     ````python
     ext.extra_link_args.append("<NAME>")
     ````
     where ``<NAME>`` is something like ``libcrypto.lib`` (depending on your version).


10. **Build using the amalgamation**

    ``cd`` into the ``pysqlcipher3`` directory and run
    ````shell
    python setup.py build_amalgamation
    ````


11. **Install ``pysqlcipher3``**

    In the same directory, run
    ````shell
    python setup.py install
    ````

You now should have a working ``pysqlcipher3`` installation! The directory of the
cloned ``pysqlcipher3`` repo can be deleted after installing the package.

Steps 5-11 can be automated using the CLI of ``pyrekordbox``:
````shell
````commandline
> python3 -m pyrekordbox install-sqlcipher --help
usage: pyrekordbox install-sqlcipher [-h] [-t TMPDIR] [-l CRYPTOLIB] [-q] [-b]

  -h, --help            show this help message and exit
  -t TMPDIR, --tmpdir TMPDIR
                        Path for storing temporary data (default: '.tmp')
  -l CRYPTOLIB, --cryptolib CRYPTOLIB
  -q, --fixquote        Don't fix the quotes in the pysqlcipher3 setup.py script
  -b, --buildonly       Don't install pysqlcipher3, only build the amalgamation
````

After the installation SQLCipher-databases can be unlocked via the `pysqlcipher3` package:
````python
from pysqlcipher3 import dbapi2 as sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute("PRAGMA key='password'")
````


#### Pre-built SQLCipher DLL's (not recommended)

Alternatively, pyrekordbox includes Python SQLite DLL's (see [this](https://stackoverflow.com/questions/58964763/using-sqlcipher-in-python-the-easy-way)
StackOverflow discussion), which can be used to open databases encrpyted by SQLCipher.
The DLL's can be found in the ``Libs/sqlcipher_py38`` directory of the pyrekordbox package.
To patch the sqlite3 installation, follow these steps:


- **Replace ``sqlite3.dll`` in the Python DLL directory**

  Rename the ``sqlcipher.dll`` file in the ``Libs/sqlcipher_py38`` directory to
  ``sqlite3.dll`` and replace the existing DLL file in the Python DLL folder with it.

   ```{tip}
   Before replacing the original file, back up ``sqlite3.dll`` in the Python DLL
   directory by renaming it to something like ``sqlite3_backup.dll``.
   ```
- **Optional: Copy `libcrypto-1_1.dll` into the Python DLL directory**

- **Optional: Copy `libssl-1_1.dll` into the Python DLL directory**

The last two steps are only required if the first step is not sufficient.

After replacing the DLL files SQLCipher-databases can be unlocked via the normal `sqlite3` package:
````python
import sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute("PRAGMA key='password'")
````

```{attention}
The included DLL's only work with *Python 3.8 (32 bit)*! For other Python versions
(specificly the version of the included SQLite3 libary) the DLL's have to be built
from source.
```

### MacOS

For MacOS follow these steps:

1) Install [Homebrew](https://brew.sh) if you do not have it on your machine.
2) Install SQLCipher with `brew install SQLCipher`.
3) With the python environment you are using to run pyrekordbox active execute the following:
```shell
git clone https://github.com/rigglemania/pysqlcipher3
cd pysqlcipher3
C_INCLUDE_PATH=/opt/homebrew/Cellar/sqlcipher/4.5.1/include LIBRARY_PATH=/opt/homebrew/Cellar/sqlcipher/4.5.1/lib python setup.py build
C_INCLUDE_PATH=/opt/homebrew/Cellar/sqlcipher/4.5.1/include LIBRARY_PATH=/opt/homebrew/Cellar/sqlcipher/4.5.1/lib python setup.py install
```
Make sure the `C_INCLUDE` and `LIBRARY_PATH` point to the installed SQLCipher path. It may differ on your machine.


### References

- [Sqlcipher](https://www.zetetic.net/sqlcipher/open-source/)
- [https://stackoverflow.com/questions/33618565/how-to-build-sql-cipher-python-binding-for-windows](https://stackoverflow.com/questions/33618565/how-to-build-sql-cipher-python-binding-for-windows)
- [https://github.com/Monogi/pysqlcipher3_install_win10](https://github.com/Monogi/pysqlcipher3_install_win10)



[VS]: https://visualstudio.microsoft.com/de/vs/community/
[OpenSSL]: https://slproweb.com/products/Win32OpenSSL.html
[pysqlcipher3]: https://github.com/rigglemania/pysqlcipher3
[Pypi]: https://pypi.org/project/pyrekordbox/
[GitHub]: https://github.com/dylanljones/pyrekordbox
[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
