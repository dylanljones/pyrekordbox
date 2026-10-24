"""Row codecs: how bytes inside a data page turn into fields.

One schema per table type. A schema says where the fixed fields sit, where the strings start,
and what the strings are called; a row is decoded by walking the fields and then the strings in
order.

The track row is the only one with an offset table in front of its strings: twenty-one entries,
because a renamed track keeps a shorter table and the old bytes stay behind it. Every other
table puts its strings straight after the fixed part.

A row that holds a byte this code cannot explain raises. Copying it through would make the
writer produce a row nobody understands, and the point of the port is that the reader and the
writer agree about what every byte means.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional

TRACK_HEAD = 94
TRACK_OFFSET_TABLE = 94
TRACK_STRING_COUNT = 21


@dataclass
class DecodedString:
    value: str
    form: str  # 'short', 'long', 'utf16'
    size: int


@dataclass
class Field:
    name: str
    offset: int
    kind: str  # 'u8', 'u16', 'u32'


@dataclass
class RowSchema:
    table: str
    head: int
    fields: List[Field] = field(default_factory=list)
    strings: List[str] = field(default_factory=list)
    # Singles after the strings, as in the tag rows, which end with a terminator byte.
    tail_bytes: List[str] = field(default_factory=list)
    # Only the track row has one: (offset of the table, entries).
    string_offsets: Optional[tuple] = None


@dataclass
class RowData:
    fields: Dict[str, int]
    strings: Dict[str, Optional[str]]
    forms: Dict[str, str]
    residual: Optional[bytes]


class UnexplainedRow(ValueError):
    """A row holds a byte the codec does not describe."""


def decode_string(buf: bytes, offset: int) -> Optional[DecodedString]:
    """Decode one DeviceSQL string as a row carries it.

    Two headers mean a long string: ``0x40`` for single byte text and ``0x90`` for UTF-16LE. Both
    hold a
    16 bit total length and take four header bytes, so the text is ``total - 4`` bytes starting four
    in.

    Everything else is a short string whose header is ``chars * 2 + 3``. Reading ``(header - 1) /
    2``
    instead pulls one byte too many into the value: measured on ``Techno`` (``0x0f``) and
    ``Drumcode``
    (``0x13``).

    Row strings and dictionary strings do not share this decoder: a dictionary entry uses ``0x80``
    for
    UTF-16 and puts the length in the low bits of the first byte, not in a 16 bit field. The two
    look
    interchangeable and are not - using the dictionary decoder here turned
    ``/Contents/UnknownArtist/...`` into ``ntents/UnknownArtist/...``.
    """
    if offset >= len(buf):
        return None
    header = buf[offset]

    if header in (0x40, 0x90):
        total = struct.unpack_from("<H", buf, offset + 1)[0]
        data_bytes = total - 4
        start = offset + 4
        if header == 0x40:
            return DecodedString(buf[start : start + data_bytes].decode("latin-1"), "long", total)
        units = [
            struct.unpack_from("<H", buf, start + index)[0] for index in range(0, data_bytes, 2)
        ]
        return DecodedString("".join(chr(unit) for unit in units), "utf16", total)

    if header < 3:
        raise UnexplainedRow(f"invalid DeviceSQL header {header} at {offset}")

    length = (header - 3) / 2
    if length != int(length):
        raise UnexplainedRow(f"odd DeviceSQL length at {offset}")
    length = int(length)
    text = buf[offset + 1 : offset + 1 + length].decode("latin-1")
    return DecodedString(text, "short", 1 + length)


def _f(name: str, offset: int, kind: str) -> Field:
    """Shorthand for the declarations below, so a schema reads as a table of offsets."""
    return Field(name=name, offset=offset, kind=kind)


# Measured field by field on a native rekordbox 7.2.19 export. Two of the track words were mistaken
# for
# hashes and gains for a long time: index 20 is the per track id the library keeps as
# content.masterContentId, and index 24 read as one 32 bit word is the id of the database that wrote
# the
# row.
TRACK_STRINGS = [
    "isrc",
    "composer",
    "num1",
    "num2",
    "unknownString4",
    "message",
    "kuvoPublic",
    "autoloadHotcues",
    "unknownString5",
    "unknownString6",
    "dateAdded",
    "releaseDate",
    "mixName",
    "unknownString7",
    "analyzePath",
    "analyzeDate",
    "comment",
    "title",
    "unknownString8",
    "filename",
    "filePath",
]

ROW_SCHEMAS: Dict[tuple, RowSchema] = {
    ("pdb", 0): RowSchema(
        table="tracks",
        head=TRACK_HEAD,
        fields=[
            _f("subtype", 0, "u16"),
            _f("indexShift", 2, "u16"),
            _f("bitmask", 4, "u32"),
            _f("sampleRate", 8, "u32"),
            _f("composerId", 12, "u32"),
            _f("fileSize", 16, "u32"),
            _f("masterContentId", 20, "u32"),
            _f("masterDbId", 24, "u32"),
            _f("artworkId", 28, "u32"),
            _f("keyId", 32, "u32"),
            _f("originalArtistId", 36, "u32"),
            _f("labelId", 40, "u32"),
            _f("remixerId", 44, "u32"),
            _f("bitrate", 48, "u32"),
            _f("trackNumber", 52, "u32"),
            _f("tempo", 56, "u32"),
            _f("genreId", 60, "u32"),
            _f("albumId", 64, "u32"),
            _f("artistId", 68, "u32"),
            _f("id", 72, "u32"),
            _f("discNumber", 76, "u16"),
            _f("playCount", 78, "u16"),
            _f("year", 80, "u16"),
            _f("sampleDepth", 82, "u16"),
            _f("duration", 84, "u16"),
            _f("analysedBits", 86, "u16"),
            _f("colorId", 88, "u8"),
            _f("rating", 89, "u8"),
            _f("fileType", 90, "u16"),
            _f("unnamed30", 92, "u16"),
        ],
        strings=TRACK_STRINGS,
        string_offsets=(TRACK_OFFSET_TABLE, TRACK_STRING_COUNT),
    ),
    ("pdb", 1): RowSchema(table="genres", head=4, fields=[_f("id", 0, "u32")], strings=["name"]),
    ("pdb", 2): RowSchema(
        table="artists",
        head=10,
        fields=[
            _f("subtype", 0, "u16"),
            _f("indexShift", 2, "u16"),
            _f("id", 4, "u32"),
            _f("unnamed3", 8, "u8"),
            _f("ofsNameNear", 9, "u8"),
        ],
        strings=["name"],
    ),
    ("pdb", 3): RowSchema(
        table="albums",
        head=22,
        fields=[
            _f("subtype", 0, "u16"),
            _f("indexShift", 2, "u16"),
            _f("unnamed2", 4, "u32"),
            _f("artistId", 8, "u32"),
            _f("id", 12, "u32"),
            _f("unnamed3", 16, "u32"),
            _f("unnamed4", 20, "u8"),
            _f("ofsNameNear", 21, "u8"),
        ],
        strings=["name"],
    ),
    ("pdb", 4): RowSchema(table="labels", head=4, fields=[_f("id", 0, "u32")], strings=["name"]),
    ("pdb", 5): RowSchema(
        table="keys",
        head=8,
        fields=[
            _f("smallId", 0, "u16"),
            _f("indexShift", 2, "u16"),
            _f("id", 4, "u32"),
        ],
        strings=["name"],
    ),
    ("pdb", 7): RowSchema(
        table="playlistTree",
        head=20,
        fields=[
            _f("parentId", 0, "u32"),
            _f("unnamed1", 4, "u32"),
            _f("sortOrder", 8, "u32"),
            _f("id", 12, "u32"),
            _f("rawIsFolder", 16, "u32"),
        ],
        strings=["name"],
    ),
    ("pdb", 8): RowSchema(
        table="playlistEntries",
        head=12,
        fields=[
            _f("entryIndex", 0, "u32"),
            _f("trackId", 4, "u32"),
            _f("playlistId", 8, "u32"),
        ],
    ),
    ("pdb", 13): RowSchema(table="artwork", head=4, fields=[_f("id", 0, "u32")], strings=["path"]),
    # exportExt.pdb keeps the tag tree in table 3 and one row in table 7. They are not the same
    # tables as export.pdb uses: a tag row ends with a terminator byte after its name, and table 7
    # holds the MyTag master id at +24 with five empty text fields behind it. The tree is what the
    # deck shows under My Tags: rows without a parent are categories, the rest are the tags in
    # them.
    ("ext", 3): RowSchema(
        table="tag",
        head=31,
        fields=[
            _f("subtype", 0, "u16"),
            _f("indexShift", 2, "u16"),
            _f("unnamed2", 4, "u32"),
            _f("unnamed3", 8, "u32"),
            _f("parentId", 12, "u32"),
            _f("sortOrder", 16, "u32"),
            _f("id", 20, "u32"),
            _f("flags", 24, "u32"),
            _f("unnamed7", 28, "u8"),
            _f("nameOffset", 29, "u8"),
            _f("nameEnd", 30, "u8"),
        ],
        strings=["name"],
        tail_bytes=["terminator"],
    ),
    ("ext", 7): RowSchema(
        table="exportExtType7",
        head=34,
        fields=[
            _f("subtype", 0, "u16"),
            _f("indexShift", 2, "u16"),
            _f("reserved2", 4, "u32"),
            _f("reserved3", 8, "u32"),
            _f("reserved4", 12, "u32"),
            _f("reserved5", 16, "u32"),
            _f("reserved6", 20, "u32"),
            _f("myTagMasterDbId", 24, "u32"),
            _f("stringMarker", 28, "u8"),
            _f("text1Offset", 29, "u8"),
            _f("text2Offset", 30, "u8"),
            _f("text3Offset", 31, "u8"),
            _f("text4Offset", 32, "u8"),
            _f("text5Offset", 33, "u8"),
        ],
        strings=["text1", "text2", "text3", "text4", "text5"],
    ),
}


def _read_field(buf: bytes, item: Field) -> int:
    """Read one declared field, little endian, at the width the schema gives it."""
    if item.kind == "u8":
        return buf[item.offset]
    if item.kind == "u16":
        return struct.unpack_from("<H", buf, item.offset)[0]
    return struct.unpack_from("<I", buf, item.offset)[0]


def _check_residual(buf: bytes, cursor: int) -> Optional[bytes]:
    """Everything after the last field must be zero padding or leftover printable text.

    Rekordbox shrinks the offset table when a track is renamed but leaves the longer old filename in
    place, so a tail of readable text is expected. Anything else means this codec is missing a
    field, and
    that has to fail loudly.
    """
    residual_start = None
    run_start = cursor
    index = cursor
    while index < len(buf):
        byte = buf[index]
        if byte == 0:
            index += 1
            run_start = index
            continue
        if 0x20 <= byte <= 0x7E:
            if residual_start is None:
                residual_start = index
            index += 1
            continue
        decoded = decode_string(buf, index)
        if decoded is not None and all(0x20 <= ord(char) <= 0x7E for char in decoded.value):
            index += decoded.size
            continue
        raise UnexplainedRow(
            f"byte 0x{byte:02x} at {index} is neither zero, printable text nor an encoded string "
            f"(run started at {run_start})"
        )
    return buf[residual_start:] if residual_start is not None else None


def decode_row(file_kind: str, table_type: int, buf: bytes) -> RowData:
    """Decode one row of the given table type in the given database."""
    schema = ROW_SCHEMAS.get((file_kind, table_type))
    if schema is None:
        raise UnexplainedRow(f"no schema for {file_kind} table type {table_type}")

    values = {item.name: _read_field(buf, item) for item in schema.fields}

    offsets = None
    cursor = schema.head
    if schema.string_offsets is not None:
        table_at, count = schema.string_offsets
        offsets = [struct.unpack_from("<H", buf, table_at + index * 2)[0] for index in range(count)]
        cursor = table_at + count * 2

    strings: Dict[str, Optional[str]] = {}
    forms: Dict[str, str] = {}
    for position, name in enumerate(schema.strings):
        at = offsets[position] if offsets is not None else cursor
        decoded = decode_string(buf, at)
        if decoded is None:
            strings[name] = None
            continue
        strings[name] = decoded.value
        forms[name] = decoded.form
        cursor = at + decoded.size

    for name in schema.tail_bytes:
        values[name] = buf[cursor]
        cursor += 1

    return RowData(
        fields=values,
        strings=strings,
        forms=forms,
        residual=_check_residual(buf, cursor),
    )


def decode_track_row(buf: bytes) -> RowData:
    """Decode one track row. Kept as a name because it is the one most callers want."""
    return decode_row("pdb", 0, buf)
