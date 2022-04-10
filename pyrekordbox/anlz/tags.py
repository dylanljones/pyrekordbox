# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import logging
from abc import ABC
import numpy as np
from . import structs

logger = logging.getLogger(__name__)


class BuildTagLengthError(Exception):
    def __init__(self, struct, len_data):
        super().__init__(
            f"`len_tag` ({struct.len_tag}) of '{struct.type}' does not "
            f"match the data-length ({len_data})!"
        )


class AbstractAnlzTag(ABC):
    """Abstract base class for struct handlers of Rekordbox analysis files."""

    type: str
    name: str
    LEN_HEADER: int = 0  # Expected value of `len_header`
    LEN_TAG: int = 0  # Expected value of `len_tag`

    def __init__(self, tag_data):
        self.struct = None
        if tag_data is not None:
            self.parse(tag_data)

    @property
    def content(self):
        return self.struct.content

    def _check_len_header(self):
        if self.LEN_HEADER != self.struct.len_header:
            logger.warning(
                "`len_header` (%s) of `%s` doesn't match the expected value %s",
                self.struct.len_header,
                self.struct.type,
                self.LEN_HEADER,
            )

    def _check_len_tag(self):
        if self.LEN_TAG != self.struct.len_tag:
            logger.warning(
                "`len_tag` (%s)  of `%s` doesn't match the expected value %s",
                self.struct.len_tag,
                self.struct.type,
                self.LEN_TAG,
            )

    def check_parse(self):
        pass

    def parse(self, tag_data):
        self.struct = structs.AnlzTag.parse(tag_data)
        if self.LEN_HEADER:
            self._check_len_header()
        if self.LEN_TAG:
            self._check_len_tag()
        self.check_parse()

    def build(self):
        data = structs.AnlzTag.build(self.struct)
        len_data = len(data)
        if len_data != self.struct.len_tag:
            raise BuildTagLengthError(self.struct, len_data)
        return data

    def get(self):
        return self.struct.content

    def set(self, *args, **kwargs) -> bytes:
        pass

    def update_len(self):
        pass

    def __repr__(self):
        len_header = self.struct.len_header
        len_tag = self.struct.len_tag
        return f"{self.__class__.__name__}(len_header={len_header}, len_tag={len_tag})"

    def __str__(self):
        return str(self.struct)


def _parse_wf_preview(tag):
    n = len(tag.entries)
    wf = np.zeros(n)
    col = np.zeros(n)
    for i in range(n):
        data = tag.entries[i]
        wf[i] = data & 0x1F
        col[i] = data >> 5
    return wf, col


class PQTZAnlzTag(AbstractAnlzTag):
    """Beat grid struct handler."""

    type = "PQTZ"
    name = "beat_grid"
    LEN_HEADER = 24

    @property
    def beats(self):
        return self.get_beats()

    @property
    def bpms(self):
        return self.get_bpms()

    @property
    def bpms_average(self):
        if len(self.content.entries):
            return np.mean(self.get_bpms())
        return 0.0

    @property
    def bpms_unique(self):
        return np.unique(self.get_bpms())

    @property
    def times(self):
        return self.get_times()

    def check_parse(self):
        assert self.struct.content.entry_count == len(self.struct.content.entries)

    def get(self):
        n = len(self.content.entries)
        beats = np.zeros(n, dtype=np.int8)
        bpms = np.zeros(n, dtype=np.float64)
        times = np.zeros(n, dtype=np.float64)
        for i, entry in enumerate(self.content.entries):
            _, beat, bpm, time = entry.values()
            beats[i] = beat
            bpms[i] = bpm / 100  # BPM is saved as 100 * BPM
            times[i] = time / 1_000  # Convert milliseconds to seconds
        return beats, bpms, times

    def get_beats(self):
        return np.array([entry.beat for entry in self.content.entries], dtype=np.int8)

    def get_bpms(self):
        return np.array([entry.tempo / 100 for entry in self.content.entries])

    def get_times(self):
        return np.array([entry.time / 1000 for entry in self.content.entries])

    def set(self, beats, bpms, times):
        for i, (beat, bpm, t) in enumerate(zip(beats, bpms, times)):
            data = {"beat": int(beat), "tempo": int(100 * bpm), "time": int(1000 * t)}
            self.content.entries[i].update(data)

    def set_beats(self, beats):
        for i, beat in enumerate(beats):
            self.content.entries[i].beat = beat

    def set_bpms(self, bpms):
        for i, bpm in enumerate(bpms):
            self.content.entries[i].bpm = int(bpm * 100)

    def set_times(self, times):
        for i, t in enumerate(times):
            self.content.entries[i].time = int(1000 * t)

    def update_len(self):
        self.struct.len_tag = self.struct.len_header + 8 * len(self.content.entries)


