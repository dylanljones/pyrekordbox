# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-10-02

import pytest
import json
from pathlib import Path
from pyrekordbox.config import update_config, get_config

RB_SETTING = """<?xml version="1.0" encoding="UTF-8"?>
<PROPERTIES><VALUE name="masterDbDirectory" val="{db_dir}"/></PROPERTIES>
"""

RB_OPTIONS = {"options": [["db-path", ""]]}


def mock_rekordbox_settings_file(pioneer_app_dir, rb_app_dir):
    db_dir = pioneer_app_dir / "rekordbox"
    text = RB_SETTING.format(db_dir=db_dir)
    file = rb_app_dir / "rekordbox3.settings"
    file.write_text(text)


def mock_rekordbox_options_file(agent_storage_dir, db_path):
    file = agent_storage_dir / "options.json"
    options = RB_OPTIONS.copy()
    options["options"][0][1] = str(db_path)
    with open(file, "w") as fp:
        json.dump(options, fp)


@pytest.fixture(scope="session")
def pioneer_app_dir(tmp_path_factory):
    root = tmp_path_factory.mktemp("Pioneer")
    rb_dir = root / "rekordbox"
    rb6_dir = root / "rekordbox6"
    agent_storage_dir = root / "rekordboxAgent" / "storage"
    rb_dir.mkdir(parents=True)
    rb6_dir.mkdir(parents=True)
    agent_storage_dir.mkdir(parents=True)

    # Mock `rekordbox3.settings` files
    mock_rekordbox_settings_file(root, rb_dir)
    mock_rekordbox_settings_file(root, rb6_dir)

    # Mock database files
    rb5_db = rb_dir / "datafile.edb"
    rb6_db = rb_dir / "master.db"
    rb5_db.touch()
    rb6_db.touch()

    # Mock `options.json` file (RBv6)
    mock_rekordbox_options_file(agent_storage_dir, rb6_db)

    return root


@pytest.fixture(scope="session")
def pioneer_install_dir(tmp_path_factory):
    root = tmp_path_factory.mktemp("Pioneer")
    rb5_dir = root / "rekordbox 5.1.1"
    rb6_dir = root / "rekordbox 6.1.1"
    rb5_dir_alt = root / "rekordbox 5.1.2"
    rb6_dir_alt = root / "rekordbox 6.1.2"

    rb5_dir.mkdir(parents=True)
    rb6_dir.mkdir(parents=True)
    rb5_dir_alt.mkdir(parents=True)
    rb6_dir_alt.mkdir(parents=True)
    return root


def test_pioneer_config(pioneer_install_dir, pioneer_app_dir):
    update_config(pioneer_install_dir, pioneer_app_dir)
    install_dir = get_config("pioneer", "install_dir")
    app_dir = get_config("pioneer", "app_dir")

    assert isinstance(install_dir, Path)
    assert isinstance(app_dir, Path)
    assert install_dir == pioneer_install_dir
    assert app_dir == pioneer_app_dir


def test_rb5_config(pioneer_install_dir, pioneer_app_dir):
    update_config(pioneer_install_dir, pioneer_app_dir)
    expected_version = "5.1.2"

    app_dir = get_config("rekordbox5", "app_dir")
    install_dir = get_config("rekordbox5", "install_dir")
    db_dir = get_config("rekordbox5", "db_dir")
    db_path = get_config("rekordbox5", "db_path")
    version = get_config("rekordbox5", "version")

    assert isinstance(install_dir, Path)
    assert isinstance(app_dir, Path)
    assert isinstance(db_dir, Path)
    assert isinstance(db_path, Path)
    assert install_dir == (pioneer_install_dir / f"rekordbox {expected_version}")
    assert app_dir == (pioneer_app_dir / "rekordbox")
    assert db_dir == (pioneer_app_dir / "rekordbox")
    assert db_path == (pioneer_app_dir / "rekordbox" / "datafile.edb")
    assert version == expected_version


def test_rb6_config(pioneer_install_dir, pioneer_app_dir):
    update_config(pioneer_install_dir, pioneer_app_dir)
    expected_version = "6.1.2"

    app_dir = get_config("rekordbox6", "app_dir")
    install_dir = get_config("rekordbox6", "install_dir")
    db_dir = get_config("rekordbox6", "db_dir")
    db_path = get_config("rekordbox6", "db_path")
    version = get_config("rekordbox6", "version")

    assert isinstance(install_dir, Path)
    assert isinstance(app_dir, Path)
    assert isinstance(db_dir, Path)
    assert isinstance(db_path, Path)
    assert install_dir == (pioneer_install_dir / f"rekordbox {expected_version}")
    assert app_dir == (pioneer_app_dir / "rekordbox6")
    assert db_dir == (pioneer_app_dir / "rekordbox")
    assert db_path == (pioneer_app_dir / "rekordbox" / "master.db")
    assert version == expected_version


def test_rb5_config_alt(pioneer_install_dir, pioneer_app_dir):
    # test default: latest version
    update_config(pioneer_install_dir, pioneer_app_dir)
    expected_version = "5.1.2"

    app_dir = get_config("rekordbox5", "app_dir")
    install_dir = get_config("rekordbox5", "install_dir")
    version = get_config("rekordbox5", "version")
    assert install_dir == (pioneer_install_dir / f"rekordbox {expected_version}")
    assert app_dir == (pioneer_app_dir / "rekordbox")
    assert version == expected_version

    # test alternative version
    update_config(
        pioneer_install_dir, pioneer_app_dir, rb5_install_dirname="rekordbox 5.1.1"
    )
    expected_version = "5.1.1"

    app_dir = get_config("rekordbox5", "app_dir")
    install_dir = get_config("rekordbox5", "install_dir")
    version = get_config("rekordbox5", "version")
    assert install_dir == (pioneer_install_dir / f"rekordbox {expected_version}")
    assert app_dir == (pioneer_app_dir / "rekordbox")
    assert version == expected_version


def test_rb6_config_alt(pioneer_install_dir, pioneer_app_dir):
    # test default: latest version
    update_config(pioneer_install_dir, pioneer_app_dir)
    expected_version = "6.1.2"

    app_dir = get_config("rekordbox6", "app_dir")
    install_dir = get_config("rekordbox6", "install_dir")
    version = get_config("rekordbox6", "version")
    assert install_dir == (pioneer_install_dir / f"rekordbox {expected_version}")
    assert app_dir == (pioneer_app_dir / "rekordbox6")
    assert version == expected_version

    # test alternative version
    update_config(
        pioneer_install_dir, pioneer_app_dir, rb6_install_dirname="rekordbox 6.1.1"
    )
    expected_version = "6.1.1"

    app_dir = get_config("rekordbox6", "app_dir")
    install_dir = get_config("rekordbox6", "install_dir")
    version = get_config("rekordbox6", "version")
    assert install_dir == (pioneer_install_dir / f"rekordbox {expected_version}")
    assert app_dir == (pioneer_app_dir / "rekordbox6")
    assert version == expected_version
