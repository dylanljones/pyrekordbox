# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
from pyrekordbox import Rekordbox6Database, open_rekordbox_database

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")
UNLOCKED = os.path.join(TEST_ROOT, "rekordbox 6", "master_unlocked.db")

db = Rekordbox6Database(UNLOCKED, unlock=False)


def test_open_rekordbox_database():
    con = open_rekordbox_database(UNLOCKED, unlock=False)
    con.execute("SELECT name FROM sqlite_master WHERE type='table';")
