# Bytes we carry without understanding

Reverse engineering explains most of an export, but not all of it. A handful of fields resist every
experiment so far: they hold values we can see and cannot explain. None of them is guessed at. Each one
is named after what we know about it (`unnamed`, `unknown`), read into the model, and written back
exactly as the file carried it.

The rule this repository follows:

- never invent a value for a field we do not understand,
- never drop one either, because a rebuild that loses a byte is a rebuild that changed the file,
- raise instead of guessing when a byte cannot be carried.

That is why a file can be rebuilt byte for byte while parts of it remain unexplained, and why the
numbers below are measurements rather than descriptions.

## Where the numbers come from

The captures behind every table on this page were taken from a Windows machine with Rekordbox 7.2.11 and
7.2.19 installed. No file says which of the two wrote it: a DeviceSQL file header has no version string,
an ANLZ file has none either, and the settings files carry a version field that is empty in every copy
measured. The version is known by the machine the stick came out of, not by the stick.

## DeviceSQL databases

Measured over 30 `export.pdb` and 30 `exportExt.pdb` files from the capture set: 1278 rows across 11
row schemas, all 60 files rebuilding byte for byte.

### The page header

| Field | Size | What the 30 databases show | Handling |
|-------|------|----------------------------|----------|
| `PageHeader.unnamed2` | u32 | 13 distinct values, 0 to 325 | copied back |
| `PageHeader.unnamed3` | u8  | 8 distinct values, all multiples of 32 (0 to 224) | copied back |
| `PageHeader.unnamed4` | u8  | 0 to 3 | copied back |

A counter, a set of flag bits and a small enum would all look like this. So would three unrelated
numbers, and the measurements cannot tell them apart.

### The row set tail

Every data page ends in row sets of 36 bytes: sixteen two byte row offsets, then four bytes nobody has
explained. Those four bytes take 23 distinct values across the capture set (`00000000`, `00000100`,
`00100018`, `00200030`, `007f8040` and more), so they are not padding that happens to be zero, and they
are not a constant either. The reader keeps them per row set and the writer puts them back.

### Row fields named `unnamed`

Eleven schemas, one or two such fields each. Where a schema has them, the values are almost always
constant, which is what makes them easy to carry and impossible to name:

| Schema | Field | Rows measured | Values seen |
|--------|-------|---------------|-------------|
| tracks (`pdb`, type 0) | `unnamed30` | 79 | 3 in every row |
| artists (`pdb`, type 2) | `unnamed3` | 11 | 3 in every row |
| albums (`pdb`, type 3) | `unnamed2`, `unnamed3`, `unnamed4` | 4 | 0, 0, 3 |
| playlist entries (`pdb`, type 7) | `unnamed1` | 5 | 0 in four rows, 3 in one |
| tags (`ext`, type 3) | `unnamed2`, `unnamed3`, `unnamed7` | 1048 | 0, 0, 3 |

### Strings the track row carries

| Field | What the 79 track rows show |
|-------|-----------------------------|
| `unknownString4` | 12 distinct values: empty in 17 rows, then a small decimal, `1` in 38 rows, then 2 to 21 |
| `unknownString5` to `unknownString8` | empty in every row |

`unknownString4` is the interesting one: a short decimal that is usually `1`. A disc number, a rating,
a count of something per track and a version number all fit; nothing measured so far separates them.

### Bytes after the last string

A row normally ends where its last string ends. In 3 of 79 track rows it does not: the remaining bytes
are a fragment of the previous row's file path (`...Limited 10 - Winnebago Warriors - Tr.mp3...`). The
codec keeps them as `residual` and the writer emits them unchanged, which is the only reason those three
rows rebuild identically.

## ANLZ files

Measured over 325 ANLZ files: 98 carry cue entries, 206 entries in total.

| Field | Size | What the capture set shows |
|-------|------|----------------------------|
| `PCOB` entry `unknown1` | 1 byte | `00` in 103 of 103 entries |
| `PCOB` entry `unknown2` | 16 bytes | 26 distinct values; all zero in 78 of 103, the rest look like two 32 bit numbers followed by zeros |
| `PCP2` entry `unknown1` | 3 bytes | `00 03 e8` (1000) in 103 of 103 entries |
| `PCP2` entry `unknown2` | 7 bytes | `01 00 00 00 00 00 00` in 103 of 103 entries |
| `PSSI` header, bytes 12 to 24 | 12 bytes | 9 distinct values; the most common is `00 00 00 18 00 1d e8 ff 0b 17 02 0b` across 36 files |

These matter more than their size suggests. The first version of the cue reader treated them as padding
and wrote zeros over them; a rebuild of a native file then differed in 415 bytes. They are now parsed as
byte runs and restored as they were.

The tag headers carry a further set of `unknown` fields that are constants in every capture
(`0x10000` in the cue point header, `0x00960000` in the waveform tags, among others). Those are declared
as `Const` in the structs, so a file that disagrees is rejected rather than silently rewritten. The
per tag list is in [the ANLZ format page](anlz.md).

## The player profile

`djprofile.nxs` is 160 bytes. Three regions are unexplained:

| Region | What 30 profiles show |
|--------|------------------------|
| bytes 0 to 12 | two distinct values across 30 profiles, one per player: `00 61 14 9b 00 00 01 9b 91 8c fd fa` and `00 6e d7 f2 00 00 01 a1 60 64 9c c7` |
| bytes 12 to 28 | zero in all 30 |
| bytes 28 to 32 | two distinct values, one per player name: `2c a1 60 95` for "Radoslaw Wysocki", `53 3c 0c 68` for "Radek Temp" |

Two profiles is two samples. Every one of those regions differs between them and is constant within
each, so none of the three can be told apart from "whatever this player's copy holds". A checksum, a pair
of counters and an id all fit, and the measurements cannot separate them. The module keeps the whole file
and rewrites only the name field, so none of it is at risk when a profile is saved.

## Settings files

| File | Size | Bytes 129 to 133 across 97 settings files |
|------|------|-------------------------------------------|
| `DJMMYSETTING.DAT` | 160 | `80 82 84 81 81` in all 30 copies |
| `MYSETTING.DAT` | 148 | `81 80 00 00 81` in 30 copies |
| `MYSETTING2.DAT` | 148 | zero in 30 copies |
| `DEVSETTING.DAT` | 140 | zero in 7 copies |

Five bytes, in a block of eighteen settings values, that no comparison of the values themselves has
explained. The same offset holds different bytes in three different files, so it is not a version stamp
or a fixed magic. Every copy of a stick rebuilds identically because the bytes are copied, not derived.

## Stored credentials

`gcred.dat` is 66 bytes: 64 of them are the base64 of 48 encrypted bytes, then `0d 0a`. The cipher is
AES-256-CBC over a 32 character hex string with PKCS#7 padding, and that much is understood. The key and
IV are constants inside the rekordbox installation, which belongs to whoever installed the program. A
library cannot carry somebody else's key, so there is no reader here and the file is documented rather
than handled.

## What would close these

Each of them needs a source of variation the capture set does not have:

- a second rekordbox version writing the same stick, to tell a version field from a constant,
- a deck or mixer that writes settings with a player attached, for the five bytes in the settings block,
- two profiles from the same player, to see which of the header words change and which do not,
- a stick from a player who used disc numbers or ratings, for `unknownString4`.

Until one of those exists, naming the field and carrying it is the honest answer, and it is the one this
package gives.
