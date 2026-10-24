"""The DJ profile a stick carries in ``djprofile.nxs``.

The file is 160 bytes and this module handles all of it: four header words nobody has explained, a
four byte
id at offset 0x1c that the deck writes once and then carries along, and the player name as a fixed
32 byte
field at 0x20. Everything else is zero.

A profile is small enough that the honest thing is to keep the bytes. The reader keeps the field it
understands, the writer puts it back where it came from and leaves the rest exactly as it was, so
saving a
profile never changes a byte the module does not own.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

FILE_SIZE = 160
NAME_OFFSET = 0x20
NAME_LENGTH = 32
ID_OFFSET = 0x1C
ID_LENGTH = 4


class NotAProfileFile(ValueError):
    """The bytes are not the 160 byte profile a stick carries."""


@dataclass
class DjProfile:
    """The player name and id from a ``djprofile.nxs``, with the rest of the file kept as it was."""

    name: str
    id: int
    raw: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "DjProfile":
        """Read a profile, keeping every byte of it."""
        if len(data) != FILE_SIZE:
            raise NotAProfileFile(f"a profile is {FILE_SIZE} bytes, got {len(data)}")
        field = data[NAME_OFFSET : NAME_OFFSET + NAME_LENGTH]
        name = field.split(b"\x00", 1)[0].decode("latin-1")
        identifier = int.from_bytes(data[ID_OFFSET : ID_OFFSET + ID_LENGTH], "big")
        return cls(name=name, id=identifier, raw=data)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "DjProfile":
        """Read a profile from disk."""
        return cls.from_bytes(Path(path).read_bytes())

    def to_bytes(self) -> bytes:
        """The file again: the name written into its field, every other byte unchanged."""
        field = self.name.encode("latin-1")
        if len(field) > NAME_LENGTH:
            raise ValueError(f"a name of {len(field)} bytes does not fit {NAME_LENGTH}")
        out = bytearray(self.raw)
        out[NAME_OFFSET : NAME_OFFSET + NAME_LENGTH] = field.ljust(NAME_LENGTH, b"\x00")
        return bytes(out)

    def save(self, path: Union[str, Path]) -> None:
        """Write the profile to disk."""
        Path(path).write_bytes(self.to_bytes())
