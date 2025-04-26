# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

"""Rekordbox My-Setting file handlers."""

import re
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Dict, Iterator, Type, Union

from construct import Struct

from . import structs

# fmt: off
CRC16_XMODEM_TABLE = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
]
# fmt: on

RE_INVALID_KEY = re.compile("[_u][0-9]?", flags=re.IGNORECASE)


def compute_checksum(data: bytes, struct: Struct) -> int:
    """Computes the CRC16 XModem checksum for My-Setting files.

    The checksum is calculated over the contents of the `data` field,
    except for `DJMSETTING.DAT` files where the checksum is calculated over all
    preceding bytes including the length fields.

    Parameters
    ----------
    data : bytes
        The binary filey contents of the My-Setting file for which the checksum is
        computed.
    struct : Struct
        The ``Struct`` of the My-Setting file. This is used for deciding which bytes
        are used for computing the checksum.

    Returns
    -------
    crc : int
        The calculated CRC16-XModem checksum.

    References
    ----------
    https://reveng.sourceforge.io/crc-catalogue/all.htm#crc.cat.crc-16-xmodem
    """
    start = 0 if struct == structs.DjmMySetting else 104
    crc = 0
    for byte in data[start:-4]:
        crc = ((crc << 8) & 0xFF00) ^ CRC16_XMODEM_TABLE[((crc >> 8) & 0xFF) ^ byte]
    return crc


def _is_valid_key(k: str) -> bool:
    return not RE_INVALID_KEY.match(k)


