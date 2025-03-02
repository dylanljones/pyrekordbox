# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-03-01

import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

import click

from pyrekordbox.config import _cache_file, write_db6_key_cache

__all__ = ["cli"]


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


def clone_repo(https_url: str) -> Path:
    path = Path.cwd() / https_url.split("/")[-1]
    if not path.exists():
        os.system(f"git clone {https_url}")
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

    # Build amalgamation and install pysqlcipher
    if not pyexecutable:
        pyexecutable = sys.executable

    with WorkingDir(pysqlcipher_dir):
        if build:
            # Build amalgamation
            print()
            os.system(f"{pyexecutable} setup.py build_static build")
        if install:
            # Install pysqlcipher package
            print()
            os.system(f"{pyexecutable} setup.py install")

    # Remove temporary files
    if cleanup:
        try:
            print()
            print("Cleaning up")
            tmpdir.unlink(missing_ok=True)
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


@click.group(name="pyrekordbox")
def cli():
    pass


@cli.command(name="download-key")
def download_key():
    """Download the Rekordbox 6 database key from the internet and write it to the cache file."""
    download_db6_key()


@cli.command(name="install-pysqlcipher")
@click.option(
    "--tmpdir",
    "-t",
    default=".tmp",
    help="Path for storing temporary data (default: '.tmp')",
)
@click.option(
    "--cryptolib",
    "-c",
    default="libcrypto.lib",
    help="The name of the OpenSSl crypto libary (default: 'libcrypto.lib'",
)
@click.option(
    "--buildonly",
    "-b",
    is_flag=True,
    default=False,
    help="Don't install sqlcipher3, only build the amalgamation",
)
def install_pysqlcipher_cli(tmpdir, crypto_lib, buildonly):
    """Build sqlcipher against amalgamation and install pysqlcipher3."""
    install_pysqlcipher(tmpdir, crypto_lib, install=not buildonly)
