"""Writing a DeviceSQL database back.

The reader refuses a file it cannot explain, so a database that parses is a database whose bytes
are understood. This module turns that model back into bytes: every page, its header, its rows
and the row sets at the end, so a database that is read and written again is the same file byte
for byte.

Two levels are offered. write_file reproduces what was read, which is what a round trip tests.
replace_rows rebuilds a table's pages from new row bytes, which is what a caller needs when it
changes something, and encode_row produces those bytes from the same schemas the reader decodes
them with.
"""

from __future__ import annotations

import struct
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence

from .page import (
    FILE_HEADER_SIZE,
    INDEX_HEAP_START,
    INDEX_TAIL_SIZE,
    PAGE_HEADER_SIZE,
    PAGE_SIZE,
    ROW_START,
    ROWSET_SIZE,
    ROWSET_SLOTS,
    SENTINEL,
    DataHeader,
    Page,
    PageHeader,
    RowSet,
)
from .rows import ROW_SCHEMAS, Field, UnexplainedRow

if TYPE_CHECKING:  # file imports this module, so the type comes second
    from .file import DeviceSQLFile

LONG_SINGLE = 0x40
LONG_UTF16 = 0x90


class RowDoesNotFit(ValueError):
    """A row is larger than the space a page has for rows."""


def encode_string(value: str, form: str = "short") -> bytes:
    """Encode one string the way a row carries it.

    ``form`` comes from a decoded string and is worth keeping: the deck writes a short header for
    short text
    and a four byte header for longer text, and a rewrite that changes the form changes bytes nobody
    asked
    about.
    """
    # A long string takes four header bytes: the marker, a sixteen bit total length that counts
    # those four
    # bytes, and one byte the format does not use. Writing three bytes instead shifts every
    # character by one
    # and the text decodes as its own tail.
    if form == "utf16":
        body = value.encode("utf-16-le")
        return struct.pack("<BHB", LONG_UTF16, len(body) + 4, 0) + body
    if form == "long":
        body = value.encode("latin-1")
        return struct.pack("<BHB", LONG_SINGLE, len(body) + 4, 0) + body
    body = value.encode("latin-1")
    return struct.pack("<B", len(body) * 2 + 3) + body


FIELD_WIDTH = {"u8": 1, "u16": 2, "u32": 4}
FIELD_FORMAT = {"u8": "<B", "u16": "<H", "u32": "<I"}


def _field_bytes(item: Field, value: int) -> bytes:
    """One fixed field, at the width the schema gives it."""
    return struct.pack(FIELD_FORMAT[item.kind], value)


def encode_row(
    file_kind: str,
    table_type: int,
    fields: Dict[str, int],
    strings: Dict[str, str],
    forms: Optional[Dict[str, str]] = None,
) -> bytes:
    """Encode one row from field values and strings, against the table's schema.

    The track row is the only one with an offset table in front of its strings: twenty-one entries
    that say
    where each string starts, counted from the start of the row. Every other table puts its strings
    straight
    after the fixed part.
    """
    schema = ROW_SCHEMAS.get((file_kind, table_type))
    if schema is None:
        raise UnexplainedRow(f"no schema for {file_kind} table type {table_type}")

    forms = forms or {}
    head = bytearray(schema.head)
    for item in schema.fields:
        if item.name not in fields:
            raise UnexplainedRow(f"missing field {item.name} for {file_kind}:{table_type}")
        head[item.offset : item.offset + FIELD_WIDTH[item.kind]] = _field_bytes(
            item, fields[item.name]
        )

    encoded: List[bytes] = []
    for name in schema.strings:
        encoded.append(encode_string(strings.get(name, ""), forms.get(name, "short")))

    if schema.string_offsets is None:
        body = bytes(head) + b"".join(encoded)
    else:
        table_at, count = schema.string_offsets
        if count != len(encoded):
            raise UnexplainedRow(
                f"schema wants {count} string offsets but has {len(encoded)} strings"
            )
        # The offset table sits between the fixed fields and the strings, so the strings start after
        # it and
        # every entry is absolute from the start of the row.
        cursor = table_at + count * 2
        offsets = []
        for item in encoded:
            offsets.append(cursor)
            cursor += len(item)
        body_buffer = bytearray(bytes(head)) + bytearray(count * 2) + b"".join(encoded)
        for index, offset in enumerate(offsets):
            struct.pack_into("<H", body_buffer, table_at + index * 2, offset)
        body = bytes(body_buffer)

    if schema.tail_bytes:
        tail = bytearray(len(schema.tail_bytes))
        for index, name in enumerate(schema.tail_bytes):
            tail[index] = fields.get(name, 0)
        body = body[: -len(schema.tail_bytes)] + bytes(tail)
    return body


