# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""Configuration handling for pyrekordbox.

Contains all the path and settings handling of the Rekordbox installation(s) on
the users machine.
"""

import os
import re
import sys
import logging
import base64
import blowfish
import json
import packaging.version
import xml.etree.cElementTree as xml
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

# Cache file for pyrekordbox data
_cache_file_version = 2
_cache_file = Path(__file__).parent / "rb.cache"

# Define empty pyrekordbox configuration
__config__ = {
    "pioneer": {
        "app_dir": Path(),
        "install_dir": Path(),
    },
    "rekordbox5": {},
    "rekordbox6": {},
}


class InvalidApplicationDirname(Exception):
    pass


def get_pioneer_install_dir(path: Union[str, Path] = None) -> Path:  # pragma: no cover
    """Returns the path of the Pioneer program installation directory.

    On Windows, the Pioneer program data is stored in `/ProgramFiles/Pioneer`
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
            path = Path(program_files) / "Pioneer"
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


def read_rekordbox_settings(rekordbox_app_dir: Union[str, Path]) -> dict:
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
            val = {k: _convert_type(v) for k, v in device_setup.attrib.items()}
        settings[name] = val
    return settings


def read_rekordbox6_options(pioneer_app_dir: Union[str, Path]) -> dict:
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


def read_rekordbox6_asar(rb6_install_dir: Union[str, Path]) -> str:
    """Finds and parses the Rekordbox 6 `app.asar` archive file.

    An ASAR file is an archive used to package source code for an application
    using Electron. Rekordbox 6 stores some useful information for opening the
    new `master.db` database in this file.

    Parameters
    ----------
    rb6_install_dir : str or Path
        The path of the Rekordbox 6 installation directory.

    Returns
    -------
    asar_data : str
        The data of the Rekordbox 6 `app.asar` archive file as ANSI encoded string.
    """
    rb6_install_dir = Path(rb6_install_dir)
    # Find location of app asar file
    if sys.platform == "win32":
        location = rb6_install_dir / "rekordboxAgent-win32-x64" / "resources"
        encoding = "ANSI"
    elif sys.platform == "darwin":
        if not str(rb6_install_dir).endswith(".app"):
            rb6_install_dir = rb6_install_dir / "rekordbox.app"
        location = (
            rb6_install_dir
            / "Contents"
            / "MacOS"
            / "rekordboxAgent.app"
            / "Contents"
            / "Resources"
        )
        encoding = "cp437"
    else:
        logger.warning(f"OS {sys.platform} not supported!")
        return ""

    # Read asar file
    path = (location / "app.asar").absolute()
    with open(path, "rb") as fh:
        data = fh.read().decode(encoding)
    return data


def _extract_version(name, major_version):
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
) -> dict:
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
    name = "rekordbox6" if major_version == 6 else "rekordbox"
    rb_app_dir = pioneer_app_dir / name
    if not rb_app_dir.exists():
        raise FileNotFoundError(f"The directory '{rb_app_dir}' doesn't exist!")
    logger.debug("Found Rekordbox %s app-dir: %s", major_version, rb_app_dir)

    # Get Rekordbox database locations for major release `major_version`
    settings = read_rekordbox_settings(rb_app_dir)
    db_dir = Path(settings["masterDbDirectory"])
    db_filename = "master.db" if major_version == 6 else "datafile.edb"
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
) -> dict:
    """Get the program configuration for Rekordbox v5.x.x."""
    major_version = 5
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, major_version, dirname)
    return conf


def _extract_pw(pioneer_install_dir: Path) -> str:  # pragma: no cover
    """Extract the password for decrypting the Rekordbox 6 database key."""
    try:
        asar_data = read_rekordbox6_asar(pioneer_install_dir)
    except FileNotFoundError as e:
        logger.warning("Could not extract password: %s", e)
        return ""

    match_result = re.search('pass: ".(.*?)"', asar_data)
    if match_result is None:
        logging.warning("Incompatible rekordbox 6 database: Could not retrieve db-key.")
        pw = ""
    else:
        match = match_result.group(0)
        pw = match.replace("pass: ", "").strip('"')
    return pw


def write_db6_key_cache(key: str) -> None:  # pragma: no cover
    """Writes the decrypted Rekordbox6 database key to the cache file.

    This method can also be used to manually cache the database key, provided
    the user has found the key somewhere else. The key can be, for example,
    found in some other projects that hard-coded it.

    Parameters
    ----------
    key : str
        The decrypted database key. To make sure the key is valid, the first
        five characters are checked before writing the key to the cache file.
        The key should start with '402fd'.

    Examples
    --------
    >>> from pyrekordbox.config import write_db6_key_cache
    >>> from pyrekordbox import Rekordbox6Database
    >>> write_db6_key_cache("402fd...")
    >>> db = Rekordbox6Database()  # The db can now be opened without providing the key
    """
    # Check if the key looks like a valid key
    if not key.startswith("402fd"):
        raise ValueError("The provided database key doesn't look valid!")
    lines = list()
    lines.append(f"version: {_cache_file_version}")
    lines.append("dp: " + key)
    text = "\n".join(lines)
    with open(_cache_file, "w") as fh:
        fh.write(text)
    # Set the config key to make sure the key is present after calling method
    __config__["rekordbox6"]["dp"] = key


