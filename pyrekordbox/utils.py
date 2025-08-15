# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""This module contains common constants and methods used in other modules."""

import base64
import os
import warnings
import xml.etree.cElementTree as xml
import zlib
from xml.dom import minidom

import psutil

warnings.simplefilter("always", DeprecationWarning)

BLOB_KEY = b"657f48f84c437cc1"


def warn_deprecated(name: str, new_name: str = "", hint: str = "", remove_in: str = "") -> None:
    s = f"'{name}' is deprecated"
    if remove_in:
        s += f" and will be removed in version '{remove_in}'"

    if new_name:
        s += f", use '{new_name}' instead!"
    else:
        s += "!"

    if hint:
        s += "\n" + hint

    warnings.warn(s, DeprecationWarning, stacklevel=3)


def get_process_id(name: str, raise_exec: bool = False) -> int:
    """Returns the ID of a process if it exists.

    Parameters
    ----------
    name : str
        The name of the process, for example 'rekordbox'.
    raise_exec : bool, optional
        Raise an exception if the process can not be found.

    Returns
    -------
    pid : int
        The ID of the process if it exists, otherwise zero.

    Raises
    ------
    RuntimeError: If ``raise_exec=True``, raises a runtime error if the application
        is not running.

    Examples
    --------
    >>> get_process_id("rekordbox")
    12345

    >>> get_process_id("rekordboxAgent")
    23456
    """
    for proc in psutil.process_iter():
        try:
            proc_name = os.path.splitext(proc.name())[0]  # needed on Windows (.exe)
            if proc_name == name:
                pid: int = proc.pid
                return pid
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    if raise_exec:
        raise RuntimeError("No process with name 'rekordbox' found!")
    return 0


def get_rekordbox_pid(raise_exec: bool = False) -> int:
    """Returns the process ID of the Rekordbox application.

    Parameters
    ----------
    raise_exec : bool, optional
        Raise an exception if the Rekordbox process can not be found.

    Returns
    -------
    pid : int
        The ID of the Rekordbox process if it exists, otherwise zero.

    Raises
    ------
    RuntimeError: If ``raise_exec=True``, raises a runtime error if the Rekordbox
        application is not running.

    Examples
    --------
    >>> get_rekordbox_pid()
    12345
    """
    return get_process_id("rekordbox", raise_exec)


def get_rekordbox_agent_pid(raise_exec: bool = False) -> int:
    """Returns the process ID of the RekordboxAgent application.

    Parameters
    ----------
    raise_exec : bool, optional
        Raise an exception if the RekordboxAgent process can not be found.

    Returns
    -------
    pid : int
        The ID of the RekordboxAgent process if it exists, otherwise zero.

    Raises
    ------
    RuntimeError: If ``raise_exec=True``, raises a runtime error if the RekordboxAgent
        application is not running.

    Examples
    --------
    >>> get_rekordbox_agent_pid()
    23456
    """
    return get_process_id("rekordboxAgent", raise_exec)


def pretty_xml(element: xml.Element, indent: str = None, encoding: str = "utf-8") -> str:
    r"""Generates a formatted string of an XML element.

    Parameters
    ----------
    element : xml.etree.cElementTree.Element
        The input XML element.
    indent : str, optional
        The indentation used for formatting the XML element. The default is 3 spaces.
    encoding : str, optional
        The encoding used for formatting the XML element. The default is 'utf-8'.

    Returns
    -------
    xml_string : str
        The formatted string of the XML element.

    Notes
    -----
    This method is needed for Python 3.8 and below. Starting with Python 3.9 the XML
    module has a built-in pretty-print function:

    >>> tree = xml.ElementTree(root)  # noqa
    >>> xml.indent(tree, space="\t", level=0)
    >>> tree.write(path, encoding="utf-8", xml_declaration=True)  # noqa

    This method will be used as soon support for Python 3.8 and below is dropped.
    """
    # Build pretty xml-string
    if indent is None:
        indent = "    "
    if encoding is None:
        encoding = "utf-8"
    rough_string = xml.tostring(element, encoding)
    reparsed = minidom.parseString(rough_string)
    string = reparsed.toprettyxml(indent=indent, encoding=encoding).decode()
    # Remove annoying empty lines
    string = "\n".join([line for line in string.splitlines() if line.strip()])
    return string


def obfuscate(plaintext: str) -> bytes:
    """Obfuscates a plaintext string using zlib compression and XOR encryption."""
    key = BLOB_KEY
    data = zlib.compress(plaintext.encode("utf-8"))
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b85encode(xored)  # bytes


def deobfuscate(blob: bytes) -> str:
    """Deobfuscates a previously obfuscated string."""
    key = BLOB_KEY
    data = base64.b85decode(blob)
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return zlib.decompress(xored).decode("utf-8")