def _header_bytes(header: PageHeader) -> bytes:
    """The forty byte page header, field by field."""
    return struct.pack(
        "<6I",
        header.magic,
        header.page_index,
        header.table_type,
        header.next_page,
        header.transaction,
        header.unnamed2,
    ) + struct.pack(
        "<4B2H",
        header.num_rows_small,
        header.unnamed3,
        header.unnamed4,
        header.page_flags,
        header.free_size,
        header.next_heap_write_offset,
    )


def _rowset_bytes(rowsets: Sequence[RowSet]) -> Dict[int, bytes]:
    """Each row set: slots in reverse order, then the four unknown bytes."""
    out = {}
    for rowset in rowsets:
        buf = bytearray(ROWSET_SIZE)
        for slot, position in enumerate(rowset.positions):
            struct.pack_into("<H", buf, (ROWSET_SLOTS - 1 - slot) * 2, position)
        buf[ROWSET_SLOTS * 2 :] = rowset.unknown[:4].ljust(4, b"\x00")
        out[rowset.index] = bytes(buf)
    return out


def write_page(page: Page) -> bytes:
    """Rebuild one page from its model, byte for byte where the reader kept every byte."""
    buf = bytearray(PAGE_SIZE)
    if page.kind == "zero":
        return bytes(buf)

    header = page.header
    assert header is not None
    if page.kind == "file-header":
        buf[0:PAGE_HEADER_SIZE] = _header_bytes(header)
        # The file header's pointer block starts at 28, inside what the page header calls its free
        # space,
        # so the gap bytes are written explicitly rather than taken from the header fields.
        buf[24:FILE_HEADER_SIZE] = b"\x00" * (FILE_HEADER_SIZE - 24)
        at = FILE_HEADER_SIZE
        for pointer in page.tables:
            struct.pack_into(
                "<4I",
                buf,
                at,
                pointer.type,
                pointer.empty_candidate,
                pointer.first_page,
                pointer.last_page,
            )
            at += 16
        return bytes(buf)

    if page.kind == "index":
        buf[0:PAGE_HEADER_SIZE] = _header_bytes(header)
        values = page.index_header or {}
        struct.pack_into(
            "<4H4I2H",
            buf,
            PAGE_HEADER_SIZE,
            values.get("unnamed1", 0x1FFF),
            values.get("unnamed2", 0x1FFF),
            values.get("unnamed3", 0x03EC),
            values.get("nextOffset", 0),
            values.get("pageIndex", header.page_index),
            values.get("nextPage", 0xFFFFFFFF),
            values.get("unnamed5", 0x03FFFFFF),
            values.get("unnamed6", 0),
            values.get("numEntries", len(page.entries)),
            values.get("firstEmptyEntry", 0x1FFF),
        )
        for index, entry in enumerate(page.entries):
            struct.pack_into("<I", buf, INDEX_HEAP_START + index * 4, entry)
        fill_end = PAGE_SIZE - INDEX_TAIL_SIZE
        at = INDEX_HEAP_START + len(page.entries) * 4
        while at < fill_end:
            struct.pack_into("<I", buf, at, SENTINEL)
            at += 4
        return bytes(buf)

    if page.kind == "data":
        buf[0:PAGE_HEADER_SIZE] = _header_bytes(header)
        data_header = page.data_header or DataHeader(0, 0, 0, 0)
        struct.pack_into(
            "<4H",
            buf,
            PAGE_HEADER_SIZE,
            data_header.unnamed5,
            data_header.num_rows_large,
            data_header.unnamed6,
            data_header.unnamed7,
        )
        for row in page.rows:
            at = ROW_START + row.offset
            buf[at : at + len(row.data)] = row.data
        for index, rowset in _rowset_bytes(page.rowsets).items():
            buf[PAGE_SIZE - (index + 1) * ROWSET_SIZE : PAGE_SIZE - index * ROWSET_SIZE] = rowset
        return bytes(buf)

    raise ValueError(f"unknown page kind {page.kind}")


