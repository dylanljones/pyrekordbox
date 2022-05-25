# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

"""This module contains common constants and methods used in other modules.

Contains all the path and settings handling of the Rekordbox installation(s) on
the users machine.
"""

import os
import sys
import json
import logging
import xml.etree.cElementTree as xml

logger = logging.getLogger(__name__)

# fmt: off
CRC16_XMODEM_TABLE = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
]
# fmt: off


def _crc16(data, crc, table):
    """Calculate CRC16 using the given table.
    `data`      - data for calculating CRC, must be a string
    `crc`       - initial value
    `table`     - table for caclulating CRC (list of 256 integers)
    Return calculated value of CRC
    """
    for byte in data:
        crc = ((crc << 8) & 0xFF00) ^ table[((crc >> 8) & 0xFF) ^ byte]
    return crc & 0xFFFF


def crc16xmodem(data, crc=0):
    """Calculate CRC-CCITT (XModem) variant of CRC16.
    `data`      - data for calculating CRC, must be a string
    `crc`       - initial value
    Return calculated value of CRC
    """
    return _crc16(data, crc, CRC16_XMODEM_TABLE)


def _read_config_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".cfg":
        from configparser import ConfigParser

        parser = ConfigParser()
        parser.read(path)
        return parser
    elif ext == ".toml":
        import toml

        return toml.load(path)
    elif ext in (".yaml", ".yml"):
        import yaml

        with open(path, "r") as stream:
            return yaml.safe_load(stream)
    return dict()


def read_pyrekordbox_configuration():
    """Reads the pyrekordbox configuration.

    So far only the `pioneer-install-dir` and `pioneer-app-dir` fileds in the
    `rekordbox` section are supported. Supported configuration files are
    pyproject.toml, setup.cfg, rekordbox.toml, rekordbox.cfg and rekordbox.yml.
    The files are searched for in that order.

    Returns
    -------
    pyrekordbox_config : dict
        The pyrekordbox configuration data, if found.
    """
    files = ["pyproject.toml", "setup.cfg"]
    for ext in [".toml", ".cfg", ".yaml", ".yml"]:
        files.append("rekordbox" + ext)

    for file in files:
        try:
            data = _read_config_file(file)
            config = dict(data["rekordbox"])
        except (ImportError, FileNotFoundError, KeyError):
            pass
        else:
            if config:
                return config
    return dict()


def get_pioneer_app_dir(path=""):
    """Returns the path of the Pioneer application data directory.

    On Windows, the Pioneer application data is stored in `/Users/user/AppData/Roaming`
    On macOS the application data is somewhere in `~/Libary/Application Support`.

    Parameters
    ----------
    path : str, optional
        If a path is given it will only be checked for validity. Otherwise,
        the default Pioneer directory will be constructed and checked.

    Returns
    -------
    pioneer_path : str
        The path to the Pioneer application data.
    """
    if not path:
        if sys.platform == "win32":
            # Windows: located in /Users/user/AppData/Roaming/
            app_data = os.environ["AppData"]
        elif sys.platform == "darwin":
            # MacOS: located in ~/Library/Application Support/
            home = os.path.expanduser("~")
            app_data = os.path.join(home, "Library", "Application Support")
        else:
            # Linux: not supported
            logger.warning(f"OS {sys.platform} not supported!")
            app_data = ""

        # Pioneer app data
        path = os.path.join(app_data, "Pioneer")

    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"The Pioneer app-dir {path} does not exist!")

    return path


def get_pioneer_install_dir(path=""):
    """Returns the path of the Pioneer program installation directory.

    On Windows, the Pioneer program data is stored in `/ProgramFiles/Pioneer`
    On macOS the program data is somewhere in `/Applications/`.

    Parameters
    ----------
    path : str, optional
        If a path is given it will only be checked for validity. Otherwise,
        the default Pioneer directory will be constructed and checked.

    Returns
    -------
    pioneer_path : str
        The path to the Pioneer program installation data.
    """
    if not path:
        if sys.platform == "win32":
            # Windows: located in /ProgramFiles/Pioneer
            program_files = os.environ["ProgramFiles"].replace("(x86)", "").strip()
            path = os.path.join(program_files, "Pioneer")
        elif sys.platform == "darwin":
            # MacOS: located in /Applications/
            path = os.path.abspath("/Applications")
        else:
            # Linux: not supported
            logger.warning(f"OS {sys.platform} not supported!")

    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"The Pioneer install-dir {path} does not exist!")

    return path


