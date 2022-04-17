# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

"""Configuration handling for pyrekordbox."""

import os
import logging
from .utils import (
    read_pyrekordbox_configuration,
    get_pioneer_app_dir,
    get_pioneer_install_dir,
    read_rekordbox_settings,
    read_rekordbox6_options,
)

logger = logging.getLogger(__name__)

# Define empty pyrekordbox configuration
__config__ = {
    "pioneer": {
        "app_dir": "",
        "install_dir": "",
    },
    "rekordbox5": {
        "version": "",
        "db_path": "",
        "db_dir": "",
        "app_dir": "",
        "install_dir": "",
    },
    "rekordbox6": {
        "version": "",
        "db_path": "",
        "db_dir": "",
        "app_dir": "",
        "install_dir": "",
        "dp": "",
    },
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


def _get_rb6_config(pioneer_prog_dir: str, pioneer_app_dir: str):
    conf = _get_rb_config(pioneer_prog_dir, pioneer_app_dir, version=6)

    # Read Rekordbox 6 'options.json'
    opts = read_rekordbox6_options(pioneer_app_dir)
    db_path = os.path.normpath(opts["db-path"])
    db_dir = os.path.dirname(db_path)
    assert conf["db_dir"] == db_dir

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"The Rekordbox database '{db_path}' doesn't exist!")

    conf.update({"db_path": db_path, "dp": opts["dp"]})
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
        logging.warning(e)

    # Update Rekordbox 6 config
    try:
        conf = _get_rb6_config(pioneer_install_dir, pioneer_app_dir)
        __config__["rekordbox6"].update(conf)
    except FileNotFoundError as e:
        logging.warning(e)


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
    lines += [f"{indent}{k + delim:<{hw}} {rb5[k]}" for k in sorted(rb5.keys())]
    lines.append("Rekordbox 6:")
    lines += [f"{indent}{k + delim:<{hw}} {rb6[k]}" for k in sorted(rb6.keys())]
    return "\n".join(lines)


def show_config():
    """Prints a formatted string of the pyrekordbox configurations."""
    print(pformat_config())