def write_file(database: "DeviceSQLFile") -> bytes:
    """Write every page of a database back, in order."""
    return b"".join(write_page(page) for page in database.pages)


def _rebuild_data_page(page: Page, rows: List[bytes]) -> Page:
    """A data page holding exactly these rows, with offsets, row sets and counters recomputed."""
    header = page.header
    assert header is not None
    rowset_count = max(1, -(-len(rows) // ROWSET_SLOTS)) if rows else 0
    usable = PAGE_SIZE - ROW_START - rowset_count * ROWSET_SIZE
    total = sum(len(row) for row in rows)
    if total > usable:
        raise RowDoesNotFit(f"rows need {total} bytes, a page has {usable}")

    offsets: List[int] = []
    cursor = 0
    for row in rows:
        offsets.append(cursor)
        cursor += len(row)

    positions_by_set: List[List[int]] = [[] for _ in range(rowset_count)]
    for index, offset in enumerate(offsets):
        positions_by_set[index // ROWSET_SLOTS].append(offset)

    rowsets: List[RowSet] = []
    for index, positions in enumerate(positions_by_set):
        padded = positions + [0] * (ROWSET_SLOTS - len(positions))
        unknown = b"\x00\x00\x00\x00"
        if index < len(page.rowsets):
            unknown = page.rowsets[index].unknown[:4]
        rowsets.append(
            RowSet(
                index=index,
                offset=PAGE_SIZE - (index + 1) * ROWSET_SIZE,
                positions=padded,
                unknown=unknown,
            )
        )

    new_header = replace(
        header,
        num_rows_small=len(rows),
        free_size=usable - total,
        next_heap_write_offset=total,
    )
    from .page import Row  # imported here to keep the module import list short

    new_rows = [
        Row(
            offset=offset,
            length=len(row),
            rowset=index // ROWSET_SLOTS,
            slot=index % ROWSET_SLOTS,
            data=row,
        )
        for index, (offset, row) in enumerate(zip(offsets, rows))
    ]
    return replace(page, header=new_header, rows=new_rows, rowsets=rowsets)


def replace_rows(
    database: "DeviceSQLFile", table_type: int, rows: Sequence[bytes]
) -> "DeviceSQLFile":
    """Return the database with one table's rows replaced by these row bytes.

    The rows are packed into the table's existing data pages, greedily and in order. A table
    that needs more room than its pages have raises instead of silently dropping the tail: a
    caller that wants to add rows to a full table has to say so, not discover it in a file that
    opens but is missing a track.
    """
    table = database.tables.get(table_type)
    if table is None:
        raise KeyError(f"no table of type {table_type} in this file")
    pages = [page for page in table.pages if page.kind == "data"]
    if not pages:
        raise ValueError(f"table {table_type} has no data pages to write into")

    capacity = PAGE_SIZE - ROW_START - ROWSET_SIZE
    buckets: List[List[bytes]] = [[]]
    used = 0
    for row in rows:
        if len(row) > capacity:
            raise RowDoesNotFit(f"a row of {len(row)} bytes cannot fit a page of {capacity}")
        if buckets[-1] and used + len(row) > capacity:
            buckets.append([])
            used = 0
        buckets[-1].append(row)
        used += len(row)
    if len(buckets) > len(pages):
        raise RowDoesNotFit(
            f"{len(rows)} rows need {len(buckets)} pages, table {table_type} has {len(pages)}"
        )

    rebuilt = []
    for index, page in enumerate(pages):
        rebuilt.append(_rebuild_data_page(page, buckets[index] if index < len(buckets) else []))

    new_pages = []
    remaining = iter(rebuilt)
    for page in database.pages:
        if page in table.pages and page.kind == "data":
            new_pages.append(next(remaining))
        else:
            new_pages.append(page)

    from .file import DeviceSQLFile, Table

    new_table = Table(type=table.type, pointer=table.pointer, pages=rebuilt)
    return DeviceSQLFile(
        pages=new_pages,
        tables={**database.tables, table_type: new_table},
    )
