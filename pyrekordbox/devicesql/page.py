"""Page model for rekordbox DeviceSQL databases (``export.pdb``, ``exportExt.pdb``).

Measured on a native rekordbox 7.2.19 export, not inferred from a description. A page is one of
five things, and ``pageFlags`` decides which:

* **zero** - an allocated page nothing was ever written to (every byte zero)
* **file header** - page 0, recognised by its second word being the page size: magic, page size,
  table count, next unused page, a sequence number, then one 16 byte pointer block per table
* **index** (``0x64``) - page header, index header, index entries, then a heap pre-filled with
  the ``0x1ffffff8`` sentinel and 20 zero bytes
* **data** (``0x24`` and ``0x34``) - page header, 8 byte data header, rows from the front,
  zeroed free space, and the row sets at the end
* anything else raises, because a page nobody can explain is a page that cannot be rebuilt
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Optional

PAGE_SIZE = 4096
PAGE_HEADER_SIZE = 32
DATA_HEADER_SIZE = 8
ROW_START = PAGE_HEADER_SIZE + DATA_HEADER_SIZE
ROWSET_SIZE = 36
ROWSET_SLOTS = 16
INDEX_HEADER_SIZE = 28
INDEX_HEAP_START = PAGE_HEADER_SIZE + INDEX_HEADER_SIZE
INDEX_TAIL_SIZE = 20
SENTINEL = 0x1FFFFFF8

DATA_PAGE_FLAGS = (0x24, 0x34)
INDEX_PAGE_FLAGS = 0x64
FILE_HEADER_SIZE = 28


def _unpack(fmt: str, buf: bytes, offset: int) -> tuple:
    """Unpack a struct, turning a short buffer into a message that says where it ran out."""
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(buf):
        raise ValueError(f"page too short for {fmt} at {offset}")
    return struct.unpack_from(fmt, buf, offset)


def _require_zeros(buf: bytes, start: int, end: int, what: str) -> None:
    """Every byte of a run that the format says is unused has to be zero."""
    if start >= end:
        return
    chunk = buf[start:end]
    if chunk.count(0) != len(chunk):
        first = next(i for i, byte in enumerate(chunk) if byte)
        raise ValueError(f"{what}: nonzero byte at {start + first}")


@dataclass
class PageHeader:
    magic: int
    page_index: int
    table_type: int
    next_page: int
    transaction: int
    unnamed2: int
    num_rows_small: int
    unnamed3: int
    unnamed4: int
    page_flags: int
    free_size: int
    next_heap_write_offset: int

    @classmethod
    def parse(cls, buf: bytes, offset: int = 0) -> "PageHeader":
        """Read the forty byte header every page starts with."""
        return cls(*_unpack("<6I4B2H", buf, offset))


@dataclass
class DataHeader:
    unnamed5: int
    num_rows_large: int
    unnamed6: int
    unnamed7: int

    @classmethod
    def parse(cls, buf: bytes, offset: int = PAGE_HEADER_SIZE) -> "DataHeader":
        """Read the thirty six byte header only a data page carries."""
        return cls(*_unpack("<4H", buf, offset))


@dataclass
class TablePointer:
    """One table's entry in the file header."""

    type: int
    empty_candidate: int
    first_page: int
    last_page: int


@dataclass
class Row:
    """One row of a data page.

    ``offset`` is relative to :data:`ROW_START`, ``rowset`` and ``slot`` say where its offset entry
    lives, and ``data`` is the row body. The length comes from the next row's offset rather than
    from
    the row itself: that is how a page knows where a row ends.
    """

    offset: int
    length: int
    rowset: int
    slot: int
    data: bytes


@dataclass
class RowSet:
    """One of the sixteen row sets a data page keeps at its end.

    The first 32 bytes are sixteen row offsets stored in reverse slot order: the last slot's offset
    comes first. The four bytes after them are unexplained on every page measured so far.
    """

    index: int
    offset: int
    positions: List[int]
    unknown: bytes


@dataclass
class Page:
    kind: str
    length: int = PAGE_SIZE
    header: Optional[PageHeader] = None
    data_header: Optional[DataHeader] = None
    rows: List[Row] = field(default_factory=list)
    rowsets: List[RowSet] = field(default_factory=list)
    tables: List[TablePointer] = field(default_factory=list)
    entries: List[int] = field(default_factory=list)
    index_header: Optional[dict] = None
    free_size: int = 0


