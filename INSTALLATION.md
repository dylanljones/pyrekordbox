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

## Installing SQLCipher

Unlocking the new Rekordbox 6 `master.db` database file requires [SQLCipher][sqlcipher].

### Windows

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


4. **Copy the openssl folder to the Microsoft Visual Studio VC include directory**

   The openssl folder can be found here:
   - 32-bit: `C:/Program Files (x86)/OpenSSL-Win32/include/openssl`
   - 64-bit: `C:/Program Files/OpenSSL-Win64/include/openssl`

   The VC include directory can be foun d in the Visual Studio installation directory:
   - 32-bit: `C:/Program Files (x86)/Microsoft Visual Studio/<year>/Community/VC/Tools/MSVC/<version>/include`
   - 64-bit: `C:/Program Files/Microsoft Visual Studio/<year>/Community/VC/Tools/MSVC/<version>/include`

   If you are using VS 14 the include path is located at `C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include`
   Confirm the following path exists `.../include/openssl/aes.h`


5. **Download / compile the SQLCipher 3 amalgamation files**

   Pre-built SQLCipher 3 amalgamation files can be downloaded from [this repo](https://github.com/geekbrother/sqlcipher-amalgamation).
   To compile the amalgamation files, follow [this tutorial](http://www.jerryrw.com/howtocompile.php).


6. **Clone [sqlcipher3] into any directory**

   ````commandline
   git clone https://github.com/coleifer/sqlcipher3
   ````


7. **Copy amalgamation files to the `sqlcipher3` directory**

   Copy files ``sqlite3.c`` and ``sqlite3.h`` from the amalgamation directory from step 5
   to the root of the ``sqlcipher3`` directory from step 6.



8. **Modify the ``sqlcipher3/setup.py`` script (optional, see [this](https://stackoverflow.com/questions/65345077/unable-to-build-sqlcipher3-on-windows) discussion)**

   If building the amalgamation fails, modify the ``setup.py`` script:

   - The library names of OpenSSL have changed in version 1.1.0. If you are using a newer version, you might have to change the library name from
     ````python
     openssl_libname = os.environ.get('OPENSSL_LIBNAME') or 'libeay32.lib'
     ````
     to
     ````python
     openssl_libname = os.environ.get('OPENSSL_LIBNAME') or '<NAME>'
     ````
     where ``<NAME>`` is something like ``libcrypto.lib`` (depending on your version).


9. **Build using the amalgamation**

    ``cd`` into the ``sqlcipher3`` directory and run
    ````commandline
    python setup.py build_static build
    ````


10. **Install ``sqlcipher3``**

    ````commandline
    python setup.py install
    ````

You now should have a working ``sqlcipher3`` installation! The directory of the
cloned ``sqlcipher3`` repo can be deleted after installing the package.

Steps 5-10 can be automated using the CLI of ``pyrekordbox``:
````commandline
> python3 -m pyrekordbox install-sqlcipher --help
usage: pyrekordbox install-sqlcipher [-h] [-t TMPDIR] [-l CRYPTOLIB] [-q] [-b]

  -h, --help            show this help message and exit
  -t TMPDIR, --tmpdir TMPDIR
                        Path for storing temporary data (default: '.tmp')
  -l CRYPTOLIB, --cryptolib CRYPTOLIB
                        The name of the OpenSSl crypto libary (default: 'libcrypto.lib')
  -b, --buildonly       Don't install sqlcipher3, only build the amalgamation
````

#### Troubleshooting

- **Microsoft Visual C++ or LINK error**

  If you are getting an error like
  ````commandline
  error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools"``
  ````
  and have Visual Studio installed, you might not have all the necessary C/C++ components.

- **LINK error**

  If you are getting an error like
  ````commandline
  LINK : fatal error LNK1158: cannot run 'rc.exe'
  ````
  or
  ````commandline
  LINK : fatal error LNK1327: failure during running rc.exe
  ````
  make sure all the necessary C/C++ components are installed and that you have selected
  the latest Win 10/11 SDK in the Visual Studio installer. If you are still getting the error,
  follow the suggestions in this [StackOverflow post](https://stackoverflow.com/questions/14372706/visual-studio-cant-build-due-to-rc-exe).


### MacOS

For MacOS follow these steps:

1) Install [Homebrew](https://brew.sh) if you do not have it on your machine.
2) Install SQLCipher with `brew install SQLCipher`.
3) With the python environment you are using to run pyrekordbox active execute the following:
```shell
git clone https://github.com/coleifer/sqlcipher3
cd sqlcipher3
SQLCIPHER_PATH=$(brew info sqlcipher | awk 'NR==4 {print $1; exit}'); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py build
SQLCIPHER_PATH=$(brew info sqlcipher | awk 'NR==4 {print $1; exit}'); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py install
```
Make sure the `C_INCLUDE` and `LIBRARY_PATH` point to the installed SQLCipher path. It may differ on your machine.


## Using SQLCipher

After the installation SQLCipher-databases can be unlocked via the `sqlcipher3` package:
````python
from sqlcipher3 import dbapi2 as sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute("PRAGMA key='password'")
````


### References:

- [https://stackoverflow.com/questions/33618565/how-to-build-sql-cipher-python-binding-for-windows](https://stackoverflow.com/questions/33618565/how-to-build-sql-cipher-python-binding-for-windows)
- [https://github.com/Monogi/pysqlcipher3_install_win10](https://github.com/Monogi/pysqlcipher3_install_win10)



[VS]: https://visualstudio.microsoft.com/de/vs/community/
[OpenSSL]: https://slproweb.com/products/Win32OpenSSL.html
[sqlcipher3]: https://github.com/coleifer/sqlcipher3
[Pypi]: https://pypi.org/project/pyrekordbox/
[GitHub]: https://github.com/dylanljones/pyrekordbox
[sqlcipher]: https://www.zetetic.net/sqlcipher/open-source/