def _convert_type(s):
    # Try to parse as int, float, list of int, list of float
    types_ = int, float
    for type_ in types_:
        try:
            return type_(s)
        except ValueError:
            pass
        try:
            return [type_(x) for x in s.split(",")]
        except ValueError:
            pass

    return s


def read_rekordbox_settings(rekordbox_app_dir):
    """Finds and parses the 'rekordbox3.settings' file in the Rekordbox 5 or 6 app-dir.

    The settings file usually is called 'rekordbox3.settings' and is
    located in the application data directory of the corresponding Rekordbox
    (major) version.

    Parameters
    ----------
    rekordbox_app_dir : str
        The path of the application-data directory of Rekordbox 5 or 6.

    Returns
    -------
    settings : dict
        The parsed Rekordbox settings data.
    """
    # Get path of the settings file
    file_name = "rekordbox3.settings"
    path = os.path.join(rekordbox_app_dir, file_name)
    # if not os.path.exists(path):
    #    raise FileNotFoundError(f"No '{file_name}' file in '{rekordbox_app_dir}'.")

    # Parse the settings file
    settings = dict()
    tree = xml.parse(path)
    for element in tree.findall("VALUE"):
        name = element.attrib["name"]
        try:
            val = _convert_type(element.attrib["val"])
        except KeyError:
            device_setup = element.find("DEVICESETUP")
            val = {k: _convert_type(v) for k, v in device_setup.attrib.items()}
        settings[name] = val
    return settings


def read_rekordbox6_options(pioneer_app_dir):
    """Finds and parses the Rekordbox 6 `options.json` file with additional settings.

    The options file contains additional settings used by Rekordbox 6, for example the
    path of the new `master.db` database. It also contains some data nedded to open
    the database, which is encrypted using SQLCipher.

    Parameters
    ----------
    pioneer_app_dir : str, optional
        The path of the Pioneer application data.

    Returns
    -------
    options : dict
        The parsed rekordbox 6 options data.
    """
    # Get path of the options file
    opt_path = os.path.join(
        pioneer_app_dir, "rekordboxAgent", "storage", "options.json"
    )

    # Read and parse the options file
    with open(opt_path, "r") as fh:
        data = json.load(fh)
    options = dict()
    for key, value in data["options"]:
        options[key] = value

    return options


def read_rekordbox6_asar(rb6_install_dir):
    """Finds and parses the Rekordbox 6 `app.asar` archive file.

    An ASAR file is an archive used to package source code for an application
    using Electron. Rekordbox 6 stores some useful information for opening the
    new `master.db` database in this file.

    Parameters
    ----------
    rb6_install_dir : str
        The path of the Rekordbox 6 installation directory.

    Returns
    -------
    asar_data : str
        The data of the Rekordbox 6 `app.asar` archive file as ANSI encoded string.
    """
    # Find location of app asar file
    if sys.platform == "win32":
        location = os.path.join(
            rb6_install_dir, "rekordboxAgent-win32-x64", "resources"
        )
        encoding = "ANSI"
    elif sys.platform == "darwin":
        root = os.path.join(rb6_install_dir, "rekordbox.app", "Contents", "MacOS")
        location = os.path.join(root, "rekordboxAgent.app", "Contents", "Resources")
        encoding = "cp437"
    else:
        raise logger.warning(f"OS {sys.platform} not supported!")

    # Read asar file
    path = os.path.abspath(os.path.join(location, "app.asar"))
    with open(path, "rb") as fh:
        data = fh.read().decode(encoding)

    return data