def page_rowsets(buf: bytes, num_rows: int) -> List[RowSet]:
    """Split a page into rowsets.

    A rowset is 36 bytes at the end of the page and holds up to sixteen two byte slots, filled from
    the last slot downwards. The rowsets grow backwards from the end of the page, so a page with
    more rows has a second rowset land in front of the first.
    """
    count = -(-num_rows // ROWSET_SLOTS) if num_rows else 0
    sets: List[RowSet] = []
    for index in range(count):
        base = PAGE_SIZE - (index + 1) * ROWSET_SIZE
        positions = [
            _unpack("<H", buf, base + (ROWSET_SLOTS - 1 - slot) * 2)[0]
            for slot in range(ROWSET_SLOTS)
        ]
        sets.append(
            RowSet(
                index=index,
                offset=base,
                positions=positions,
                unknown=buf[base + ROWSET_SLOTS * 2 : base + ROWSET_SIZE],
            )
        )
    return sets


def page_rows(buf: bytes, header: PageHeader, sets: List[RowSet]) -> List[Row]:
    """Read the rows, which are written from the front of the page towards the row sets."""
    offsets = []
    for rowset in sets:
        for slot, offset in enumerate(rowset.positions):
            if rowset.index * ROWSET_SLOTS + slot < header.num_rows_small:
                offsets.append((offset, rowset.index, slot))
    offsets.sort()

    rows: List[Row] = []
    for index, (offset, rowset, slot) in enumerate(offsets):
        start = ROW_START + offset
        end = (
            ROW_START + offsets[index + 1][0]
            if index + 1 < len(offsets)
            else ROW_START + header.next_heap_write_offset
        )
        if start >= end or end > PAGE_SIZE:
            raise ValueError(f"row {index} spans {start}..{end}, outside the page")
        rows.append(
            Row(offset=offset, length=end - start, rowset=rowset, slot=slot, data=buf[start:end])
        )
    return rows


def parse_page(buf: bytes) -> Page:
    """Parse one page. The kind decides what the rest of the page means."""
    if len(buf) < PAGE_SIZE:
        raise ValueError(f"a page is {PAGE_SIZE} bytes, got {len(buf)}")
    page = buf[:PAGE_SIZE]
    if page.count(0) == PAGE_SIZE:
        return Page(kind="zero")

    header = PageHeader.parse(page)

    if header.page_index == PAGE_SIZE:
        tables = []
        for index in range(header.table_type):
            at = FILE_HEADER_SIZE + index * 16
            tables.append(TablePointer(*_unpack("<4I", page, at)))
        _require_zeros(
            page, FILE_HEADER_SIZE + header.table_type * 16, PAGE_SIZE, "file header tail"
        )
        return Page(kind="file-header", header=header, tables=tables)

    if header.page_flags == INDEX_PAGE_FLAGS:
        index_header = dict(
            zip(
                (
                    "unnamed1",
                    "unnamed2",
                    "unnamed3",
                    "nextOffset",
                    "pageIndex",
                    "nextPage",
                    "unnamed5",
                    "unnamed6",
                    "numEntries",
                    "firstEmptyEntry",
                ),
                _unpack("<4H4I2H", page, PAGE_HEADER_SIZE),
            )
        )
        entries = [
            _unpack("<I", page, INDEX_HEAP_START + index * 4)[0]
            for index in range(index_header["numEntries"])
        ]
        heap_start = INDEX_HEAP_START + len(entries) * 4
        heap_end = PAGE_SIZE - INDEX_TAIL_SIZE
        for at in range(heap_start, heap_end, 4):
            if _unpack("<I", page, at)[0] != SENTINEL:
                raise ValueError(f"index page: missing sentinel at {at}")
        _require_zeros(page, heap_end, PAGE_SIZE, "index page tail")
        return Page(kind="index", header=header, entries=entries, index_header=index_header)

    if header.page_flags in DATA_PAGE_FLAGS:
        data_header = DataHeader.parse(page)
        sets = page_rowsets(page, header.num_rows_small)
        rows = page_rows(page, header, sets)
        free_start = ROW_START + header.next_heap_write_offset
        free_end = PAGE_SIZE - len(sets) * ROWSET_SIZE
        _require_zeros(page, free_start, free_end, f"data page {header.page_index} free space")
        return Page(
            kind="data",
            header=header,
            data_header=data_header,
            rows=rows,
            rowsets=sets,
            free_size=free_end - free_start,
        )

    raise ValueError(f"unknown page type: flags=0x{header.page_flags:02x}")
