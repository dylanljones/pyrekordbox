"""Reading a whole DeviceSQL database.

``export.pdb`` and ``exportExt.pdb`` are a file header followed by pages that belong to tables.
The file header names every table and the first and last page of its chain; pages within a chain
point at the next one, and a data page carries that table's rows.

This module walks those chains and returns the rows per table type. It does not decode a row
itself, that is the table's own codec in ``rows``, so a row is handed over as bytes plus the page
and the slot it came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .page import PAGE_SIZE, Page, Row, TablePointer, parse_page


@dataclass
class Table:
    """One table: its pointer from the file header, its pages, and the rows they hold."""

    type: int
    pointer: TablePointer
    pages: List[Page] = field(default_factory=list)

    @property
    def rows(self) -> List[Row]:
        """Every row of this table, page by page, in the order the chain gives."""
        return [row for page in self.pages for row in page.rows]


@dataclass
class DeviceSQLFile:
    pages: List[Page]
    tables: Dict[int, Table]

    def rows(self, table_type: int) -> List[Row]:
        """The rows of one table, by its number.

        Raises ``KeyError`` when the file has no such table, which is the honest answer: an empty
        list would read as "the table is there and empty", and those are two different statements.
        """
        table = self.tables.get(table_type)
        if table is None:
            raise KeyError(f"no table of type {table_type} in this file")
        return table.rows

    @property
    def total_rows(self) -> int:
        """How many rows the whole file holds, across every table."""
        return sum(len(table.rows) for table in self.tables.values())


class NotADeviceSQLFile(ValueError):
    """The bytes do not start with a DeviceSQL file header."""


def read_file(data: bytes) -> DeviceSQLFile:
    """Parse every page and group the data pages by table."""
    if len(data) < PAGE_SIZE or len(data) % PAGE_SIZE != 0:
        raise NotADeviceSQLFile(f"file is {len(data)} bytes, not a multiple of {PAGE_SIZE}")

    pages = [
        parse_page(data[index * PAGE_SIZE : (index + 1) * PAGE_SIZE])
        for index in range(len(data) // PAGE_SIZE)
    ]

    if not pages or pages[0].kind != "file-header":
        raise NotADeviceSQLFile("first page is not a DeviceSQL file header")

    header = pages[0]
    tables: Dict[int, Table] = {}
    for pointer in header.tables:
        tables[pointer.type] = Table(type=pointer.type, pointer=pointer)

    # A page belongs to a table by its own type word; the pointer blocks say which page the chain
    # starts
    # at, which the writer needs and the reader can check.
    for page in pages[1:]:
        if page.kind != "data" or page.header is None:
            continue
        table = tables.get(page.header.table_type)
        if table is None:
            raise NotADeviceSQLFile(
                f"data page {page.header.page_index} belongs to table {page.header.table_type}, "
                "which the file header does not list"
            )
        table.pages.append(page)

    for table in tables.values():
        table.pages.sort(key=lambda page: page.header.page_index if page.header else -1)

    return DeviceSQLFile(pages=pages, tables=tables)
