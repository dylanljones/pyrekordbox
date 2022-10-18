# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

from pyrekordbox import utils


def test_read_configuration():
    config = utils.read_pyrekordbox_configuration()
    assert config["pioneer-install-dir"] == r"C:/Program Files/Pioneer"
    assert config["pioneer-app-dir"] == r"C:/Users/user/AppData/Roaming/Pioneer"
