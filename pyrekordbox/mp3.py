# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2024-01-11

"""Mp3 file frame header parser.

This module provides methods to parse and read mp3 file frames.
As default, Ffmpeg is used to parse the frame headers. If Ffmpeg is not available,
a pure python implementation is used. Only the *frame header* is parsed.
The *frame data* is not decoded and can only be read as raw bytes.
For more information about the mp3 file format see for
example [mpgedit.org](http://mpgedit.org/mpgedit/mpeg_format/mpeghdr.htm).

An MPEG audio file is built up from smaller parts called frames. Generally, frames are
independent items. Usually, a MP3 file starts with the ID3 tags.
The ID3 tags are followed by a sequence of MPEG frames.
The last frame may be followed by a tag such as the ID3v1 tag or other.
There is no file header. Each MPEG frame has its own header and audio information.
The frame header is 4 bytes (32 bits) long and has the following structure:

AAAAAAAA AAABBCCD EEEEFFGH IIJJKLMM

| Sign | bits | Description                                             |
| :--- | :--- | :------------------------------------------------------ |
| A    | 11   | Frame sync (all bits must be 1)                         |
| B    | 2    | MPEG Audio version ID                                   |
| C    | 2    | Layer description                                       |
| D    | 1    | Protection bit                                          |
| E    | 4    | Bitrate index                                           |
| F    | 2    | Sampling rate frequency index                           |
| G    | 1    | Padding bit                                             |
| H    | 1    | Private bit (only used in first byte of header)         |
| I    | 2    | Channel Mode (Stereo, Joint stereo, Dual channel, Mono) |
| J    | 2    | Mode extension (only used in Joint stereo)              |
| K    | 1    | Copyright bit                                           |
| L    | 1    | Original bit                                            |
| M    | 2    | Emphasis                                                |


The ID3v2 header is 10 bytes long. The header has the following structure:

| Sign | bytes | Description                                            |
| :--- | :---- | :----------------------------------------------------- |
| A    | 3     | Header ID (always 'ID3'                                |
| B    | 1     | Minor version (2, 3 or 4)                              |
| C    | 1     | Revision version                                       |
| D    | 1     | Flag bits                                              |
| E    | 4     | ID3 section size (without header)                      |

The size is encoded with four bytes where the most significant bit (bit 7) is set to
zero in every byte, making a total of 28 bits (synchsafe). The zeroed bits are ignored,
so a 257 bytes long tag is represented as $00 00 02 01.

The bits in the flag byte are assigned as follows:

ID3v2 flag:  abcd0000

| Sign | Bit | Minor version | Description                              |
| :--- | :-- | :------------ | :--------------------------------------- |
| a    | 7   | 2             | Unsynchronisation                        |
| b    | 6   | 2, 3          | Extended header                          |
| c    | 5   | 2, 3          | Experimental indicator                   |
| d    | 4   | 2, 3, 4       | Footer present                           |

"""

import enum
import json
from typing import Union, BinaryIO, Iterator
from pathlib import Path
from subprocess import PIPE, Popen
from dataclasses import dataclass

from construct import (
    Const,
    Int8ub,
    Struct,
    BitStruct,
    ConstError,
    BitsInteger,
    StreamError,
    BytesInteger,
    IntegerError,
    evaluate,
    singleton,
    swapbytes,
    stream_read,
    stream_write,
)

ID3_FLAG_BITS = [0x80, 0x40, 0x20, 0x10]
UNDEFINED_FLAGS_MASK = {2: 0x3F, 3: 0x1F, 4: 0x0F}

#              MPEG 1          |     MPEG 2/2.5
# Layer I  Layer II  Layer III | Layer I  Layer II/III
MPEG_BITRATE = [
    [0, 0, 0, 0, 0],
    [32, 32, 32, 32, 8],
    [64, 48, 40, 48, 16],
    [96, 56, 48, 56, 24],
    [128, 64, 56, 64, 32],
    [160, 80, 64, 80, 40],
    [192, 96, 80, 96, 40],
    [224, 112, 96, 112, 56],
    [256, 128, 112, 128, 64],
    [288, 160, 128, 144, 80],
    [320, 192, 160, 160, 96],
    [352, 224, 192, 176, 112],
    [384, 256, 224, 192, 128],
    [416, 320, 256, 224, 144],
    [448, 384, 320, 256, 160],
]

# MPEG 1 | MPEG 2 | MPEG 2.5
MPEG_SAMPLERATE = [[44100, 22050, 11025], [48000, 24000, 12000], [32000, 16000, 8000]]

# Ffprobe args
FF_OUTPUT = "-show_streams -show_frames -select_streams a"
FF_STREAMS = "stream=channels"
FF_FRAMES = "frame=stream_index,pkt_pos,nb_samples,pkt_size,pkt_duration_time"
FF_ARGS = f"-v quiet -of json {FF_OUTPUT} -show_entries {FF_STREAMS}:{FF_FRAMES}"
FF_CMD = "ffprobe " + FF_ARGS + ' -i "{}"'


class Id3HeaderParseError(Exception):
    """Exception raised for errors while parsing the ID3 tags."""

    pass


