# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import re
from construct import Struct
from collections.abc import MutableMapping
from . import structs
from ..utils import crc16xmodem

RE_INVALID_KEY = re.compile("[_u][0-9]?", flags=re.IGNORECASE)


def compute_checksum(data, struct):
    """Computes the CRC16 XMODEM checksum for MySetting files.

    The checksum is calculated over the contents of the `data` field,
    except for `DJMSETTING.DAT` files where the checksum is calculated over all
    preceding bytes including the length fields.

    References
    ----------
    https://reveng.sourceforge.io/crc-catalogue/all.htm#crc.cat.crc-16-xmodem
    """
    start = 0 if struct == structs.DjmMySetting else 104
    return crc16xmodem(data[start:-4])


def _is_valid_key(k: str):
    return not RE_INVALID_KEY.match(k)


class SettingsFile(MutableMapping):
    """Abtract base class of Rekordbox settings files."""

    struct: Struct
    defaults: dict
    version: str = ""  # only used by DEVSETTING

    def __init__(self):
        super().__init__()
        self.parsed = None
        self.items = dict()

    @classmethod
    def parse(cls, data: bytes):
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
    def parse_file(cls, path: str):
        """Reads and parses a Rekordbox settings binary file.

        Parameters
        ----------
        path : str
            The path of a Rekordbox settings file which is used to read
            the file contents before parsing the binary data.

        Returns
        -------
        self : AnlzFile
            The new instance with the parsed file content.

        See Also
        --------
        SettingsFile.parse: Parses the data of a Rekordbox settings file.
        """
        with open(path, "rb") as fh:
            data = fh.read()
        return cls.parse(data)

    def _parse(self, data):
        parsed = self.struct.parse(data)
        keys = filter(_is_valid_key, parsed.data.keys())
        items = dict()
        for key in keys:
            items[key] = str(parsed.data[key])

        self.parsed = parsed
        self.items.update(items)

    def build(self):
        # Copy defaults and update with cuirrent data
        items = self.defaults.copy()
        items.update(self.items)

        # Create file data
        file_items = {"data": items, "checksum": 0}
        if self.version:
            file_items["version"] = self.version

        # Compute and update checksum. For this the data has to be serialized twice:
        # Once for generating the checksum and another time for writing the data
        # with the updated checksum
        data = self.struct.build(file_items)
        checksum = compute_checksum(data, self.struct)
        file_items["checksum"] = checksum

        # Write data with updated checksum
        return self.struct.build(file_items)

    def save(self, path):
        data = self.build()
        with open(path, "wb") as fh:
            fh.write(data)

    def __len__(self):
        return len(self.defaults.keys())

    def __iter__(self):
        return iter(self.defaults)

    def __getitem__(self, key):
        try:
            return self.items[key]
        except KeyError:
            return self.defaults[key]

    def __setitem__(self, key, value):
        if key not in self.defaults.keys():
            raise KeyError(f"Key {key} not a valid field of {self.__class__.__name__}")
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def set(self, key, value):
        self.__setitem__(key, value)

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class DevSettingFile(SettingsFile):

    struct = structs.DevSetting
    defaults = dict(entries="")


class DjmMySettingFile(SettingsFile):

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


class MySettingFile(SettingsFile):

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


FILES = {
    "DEVSETTING.DAT": DevSettingFile,
    "DJMMYSETTING.DAT": DjmMySettingFile,
    "MYSETTING.DAT": MySettingFile,
    "MYSETTING2.DAT": MySetting2File,
}
