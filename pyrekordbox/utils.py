# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""This module contains common constants and methods used in other modules."""

import os
import warnings
import psutil
import urllib.parse
from xml.dom import minidom
import xml.etree.cElementTree as xml

warnings.simplefilter("always", DeprecationWarning)

XML_URL_PREFIX = "file://localhost/"


def warn_deprecated(name, new_name="", hint="", remove_in=""):
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


def get_process_id(name: str, raise_exec=False) -> int:
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
                return proc.pid
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    if raise_exec:
        raise RuntimeError("No process with name 'rekordbox' found!")
    return 0


def get_rekordbox_pid(raise_exec=False):
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


def get_rekordbox_agent_pid(raise_exec=False):
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


def encode_xml_path(path):
    r"""Encodes a file path as URI string for an XML file.

    Parameters
    ----------
    path : str or Path
        The file path to encode.

    Returns
    -------
    url : str
        The encoded file path as URI string.

    Examples
    --------
    >>> s = r"C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3"  # noqa: W605
    >>> encode_xml_path(s)
    file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3

    """
    url_path = urllib.parse.quote(str(path), safe=":/\\")
    url = XML_URL_PREFIX + url_path.replace("\\", "/")
    return url


def decode_xml_path(url):
    r"""Decodes an as URI string encoded file path from an XML file.

    Parameters
    ----------
    url : str
        The encoded file path to decode.

    Returns
    -------
    path : str
        The decoded file path.

    Examples
    --------
    >>> s = r"file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3"
    >>> decode_xml_path(s)
    C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3  # noqa: W605

    """
    path = urllib.parse.unquote(url)
    path = path.replace(XML_URL_PREFIX, "")
    return os.path.normpath(path)


def pretty_xml(element, indent=None, encoding="utf-8"):
    """Generates a formatted string of an XML element.

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


class XmlFile:
    def __init__(self, path=None, **kwargs):
        self._root = None
        self._path = path
        if path is not None:
            self._parse(path)
        else:
            self._init(**kwargs)

    def _parse(self, path):
        """Parse an existing XML file.

        Parameters
        ----------
        path : str or Path
            The path to the XML file to parse.
        """
        pass

    def _init(self, **kwargs):
        """Initialize a new XML file."""
        pass

    def tostring(self, indent=None):
        """Returns the contents of the XML file as a string.

        Parameters
        ----------
        indent : str, optional
            The indentation used for formatting the XML file. The default is 3 spaces.

        Returns
        -------
        s : str
            The contents of the XML file
        """
        return pretty_xml(self._root, indent, encoding="utf-8")

    def save(self, path="", indent=None):
        """Saves the contents to an XML file.

        Parameters
        ----------
        path : str or Path, optional
            The path for saving the XML file. The default is the original file.
        indent : str, optional
            The indentation used for formatting the XML element.
            The default is 3 spaces.
        """
        string = self.tostring(indent)
        if not path:
            path = self._path
        with open(path, "w") as fh:
            fh.write(string)