class PQT2AnlzTag(AbstractAnlzTag):
    """Extended (nxs2) beat grid struct handler."""

    type = "PQT2"
    name = "beat_grid2"
    LEN_HEADER = 56

    @property
    def beats(self):
        return self.get_beats()

    @property
    def bpms(self):
        return self.get_bpms()

    @property
    def times(self):
        return self.get_times()

    @property
    def beat_grid_count(self):
        return self.content.entry_count

    @property
    def bpms_unique(self):
        return np.unique(self.get_bpms())

    def check_parse(self):
        len_beats = self.struct.content.entry_count
        if len_beats:
            expected = self.struct.len_tag - self.struct.len_header
            actual = 2 * len(self.content.entries)  # each entry consist of 2 bytes
            assert actual == expected, f"{actual} != {expected}"

    def get(self):
        n = len(self.content.entries)
        beats = np.zeros(n, dtype=np.int8)
        bpms = np.zeros(n, dtype=np.float64)
        times = np.zeros(n, dtype=np.float64)
        for i, entry in enumerate(self.content.entries):
            _, beat, bpm, time = entry.values()
            beats[i] = beat
            bpms[i] = bpm / 100  # BPM is saved as 100 * BPM
            times[i] = time / 1_000  # Convert milliseconds to seconds
        return beats, bpms, times

    def get_beats(self):
        return np.array([entry.beat for entry in self.content.entries], dtype=np.int8)

    def get_bpms(self):
        return np.array([entry.tempo / 100 for entry in self.content.entries])

    def get_times(self):
        return np.array([entry.time / 1000 for entry in self.content.entries])

    def set_beats(self, beats):
        for i, beat in enumerate(beats):
            self.content.entries[i].beat = beat

    def set_bpms(self, bpms):
        for i, bpm in enumerate(bpms):
            self.content.entries[i].bpm = int(bpm * 100)

    def set_times(self, times):
        for i, t in enumerate(times):
            self.content.entries[i].time = int(1000 * t)

    def build(self):
        data = structs.AnlzTag.build(self.struct)
        if self.struct.content.entry_count == 0:
            data = data[: self.struct.len_tag]

        len_data = len(data)
        if len_data != self.struct.len_tag:
            raise BuildTagLengthError(self.struct, len_data)
        return data


class PCOBAnlzTag(AbstractAnlzTag):
    """Cue list struct handler."""

    type = "PCOB"
    name = "cue_list"
    LEN_HEADER = 24


class PCO2AnlzTag(AbstractAnlzTag):
    """Extended (nxs2) cue list struct handler."""

    type = "PCO2"
    name = "cue_list2"
    LEN_HEADER = 20


class PPTHAnlzTag(AbstractAnlzTag):
    """Path struct handler."""

    type = "PPTH"
    name = "path"
    LEN_HEADER = 16

    @property
    def path(self):
        return self.content.path

    def get(self):
        return self.content.path

    def set(self, path):
        path = path.replace("\\", "/")
        len_path = len(path.encode("utf-16-be")) + 2
        self.content.path = path
        self.content.len_path = len_path

    def update_len(self):
        self.struct.len_tag = self.struct.len_header + self.content.len_path


class PVBRAnlzTag(AbstractAnlzTag):
    """VBR struct handler."""

    type = "PVBR"
    name = "vbr"
    LEN_HEADER = 16
    LEN_TAG = 1620

    def get(self):
        return np.array(self.content.idx)


class PSSIAnlzTag(AbstractAnlzTag):
    """Song structure struct handler."""

    type = "PSSI"
    name = "structure"
    LEN_HEADER = 32


class PWAVAnlzTag(AbstractAnlzTag):
    """Waveform preview struct handler."""

    type = "PWAV"
    name = "wf_preview"
    LEN_HEADER = 20

    def get(self):
        return _parse_wf_preview(self.content)


class PWV2AnlzTag(AbstractAnlzTag):
    """Tiny waveform preview struct handler."""

    type = "PWV2"
    name = "wf_tiny_preview"
    LEN_HEADER = 20

    def get(self):
        return _parse_wf_preview(self.content)


