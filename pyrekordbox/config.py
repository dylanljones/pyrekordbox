# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""Configuration handling for pyrekordbox."""

import os
import re
import logging
import base64
import blowfish
from .utils import (
    read_pyrekordbox_configuration,
    get_pioneer_app_dir,
    get_pioneer_install_dir,
    read_rekordbox_settings,
    read_rekordbox6_options,
    read_rekordbox6_asar,
)

logger = logging.getLogger(__name__)

# Cache file for pyrekordbox data
_cache_file_version = 2
_cache_file = os.path.join(os.path.dirname(__file__), "rb.cache")

# Define empty pyrekordbox configuration
__config__ = {
    "pioneer": {
        "app_dir": "",
        "install_dir": "",
    },
    "rekordbox5": {},
    "rekordbox6": {},
}


def _get_rb_config(pioneer_prog_dir: str, pioneer_app_dir: str, version: int):
    # Get latest Rekordbox installation directory for major release `version`
    # -----------------------------------------------------------------------

    # Find all 'V.x.x' version strings in dir names
    versions = list()
    for name in os.listdir(pioneer_prog_dir):
        if name.startswith("rekordbox"):
            ver_str = name.replace("rekordbox", "").strip()
            if ver_str.startswith(str(version)):
                versions.append(ver_str)

    # Get latest 'V.x.x' version string and assure there is one
    versions.sort(key=lambda s: list(map(int, s.split("."))))
    try:
        rb_version = versions[-1]
    except IndexError:
        raise FileNotFoundError(
            f"No Rekordbox {version} folder found in {pioneer_prog_dir}"
        )

    # Find Rekordbox installation directory path
    rb_prog_dir = os.path.join(pioneer_prog_dir, f"rekordbox {rb_version}")
    # Check installation directory
    if not os.path.exists(rb_prog_dir):
        raise FileNotFoundError(f"The directory '{rb_prog_dir}' doesn't exist!")

    logger.debug("Found Rekordbox %s install-dir: %s", version, rb_prog_dir)

    # Get Rekordbox application directory path for major release `version`
    # -------------------------------------------------------------------

    name = "rekordbox6" if version == 6 else "rekordbox"
    rb_app_dir = os.path.join(pioneer_app_dir, name)
    if not os.path.exists(rb_app_dir):
        raise FileNotFoundError(f"The directory '{rb_app_dir}' doesn't exist!")

    logger.debug("Found Rekordbox %s app-dir: %s", version, rb_app_dir)

    # Get Rekordbox database locations for major release `version`
    # ------------------------------------------------------------

    settings = read_rekordbox_settings(rb_app_dir)

    db_dir = os.path.normpath(settings["masterDbDirectory"])
    db_filename = "master.db" if version == 6 else "datafile.edb"
    db_path = os.path.join(db_dir, db_filename)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"The Rekordbox database '{db_path}' doesn't exist!")

    conf = {
        "version": rb_version,
        "install_dir": rb_prog_dir,
        "app_dir": rb_app_dir,
        "db_dir": db_dir,
    }
    return conf


def _get_rb5_config(pioneer_prog_dir: str, pioneer_app_dir: str):
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, version=5)

    # RB5 database is called 'datafile.edb'
    db_path = os.path.join(conf["db_dir"], "datafile.edb")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"The Rekordbox database '{db_path}' doesn't exist!")

    conf.update({"db_path": db_path})
    return conf


def _extract_pw(pioneer_install_dir: str):
    asar_data = read_rekordbox6_asar(pioneer_install_dir)
    match_result = re.search('pass: ".(.*?)"', asar_data)
    if match_result is None:
        logging.warning("Incompatible rekordbox 6 database: Could not retrieve db-key.")
        pw = ""
    else:
        match = match_result.group(0)
        pw = match.replace("pass: ", "").strip('"')
    return pw


def write_db6_key_cache(key: str) -> None:
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


def _get_rb6_config(pioneer_prog_dir: str, pioneer_app_dir: str):
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, version=6)

    # Read Rekordbox 6 'options.json'
    opts = read_rekordbox6_options(pioneer_app_dir)
    db_path = os.path.normpath(opts["db-path"])
    db_dir = os.path.dirname(db_path)
    assert conf["db_dir"] == db_dir
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"The Rekordbox database '{db_path}' doesn't exist!")

    conf["db_path"] = db_path
    cache_version = 0
    pw, dp = "", ""
    if os.path.exists(_cache_file):
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

    if cache_version < _cache_file_version:
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


def update_config(pioneer_install_dir="", pioneer_app_dir=""):
    """Update the pyrekordbox configuration.

    This method scans the system for the Rekordbox installation and application data
    directories and extracts the reuired file locations. For this the default Pioneer
    directories (installation and application data) are used. If the method fails to
    find the directories they can be supplied as parameters. If no Rekordbox
    installation is found the fileds are left unchanged.
    On import configuration with the default locations is loaded.

    Parameters
    ----------
    pioneer_install_dir : str, optional
        The path to the Pioneer installation directory. This is where the program files
        of Pioneer applications are stored. By default, the normal location of Pioneer
        programs is used.
    pioneer_app_dir : str, optional
        The path to the Pioneer application directory. This is where the application
        user data of Pioneer programs is stored. By default, the normal location of
        the Pioneer application data is used.
    """
    conf = read_pyrekordbox_configuration()
    if not pioneer_install_dir and "pioneer-install-dir" in conf:
        pioneer_install_dir = conf["pioneer-install-dir"]
    if not pioneer_app_dir and "pioneer-app-dir" in conf:
        pioneer_app_dir = conf["pioneer-app-dir"]

    try:
        # Pioneer installation directory
        pioneer_install_dir = get_pioneer_install_dir(pioneer_install_dir)
        __config__["pioneer"]["install_dir"] = pioneer_install_dir
    except FileNotFoundError as e:
        logger.warning(e)
        return

    try:
        # Pioneer application data directory
        pioneer_app_dir = get_pioneer_app_dir(pioneer_app_dir)
        __config__["pioneer"]["app_dir"] = pioneer_app_dir
    except FileNotFoundError as e:
        logger.warning(e)
        return

    # Update Rekordbox 5 config
    try:
        conf = _get_rb5_config(pioneer_install_dir, pioneer_app_dir)
        __config__["rekordbox5"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)

    # Update Rekordbox 6 config
    try:
        conf = _get_rb6_config(pioneer_install_dir, pioneer_app_dir)
        __config__["rekordbox6"].update(conf)
    except FileNotFoundError as e:
        logger.info(e)


# Fill the pyrekordbox-configuration
update_config()


def get_config(section, key=None):
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
    data : str or dict
        The data of a section or a specific configuration value.
    """
    conf = __config__[section]
    if key is None:
        return conf
    return conf[key]


def pformat_config(indent="   ", hw=14, delim=" = "):
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


def show_config():
    """Prints a formatted string of the pyrekordbox configurations."""
    print(pformat_config())
