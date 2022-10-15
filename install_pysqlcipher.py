# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os.path
import shutil
import sys


class WorkingDir:
    def __init__(self, path):
        self._prev = os.getcwd()
        self.path = path

    def __enter__(self):
        if self.path != self._prev:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            os.chdir(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path != self._prev:
            os.chdir(self._prev)


def clone_repo(https_url):
    path = os.path.join(os.getcwd(), https_url.split("/")[-1])
    if not os.path.exists(path):
        os.system(f"git clone {https_url}")
        assert os.path.exists(path)
    return path


def clone_pysqlcipher3():
    return clone_repo(r"https://github.com/rigglemania/pysqlcipher3")


def clone_sqlcipher_amalgamation():
    return clone_repo(r"https://github.com/geekbrother/sqlcipher-amalgamation")


def patch_pysqlcipher_setup(pysqlcipher_dir, cryptolib="libcrypto.lib", fix_quote=True):
    path = os.path.join(pysqlcipher_dir, "setup.py")

    with open(path, "r") as fh:
        text = fh.read()

    if fix_quote:
        quote_old = "if sys.platform != 'win32' else '\\\\\"'"
        quote_new = ""
        text = text.replace(quote_old, quote_new)

    if cryptolib:
        lib_old = 'ext.extra_link_args.append("libeay32.lib")'
        lib_new = f'ext.extra_link_args.append("{cryptolib}")'
        text = text.replace(lib_old, lib_new)

    with open(path, "w") as fh:
        fh.write(text)


def prepare_pysqlcipher(pysqlcipher_dir, amalgamation_src):
    cpath = os.path.join(amalgamation_src, "sqlite3.c")
    hpath = os.path.join(amalgamation_src, "sqlite3.h")
    epath = os.path.join(amalgamation_src, "sqlite3ext.h")

    # Create amalagamation directory
    root = os.path.join(pysqlcipher_dir, "amalgamation")
    if not os.path.exists(root):
        os.makedirs(root)
    shutil.copy2(cpath, os.path.join(root, "sqlite3.c"))
    shutil.copy2(hpath, os.path.join(root, "sqlite3.h"))

    # Create sqlcipher directory
    root = os.path.join(pysqlcipher_dir, "src", "python3", "sqlcipher")
    if not os.path.exists(root):
        os.makedirs(root)
    shutil.copy2(cpath, os.path.join(root, "sqlite3.c"))
    shutil.copy2(hpath, os.path.join(root, "sqlite3.h"))
    shutil.copy2(epath, os.path.join(root, "sqlite3ext.h"))


def install_pysqlcipher(
    tmpdir="pysqlcipher3",
    crypto_lib="libcrypto.lib",
    fix_quote=True,
    pyexecutable="",
    build=True,
    install=True,
    cleanup=True,
):
    # Download pysqlcipher3 and prepare amalgamation build
    with WorkingDir(tmpdir):
        pysqlcipher_dir = clone_pysqlcipher3()
        amalgamation_dir = clone_sqlcipher_amalgamation()
        amalgamation_src = os.path.join(amalgamation_dir, "src")

        prepare_pysqlcipher(pysqlcipher_dir, amalgamation_src)
        patch_pysqlcipher_setup(pysqlcipher_dir, crypto_lib, fix_quote)

    # Build amalgamation and install pysqlcipher
    if not pyexecutable:
        pyexecutable = sys.executable

    with WorkingDir(pysqlcipher_dir):
        if build:
            # Build amalgamation
            print()
            os.system(f"{pyexecutable} setup.py build_amalgamation")
        if install:
            # Install pysqlcipher package
            print()
            os.system(f"{pyexecutable} setup.py install")

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


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-t",
        "--tmpdir",
        type=str,
        default=".tmp",
        help="Path for storing temporary data (default: '.tmp')",
    )
    parser.add_argument(
        "-l",
        "--cryptolib",
        type=str,
        default="libcrypto.lib",
        help="The name of the OpenSSl crypto libary (default: 'libcrypto.lib')",
    )
    parser.add_argument(
        "-q",
        "--fixquote",
        action="store_false",
        help="Don't fix the quotes in the pysqlcipher3 setup.py script",
    )
    parser.add_argument(
        "-b",
        "--buildonly",
        action="store_true",
        help="Don't install pysqlcipher3, only build the amalgamation",
    )

    args = parser.parse_args(sys.argv[1:])
    if sys.platform == "win32":
        install_pysqlcipher(
            args.tmpdir, args.cryptolib, args.fixquote, install=not args.buildonly
        )
    else:
        print("Not on Windows, aborting...")


if __name__ == "__main__":
    main()
