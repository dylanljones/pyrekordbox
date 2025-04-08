# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-08-15

import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from subprocess import CalledProcessError, run

from pyrekordbox.config import _cache_file, write_db6_key_cache

KEY_SOURCES = [
    {
        "url": r"https://raw.githubusercontent.com/mganss/CueGen/19878e6eb3f586dee0eb3eb4f2ce3ef18309de9d/CueGen/Generator.cs",  # noqa: E501
        "regex": re.compile(
            r'((.|\n)*)Config\.UseSqlCipher.*\?.*"(?P<dp>.*)".*:.*null',
            flags=re.IGNORECASE | re.MULTILINE,
        ),
    },
    {
        "url": r"https://raw.githubusercontent.com/dvcrn/go-rekordbox/8be6191ba198ed7abd4ad6406d177ed7b4f749b5/cmd/getencryptionkey/main.go",  # noqa: E501
        "regex": re.compile(
            r'((.|\n)*)fmt\.Print\("(?P<dp>.*)"\)', flags=re.IGNORECASE | re.MULTILINE
        ),
    },
]


class WorkingDir:
    def __init__(self, path):
        self._prev = Path.cwd()
        self.path = Path(path)

    def __enter__(self):
        if self.path != self._prev:
            self.path.mkdir(parents=True, exist_ok=True)
            os.chdir(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path != self._prev:
            os.chdir(self._prev)


def set_sqlcipher_paths():
    result = run(["brew", "--prefix", "sqlcipher"], capture_output=True, text=True)
    if result.returncode != 0:
        raise CalledProcessError(
            result.returncode, result.args, output=result.stdout, stderr=result.stderr
        )
    sqlcipher_path = result.stdout.strip()

    # Ensure OpenSSL paths
    openssl_include_path = "/usr/local/opt/openssl/include"
    openssl_lib_path = "/usr/local/opt/openssl/lib"

    os.environ["C_INCLUDE_PATH"] = f"{sqlcipher_path}/include:{openssl_include_path}"
    os.environ["LIBRARY_PATH"] = f"{sqlcipher_path}/lib:{openssl_lib_path}"
    os.environ["PKG_CONFIG_PATH"] = f"{sqlcipher_path}/lib/pkgconfig"
    os.environ["CFLAGS"] = (
        f"-I{sqlcipher_path}/include -I{openssl_include_path} -Wno-deprecated-declarations -Wno-unused-variable -Wno-unreachable-code -Wno-sign-compare"
    )
    os.environ["LDFLAGS"] = f"-L{sqlcipher_path}/lib -L{openssl_lib_path}"

    print(f"SQLCipher path: {sqlcipher_path}")
    print(f"C_INCLUDE_PATH: {os.environ['C_INCLUDE_PATH']}")
    print(f"LIBRARY_PATH: {os.environ['LIBRARY_PATH']}")
    print(f"PKG_CONFIG_PATH: {os.environ['PKG_CONFIG_PATH']}")
    print(f"CFLAGS: {os.environ['CFLAGS']}")
    print(f"LDFLAGS: {os.environ['LDFLAGS']}")


def create_symlinks():
    result = run(["brew", "--prefix", "sqlcipher"], capture_output=True, text=True)
    if result.returncode != 0:
        raise CalledProcessError(
            result.returncode, result.args, output=result.stdout, stderr=result.stderr
        )
    sqlcipher_path = result.stdout.strip()
    symlink_dir = Path("/usr/local")

    if os.uname().machine == "arm64":
        print("Creating symlinks for M1 Mac...")
        symlink_dir.mkdir(parents=True, exist_ok=True)
        (symlink_dir / "lib").mkdir(parents=True, exist_ok=True)
        (symlink_dir / "include").mkdir(parents=True, exist_ok=True)

        lib_sqlcipher_a = symlink_dir / "lib/libsqlcipher.a"
        if not lib_sqlcipher_a.exists():
            lib_sqlcipher_a.symlink_to(
                f"{sqlcipher_path}/lib/libsqlcipher.a", target_is_directory=False
            )

        include_sqlcipher = symlink_dir / "include/sqlcipher"
        if not include_sqlcipher.exists():
            include_sqlcipher.symlink_to(
                f"{sqlcipher_path}/include/sqlcipher", target_is_directory=True
            )

    if not (symlink_dir / "include/sqlcipher").exists():
        print("Creating necessary symlinks for SQLCipher headers...")
        (symlink_dir / "include").mkdir(parents=True, exist_ok=True)
        include_sqlcipher = symlink_dir / "include/sqlcipher"
        if not include_sqlcipher.exists():
            include_sqlcipher.symlink_to(
                f"{sqlcipher_path}/include/sqlcipher", target_is_directory=True
            )


def clone_repo(https_url: str) -> Path:
    path = Path.cwd() / https_url.split("/")[-1]
    if not path.exists():
        run(["git", "clone", https_url], check=True)
        assert path.exists()
    else:
        print(f"Repository {https_url} already cloned")
    return path


def clone_pysqlcipher3() -> Path:
    return clone_repo(r"https://github.com/coleifer/sqlcipher3")


def clone_sqlcipher_amalgamation() -> Path:
    return clone_repo(r"https://github.com/geekbrother/sqlcipher-amalgamation")


def patch_pysqlcipher_setup(pysqlcipher_dir, cryptolib="libcrypto.lib"):
    path = Path(pysqlcipher_dir, "setup.py")

    with open(path, "r") as fh:
        text = fh.read()

    if cryptolib:
        lib_old = "os.environ.get('OPENSSL_LIBNAME') or 'libeay32.lib'"
        lib_new = f"os.environ.get('OPENSSL_LIBNAME') or '{cryptolib}'"
        text = text.replace(lib_old, lib_new)

    with open(path, "w") as fh:
        fh.write(text)


def prepare_pysqlcipher(pysqlcipher_dir: Path, amalgamation_src: Path):
    # Copy amalgamation files to pysqlcipher directory
    root = pysqlcipher_dir
    root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(amalgamation_src / "sqlite3.c", root / "sqlite3.c")
    shutil.copy2(amalgamation_src / "sqlite3.h", root / "sqlite3.h")


def install_pysqlcipher(
    tmpdir="pysqlcipher3",
    crypto_lib="libcrypto.lib",
    pyexecutable="",
    build=True,
    install=True,
    cleanup=True,
):
    tmpdir = Path(tmpdir)
    # Download pysqlcipher3 and prepare amalgamation build
    with WorkingDir(tmpdir):
        pysqlcipher_dir = clone_pysqlcipher3()
        amalgamation_dir = clone_sqlcipher_amalgamation()
        amalgamation_src = amalgamation_dir / "src"

        prepare_pysqlcipher(pysqlcipher_dir, amalgamation_src)
        if sys.platform == "win32" and os.getenv("OPENSSL_LIBNAME") is None:
            print("No OPENSSL_LIBNAME environment variable found, updating `setup.py`!")
            patch_pysqlcipher_setup(pysqlcipher_dir, crypto_lib)

    # Set environment paths and create symlinks
    set_sqlcipher_paths()
    create_symlinks()

    # Build amalgamation and install pysqlcipher
    if not pyexecutable:
        pyexecutable = sys.executable

    with WorkingDir(pysqlcipher_dir):
        if build:
            # Build amalgamation
            print()
            os.system(f"{pyexecutable} -m build --wheel")
        if install:
            # Install pysqlcipher package
            print()

    # Remove temporary files
    if cleanup:
        try:
            print()
            print("Cleaning up")
            shutil.rmtree(tmpdir)
        except PermissionError as e:
            print()
            print(e)
            print(f"Could not remove temporary directory '{tmpdir}'!")


def download_db6_key():
    dp = ""
    for source in KEY_SOURCES:
        url = source["url"]
        regex = source["regex"]
        print(f"Looking for key: {url}")

        res = urllib.request.urlopen(url)
        data = res.read().decode("utf-8")
        match = regex.match(data)
        if match:
            dp = match.group("dp")
            break
    if dp:
        print(f"Found key, updating cache file {_cache_file}")
        write_db6_key_cache(dp)
    else:
        print("No key found in the online sources.")


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser("pyrekordbox")
    subparsers = parser.add_subparsers(dest="command")

    # Download Rekordbx 6 database key command
    subparsers.add_parser(
        "download-key",
        help="Download the Rekordbox 6 database key from the internet "
        "and write it to the cache file.",
    )

    # Install pysqlcipher3 command (Windows/Mac OS)
    install_parser = subparsers.add_parser(
        "install-sqlcipher",
        help="Build sqlcipher against amalgamation and install pysqlcipher3",
    )
    install_parser.add_argument(
        "-t",
        "--tmpdir",
        type=str,
        default=".tmp",
        help="Path for storing temporary data (default: '.tmp')",
    )
    install_parser.add_argument(
        "-l",
        "--cryptolib",
        type=str,
        default="libcrypto.lib",
        help="The name of the OpenSSl crypto libary (default: 'libcrypto.lib')",
    )
    install_parser.add_argument(
        "-b",
        "--buildonly",
        action="store_true",
        help="Don't install sqlcipher3, only build the amalgamation",
    )

    # Parse args and handle command
    args = parser.parse_args(sys.argv[1:])
    if args.command == "download-key":
        download_db6_key()
    elif args.command == "install-sqlcipher":
        install_pysqlcipher(args.tmpdir, args.cryptolib, install=not args.buildonly)


if __name__ == "__main__":
    main()