class SettingsFile(MutableMapping):  # type: ignore[type-arg]
    """Base class for the Rekordbox My-Setting file handler.

    The base class implements the getters and setter defined by the keys and
    default values in the ``defaults`` class attribute.
    The keys of the ``defaults`` dictionary, which has to be defined by the inheriting
    class, defines the valid attributes of the My-Setting file. The values are used
    as default values if a new (and empty) My-Setting file is initialized.
    """

    struct: Struct
    defaults: Dict[str, str]
    version: str = ""  # only used by DEVSETTING

    def __init__(self) -> None:
        super().__init__()
        self.parsed = None
        self._items: Dict[str, str] = dict()

    @classmethod
    def parse(cls, data: bytes) -> "SettingsFile":
        """Parses the in-memory data of a Rekordbox settings binary file.

        Parameters
        ----------
        data : bytes
            The in-memory binary contents of a Rekordbox settings file.

        Returns
        -------
        self : SettingsFile
            The new instance with the parsed file content.
        """
        self = cls()
        self._parse(data)
        return self

    @classmethod
    def parse_file(cls, path: Union[str, Path]) -> "SettingsFile":
        """Reads and parses a Rekordbox settings binary file.

        Parameters
        ----------
        path : str or Path
            The path of a Rekordbox settings file which is used to read
            the file contents before parsing the binary data.

        Returns
        -------
        self : SettingsFile
            The new instance with the parsed file content.

        See Also
        --------
        SettingsFile.parse: Parses the data of a Rekordbox settings file.
        """
        with open(path, "rb") as fh:
            data = fh.read()
        return cls.parse(data)

    def _parse(self, data: bytes) -> None:
        parsed = self.struct.parse(data)
        keys = filter(_is_valid_key, parsed.data.keys())
        items = dict()
        for key in keys:
            items[key] = str(parsed.data[key])

        self.parsed = parsed
        self._items.update(items)

    def __len__(self) -> int:
        return len(self.defaults.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.defaults)

    def __getitem__(self, key: str) -> str:
        try:
            return self._items[key]
        except KeyError:
            return self.defaults[key]

    def __setitem__(self, key: str, value: str) -> None:
        if key not in self.defaults.keys():
            raise KeyError(f"Key {key} not a valid field of {self.__class__.__name__}")
        self._items[key] = value

    def __delitem__(self, key: str) -> None:
        del self._items[key]

    def get(self, key: str, default: str = None) -> Union[str, None]:  # type: ignore[override]
        """Returns the value of a setting of the My-Setting file.

        If the key is not found in the My-Setting data, but it is present in the
        ``defaults`` class dictionary, that default value is used. Otherwise, the
        parameter ``default`` is used as default value.

        Parameters
        ----------
        key : str
            The key of the setting.
        default : Any, optional
            The default value returned if the setting does not exist in the
            My-Setting file data or the ``defaults`` dictionary.

        Returns
        -------
        value : Any
            The value of the setting.
        """
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def set(self, key: str, value: str) -> None:
        """Sets the value of a setting of the My-Setting file.

        Parameters
        ----------
        key : str
            The key of the setting.
        value : Any
            The new value for updating the setting.
        """
        self.__setitem__(key, value)

    def build(self) -> bytes:
        """Constructs the binary data for saving the My-Setting file.

        Returns
        -------
        byte_data : bytes
            The binary file contents fot eh My-Setting file.
        """
        # Copy defaults and update with cuirrent data
        items = self.defaults.copy()
        items.update(self._items)

        # Create file data
        file_items: Dict[str, Any] = {"data": items, "checksum": 0}
        if self.version:
            file_items["version"] = self.version

        # Compute and update checksum. For this the data has to be serialized twice:
        # Once for generating the checksum and another time for writing the data
        # with the updated checksum
        data = self.struct.build(file_items)
        checksum = compute_checksum(data, self.struct)
        file_items["checksum"] = checksum

        # Write data with updated checksum
        bytedata: bytes = self.struct.build(file_items)
        return bytedata

    def save(self, path: Union[str, Path]) -> None:
        """Save the contents of the My-Setting file object.

        Parameters
        ----------
        path : str
            The file path used for saving.

        See Also
        --------
        build: Constructs the binary data of the file.
        """
        data = self.build()
        with open(path, "wb") as fh:
            fh.write(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class MySettingFile(SettingsFile):
    """Rekordbox `MYSETTING.DAT` file handler.

    See Also
    --------
    SettingsFile : Base class implementing getters and setter defined by the keys and
        default values in the ``defaults`` class attribute.
    """

    struct = structs.MySetting
    defaults = {
        "auto_cue": structs.AutoCue.on,
        "auto_cue_level": structs.AutoCueLevel.memory,
        "disc_slot_illumination": structs.DiscSlotIllumination.bright,
        "eject_lock": structs.EjectLock.unlock,
        "hotcue_autoload": structs.HotCueAutoLoad.on,
        "hotcue_color": structs.HotCueColor.off,
        "jog_mode": structs.JogMode.vinyl,
        "jog_ring_brightness": structs.JogRingBrightness.bright,
        "jog_ring_indicator": structs.JogRingIndicator.on,
        "language": structs.Language.english,
        "lcd_brightness": structs.LCDBrightness.three,
        "master_tempo": structs.MasterTempo.off,
        "needle_lock": structs.NeedleLock.lock,
        "on_air_display": structs.OnAirDisplay.on,
        "phase_meter": structs.PhaseMeter.type1,
        "play_mode": structs.PlayMode.single,
        "quantize": structs.Quantize.on,
        "quantize_beat_value": structs.QuantizeBeatValue.one,
        "slip_flashing": structs.SlipFlashing.on,
        "sync": structs.Sync.off,
        "tempo_range": structs.TempoRange.ten,
        "time_mode": structs.TimeMode.remain,
    }


class MySetting2File(SettingsFile):
    """Rekordbox `MYSETTING2.DAT` file handler.

    See Also
    --------
    SettingsFile : Base class implementing getters and setter defined by the keys and
        default values in the ``defaults`` class attribute.
    """

    struct = structs.MySetting2
    defaults = {
        "vinyl_speed_adjust": structs.VinylSpeedAdjust.touch,
        "jog_display_mode": structs.JogDisplayMode.auto,
        "pad_button_brightness": structs.PadButtonBrightness.three,
        "jog_lcd_brightness": structs.JogLCDBrightness.three,
        "waveform_divisions": structs.WaveformDivisions.phrase,
        "waveform": structs.Waveform.waveform,
        "beat_jump_beat_value": structs.BeatJumpBeatValue.sixteen,
    }


class DjmMySettingFile(SettingsFile):
    """Rekordbox `DJMMYSETTING.DAT` file handler.

    See Also
    --------
    SettingsFile : Base class implementing getters and setter defined by the keys and
        default values in the ``defaults`` class attribute.
    """

    struct = structs.DjmMySetting
    defaults = {
        "channel_fader_curve": structs.ChannelFaderCurve.linear,
        "cross_fader_curve": structs.CrossfaderCurve.fast_cut,
        "headphones_pre_eq": structs.HeadphonesPreEQ.post_eq,
        "headphones_mono_split": structs.HeadphonesMonoSplit.stereo,
        "beat_fx_quantize": structs.BeatFXQuantize.on,
        "mic_low_cut": structs.MicLowCut.on,
        "talk_over_mode": structs.TalkOverMode.advanced,
        "talk_over_level": structs.TalkOverLevel.minus_18db,
        "midi_channel": structs.MidiChannel.one,
        "midi_button_type": structs.MidiButtonType.toggle,
        "display_brightness": structs.MixerDisplayBrightness.five,
        "indicator_brightness": structs.MixerIndicatorBrightness.three,
        "channel_fader_curve_long": structs.ChannelFaderCurveLong.exponential,
    }


class DevSettingFile(SettingsFile):
    """Rekordbox `DEVSETTING.DAT` file handler.

    Warnings
    --------
    The data of the `DEVSETTING.DAT` file is not supported. Only the header can be
    parsed and written. This class is implemented for completness only.

    See Also
    --------
    SettingsFile : Base class implementing getters and setter defined by the keys and
        default values in the ``defaults`` class attribute.
    """

    struct = structs.DevSetting
    defaults = dict(entries="")


FILES: Dict[str, Type[SettingsFile]] = {
    "DEVSETTING.DAT": DevSettingFile,
    "DJMMYSETTING.DAT": DjmMySettingFile,
    "MYSETTING.DAT": MySettingFile,
    "MYSETTING2.DAT": MySetting2File,
}
