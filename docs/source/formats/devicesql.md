# DeviceSQL Database Format

A USB stick exported by Rekordbox carries two databases that the decks read without a computer:

- `PIONEER/rekordbox/export.pdb` holds the tracks, the dictionaries behind them, the playlists and the
  artwork list.
- `PIONEER/rekordbox/exportExt.pdb` holds the tag tree the deck shows under My Tags, and the row that
  carries the MyTag master id.

Both are the same file format, called DeviceSQL, and both are read by {mod}`pyrekordbox.devicesql`.

```{admonition} Table numbers are per database
The two files do not agree on what a table number means. Table `3` is albums in `export.pdb` and the
tag tree in `exportExt.pdb`; table `7` is the playlist tree in `export.pdb` and a single row in
`exportExt.pdb`. A codec is therefore chosen by database and table, never by table alone.
```

## File structure

The file is a whole number of 4096 byte pages. Page `0` is the file header and lists every table:

| Field           | Type | Meaning                                   |
|-----------------|------|-------------------------------------------|
| `type`          | u32  | the table number                          |
| `empty_candidate` | u32 | zero when the table has at least one row   |
| `first_page`    | u32  | the page the table's chain starts at      |
| `last_page`     | u32  | the page the chain ends at                |

The list ends with a pointer whose `type` is zero and it is followed by a run of zero bytes up to the end
of the page, which is checked rather than skipped: a file that writes something else there is rejected
instead of being read as if the bytes were padding.

## Page structure

Every page starts with a 40 byte header:

| Field                    | Type | Meaning                                        |
|--------------------------|------|------------------------------------------------|
| `magic`                  | u32  | `0` for an unused page                          |
| `page_index`             | u32  | this page's own number                          |
| `table_type`             | u32  | which table the page belongs to                 |
| `next_page`              | u32  | the next page in the chain, `0xffffffff` at the end |
| `transaction`            | u32  | the write that last touched the page            |
| `unnamed2`               | u32  | not explained by any measurement                |
| `num_rows_small`         | u8   | rows in the first rowset                        |
| `unnamed3`               | u8   | not explained                                   |
| `unnamed4`               | u8   | not explained                                   |
| `page_flags`             | u8   | bit 2 marks a data page                         |
| `free_size`              | u16  | free bytes left on the page                     |
| `next_heap_write_offset` | u16  | where the next row body starts                  |

Three kinds of page follow:

- a page whose magic is zero is unused and holds nothing;
- a page with the header flag but no data flag is the table list;
- a page with the data flag carries rows.

A data page has a further 36 byte header and then the rows. The rows grow forward from the start of that
area and their offsets grow backward from the end of the page: the last 36 bytes of a page are a rowset,
sixteen two byte offsets written in reverse slot order, followed by four bytes that no measurement has
explained yet. A row's length is not stored with the row; it is the distance to the next row's offset,
which is why a page has to be read as a whole before any of its rows can be sized.

## Row structure

A row is a run of fixed fields followed by strings. The fields are the same width for every row of a
table, so the schema of a table is a list of offsets; a track row, for example, has a 32 bit id at offset
0, the play time in milliseconds at 8 and the bitrate in bytes per second at 16, with 94 bytes of fields
in total.

Strings come in two forms, and they do not share a decoder:

- a **short** string has a header byte of `chars * 2 + 3` and then one byte per character, read as
  latin-1. The factor of two is in the header only, which is worth knowing: reading the length as
  `(header - 1) / 2` pulls one byte too many into the value.
- a **long** string has the header `0x40` for latin-1 or `0x90` for UTF-16LE, a 16 bit total length that
  counts the four header bytes, and then the text.

A dictionary entry is not a row and its strings are read differently again: `0x80` means UTF-16 and the
length sits in the low bits of the first byte. Using the dictionary decoder on a row turns
`/Contents/UnknownArtist/...` into `ntents/UnknownArtist/...`, which is how the two were told apart.

## What is covered

| Element | Status |
|---------|--------|
| page model: zero, table list, data pages, rowsets | read |
| file header and table chains | read |
| tracks, genres, artists, albums, labels, keys | read |
| playlist tree and playlist entries | read |
| artwork references | read |
| tag tree and MyTag master row in `exportExt.pdb` | read |
| writing a database back | written, byte for byte |

## Writing

Three calls, from the smallest to the most useful:

````python
from pyrekordbox.devicesql import encode_row, read_file, replace_rows, write_file

database = read_file(open("export.pdb", "rb").read())

# One row, encoded against the table's schema.
row = encode_row("pdb", 0, fields, {"title": "New title", "filePath": "/Contents/x.mp3"})

# The same database with that table rewritten from these rows, then the bytes.
rebuilt = replace_rows(database, 0, [row] + [r.data for r in database.rows(0)[1:]])
open("export.pdb", "wb").write(write_file(rebuilt))
````

A database that is read and written back with nothing changed is the same file byte for byte, and that is
how the writer is tested: the suite rebuilds every capture it is given and compares the bytes.

The limits are worth knowing. Rows are packed into the pages a table already has, so a table that needs
more room than its pages raises instead of dropping rows, and a row larger than a page raises too. Adding
pages is a different feature and is not implemented.

Anything a row holds that its schema cannot explain raises {class}`pyrekordbox.devicesql.rows.UnexplainedRow`
rather than being passed through, so a row that decodes is a row that is understood. That is the property
the rebuild will rest on once the writer exists.
