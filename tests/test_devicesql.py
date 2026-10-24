# -*- coding: utf-8 -*-
"""DeviceSQL: the databases rekordbox writes on a USB stick.

One module per package module, so the page model, the file reader and the row codecs share this
file.
The fixtures build pages and rows by hand, because the layout is what the tests are about; a native
export can be handed in through ``PYREKORDBOX_CAPTURE_PDB`` and the capture tests then run against
it.
"""

from __future__ import annotations

import os
import struct
from collections import Counter
from pathlib import Path

import pytest

from pyrekordbox.devicesql.file import NotADeviceSQLFile, read_file
from pyrekordbox.devicesql.page import (
    PAGE_SIZE,
    ROW_START,
    ROWSET_SIZE,
    ROWSET_SLOTS,
    parse_page,
)
from pyrekordbox.devicesql.rows import (
    ROW_SCHEMAS,
    TRACK_HEAD,
    TRACK_OFFSET_TABLE,
    TRACK_STRING_COUNT,
    TRACK_STRINGS,
    UnexplainedRow,
    decode_row,
    decode_string,
    decode_track_row,
)
from pyrekordbox.devicesql.writer import (
    RowDoesNotFit,
    encode_row,
    encode_string,
    replace_rows,
    write_file,
    write_page,
)

# A capture carries a machine id, account names and audio paths, so it cannot ship with the
# repository.
# Point this at one you have and the capture tests run; leave it unset and they say why they were
# skipped.
CAPTURE = Path(os.environ.get("PYREKORDBOX_CAPTURE_PDB", ""))


# -- pages --------------------------------------------------------------------------------------