class PWV3AnlzTag(AbstractAnlzTag):
    """Waveform detail struct handler."""

    type = "PWV3"
    name = "wf_detail"
    LEN_HEADER = 24

    def get(self):
        n = len(self.content.entries)
        wf = np.zeros(n)
        col = np.zeros(n)
        for i in range(n):
            data = self.content.entries[i]
            wf[i] = data & 0x1F
            col[i] = data >> 5
        return wf, col


class PWV4AnlzTag(AbstractAnlzTag):
    """Waveform color preview struct handler."""

    type = "PWV4"
    name = "wf_color"
    LEN_HEADER = 24

    def get(self):
        num_entries = self.content.len_entries
        data = self.content.entries
        ws, hs = 1, 1
        w = int(num_entries / ws)
        # parse color and blue waveforms
        col_color = np.zeros((num_entries, 2, 3), dtype=np.int64)
        col_blues = np.zeros((num_entries, 2, 3), dtype=np.int64)
        heights = np.zeros((num_entries, 2), dtype=np.int64)
        for x in range(w):
            # d0 = data[x * ws * 6 + 0]  # unknown?
            d1 = data[x * ws * 6 + 1]  # some kind of luminance boost?
            d2 = data[x * ws * 6 + 2] & 0x7F  # inverse intensity for blue waveform
            d3 = data[x * ws * 6 + 3] & 0x7F  # red
            d4 = data[x * ws * 6 + 4] & 0x7F  # green
            d5 = data[x * ws * 6 + 5] & 0x7F  # blue and height of front waveform
            bh = int(max(d2, d3, d4) / hs)  # back height is max of d3, d4 probably d2?
            fh = int(d5 / hs)  # front height is d5
            fl = 32  # front luminosity increase (arbitrary)
            # waveform heights
            heights[x] = fh, bh
            # color waveform
            col = np.array([d3, d4, d5]) * (d1 / 127)
            col_color[x] = col, col + fl
            # blue waveform
            col = 95 - d2 * np.array([1.0, 0.5, 0.25])
            col_blues[x] = col, col + fl
        return heights, col_color, col_blues


class PWV5AnlzTag(AbstractAnlzTag):
    """Waveform color detail struct handler."""

    type = "PWV5"
    name = "wf_color_detail"
    LEN_HEADER = 24

    def get(self):
        """Parse the Waveform Color Detail Tag (PWV5)

        The format of the entries is:

          f  e  d  c  b  a  9  8  7  6  5  4  3  2  1  0
        │   red  │  green │  blue  │    height    │00 00│
        """
        rmask = 0xE000  # 111 000 000 00000 00
        gmask = 0x1C00  # 000 111 000 00000 00
        bmask = 0x380  # 000 000 111 00000 00
        hmask = 0x7C  # 000 000 000 11111 00

        n = self.content.len_entries
        heights = np.zeros(n, dtype=np.int64)
        colors = np.zeros((n, 3), dtype=np.int64)
        for i, x in enumerate(self.content.entries):
            red = (x & rmask) >> 12
            green = (x & gmask) >> 10
            blue = (x & bmask) >> 7
            heights[i] = (x & hmask) >> 2
            colors[i] = red, green, blue
        # Normalize heights to 1:
        heights = heights / 31
        return heights, colors


class PWV6AnlzTag(AbstractAnlzTag):
    """PWV6 struct handler."""

    type = "PWV6"
    name = type
    LEN_HEADER = 20


class PWV7AnlzTag(AbstractAnlzTag):
    """PWV7 struct handler."""

    type = "PWV7"
    name = type
    LEN_HEADER = 24


class PWVCAnlzTag(AbstractAnlzTag):
    """PWVC struct handler."""

    type = "PWVC"
    name = type
    LEN_HEADER = 14


TAGS = {
    "PQTZ": PQTZAnlzTag,
    "PQT2": PQT2AnlzTag,
    "PCOB": PCOBAnlzTag,  # seen in both DAT and EXT files
    "PCO2": PCO2AnlzTag,  # seen in EXT files
    "PPTH": PPTHAnlzTag,
    "PVBR": PVBRAnlzTag,
    "PSSI": PSSIAnlzTag,  # seen in EXT files
    "PWAV": PWAVAnlzTag,
    "PWV2": PWV2AnlzTag,
    "PWV3": PWV3AnlzTag,  # seen in EXT files
    "PWV4": PWV4AnlzTag,  # seen in EXT files
    "PWV5": PWV5AnlzTag,  # seen in EXT files
    "PWV6": PWV6AnlzTag,  # seen in 2EX files
    "PWV7": PWV7AnlzTag,  # seen in 2EX files
    "PWVC": PWVCAnlzTag,  # seen in 2EX files
}
