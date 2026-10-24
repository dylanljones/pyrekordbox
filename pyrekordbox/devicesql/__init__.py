"""DeviceSQL: the databases rekordbox writes on a USB stick.

This is a port of the reader and writer that DjManager carries in JavaScript, field by field
against the same measured captures. Nothing here is derived from a format description: every
constant comes from a page of a native rekordbox 7.2.19 export, and a page the code cannot
explain raises instead of being copied through.

``export.pdb`` and ``exportExt.pdb`` share the layout; the row inside a data page differs per
table and is handled by the table's own codec.
"""

from .file import DeviceSQLFile, NotADeviceSQLFile, Table, read_file
from .page import (
    DATA_HEADER_SIZE,
    INDEX_HEADER_SIZE,
    PAGE_HEADER_SIZE,
    PAGE_SIZE,
    ROW_START,
    ROWSET_SIZE,
    ROWSET_SLOTS,
    SENTINEL,
    DataHeader,
    Page,
    PageHeader,
    Row,
    RowSet,
    TablePointer,
    page_rows,
    page_rowsets,
    parse_page,
)
from .rows import (
    ROW_SCHEMAS,
    DecodedString,
    Field,
    RowData,
    RowSchema,
    UnexplainedRow,
    decode_row,
    decode_string,
    decode_track_row,
)
from .writer import (
    RowDoesNotFit,
    encode_row,
    encode_string,
    replace_rows,
    write_file,
    write_page,
)

__all__ = [
    "ROW_SCHEMAS",
    "DecodedString",
    "Field",
    "RowData",
    "RowSchema",
    "UnexplainedRow",
    "decode_row",
    "decode_string",
    "decode_track_row",
    "RowDoesNotFit",
    "encode_row",
    "encode_string",
    "replace_rows",
    "write_file",
    "write_page",
    "DeviceSQLFile",
    "NotADeviceSQLFile",
    "Table",
    "read_file",
    "DATA_HEADER_SIZE",
    "DataHeader",
    "INDEX_HEADER_SIZE",
    "PAGE_HEADER_SIZE",
    "PAGE_SIZE",
    "ROW_START",
    "ROWSET_SIZE",
    "ROWSET_SLOTS",
    "SENTINEL",
    "Page",
    "PageHeader",
    "Row",
    "RowSet",
    "TablePointer",
    "page_rows",
    "page_rowsets",
    "parse_page",
]
