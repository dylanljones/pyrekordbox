# Installing SQLCipher for Python on Windows


## Building SQLCipher and installing pysqlcipher3 (recommended)


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

   ````commandline
   git clone https://github.com/rigglemania/pysqlcipher3
   ````


7. **Create directory ``...\pysqlcipher3\amalgamation``**

   Copy files ``sqlite3.c`` and ``sqlite3.h`` from the amalgamation directory from step 5


8. **Create directory ``...\pysqlcipher3\src\python3\sqlcipher``**

   Copy files ``sqlite3.c``, ``sqlite3.h`` and ``sqlite3ext.h`` from the amalgamation directory from step 5


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
    ````commandline
    python setup.py build_amalgamation
    ````


11. **Install ``pysqlcipher3``**

    ````commandline
    python setup.py install
    ````

You now should have a working ``pysqlcipher3`` installation! The directory of the
cloned ``pysqlcipher3`` repo can be deleted after installing the package.

Steps 5-11 can be automated using the included ``install_pysqlcipher`` script:
````commandline
usage: install_pysqlcipher.py [-h] [-t TMPDIR] [-l CRYPTOLIB] [-q] [-b]

options:
  -h, --help            show this help message and exit
  -t TMPDIR, --tmpdir TMPDIR
                        Path for storing temporary data (default: '.tmp')
  -l CRYPTOLIB, --cryptolib CRYPTOLIB
                        The name of the OpenSSl crypto libary (default: 'libcrypto.lib')
  -q, --fixquote        Don't fix the quotes in the pysqlcipher3 setup.py script
  -b, --buildonly       Don't install pysqlcipher3, only build the amalgamation
````

After the installation SQLCipher-databases can be unlocked via the
`pysqlcipher3` package by providing a key via the `PRAGMA key='db-key'` SQL statement:
````python
from pysqlcipher3 import dbapi2 as sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute("PRAGMA key='password'")
````


## Pre-built SQLCipher DLL's (not recommended)

Alternatively, pyrekordbox includes Python SQLite DLL's (see [this](https://stackoverflow.com/questions/58964763/using-sqlcipher-in-python-the-easy-way)
StackOverflow discussion), which can be used to open databases encrpyted by SQLCipher.
The DLL's can be found in the ``Libs/sqlcipher_py38`` directory of the pyrekordbox package.
To patch the sqlite3 installation, follow these steps:


- **Replace ``sqlite3.dll`` in the Python DLL directory**

  Rename the ``sqlcipher.dll`` file in the ``Libs/sqlcipher_py38`` directory to
  ``sqlite3.dll`` and replace the existing DLL file in the Python DLL folder with it.

  *Note*: Before replacing the original file, back up ``sqlite3.dll`` in the Python DLL directory by renaming it to something like ``sqlite3_backup.dll``.

- **Optional: Copy `libcrypto-1_1.dll` into the Python DLL directory**

- **Optional: Copy `libssl-1_1.dll` into the Python DLL directory**

The last two steps are only required if the first step is not sufficient.

After replacing the DLL files SQLCipher-databases can be unlocked via the normal
`sqlite3` package by providing a key via the `PRAGMA key='db-key'` SQL statement:
````python
import sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute("PRAGMA key='password'")
````

| ❗  | The included DLL's only work with *Python 3.8 (32 bit)*! For other Python versions (specificly the version of the included SQLite3 libary) the DLL's have to be built from source. |
|----|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|


## References:

- [Sqlcipher](https://www.zetetic.net/sqlcipher/open-source/)
- [Stackoverflow discussion](https://stackoverflow.com/questions/33618565/how-to-build-sql-cipher-python-binding-for-windows)
- https://github.com/Monogi/pysqlcipher3_install_win10

[VS]: https://visualstudio.microsoft.com/de/vs/community/
[OpenSSL]: https://slproweb.com/products/Win32OpenSSL.html
[pysqlcipher3]: https://github.com/rigglemania/pysqlcipher3