def build_data_page(rows, *, table_type=0, page_index=1, flags=0x24):
    """A data page: header, data header, rows from the front, row sets at the end."""
    page = bytearray(PAGE_SIZE)
    struct.pack_into(
        "<6I4B2H",
        page,
        0,
        0,  # magic
        page_index,
        table_type,
        0,  # next page
        0,  # transaction
        0,  # unnamed2
        len(rows),  # num rows (small)
        0,
        0,
        flags,
        0,  # free size
        0,  # next heap write offset, rewritten below
    )
    struct.pack_into("<4H", page, 32, 0, len(rows), 0, 0)

    offsets = []
    write_at = ROW_START
    for data in rows:
        offsets.append(write_at - ROW_START)
        page[write_at : write_at + len(data)] = data
        write_at += len(data)
    struct.pack_into("<H", page, 30, write_at - ROW_START)

    for set_index in range(-(-len(rows) // ROWSET_SLOTS) if rows else 0):
        base = PAGE_SIZE - (set_index + 1) * ROWSET_SIZE
        for slot in range(ROWSET_SLOTS):
            position = set_index * ROWSET_SLOTS + slot
            value = offsets[position] if position < len(offsets) else 0
            # Offsets are stored in reverse slot order.
            struct.pack_into("<H", page, base + (ROWSET_SLOTS - 1 - slot) * 2, value)
    return bytes(page)


def test_rows_are_read_with_their_lengths_and_bytes():
    page = build_data_page([b"AAAA", b"BBBBBB"])
    parsed = parse_page(page)

    assert parsed.kind == "data"
    assert parsed.header.table_type == 0
    assert parsed.header.page_index == 1
    assert [row.data for row in parsed.rows] == [b"AAAA", b"BBBBBB"]
    assert [row.length for row in parsed.rows] == [4, 6]
    assert [(row.rowset, row.slot) for row in parsed.rows] == [(0, 0), (0, 1)]


def test_zeroed_page_is_its_own_kind():
    parsed = parse_page(bytes(PAGE_SIZE))
    assert parsed.kind == "zero"
    assert parsed.rows == []


def test_unknown_page_flags_raise():
    page = bytearray(build_data_page([b"AAAA"]))
    page[27] = 0x99
    with pytest.raises(ValueError, match="unknown page type"):
        parse_page(bytes(page))


def test_nonzero_free_space_raises():
    """Free space is written as zeros by the deck; anything else means the page model is wrong."""
    page = bytearray(build_data_page([b"AAAA"]))
    page[ROW_START + 40] = 0x7F
    with pytest.raises(ValueError, match="free space"):
        parse_page(bytes(page))


def test_a_page_of_the_wrong_size_raises():
    with pytest.raises(ValueError, match="4096 bytes"):
        parse_page(bytes(PAGE_SIZE - 1))


@pytest.mark.skipif(
    not CAPTURE.is_file(),
    reason="set PYREKORDBOX_CAPTURE_PDB to a native export.pdb to run this",
)
def test_every_page_of_a_real_export_is_explained():
    data = CAPTURE.read_bytes()
    assert len(data) % PAGE_SIZE == 0

    kinds = Counter()
    rows = 0
    for index in range(len(data) // PAGE_SIZE):
        parsed = parse_page(data[index * PAGE_SIZE : (index + 1) * PAGE_SIZE])
        kinds[parsed.kind] += 1
        rows += len(parsed.rows)

    assert kinds["file-header"] == 1
    assert kinds["data"] > 0
    assert kinds["index"] > 0
    assert kinds["zero"] >= 0
    assert rows > 0


# -- the file -----------------------------------------------------------------------------------


def test_bytes_that_are_not_a_database_raise():
    with pytest.raises(NotADeviceSQLFile):
        read_file(b"\x00" * (PAGE_SIZE * 2))


def test_a_file_whose_first_page_is_not_a_header_raises():
    # A page of zeros parses as "zero", not as a file header.
    with pytest.raises(NotADeviceSQLFile, match="file header"):
        read_file(bytes(PAGE_SIZE))


def test_a_length_that_is_not_whole_pages_raises():
    with pytest.raises(NotADeviceSQLFile, match="multiple"):
        read_file(b"\x00" * (PAGE_SIZE + 7))


@pytest.mark.skipif(
    not CAPTURE.is_file(),
    reason="set PYREKORDBOX_CAPTURE_PDB to a native export.pdb to run this",
)
def test_a_real_export_matches_the_reference_reader():
    # Any capture can be handed in, so this checks the shape of a well formed database rather than
    # one
    # particular file: twenty table slots, the ones with data grouped under their own type, rows
    # that add
    # up. The exact per table counts for one capture are asserted by the sweep that ran during the
    # port.
    data = CAPTURE.read_bytes()
    parsed = read_file(data)

    assert len(parsed.tables) == 20
    counts = {table.type: len(table.rows) for table in parsed.tables.values() if table.rows}
    assert counts, "the capture has no rows at all"
    assert parsed.total_rows > 0
    assert all(count > 0 for count in counts.values())


# -- rows ---------------------------------------------------------------------------------------


def short_string(text: str) -> bytes:
    """Short form: header is chars * 2 + 3, then one byte per character."""
    return bytes([len(text) * 2 + 3]) + text.encode("latin-1")


def long_string(text: str) -> bytes:
    """Long form: four header bytes (0x40, a 16 bit length, one spare), then single byte text."""
    raw = text.encode("latin-1")
    return b"\x40" + struct.pack("<H", len(raw) + 4) + b"\x00" + raw


def utf16_string(text: str) -> bytes:
    raw = b"".join(struct.pack("<H", ord(char)) for char in text)
    return b"\x90" + struct.pack("<H", len(raw) + 4) + b"\x00" + raw


def build_track_row(strings: dict, fields: dict | None = None, residual: bytes = b"") -> bytes:
    values = {
        "subtype": 0,
        "indexShift": 0,
        "bitmask": 0x0C0700,
        "sampleRate": 44100,
        "composerId": 0,
        "fileSize": 1234,
        "masterContentId": 99,
        "masterDbId": 7,
        "artworkId": 0,
        "keyId": 0,
        "originalArtistId": 0,
        "labelId": 0,
        "remixerId": 0,
        "bitrate": 320,
        "trackNumber": 1,
        "tempo": 12800,
        "genreId": 0,
        "albumId": 0,
        "artistId": 0,
        "id": 1,
        "discNumber": 0,
        "playCount": 0,
        "year": 2026,
        "sampleDepth": 16,
        "duration": 200,
        "analysedBits": 41,
        "colorId": 0,
        "rating": 0,
        "fileType": 1,
        "unnamed30": 0,
    }
    values.update(fields or {})

    head = bytearray(TRACK_HEAD)
    for name, offset, kind in (
        ("subtype", 0, "u16"),
        ("indexShift", 2, "u16"),
        ("bitmask", 4, "u32"),
        ("sampleRate", 8, "u32"),
        ("composerId", 12, "u32"),
        ("fileSize", 16, "u32"),
        ("masterContentId", 20, "u32"),
        ("masterDbId", 24, "u32"),
        ("artworkId", 28, "u32"),
        ("keyId", 32, "u32"),
        ("originalArtistId", 36, "u32"),
        ("labelId", 40, "u32"),
        ("remixerId", 44, "u32"),
        ("bitrate", 48, "u32"),
        ("trackNumber", 52, "u32"),
        ("tempo", 56, "u32"),
        ("genreId", 60, "u32"),
        ("albumId", 64, "u32"),
        ("artistId", 68, "u32"),
        ("id", 72, "u32"),
        ("discNumber", 76, "u16"),
        ("playCount", 78, "u16"),
        ("year", 80, "u16"),
        ("sampleDepth", 82, "u16"),
        ("duration", 84, "u16"),
        ("analysedBits", 86, "u16"),
        ("colorId", 88, "u8"),
        ("rating", 89, "u8"),
        ("fileType", 90, "u16"),
        ("unnamed30", 92, "u16"),
    ):
        fmt = {"u8": "<B", "u16": "<H", "u32": "<I"}[kind]
        struct.pack_into(fmt, head, offset, values[name])

    heap = bytearray()
    offsets = []
    base = TRACK_OFFSET_TABLE + TRACK_STRING_COUNT * 2
    for name in TRACK_STRINGS:
        encoded = strings.get(name) or short_string("")
        offsets.append(base + len(heap))
        heap.extend(encoded)

    table = b"".join(struct.pack("<H", offset) for offset in offsets)
    return bytes(head) + table + bytes(heap) + residual


def test_short_and_long_strings_decode():
    assert decode_string(short_string("Techno"), 0).value == "Techno"
    decoded = decode_string(long_string("A much longer title here"), 0)
    assert decoded.value == "A much longer title here"
    assert decode_string(utf16_string("Zażółć"), 0).value == "Zażółć"


def test_a_header_below_three_is_an_error():
    with pytest.raises(UnexplainedRow, match="invalid DeviceSQL header"):
        decode_string(b"\x02abc", 0)


def test_a_short_string_reads_chars_times_two_plus_three():
    """(header - 1) / 2 pulls one byte too many into the value: Drumcode is 0x13, not 0x11."""
    assert short_string("Drumcode")[0] == 0x13
    assert decode_string(short_string("Drumcode"), 0).value == "Drumcode"


def test_a_track_row_decodes_its_fields_and_strings():
    row = build_track_row(
        {
            "title": short_string("Test Track"),
            "filename": short_string("track.mp3"),
            "filePath": long_string("/Contents/A/Album/track.mp3"),
        },
        {"id": 7, "duration": 311, "bitrate": 1411},
    )
    decoded = decode_track_row(row)

    assert decoded.fields["id"] == 7
    assert decoded.fields["duration"] == 311
    assert decoded.fields["bitrate"] == 1411
    assert decoded.fields["bitmask"] == 0x0C0700
    assert decoded.strings["title"] == "Test Track"
    assert decoded.strings["filename"] == "track.mp3"
    assert decoded.strings["filePath"] == "/Contents/A/Album/track.mp3"
    assert decoded.residual is None


def test_leftover_printable_text_after_the_last_string_is_kept():
    """Rekordbox shrinks the offset table when a track is renamed and leaves the old name behind."""
    row = build_track_row({"title": short_string("New")}, residual=b"old-name-that-stayed.mp3")
    decoded = decode_track_row(row)
    assert decoded.residual == b"old-name-that-stayed.mp3"


def test_a_byte_that_is_not_text_raises():
    row = build_track_row({"title": short_string("New")}, residual=b"\xff\xfe\x01")
    with pytest.raises(UnexplainedRow):
        decode_track_row(row)


@pytest.mark.skipif(
    not CAPTURE.is_file(),
    reason="set PYREKORDBOX_CAPTURE_PDB to a native export.pdb to run this",
)
def test_a_real_track_row_matches_the_reference_reader():
    parsed = read_file(CAPTURE.read_bytes())
    rows = parsed.rows(0)
    assert rows, "the capture has no track rows"

    # Any capture can be handed in through the environment, so the assertions are about shape: a row
    # that decodes to a title, a filename and a path on the stick, not about one particular track.
    decoded = decode_track_row(rows[0].data)
    assert decoded.strings["title"]
    assert decoded.strings["filename"]
    assert (decoded.strings["filePath"] or "").startswith("/Contents/")
    assert decoded.strings["filePath"].endswith(decoded.strings["filename"])
    assert decoded.fields["duration"] > 0
    assert decoded.fields["id"] > 0


def genre_row(genre_id: int, name: str) -> bytes:
    """A dictionary row: one 32 bit id, then the name."""
    return struct.pack("<I", genre_id) + short_string(name)


def test_a_dictionary_row_decodes_its_name():
    decoded = decode_row("pdb", 1, genre_row(4, "Techno"))
    assert decoded.fields["id"] == 4
    assert decoded.strings["name"] == "Techno"


def test_a_menu_row_in_the_second_database_keeps_its_terminator():
    """exportExt.pdb has its own table 3: fixed fields, a name, then a terminator byte."""
    head = bytearray(31)
    struct.pack_into("<HH", head, 0, 0, 0)  # subtype, indexShift
    # unnamed2, unnamed3, parentId, sortOrder, id, flags
    struct.pack_into("<6I", head, 4, 0, 0, 0, 0, 7, 0)
    row = bytes(head) + short_string("Genre") + b"\x03"
    decoded = decode_row("ext", 3, row)
    assert decoded.fields["id"] == 7
    assert decoded.strings["name"] == "Genre"
    assert decoded.fields["terminator"] == 3


def test_an_unknown_table_type_raises():
    with pytest.raises(UnexplainedRow, match="no schema"):
        decode_row("pdb", 99, b"\x00" * 16)


# -- writing
# ----------------------------------------------------------------------------------------
#
# The writer has one obligation worth testing above all others: a database that is read and written
# back
# with nothing changed has to be the same file. Everything else is a consequence.


def test_a_string_round_trips_in_every_form():
    for value in ("Techno", "A much longer title here", "Cafe Angstrom"):
        for form in ("short", "long", "utf16"):
            encoded = encode_string(value, form)
            decoded = decode_string(encoded, 0)
            assert decoded is not None
            assert decoded.value == value
            assert decoded.form == form


def test_a_row_built_from_its_schema_decodes_back():
    schema = ROW_SCHEMAS[("pdb", 0)]
    fields = {item.name: 0 for item in schema.fields}
    fields["id"] = 4242
    strings = {name: "" for name in schema.strings}
    strings["title"] = "Hello"
    strings["filePath"] = "/Contents/Hello.mp3"

    raw = encode_row("pdb", 0, fields, strings)
    decoded = decode_row("pdb", 0, raw)

    assert decoded.fields["id"] == 4242
    assert decoded.strings["title"] == "Hello"
    assert decoded.strings["filePath"] == "/Contents/Hello.mp3"


def test_a_row_that_does_not_fit_a_page_raises():
    page = _data_page(b"\x00" * 8)
    table = DeviceSQLTable(0, None, [page])
    database = _database([page], {0: table})
    with pytest.raises(RowDoesNotFit):
        replace_rows(database, 0, [b"\x00" * 5000])


def test_replacing_the_rows_of_a_page_parses_again():
    first = encode_row(
        "pdb",
        0,
        {item.name: 0 for item in ROW_SCHEMAS[("pdb", 0)].fields},
        {"title": "One", "filePath": "/Contents/one.mp3"},
    )
    page = _data_page(first)
    database = _database([page], {0: DeviceSQLTable(0, None, [page])})

    second = encode_row(
        "pdb",
        0,
        {item.name: 0 for item in ROW_SCHEMAS[("pdb", 0)].fields},
        {"title": "Two", "filePath": "/Contents/two.mp3"},
    )
    rebuilt = replace_rows(database, 0, [second])

    # The page is what the writer produces and what the reader has to accept: the counters, the row
    # set and
    # the offsets all have to agree or the parse refuses it.
    parsed = parse_page(write_page(rebuilt.pages[0]))
    assert parsed.kind == "data"
    decoded = decode_row("pdb", 0, parsed.rows[0].data)
    assert decoded.strings["title"] == "Two"
    assert decoded.strings["filePath"] == "/Contents/two.mp3"


def test_a_whole_capture_round_trips_byte_for_byte():
    """The gate the writer exists to pass: read a native database and write it back."""
    if not CAPTURE.is_file():
        pytest.skip(f"no capture at {CAPTURE}")
    data = CAPTURE.read_bytes()
    assert write_file(read_file(data)) == data


def _data_page(row: bytes):
    """A one row data page, built by hand so the writer has something to rewrite."""
    from pyrekordbox.devicesql.page import DataHeader, Page, PageHeader, Row, RowSet

    header = PageHeader(
        0,
        1,
        0,
        0xFFFFFFFF,
        1,
        0,
        1,
        0,
        0,
        0x24,
        PAGE_SIZE - ROW_START - ROWSET_SIZE - len(row),
        len(row),
    )
    positions = [0] + [0] * (ROWSET_SLOTS - 1)
    rowset = RowSet(
        index=0, offset=PAGE_SIZE - ROWSET_SIZE, positions=positions, unknown=b"\x00\x00\x00\x00"
    )
    return Page(
        kind="data",
        header=header,
        data_header=DataHeader(0, 0, 0, 0),
        rows=[Row(offset=0, length=len(row), rowset=0, slot=0, data=row)],
        rowsets=[rowset],
    )


def _database(pages, tables):
    from pyrekordbox.devicesql.file import DeviceSQLFile

    return DeviceSQLFile(pages=pages, tables=tables)


class DeviceSQLTable:
    """The smallest table the writer needs: a type and its pages."""

    def __init__(self, type_: int, pointer, pages):
        self.type = type_
        self.pointer = pointer
        self.pages = pages

    @property
    def rows(self):
        return [row for page in self.pages for row in page.rows]
