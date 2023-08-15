# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

"""Binary structures of Rekordbox MySettings files.

Files in this format include:

- `DEVSETTINGS.DAT`
- `DJMMYSETTING.DAT`
- `MYSETTING.DAT`
- `MYSETTING2.DAT`

References
----------
.. [1] Jan Holthuis. rekordcrate.
   https://holzhaus.github.io/rekordcrate/rekordcrate/setting/struct.Setting.html
"""

from construct import Int8ul, Int16ul, Int32ul, PaddedString, Const, Padding
from construct import Enum, Bytes, Struct, Default, Select


# -- DjmSettings -----------------------------------------------------------------------

ChannelFaderCurve = Enum(Int8ul, steep_top=0x80, linear=0x81, steep_bottom=0x82)
CrossfaderCurve = Enum(Int8ul, constant=0x80, slow_cut=0x81, fast_cut=0x82)
HeadphonesPreEQ = Enum(Int8ul, post_eq=0x80, pre_eq=0x81)
HeadphonesMonoSplit = Enum(Int8ul, stereo=0x80, mono_split=0x81)
BeatFXQuantize = Enum(Int8ul, off=0x80, on=0x81)
MicLowCut = Enum(Int8ul, off=0x80, on=0x81)
TalkOverMode = Enum(Int8ul, advanced=0x80, normal=0x81)
TalkOverLevel = Enum(
    Int8ul,
    minus_24db=0x80,
    minus_18db=0x81,
    minus_12db=0x82,
    minus_6db=0x83
)
MidiChannel = Enum(
    Int8ul,
    one=0x80,
    two=0x81,
    three=0x82,
    four=0x83,
    five=0x84,
    six=0x85,
    seven=0x86,
    eight=0x87,
    nine=0x88,
    ten=0x89,
    eleven=0x8A,
    twelve=0x8B,
    thirteen=0x8C,
    fourteen=0x8D,
    fifteen=0x8E,
    sixteen=0x8F
)
MidiButtonType = Enum(Int8ul, toggle=0x80, trigger=0x81)
MixerDisplayBrightness = Enum(
    Int8ul,
    white=0x80,
    one=0x81,
    two=0x82,
    three=0x83,
    four=0x84,
    five=0x85)
MixerIndicatorBrightness = Enum(Int8ul, one=0x80, two=0x81, three=0x82)
ChannelFaderCurveLong = Enum(Int8ul, exponential=0x80, smooth=0x81, linear=0x82)


# 52 bytes
DjmMySettingBody = Struct(
    "u1" / Default(Bytes(12), b"xV4\x12\x01\x00\x00\x00 \x00\x00\x00"),
    "channel_fader_curve" / ChannelFaderCurve,
    "cross_fader_curve" / CrossfaderCurve,
    "headphones_pre_eq" / HeadphonesPreEQ,
    "headphones_mono_split" / HeadphonesMonoSplit,
    "beat_fx_quantize" / BeatFXQuantize,
    "mic_low_cut" / MicLowCut,
    "talk_over_mode" / TalkOverMode,
    "talk_over_level" / TalkOverLevel,
    "midi_channel" / MidiChannel,
    "midi_button_type" / MidiButtonType,
    "display_brightness" / MixerDisplayBrightness,
    "indicator_brightness" / MixerIndicatorBrightness,
    "channel_fader_curve_long" / ChannelFaderCurveLong,
    "u2" / Padding(27)  # Unknown values, always 0 (27 bytes)
)

# -- MySettings ------------------------------------------------------------------------

OnAirDisplay = Enum(Int8ul, off=0x80, on=0x81)
LCDBrightness = Enum(Int8ul, one=0x81, two=0x82, three=0x83, four=0x84, five=0x85)
Quantize = Enum(Int8ul, off=0x80, on=0x81)
AutoCueLevel = Enum(
    Int8ul,
    minus_36db=0x80,
    minus_42db=0x81,
    minus_48db=0x82,
    minus_54db=0x83,
    minus_60db=0x84,
    minus_66db=0x85,
    minus_72db=0x86,
    minus_78db=0x87,
    memory=0x88,
)
Language = Enum(
    Int8ul,
    english=0x81,
    french=0x82,
    german=0x83,
    italian=0x84,
    dutch=0x85,
    spanish=0x86,
    russian=0x87,
    korean=0x88,
    chinese_simplified=0x89,
    chinese_traditional=0x8A,
    japanese=0x8B,
    portuguese=0x8C,
    swedish=0x8D,
    czech=0x8E,
    hungarian=0x8F,
    danish=0x90,
    greek=0x91,
    turkish=0x92
)
JogRingBrightness = Enum(Int8ul, off=0x80, dark=0x81, bright=0x82)
JogRingIndicator = Enum(Int8ul, off=0x80, on=0x81)
SlipFlashing = Enum(Int8ul, off=0x80, on=0x81)
DiscSlotIllumination = Enum(Int8ul, off=0x80, dark=0x81, bright=0x82)
EjectLock = Enum(Int8ul, unlock=0x80, lock=0x81)
Sync = Enum(Int8ul, off=0x80, on=0x81)
PlayMode = Enum(Int8ul, continue_=0x80, single=0x81)
QuantizeBeatValue = Enum(Int8ul, one=0x80, half=0x81, quarter=0x82, eighth=0x83)
HotCueAutoLoad = Enum(Int8ul, off=0x80, on=0x81, rekordbox=0x82)
HotCueColor = Enum(Int8ul, off=0x80, on=0x81)
NeedleLock = Enum(Int8ul, unlock=0x80, lock=0x81)
TimeMode = Enum(Int8ul, elapsed=0x80, remain=0x81)
JogMode = Enum(Int8ul, cdj=0x80, vinyl=0x81)
AutoCue = Enum(Int8ul, off=0x80, on=0x81)
MasterTempo = Enum(Int8ul, off=0x80, on=0x81)
TempoRange = Enum(Int8ul, six=0x80, ten=0x81, sixteen=0x82, wide=0x83)
PhaseMeter = Enum(Int8ul, type1=0x80, type2=0x81)


