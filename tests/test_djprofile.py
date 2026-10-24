# -*- coding: utf-8 -*-
"""The DJ profile a stick carries.

The file is 160 bytes and only two fields are understood, so the tests are about the property that
matters:
a profile that is read and written back unchanged is the same file, and saving a new name touches
the name
field and nothing else.
"""

import struct

import pytest

from pyrekordbox.djprofile import (
    FILE_SIZE,
    ID_OFFSET,
    NAME_LENGTH,
    NAME_OFFSET,
    DjProfile,
    NotAProfileFile,
)


def build_profile(name: str = "Radoslaw Wysocki", identifier: int = 0x2CA16095) -> bytes:
    """A profile as the deck writes it: header bytes, an id, the name field, zero padding."""
    data = bytearray(FILE_SIZE)
    data[0:4] = bytes.fromhex("0061149b")
    data[4:8] = bytes.fromhex("0000019b")
    struct.pack_into(">I", data, ID_OFFSET, identifier)
    field = name.encode("latin-1")
    data[NAME_OFFSET : NAME_OFFSET + NAME_LENGTH] = field.ljust(NAME_LENGTH, b"\x00")
    return bytes(data)


def test_the_name_and_id_are_read():
    profile = DjProfile.from_bytes(build_profile("Radoslaw Wysocki", 0x2CA16095))
    assert profile.name == "Radoslaw Wysocki"
    assert profile.id == 0x2CA16095


def test_a_profile_written_back_is_the_same_file():
    data = build_profile()
    assert DjProfile.from_bytes(data).to_bytes() == data


def test_a_new_name_changes_only_the_name_field():
    data = build_profile("Radoslaw Wysocki")
    profile = DjProfile.from_bytes(data)
    profile.name = "Radek Temp"
    out = profile.to_bytes()

    assert len(out) == FILE_SIZE
    assert out[NAME_OFFSET : NAME_OFFSET + NAME_LENGTH].rstrip(b"\x00") == b"Radek Temp"
    assert out[:NAME_OFFSET] == data[:NAME_OFFSET]
    assert out[NAME_OFFSET + NAME_LENGTH :] == data[NAME_OFFSET + NAME_LENGTH :]


def test_a_file_of_the_wrong_size_is_refused():
    with pytest.raises(NotAProfileFile):
        DjProfile.from_bytes(b"\x00" * (FILE_SIZE - 1))


def test_a_name_that_does_not_fit_is_refused():
    profile = DjProfile.from_bytes(build_profile())
    profile.name = "x" * (NAME_LENGTH + 1)
    with pytest.raises(ValueError):
        profile.to_bytes()


def test_a_profile_saves_and_loads(tmp_path):
    profile = DjProfile.from_bytes(build_profile())
    target = tmp_path / "djprofile.nxs"
    profile.save(target)
    assert DjProfile.load(target).to_bytes() == profile.to_bytes()
