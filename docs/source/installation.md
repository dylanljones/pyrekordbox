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
$ pip install .
```


## Installing SQLCipher

Unlocking the new Rekordbox 6 `master.db` database file requires [SQLCipher][sqlcipher].
Pyrekordbox tries to install pre-built wheels with included sqlcipher binaries via the [sqlcipher3-wheels] package.
If this fails, it can be installed manually following the instructions below.

[sqlcipher3] can either be built with the system [SQLCipher][sqlcipher] or built against
a statically linked amalgamation of the SQLite3 source code.

### Windows

#### SQLCipher Amalagamation

The easiest method to install SQLCipher on Windows is to build [sqlcipher3]
against an amalgamation of the SQLite3 source code.

1. **Install [Visual Studio Community Edition][VS]**

   Make sure to select all the GCC options (VC++, C++, etc) in the installation process.
   The following workloads under ``Desktop & Mobile`` should be sufficient:
   - Desktop Development with C++
   - .NET desktop development


2. **Install a prebuilt [OpenSSL binary][OpenSSL]**

   Choose the latest Win32/Win64 version. Make sure to download the full version,
   not the light version.


3. **Confirm that the `OPENSSL_CONF` environment variable is set properly in environment variables**

   This should not be root openssl path (ex: `C:/Program Files/openssl-Win64`),
   but instead should be the path to the config file, for example:
   - 32-bit: ``C:/Program Files (x86)/openssl-Win32/bin/openssl.cfg``
   - 64-bit: ``C:/Program Files/openssl-Win64/bin/openssl.cfg``

   ```{note}
   The library names of OpenSSL have changed in version 1.1.0 (see [this](https://stackoverflow.com/questions/65345077/unable-to-build-sqlcipher3-on-windows) discussion).
   If you are using a newer version, you can set an environment variable
   ``OPENSSL_LIBNAME`` to the name of the library, e.g. ``libcrypto.lib``.
   Alternatively, you can modify the ``setup.py`` script (see step 8 below).

   You might have to restart Windows for the changes to take effect.
   ```

4. **Copy the openssl folder to the Microsoft Visual Studio 14 VC include directory**

   The openssl folder can be found here:
   - 32-bit: `C:/Program Files (x86)/OpenSSL-Win32/include/openssl`
   - 64-bit: `C:/Program Files/OpenSSL-Win64/include/openssl`

   The VC include directory can be found in the
   Visual Studio 14 installation directory:

   > C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include

   In newer versions it might aso be in

   > C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/[version]/include

   Confirm the following path exists `.../include/openssl/aes.h`


5. **Download / compile the SQLCipher 3 amalgamation files**

   Pre-built SQLCipher amalgamation files can be downloaded from [this repo][amalgamation]:
   ````shell
   git clone https://github.com/geekbrother/sqlcipher-amalgamation
   ````
   To compile the amalgamation files on your own, follow [this tutorial](http://www.jerryrw.com/howtocompile.php).


6. **Clone [sqlcipher3] into any directory**

   ````shell
   git clone https://github.com/coleifer/sqlcipher3
   ````


7. **Copy amalgamation files to the `sqlcipher3` directory**

   Copy files ``sqlite3.c`` and ``sqlite3.h`` from the amalgamation directory from step 5
   to the root of the ``sqlcipher3`` directory from step 6.
   ````shell
   Copy-Item -Path 'sqlcipher-amalgamation/src/sqlite3.c' -Destination "sqlcipher3/"
   Copy-Item -Path 'sqlcipher-amalgamation/src/sqlite3.h' -Destination "sqlcipher3/"
   ````


8. **Modify the ``sqlcipher3/setup.py`` script (optional)**

   If building the amalgamation fails and you haven't set the ``OPENSSL_LIBNAME``
   environment variable in step 3, you have to modify the ``setup.py`` script. Change
   ````python
   openssl_libname = os.environ.get('OPENSSL_LIBNAME') or 'libeay32.lib'
   ````
   to
   ````python
   openssl_libname = os.environ.get('OPENSSL_LIBNAME') or 'libcrypto.lib'
   ````


9. **Build using the amalgamation and install**

    ``cd`` into the ``sqlcipher3`` directory and run
    ````shell
    python setup.py build_static build
    python setup.py install
    ````


You now should have a working ``sqlcipher3`` installation! The directory of the
cloned ``sqlcipher3`` repo can be deleted after installing the package.

Steps 5-9 can be automated using the CLI of ``pyrekordbox``:

    > python3 -m pyrekordbox install-sqlcipher --help
    usage: pyrekordbox install-sqlcipher [-h] [-t TMPDIR] [-l CRYPTOLIB] [-q] [-b]

      -t TMPDIR, --tmpdir TMPDIR
                            Path for storing temporary data (default: '.tmp')
      -l CRYPTOLIB, --cryptolib CRYPTOLIB
                            The name of the OpenSSl crypto libary (default: 'libcrypto.lib')
      -b, --buildonly       Don't install sqlcipher3, only build the amalgamation


##### Troubleshooting

- **Microsoft Visual C++ error**

  If you are getting an error like
  ````shell
  error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools"``
  ````
  and have Visual Studio installed, you might not have all the necessary C/C++ components.

- **LINK error**

  If you are getting an error like
  ````shell
  LINK : fatal error LNK1158: cannot run 'rc.exe'
  ````
  or
  ````shell
  LINK : fatal error LNK1327: failure during running rc.exe
  ````
  make sure all the necessary C/C++ components are installed and that you have selected
  the latest Win 10/11 SDK in the Visual Studio installer. If you are still getting the error,
  follow the suggestions in this [StackOverflow post](https://stackoverflow.com/questions/14372706/visual-studio-cant-build-due-to-rc-exe).


### MacOS


#### System SQLCipher

For building [sqlcipher3] against the system SQLCipher installation on MacOS follow these steps:

1) Install [Homebrew](https://brew.sh) if you do not have it on your machine.
2) Install SQLCipher with `brew install SQLCipher`.
3) With the python environment you are using to run pyrekordbox active execute the following:
```shell
git clone https://github.com/coleifer/sqlcipher3
cd sqlcipher3
SQLCIPHER_PATH=$(brew info sqlcipher | awk 'NR==5 {print $1; exit}'); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py build
SQLCIPHER_PATH=$(brew info sqlcipher | awk 'NR==5 {print $1; exit}'); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py install
```
Make sure the `C_INCLUDE` and `LIBRARY_PATH` point to the installed SQLCipher path. It may differ on your machine.

````{note}
If you are having issues building sqlcipher on M1 Macs you might have to add some symlinks:
```shell
ln -s /opt/homebrew/lib/libsqlcipher.a /usr/local/lib/libsqlcipher.a
ln -s /opt/homebrew/include/sqlcipher /usr/local/include/sqlcipher
```
````
#### SQLCipher Amalagamation

You can also build [sqlcipher3] against an amalgamation on MacOS.

1. **Download / compile the SQLCipher amalgamation files**

   Pre-built SQLCipher amalgamation files can be downloaded from [this repo][amalgamation]:
   ````shell
   git clone https://github.com/geekbrother/sqlcipher-amalgamation
   ````
   You can also build the amalagamtion files on your own.


2. **Clone [sqlcipher3] into any directory**

   ````shell
   git clone https://github.com/coleifer/sqlcipher3
   ````


3. **Copy amalgamation files to the `sqlcipher3` directory**

   Copy files ``sqlite3.c`` and ``sqlite3.h`` from the amalgamation directory from step 1
   to the root of the ``sqlcipher3`` directory from step 2.
   ````shell
   cp sqlcipher-amalgamation/src/sqlite3.[ch] sqlcipher3/
   ````

4. **Build using the amalgamation and install**

    ``cd`` into the ``sqlcipher3`` directory and run
    ````shell
    python setup.py build_static build
    python setup.py install
    ````

The steps above can be automated using the CLI of ``pyrekordbox``

    > python3 -m pyrekordbox install-sqlcipher --help
    usage: pyrekordbox install-sqlcipher [-h] [-t TMPDIR] [-l CRYPTOLIB] [-q] [-b]

      -t TMPDIR, --tmpdir TMPDIR
                            Path for storing temporary data (default: '.tmp')
      -b, --buildonly       Don't install sqlcipher3, only build the amalgamation


```{note}
The `CRYPTOLIB` argument is only used on Windows
```


### Using SQLCipher

After the installation SQLCipher-databases can be unlocked via the `sqlcipher3` package:
````python
from sqlcipher3 import dbapi2 as sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute("PRAGMA key='password'")
````



[VS]: https://visualstudio.microsoft.com/de/vs/community/
[OpenSSL]: https://slproweb.com/products/Win32OpenSSL.html
[sqlcipher3]: https://github.com/coleifer/sqlcipher3
[amalgamation]: https://github.com/geekbrother/sqlcipher-amalgamation
[Pypi]: https://pypi.org/project/pyrekordbox/
[GitHub]: https://github.com/dylanljones/pyrekordbox
[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
[sqlcipher3-wheels]: https://github.com/laggykiller/sqlcipher3
