# Building SQLCipher Python Bindings for Windows


## Requirements

Building the SQLCipher bindings requires

- [Visual Studio Community Edition][VS]
- [Prebuilt OpenSSL binary][OpenSSL]
- [pysqlcipher3]


## Building SQLCipher against amalgamation

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

5. **[Download](https://github.com/geekbrother/sqlcipher-amalgamation) or compile the SQLCipher 3 amalgamations**

   To compile the amalgamations, follow [this](http://www.jerryrw.com/howtocompile.php) tutorial

6. **Clone [pysqlcipher3] into any directory**

   ````commandline
   git clone https://github.com/rigglemania/pysqlcipher3
   ````

7. **Create directory ``...\pysqlcipher3\amalagamation``**

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
     ext.extra_link_args.append("lib<NAME>.lib")
     ````
     where ``NAME`` is something like ``libcrypto.lib``


10. **Build using the amalgamation**

    Run
    ````commandline
    python setup.py build_amalgamation
    ````

11. **Install ``pysqlcipher3``**

    Run
    ````commandline
    python setup.py install
    ````


## References:

- [Sqlcipher](https://www.zetetic.net/sqlcipher/open-source/)
- [Stackoverflow discussion](https://stackoverflow.com/questions/33618565/how-to-build-sql-cipher-python-binding-for-windows)
- https://github.com/Monogi/pysqlcipher3_install_win10

[VS]: https://visualstudio.microsoft.com/de/vs/community/
[OpenSSL]: https://slproweb.com/products/Win32OpenSSL.html
[pysqlcipher3]: https://github.com/rigglemania/pysqlcipher3