def _get_rb6_config(
    pioneer_prog_dir: Path, pioneer_app_dir: Path, dirname: str = ""
) -> dict:
    """Get the program configuration for Rekordbox v6.x.x."""
    major_version = 6
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, major_version, dirname)

    # Read Rekordbox 6 'options.json' and check db_path
    opts = read_rekordbox6_options(pioneer_app_dir)
    db_path = Path(opts["db-path"])
    db_dir = db_path.parent
    assert str(conf["db_dir"]) == str(db_dir)
    assert str(conf["db_path"]) == str(db_path)

    cache_version = 0
    pw, dp = "", ""
    if _cache_file.exists():  # pragma: no cover
        # Read cache file
        with open(_cache_file, "r") as fh:
            text = fh.read()
        lines = text.splitlines()
        if lines[0].startswith("version:"):
            cache_version = int(lines[0].split(":")[1].strip())
        else:
            cache_version = 1
        if cache_version == 1:
            # Cache file introduced in pyrekordbox 0.1.6 contains only the password
            pw = lines[0]
        elif cache_version == 2:
            # Cache file introduced in pyrekordbox 0.1.7 contains version and db key
            dp = lines[1].split(":")[1].strip()
        else:
            raise ValueError(f"Invalid cache version: {cache_version}")

    if cache_version < _cache_file_version:  # pragma: no cover
        # Update cache file
        if not pw:
            logger.debug("Extracting pw")
            pw = _extract_pw(conf["install_dir"])
        if not dp and pw:
            cipher = blowfish.Cipher(pw.encode())
            dp = base64.standard_b64decode(opts["dp"])
            dp = b"".join(cipher.decrypt_ecb(dp)).decode()
        if dp:
            write_db6_key_cache(dp)

    # Add database key to config if found
    if dp:
        conf["dp"] = dp

    return conf


# noinspection PyPackageRequirements,PyUnresolvedReferences
def _read_config_file(path: str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No such file or directory: '{path}'")

    ext = path.suffix.lower()
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
        files.append("pyrekordbox" + ext)

    for file in files:
        try:
            data = _read_config_file(file)
            config = dict(data["rekordbox"])
            logger.debug("Read configuration from '%s'", file)
        except (ImportError, FileNotFoundError) as e:
            logger.debug("Could not read config file '%s': %s", file, e)
        except KeyError:
            pass
        else:
            if config:
                return config
    return dict()


def update_config(
    pioneer_install_dir: Union[str, Path] = None,
    pioneer_app_dir: Union[str, Path] = None,
    rb5_install_dirname: str = "",
    rb6_install_dirname: str = "",
):
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
    """
    # Read config file
    conf = read_pyrekordbox_configuration()
    if pioneer_install_dir is None and "pioneer-install-dir" in conf:
        pioneer_install_dir = conf["pioneer-install-dir"]
    if pioneer_app_dir is None and "pioneer-app-dir" in conf:
        pioneer_app_dir = conf["pioneer-app-dir"]
    if not rb5_install_dirname and "rekordbox5-install-dirname" in conf:
        rb5_install_dirname = conf["rekordbox5-install-dirname"]
    if not rb6_install_dirname and "rekordbox6-install-dirname" in conf:
        rb6_install_dirname = conf["rekordbox6-install-dirname"]

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
        conf = _get_rb5_config(
            pioneer_install_dir, pioneer_app_dir, rb5_install_dirname
        )
        __config__["rekordbox5"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)

    # Update Rekordbox 6 config
    try:
        conf = _get_rb6_config(
            pioneer_install_dir, pioneer_app_dir, rb6_install_dirname
        )
        __config__["rekordbox6"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)


# Fill the pyrekordbox-configuration
update_config()


def get_config(section: str, key: str = None):
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
    conf = __config__[section]
    if key is None:
        return conf
    return conf[key]


def pformat_config(indent: str = "   ", hw: int = 14, delim: str = " = ") -> str:
    """Returns a formatted string of the pyrekordbox configurations."""
    pioneer = __config__["pioneer"]
    rb5 = __config__["rekordbox5"]
    rb6 = __config__["rekordbox6"]

    lines = ["Pioneer:"]
    lines += [f"{indent}{k + delim:<{hw}} {pioneer[k]}" for k in sorted(pioneer.keys())]
    lines.append("Rekordbox 5:")
    if rb5:
        lines += [f"{indent}{k + delim:<{hw}} {rb5[k]}" for k in sorted(rb5.keys())]
    lines.append("Rekordbox 6:")
    if rb6:
        rb6_keys = [k for k in rb6.keys() if k not in ("dp", "p")]
        lines += [f"{indent}{k + delim:<{hw}} {rb6[k]}" for k in sorted(rb6_keys)]
    return "\n".join(lines)


def show_config() -> None:
    """Prints a formatted string of the pyrekordbox configurations."""
    print(pformat_config())
