# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""Configuration handling for pyrekordbox.

Contains all the path and settings handling of the Rekordbox installation(s) on
the users machine.
"""

import json
import logging
import os
import sys
import xml.etree.cElementTree as xml
from pathlib import Path
from typing import Any, Dict, List, Union

import packaging.version

logger = logging.getLogger(__name__)

# Define empty pyrekordbox configuration
__config__ = {
    "pioneer": {
        "app_dir": Path(),
        "install_dir": Path(),
    },
    "rekordbox5": {},
    "rekordbox6": {},
    "rekordbox7": {},
}


class InvalidApplicationDirname(Exception):
    pass


def get_pioneer_install_dir(path: Union[str, Path] = None) -> Path:  # pragma: no cover
    """Returns the path of the Pioneer program installation directory.

    On Windows, the Pioneer program data is stored in `/ProgramFiles/Pioneer`.
    For rekordbox version 7 this has changed to `/ProgramFiles/rekordbox`.
    On macOS the program data is somewhere in `/Applications/`.

    Parameters
    ----------
    path : str or Path, optional
        If a path is given it will only be checked for validity. Otherwise,
        the default Pioneer directory will be constructed and checked.

    Returns
    -------
    pioneer_path : Path
        The path to the Pioneer program installation data.
    """
    if path is None:
        if sys.platform == "win32":
            # Windows: located in /ProgramFiles/Pioneer
            program_files = os.environ["ProgramFiles"].replace("(x86)", "").strip()
            path = Path(program_files)
        elif sys.platform == "darwin":
            # MacOS: located in /Applications/
            path = Path("/Applications")
        else:
            # Linux: not supported
            logger.warning(f"OS {sys.platform} not supported!")
            return Path()
    else:
        path = Path(path)

    path = path.absolute()
    if not path.exists():
        raise FileNotFoundError(f"The Pioneer install-dir {path} does not exist!")

    return path


def get_pioneer_app_dir(path: Union[str, Path] = None) -> Path:  # pragma: no cover
    """Returns the path of the Pioneer application data directory.

    On Windows, the Pioneer application data is stored in `/Users/user/AppData/Roaming`
    On macOS the application data is somewhere in `~/Libary/Application Support`.

    Parameters
    ----------
    path : str or Path, optional
        If a path is given it will only be checked for validity. Otherwise,
        the default Pioneer directory will be constructed and checked.

    Returns
    -------
    pioneer_path : Path
        The path to the Pioneer application data.
    """
    if path is None:
        if sys.platform == "win32":
            # Windows: located in /Users/user/AppData/Roaming/
            app_data = Path(os.environ["AppData"])
        elif sys.platform == "darwin":
            # MacOS: located in ~/Library/Application Support/
            app_data = Path("~").expanduser() / "Library" / "Application Support"
        else:
            # Linux: not supported
            logger.warning(f"OS {sys.platform} not supported!")
            return Path()
        # Pioneer app data
        path = app_data / "Pioneer"
    else:
        path = Path(path)

    path = path.absolute()
    if not path.exists():
        raise FileNotFoundError(f"The Pioneer app-dir {path} does not exist!")

    return path


def _convert_type(s: str) -> Union[str, int, float, List[int], List[float]]:
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


def read_rekordbox_settings(rekordbox_app_dir: Union[str, Path]) -> Dict[str, Any]:
    """Finds and parses the 'rekordbox3.settings' file in the Rekordbox 5 or 6 app-dir.

    The settings file usually is called 'rekordbox3.settings' and is
    located in the application data directory of the corresponding Rekordbox
    (major) version.

    Parameters
    ----------
    rekordbox_app_dir : str or Path
        The path of the application-data directory of Rekordbox 5 or 6.

    Returns
    -------
    settings : dict
        The parsed Rekordbox settings data.
    """
    # Get path of the settings file
    rekordbox_app_dir = Path(rekordbox_app_dir)
    path = rekordbox_app_dir / "rekordbox3.settings"

    # Parse the settings file
    settings = dict()
    tree = xml.parse(path)
    for element in tree.findall("VALUE"):
        name = element.attrib["name"]
        try:
            val = _convert_type(element.attrib["val"])
        except KeyError:
            device_setup = element.find("DEVICESETUP")
            val = {k: _convert_type(v) for k, v in device_setup.attrib.items()}  # type: ignore
        settings[name] = val
    return settings


def read_rekordbox6_options(pioneer_app_dir: Union[str, Path]) -> Dict[str, Any]:
    """Finds and parses the Rekordbox 6 `options.json` file with additional settings.

    The options file contains additional settings used by Rekordbox 6, for example the
    path of the new `master.db` database. It also contains some data nedded to open
    the database, which is encrypted using SQLCipher.

    Parameters
    ----------
    pioneer_app_dir : str or Path, optional
        The path of the Pioneer application data.

    Returns
    -------
    options : dict
        The parsed rekordbox 6 options data.
    """
    # Get path of the options file
    pioneer_app_dir = Path(pioneer_app_dir)
    opt_path = pioneer_app_dir / "rekordboxAgent" / "storage" / "options.json"
    # Read and parse the options file
    with open(opt_path, "r") as fh:
        data = json.load(fh)
    options = dict()
    for key, value in data["options"]:
        options[key] = value
    return options


def _extract_version(name: str, major_version: int) -> str:
    name = name.replace(".app", "")  # Needed for MacOS
    ver_str = name.replace("rekordbox", "").strip()
    if not ver_str:
        ver_str = str(major_version)
    return ver_str


def _get_rb_config(
    pioneer_install_dir: Path,
    pioneer_app_dir: Path,
    major_version: int,
    application_dirname: str = "",
) -> Dict[str, Any]:
    """Get the program configuration for a given Rekordbox major version.

    Parameters
    ----------
    pioneer_install_dir : Path
        The path of the Pioneer installation directory.
    pioneer_app_dir : Path
        The path of the Pioneer application data directory.
    major_version : int
        The major version of Rekordbox.
    application_dirname : str, optional
        The name of the Rekordbox application directory. If not given, the latest
        Rekordbox installation directory for major version `major_version` is used.

    Returns
    -------
    config : dict
        The program configuration.
    """
    if sys.platform == "win32":
        if major_version >= 7:
            pioneer_install_dir = pioneer_install_dir / "rekordbox"
        else:
            pioneer_install_dir = pioneer_install_dir / "Pioneer"

    if application_dirname:
        # Applitcation dirname is given, only extract version from it
        # `major_version` is compared to the version string
        rb_prog_dir = pioneer_install_dir / application_dirname
        if not rb_prog_dir.exists():
            raise InvalidApplicationDirname(
                f"The supplied application dirname '{application_dirname}' does not "
                f"exist in '{pioneer_install_dir}'"
            )
        rb_version = _extract_version(application_dirname, major_version)
    else:
        # Get latest Rekordbox installation directory for major release `major_version`

        # Find all 'V.x.x' version strings in dir names
        installations = {}
        for p in pioneer_install_dir.iterdir():
            name = p.name
            if name.startswith("rekordbox"):
                ver_str = _extract_version(name, major_version)
                if ver_str.startswith(str(major_version)):
                    version = packaging.version.parse(ver_str)
                    installations[version] = name
        # Get latest 'V.x.x' version string and assure there is one
        versions = list(installations.keys())
        versions.sort()
        try:
            version = versions[-1]
        except IndexError:
            raise FileNotFoundError(
                f"No Rekordbox {major_version} folder found in installation "
                f"directory '{pioneer_install_dir}'"
            )
        # Name of the Rekordbox application directory in `pioneer_install_dir`
        rb_version = str(versions[-1])
        rb_prog_dir = pioneer_install_dir / installations[version]

    # Check installation directory
    if not rb_prog_dir.exists():
        raise FileNotFoundError(
            f"The Rekordbox installation directory '{rb_prog_dir}' doesn't exist"
        )
    logger.debug("Found Rekordbox %s install-dir: '%s'", major_version, rb_prog_dir)

    # Get Rekordbox application directory path for major release `major_version`
    name = "rekordbox6" if major_version >= 6 else "rekordbox"
    rb_app_dir = pioneer_app_dir / name
    if not rb_app_dir.exists():
        raise FileNotFoundError(f"The directory '{rb_app_dir}' doesn't exist!")
    logger.debug("Found Rekordbox %s app-dir: %s", major_version, rb_app_dir)

    # Get Rekordbox database locations for major release `major_version`
    settings = read_rekordbox_settings(rb_app_dir)
    db_dir = Path(settings["masterDbDirectory"])
    db_filename = "master.db" if major_version >= 6 else "datafile.edb"
    db_path = db_dir / db_filename
    if not db_path.exists():
        raise FileNotFoundError(f"The Rekordbox database '{db_path}' doesn't exist!")

    conf = {
        "version": rb_version,
        "install_dir": rb_prog_dir,
        "app_dir": rb_app_dir,
        "db_dir": db_dir,
        "db_path": db_path,
    }
    return conf


def _get_rb5_config(
    pioneer_prog_dir: Path, pioneer_app_dir: Path, dirname: str = ""
) -> Dict[str, Any]:
    """Get the program configuration for Rekordbox v5.x.x."""
    major_version = 5
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, major_version, dirname)
    return conf


def _get_rb6_config(
    pioneer_prog_dir: Path, pioneer_app_dir: Path, dirname: str = ""
) -> Dict[str, Any]:
    """Get the program configuration for Rekordbox v6.x.x."""
    major_version = 6
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, major_version, dirname)

    # Read Rekordbox 6 'options.json' and check db_path
    opts = read_rekordbox6_options(pioneer_app_dir)
    db_path = Path(opts["db-path"])
    db_dir = db_path.parent
    assert str(conf["db_dir"]) == str(db_dir)
    assert str(conf["db_path"]) == str(db_path)

    return conf


def _get_rb7_config(
    pioneer_prog_dir: Path, pioneer_app_dir: Path, dirname: str = ""
) -> Dict[str, Any]:
    """Get the program configuration for Rekordbox v7.x.x."""
    major_version = 7
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, major_version, dirname)

    # Read Rekordbox 6 'options.json' and check db_path
    opts = read_rekordbox6_options(pioneer_app_dir)
    db_path = Path(opts["db-path"])
    db_dir = db_path.parent
    assert str(conf["db_dir"]) == str(db_dir)
    assert str(conf["db_path"]) == str(db_path)

    return conf


def update_config(
    pioneer_install_dir: Union[str, Path] = None,
    pioneer_app_dir: Union[str, Path] = None,
    rb5_install_dirname: str = "",
    rb6_install_dirname: str = "",
    rb7_install_dirname: str = "",
) -> None:
    """Update the pyrekordbox configuration.

    This method scans the system for the Rekordbox installation and application data
    directories and extracts the reuired file locations. For this the default Pioneer
    directories (installation and application data) are used. If the method fails to
    find the directories they can be supplied as parameters. If no Rekordbox
    installation is found the fileds are left unchanged.
    On import configuration with the default locations is loaded.

    Parameters
    ----------
    pioneer_install_dir : str or Path, optional
        The path to the Pioneer installation directory. This is where the program files
        of Pioneer applications are stored. By default, the normal location of Pioneer
        programs is used.
    pioneer_app_dir : str or Path, optional
        The path to the Pioneer application directory. This is where the application
        user data of Pioneer programs is stored. By default, the normal location of
        the Pioneer application data is used.
    rb5_install_dirname : str, optional
        The name of the Rekordbox 5 installation directory. By default, the normal
        directory name is used (Windows: 'rekordbox 5.x.x', macOS: 'rekordbox 5.app').
    rb6_install_dirname : str, optional
        The name of the Rekordbox 6 installation directory. By default, the normal
        directory name is used (Windows: 'rekordbox 6.x.x', macOS: 'rekordbox 6.app').
    rb7_install_dirname : str, optional
        The name of the Rekordbox 7 installation directory. By default, the normal
        directory name is used (Windows: 'rekordbox 7.x.x', macOS: 'rekordbox 7.app').
    """
    # Pioneer installation directory
    try:
        pioneer_install_dir = get_pioneer_install_dir(pioneer_install_dir)
        __config__["pioneer"]["install_dir"] = pioneer_install_dir
    except FileNotFoundError as e:
        logger.warning(e)
        return

    # Pioneer application data directory
    try:
        pioneer_app_dir = get_pioneer_app_dir(pioneer_app_dir)
        __config__["pioneer"]["app_dir"] = pioneer_app_dir
    except FileNotFoundError as e:
        logger.warning(e)
        return

    # Update Rekordbox 5 config
    try:
        conf = _get_rb5_config(pioneer_install_dir, pioneer_app_dir, rb5_install_dirname)
        __config__["rekordbox5"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)

    # Update Rekordbox 6 config
    try:
        conf = _get_rb6_config(pioneer_install_dir, pioneer_app_dir, rb6_install_dirname)
        __config__["rekordbox6"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)

    # Update Rekordbox 7 config
    try:
        conf = _get_rb7_config(pioneer_install_dir, pioneer_app_dir, rb7_install_dirname)
        __config__["rekordbox7"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)


def get_config(section: str, key: str = None) -> Any:
    """Gets a section or value of the pyrekordbox configuration.

    Parameters
    ----------
    section : str
        The name of the section.
    key : str, optional
        The name of the specific value to return. If not given all values of the section
        are returned as dictionary.

    Returns
    -------
    data : str or Path or dict
        The data of a section or a specific configuration value.
    """
    # Update config if not done yet
    if not __config__[section]:
        update_config()

    conf = __config__[section]
    if key is None:
        return conf
    return conf[key]


def pformat_config(indent: str = "   ", hw: int = 14, delim: str = " = ") -> str:
    """Returns a formatted string of the pyrekordbox configurations."""
    pioneer = get_config("pioneer")
    rb5 = get_config("rekordbox5")
    rb6 = get_config("rekordbox6")
    rb7 = get_config("rekordbox7")

    lines = ["Pioneer:"]
    lines += [f"{indent}{k + delim:<{hw}} {pioneer[k]}" for k in sorted(pioneer.keys())]
    lines.append("Rekordbox 5:")
    if rb5:
        lines += [f"{indent}{k + delim:<{hw}} {rb5[k]}" for k in sorted(rb5.keys())]
    lines.append("Rekordbox 6:")
    if rb6:
        rb6_keys = [k for k in rb6.keys() if k not in ("dp", "p")]
        lines += [f"{indent}{k + delim:<{hw}} {rb6[k]}" for k in sorted(rb6_keys)]
    lines.append("Rekordbox 7:")
    if rb7:
        rb7_keys = [k for k in rb7.keys() if k not in ("dp", "p")]
        lines += [f"{indent}{k + delim:<{hw}} {rb7[k]}" for k in sorted(rb7_keys)]
    return "\n".join(lines)


def show_config() -> None:
    """Prints a formatted string of the pyrekordbox configurations."""
    print(pformat_config())
