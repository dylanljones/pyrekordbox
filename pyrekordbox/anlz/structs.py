# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-10-24

"""Binary structures of Rekordbox ANLZ-files.

References
----------
.. [1] Rekordbox Export Structure Analysis: Analysis Files,
   https://djl-analysis.deepsymmetry.org/rekordbox-export-analysis/anlz.html
"""

from construct import Int8ub, Int16ub, Int32ub, PaddedString, Int32sb, StopIf
from construct import Const, Array, Padding, Bytes
from construct import Default, Enum, GreedyRange, Struct, Switch, this


# -- Beat Grid Tag (PQTZ) --------------------------------------------------------------

AnlzQuantizeTick = Struct(
    "beat" / Int16ub,
    "tempo" / Int16ub,
    "time" / Int32ub  # in ms from start
)

# len_header: 24
PQTZ = Struct(
    "u1" / Padding(4),
    "u2" / Const(0x80000, Int32ub),
    "entry_count" / Int32ub,
    "entries" / Array(this.entry_count, AnlzQuantizeTick),
)


# Extended Beat Grid Tag (PQT2)

AnlzQuantizeTick2 = Struct(
    "beat" / Int8ub,    # 1 byte
    "unkown" / Int8ub,    # 1 byte
)

# len_header: 56
PQT2 = Struct(
    Padding(4), # -> 16
    "u1" / Const(0x01000002, Int32ub),  # -> 20, count of "bpm" objects?
    Padding(4), # -> 24
    "bpm" / Array(2, AnlzQuantizeTick),  # -> 40 (2 * 8 bytes = 16 bytes)
    "entry_count" / Int32ub,  # -> 44 number of entries of 2 bytes
    "u3" / Int32ub,  # -> 48
    "u4" / Int32ub,  # -> 52
    "u5" / Int32ub,  # -> 56
    # End header
    StopIf(this.entry_count == 0),
    # "entries" / Array(this.entry_count, Bytes(2)),
    "entries" / Array(this.entry_count, AnlzQuantizeTick2),
)


# -- Cue List Tag (PCOB) ---------------------------------------------------------------

AnlzCuePointType = Enum(Int8ub, single=1, loop=2)

AnlzCuePointStatus = Enum(Int32ub, disabled=0, enabled=4)

AnlzTagCueObjectType = Enum(Int32ub, memory=0, hotcue=1)

AnlzCuePoint = Struct(
    "type" / Const("PCPT", PaddedString(4, encoding="ascii")),
    "len_header" / Int32ub,
    "len_entry" / Int32ub,
    "hot_cue" / Int32ub,  # 0 for memory
    "status" / AnlzCuePointStatus,
    "u1" / Const(0x10000, Int32ub),
    "order_first" / Int16ub,  # 0xffff for first cue, 0,1,3 for next
    "order_last" / Int16ub,  # 1,2,3 for first, second, third cue, 0xffff for last
    "type" / AnlzCuePointType,
    Padding(1),
    "u2" / Const(1000, Int16ub),
    "time" / Int32ub,
    "loop_time" / Default(Int32ub, -1),
    Padding(16),
)

# len_header: 24
PCOB = Struct(
    "cue_type" / AnlzTagCueObjectType,
    "unk" / Int16ub,
    "count" / Int16ub,
    "memory_count" / Int32sb,
    "entries" / Array(this.count, AnlzCuePoint),
)


# Extended (nxs2) Cue List Tag (PCO2)

AnlzCuePoint2 = Struct(
    "type" / Const("PCP2", PaddedString(4, encoding="ascii")),
    "len_header" / Int32ub,
    "len_entry" / Int32ub,
    "hot_cue" / Int32ub,  # 0 for memory
    "type" / Int8ub,  # spotted: 0x010003e8 0x020003e8
    Padding(3),
    "time" / Int32ub,
    "loop_time" / Default(Int32ub, -1),
    "color_id" / Int8ub,
    Padding(7),
    "loop_enumerator" / Int16ub,
    "loop_denominator" / Int16ub,
    "len_comment" / Int32ub,
    "comment" / PaddedString(this.len_comment, encoding="utf-16-be"),
    "color_code" / Int8ub,
    "color_red" / Int8ub,
    "color_green" / Int8ub,
    "color_blue" / Int8ub,
    Padding(this.len_entry - 48 - this.len_comment),
)

# len_header: 20
PCO2 = Struct(
    "type" / AnlzTagCueObjectType,
    "count" / Int16ub,
    "unknown" / Int16ub,
    "entries" / Array(this.count, AnlzCuePoint2),
)


# -- Path Tag (PPTH) -------------------------------------------------------------------

# len_header: 16
PPTH = Struct(
    "len_path" / Int32ub,  # is 0 for some tag types
    "path" / PaddedString(this.len_path - 2, encoding="utf-16-be"),
    Padding(2),
)


# -- VBR Tag (PVBR) --------------------------------------------------------------------