class Mp3FrameParseError(Exception):
    """Exception raised for errors while parsing an mp3 frame."""

    pass


class BytesIntegerSynchsafe(BytesInteger):
    """Synchsafe integer implementation."""

    def _parse(self, stream, context, path):
        length = evaluate(self.length, context)
        if length <= 0:
            raise IntegerError(f"length {length} must be positive", path=path)
        data = stream_read(stream, length, path)
        if evaluate(self.swapped, context):
            data = swapbytes(data)
        try:
            num = 0x00  # Initialize the integer value to 0x00
            for i in range(self.length):
                # Shift current value left by 7 bits and add the value of the byte
                num = (num << 7) + int(data[i])
            return int(num)  # Return the final constructed integer

        except ValueError as e:
            raise IntegerError(str(e), path=path)

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, int):
            raise IntegerError(f"value {obj} is not an integer", path=path)
        length = evaluate(self.length, context)
        if length <= 0:
            raise IntegerError(f"length {length} must be positive", path=path)
        try:
            data = bytearray()
            mask = 0x7F  # Mask to extract 7 bits
            for i in range(length):
                current_byte = obj & mask  # Extract the lowest 7 bits
                data.insert(0, current_byte)  # Insert the byte at the beginning
                obj >>= 7  # Shift to get the next 7 bits
            data = bytes(data)

        except ValueError as e:
            raise IntegerError(str(e), path=path)
        if evaluate(self.swapped, context):
            data = swapbytes(data)
        stream_write(stream, data, length, path)
        return obj


@singleton
def Int32ubsf():  # noqa: N802
    return BytesIntegerSynchsafe(4, signed=False, swapped=False)


# noinspection PyUnresolvedReferences
ID3HeaderStruct = Struct(
    Const(b"ID3"),
    "version"
    / Struct(
        "minor" / Int8ub,
        "revision" / Int8ub,
    ),
    "flags" / Int8ub,
    "size" / Int32ubsf,
)


Mp3FrameHeaderStruct = BitStruct(
    "sync" / BitsInteger(11),
    "version" / BitsInteger(2),
    "layer" / BitsInteger(2),
    "protection" / BitsInteger(1),
    "bitrate" / BitsInteger(4),
    "samplerate" / BitsInteger(2),
    "padding" / BitsInteger(1),
    "private" / BitsInteger(1),
    "channel_mode" / BitsInteger(2),
    "mode_extension" / BitsInteger(2),
    "copyright" / BitsInteger(1),
    "original" / BitsInteger(1),
    "emphasis" / BitsInteger(2),
)


class Version(enum.IntEnum):
    MPEG2_5 = 0
    Reserved = 1
    MPEG2 = 2
    MPEG1 = 3


class Layer(enum.IntEnum):
    Reserved = 0
    Layer3 = 1
    Layer2 = 2
    Layer1 = 3


class ChannelMode(enum.IntEnum):
    Stereo = 0
    JointStereo = 1
    DualChannel = 2
    Mono = 3


@dataclass(frozen=True)
class Id3Header:
    version: str = ""
    data_size: int = 0
    size: int = 0
    unsynchronisation: int = False
    extended_header: int = False
    experimental: int = False
    footer: int = False

    @property
    def is_valid(self) -> bool:
        return self.size > 0


@dataclass(frozen=True)
class Mp3FrameHeader:
    # version: Version = Version.MPEG1
    # layer: int = 0
    pos: int = 0
    bit_rate: int = 0
    sample_rate: int = 0
    channels: int = 0
    num_samples: int = 0
    size: int = 0
    length: float = 0.0

    @property
    def is_valid(self) -> bool:
        return self.size > 0


def read_id3_header(fp: BinaryIO):
    try:
        parsed = ID3HeaderStruct.parse_stream(fp)
    except ConstError:
        # Not valid, return invalid header
        return Id3Header()
    except Exception as e:
        raise Id3HeaderParseError("Could not parse ID3 header") from e

    # Parse the header
    version = f"2.{parsed.version.minor}.{parsed.version.revision}"
    # Check and set flags
    try:
        mask = UNDEFINED_FLAGS_MASK[parsed.version.minor]
    except KeyError:
        raise KeyError(f"Unknown ID3 version {version}")
    if parsed.flags & mask:  # Undefined flags are set
        return Id3Header()
    flags = tuple(int(parsed.flags & op) for op in ID3_FLAG_BITS)
    unsync, extended, experimental, footer = flags
    data_size = parsed.size
    size = parsed.size + 10
    if footer:
        size += 10

    return Id3Header(version, data_size, size, unsync, extended, experimental, footer)