# 40 bytes
MySettingBody = Struct(
    "u1" / Default(Bytes(8), b"xV4\x12\x02\x00\x00\x00"),
    "on_air_display" / OnAirDisplay,
    "lcd_brightness" / LCDBrightness,
    "quantize" / Quantize,
    "auto_cue_level" / AutoCueLevel,
    "language" / Language,
    "u2" / Default(Int8ul, 0x01),
    "jog_ring_brightness" / JogRingBrightness,
    "jog_ring_indicator" / JogRingIndicator,
    "slip_flashing" / SlipFlashing,
    "u3" / Default(Bytes(3), b"\x01\x01\x01"),
    "disc_slot_illumination" / DiscSlotIllumination,
    "eject_lock" / EjectLock,
    "sync" / Sync,
    "play_mode" / PlayMode,
    "quantize_beat_value" / QuantizeBeatValue,
    "hotcue_autoload" / HotCueAutoLoad,
    "hotcue_color" / HotCueColor,
    "u4" / Const(0, Int16ul),   # Unknown, always 0
    "needle_lock" / NeedleLock,
    "u5" / Const(0, Int16ul),   # Unknown, always 0
    "time_mode" / TimeMode,
    "jog_mode" / JogMode,
    "auto_cue" / AutoCue,
    "master_tempo" / MasterTempo,
    "tempo_range" / TempoRange,
    "phase_meter" / PhaseMeter,
    "u6" / Const(0, Int16ul),
)


# -- MySettings2 -----------------------------------------------------------------------

VinylSpeedAdjust = Enum(Int8ul, touch_release=0x80, touch=0x81, release=0x82)
JogDisplayMode = Enum(Int8ul, auto=0x80, info=0x81, simple=0x82, artwork=0x83)
PadButtonBrightness = Enum(Int8ul, one=0x81, two=0x82, three=0x83, four=0x84)
JogLCDBrightness = Enum(Int8ul, one=0x81, two=0x82, three=0x83, four=0x84, five=0x85)
WaveformDivisions = Enum(Int8ul, time_scale=0x80, phrase=0x81)
Waveform = Enum(Int8ul, waveform=0x80, phase_meter=0x81)
BeatJumpBeatValue = Enum(
    Int8ul,
    half=0x80,
    one=0x81,
    two=0x82,
    four=0x83,
    eight=0x84,
    sixteen=0x85,
    thirtytwo=0x86,
    sixtyfour=0x87
)


# 40 bytes
MySetting2Body = Struct(
    "vinyl_speed_adjust" / VinylSpeedAdjust,
    "jog_display_mode" / JogDisplayMode,
    "pad_button_brightness" / PadButtonBrightness,
    "jog_lcd_brightness" / JogLCDBrightness,
    "waveform_divisions" / WaveformDivisions,
    "u1" / Padding(5),
    "waveform" / Waveform,
    "u2" / Default(Int8ul, 0x81),
    "beat_jump_beat_value" / BeatJumpBeatValue,
    "u3" / Padding(27),   # Unknown (27 bytes), always 0
)


# -- DevSettings -----------------------------------------------------------------------

# 32 bytes
DevSettingBody = Struct(
    "u1" / Default(Bytes(8), b"xV4\x12\x02\x00\x00\x00"),
    "entries" / Bytes(24),
)


# -- Main Tags -------------------------------------------------------------------------


DjmMySetting = Struct(
    "len_strings" / Const(0x0060, Int32ul),
    "brand" / Const("PioneerDJ", PaddedString(32, "ascii")),
    "software" / Const("rekordbox", PaddedString(32, "ascii")),
    "version" / Const("1.000", PaddedString(32, "ascii")),
    "len_data" / Const(52, Int32ul),
    # Main data
    "data" / DjmMySettingBody,
    # Footer
    "checksum" / Int16ul,
    "unknown" / Const(0x00, Int16ul),
)


MySetting = Struct(
    "len_strings" / Const(0x0060, Int32ul),
    "brand" / Const("PIONEER", PaddedString(32, "ascii")),
    "software" / Const("rekordbox", PaddedString(32, "ascii")),
    "version" / Const("0.001", PaddedString(32, "ascii")),
    "len_data" / Const(40, Int32ul),
    # Main data
    "data" / MySettingBody,
    # Footer
    "checksum" / Int16ul,
    "unknown" / Const(0x00, Int16ul),
)


MySetting2 = Struct(
    "len_strings" / Const(0x0060, Int32ul),
    "brand" / Const("PIONEER", PaddedString(32, "ascii")),
    "software" / Const("rekordbox", PaddedString(32, "ascii")),
    "version" / Const("0.001", PaddedString(32, "ascii")),
    "len_data" / Const(40, Int32ul),
    # Main data
    "data" / MySetting2Body,
    # Footer
    "checksum" / Int16ul,
    "unknown" / Const(0x00, Int16ul),
)


DevSetting = Struct(
    "len_strings" / Const(0x0060, Int32ul),
    "brand" / Const("PIONEER DJ", PaddedString(32, "ascii")),
    "software" / Const("rekordbox", PaddedString(32, "ascii")),
    "version" / PaddedString(32, "ascii"),
    "len_data" / Const(32, Int32ul),
    # Main data
    "data" / DevSettingBody,
    # Footer
    "checksum" / Int16ul,
    "unknown" / Const(0x00, Int16ul),
)