# len_header: 16
PVBR = Struct(
    "u1" / Int32ub,
    "idx" / Array(400, Int32ub),
    "u2" / Int32ub
)


# -- (Tiny) Waveform Preview Tag (PWAV / PWV2) -----------------------------------------

# len_header: 20
PWAV = Struct(
    "len_preview" / Int32ub,  # is 0 for some tag types
    "unknown" / Const(0x10000, Int32ub),
    "entries" / Array(this.len_preview, Int8ub),
)

# len_header: 20
PWV2 = Struct(
    "len_preview" / Int32ub,  # is 0 for some tag types
    "unknown" / Const(0x10000, Int32ub),
    "entries" / Array(this.len_preview, Int8ub),
)


# -- Waveform Detail Tag (PWV3) --------------------------------------------------------

# len_header: 24
PWV3 = Struct(
    "len_entry_bytes" / Const(1, Int32ub),
    "len_entries" / Int32ub,
    "u1" / Const(0x00960000, Int32ub),
    "entries" / Array(this.len_entries, Int8ub),
)


# -- Waveform Color Preview Tag (PWV4) -------------------------------------------------

# len_header: 24
PWV4 = Struct(
    "len_entry_bytes" / Const(0x00000006, Int32ub),
    "len_entries" / Int32ub,
    "unknown" / Int32ub,
    "entries" / Bytes(this.len_entry_bytes * this.len_entries),
)


# -- Waveform Color Detail Tag (PWV5) --------------------------------------------------

# len_header: 24
PWV5 = Struct(
    "len_entry_bytes" / Const(0x00000002, Int32ub),
    "len_entries" / Int32ub,
    "unknown" / Int32ub,
    "entries" / Array(this.len_entries, Int16ub),
)

# -- Song Structure Tag (PSSI) ---------------------------------------------------------

SongStructureEntry = Struct(
    "index" / Int16ub,
    "beat" / Int16ub,
    "kind" / Int16ub,
    "u1" / Int8ub,
    "k1" / Int8ub,
    "u2" / Int8ub,
    "k2" / Int8ub,
    "u3" / Int8ub,
    "b" / Int8ub,
    "beat_2" / Int16ub,
    "beat_3" / Int16ub,
    "beat_4" / Int16ub,
    "u4" / Int8ub,
    "k3" / Int8ub,
    "u5" / Int8ub,
    "fill" / Int8ub,
    "beat_fill" / Int16ub,
)

# len_header: 32
PSSI = Struct(
    "len_entry_bytes" /  Const(24, Int32ub),
    "len_entries" / Int16ub,
    "mood" / Int16ub,
    "u1" / Bytes(6),
    "end_beat" / Int16ub,
    "u2" / Bytes(2),
    "bank" / Int8ub,
    "u3" / Bytes(1),
    "entries" / Array(this.len_entries, SongStructureEntry),
)

# -- PWV6 ------------------------------------------------------------------------------

# len_header: 20
PWV6 = Struct(
    "len_entry_bytes" /  Const(0x00000003, Int32ub),
    "len_entries" / Int32ub,
    "entries" /  Bytes(this.len_entry_bytes * this.len_entries),
)

# -- PWV7 ------------------------------------------------------------------------------

# len_header: 24
PWV7 = Struct(
    "len_entry_bytes" /  Const(0x00000003, Int32ub),
    "len_entries" / Int32ub,
    "unknown" / Const(0x00960000, Int32ub),
    "entries" / Bytes(this.len_entry_bytes * this.len_entries),
)

# -- PWVC ------------------------------------------------------------------------------

# len_header: 14
PWVC = Struct(
    "unknown" /  Int16ub,
    "data" / Array(3, Int16ub)
)


# -- Main Items ------------------------------------------------------------------------

AnlzFileHeader = Struct(
    "type" / PaddedString(4, encoding="ascii"),
    "len_header" / Int32ub,
    "len_file" / Int32ub,
    "u1" / Int32ub,
    "u2" / Int32ub,
    "u3" / Int32ub,
    "u4" / Int32ub,
)


AnlzTag = Struct(
    "type" / PaddedString(4, encoding="ascii"),
    "len_header" / Int32ub,
    "len_tag" / Int32ub,
    "content" / Switch(
        this.type,
        {
            "PQTZ": PQTZ,
            "PQT2": PQT2,
            "PCOB": PCOB,  # seen in both DAT and EXT files
            "PCO2": PCO2,  # seen in EXT files
            "PPTH": PPTH,
            "PVBR": PVBR,
            "PSSI": PSSI,  # seen in EXT files
            "PWAV": PWAV,
            "PWV2": PWV2,
            "PWV3": PWV3,  # seen in EXT files
            "PWV4": PWV4,  # seen in EXT files
            "PWV5": PWV5,  # seen in EXT files
            "PWV6": PWV6,  # seen in 2EX files
            "PWV7": PWV7,  # seen in 2EX files
            "PWVC": PWVC,  # seen in 2EX files
        },
        default=Bytes(this.len_tag - 12),
    ),
)