def read_mp3_frame_header(fp: BinaryIO):
    pos = fp.tell()
    parsed = Mp3FrameHeaderStruct.parse_stream(fp)

    # Check if frame is valid

    # Test for the mp3 frame sync: 11 set bits.
    if parsed.sync != 0b11111111111:
        return Mp3FrameHeader()
    # The remaining tests are not entirely required, but help in finding false syncs
    if parsed.version == Version.Reserved:
        return Mp3FrameHeader()
    if parsed.layer == Layer.Reserved:
        return Mp3FrameHeader()
    if parsed.bitrate in (0, 15):
        # free and bad bitrate values
        return Mp3FrameHeader()
    if parsed.samplerate == 3:
        # this is a "reserved" sample rate
        return Mp3FrameHeader()

    version = Version(parsed.version)
    # Convert layer to int
    raw_layer = Layer(parsed.layer)
    if raw_layer == Layer.Layer1:
        layer = 1
    elif raw_layer == Layer.Layer2:
        layer = 2
    elif raw_layer == Layer.Layer3:
        layer = 3
    else:
        raise ValueError(f"Invalid layer {raw_layer}")

    if version == Version.MPEG1:
        col = layer - 1
    else:
        col = 3 if layer == 1 else 4
    bit_rate = MPEG_BITRATE[parsed.bitrate][col] * 1000

    if version == Version.MPEG1:
        col = 0
    elif version == Version.MPEG2:
        col = 1
    elif version == Version.MPEG2_5:
        col = 2
    else:
        raise ValueError(f"Invalid version {version}")
    sample_rate = MPEG_SAMPLERATE[parsed.samplerate][col]

    padding = bool(parsed.padding)

    nsamples = 0
    if layer == 3:
        if version == Version.MPEG1:
            nsamples = 1152
        else:
            nsamples = 576
    elif layer == 2:
        nsamples = 1152
    elif layer == 1:
        nsamples = 384

    channels = 2 if parsed.channel_mode == ChannelMode.Stereo else 1
    size = int(((nsamples / 8) * bit_rate) / sample_rate)
    if padding:
        size += 1
    length = float(nsamples / sample_rate)

    header = Mp3FrameHeader(
        pos, bit_rate, sample_rate, channels, nsamples, size, length
    )
    return header


def find_mp3_frame(fp, offset: int, search_range: int) -> int:
    for _ in range(search_range):
        fp.seek(offset)
        header = read_mp3_frame_header(fp)
        if header.is_valid:
            # Look for next frame
            next_offset = offset + header.size
            fp.seek(next_offset)
            next_header = read_mp3_frame_header(fp)
            if next_header.is_valid:
                return offset
        offset += 1
    raise ValueError("Could not find first valid MP3 frame")


def mp3_frames_offset(fp, offset=0, max_search_range=64):
    fp.seek(offset)

    # There can be multiple ID3 tags at the start of the file, usually different
    # versions with the same tags. Parse until we find other data.
    id3_headers = list()
    while fp.read(3) == b"ID3":
        fp.seek(offset)
        id3 = read_id3_header(fp)
        id3_headers.append(id3)
        offset += id3.size
        fp.seek(offset)
        # Skip zero bytes at the end
        while fp.read(1) == b"\x00":
            pass  # noqa
        offset = fp.tell() - 1
        fp.seek(offset)

    # Sometimes there is garbage in front of the first frame, so we need to
    # search for the first valid frame. Usually this is only a few bytes.
    offset = find_mp3_frame(fp, offset, search_range=max_search_range)

    return id3_headers, offset


def read_mp3_frame_headers(fp) -> Iterator[Mp3FrameHeader]:
    id3_headers, offset = mp3_frames_offset(fp)
    # Read all valid frames and parse header
    while True:
        fp.seek(offset)
        try:
            header = read_mp3_frame_header(fp)
        except StreamError:
            break
        except Exception as e:
            raise Mp3FrameParseError(
                f"Failed to parse frame header at offset {offset}"
            ) from e
        if not header.is_valid:
            break
        yield header
        offset += header.size


def _load_mp3_frame_headers_py(path: Union[str, Path]) -> Iterator[Mp3FrameHeader]:
    with open(path, "rb") as fp:
        yield from read_mp3_frame_headers(fp)


def _load_mp3_frame_headers_ffmpeg(file):
    cmd = FF_CMD.format(file)
    p = Popen(cmd, stdout=PIPE, stderr=None)
    data = json.loads(p.stdout.read().decode())

    streams = data["streams"]
    assert len(streams) == 1
    channels = int(streams[0]["channels"])

    for item in data["frames"]:
        idx = int(item["stream_index"])
        assert idx == 0
        pos = int(item["pkt_pos"])
        nsamples = int(item["nb_samples"])
        size = int(item["pkt_size"])
        length = float(item["pkt_duration_time"])
        sample_rate = nsamples / length
        bit_rate = 8 * sample_rate * size / nsamples
        sample_rate = int(round(0.1 * sample_rate) * 10)
        bit_rate = int(round(0.001 * bit_rate) * 1000)
        header = Mp3FrameHeader(
            pos, bit_rate, sample_rate, channels, nsamples, size, length
        )
        yield header


def load_mp3_frame_headers(
    path: Union[str, Path], backend="py"
) -> Iterator[Mp3FrameHeader]:
    if backend == "py":
        yield from _load_mp3_frame_headers_py(path)
    elif backend == "ffmpeg":
        yield from _load_mp3_frame_headers_ffmpeg(path)
    else:
        raise ValueError(f"Unknown backend {backend}")
