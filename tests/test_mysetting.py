# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
from pyrekordbox.mysettings import read_mysetting_file, FILES
from pyrekordbox.mysettings.file import compute_checksum

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")

ver = 6


def _read_setting(type_, key, value):
    file = type_.upper() + ".DAT"
    root = os.path.join(TEST_ROOT, "mysettings", type_)
    path = os.path.join(root, key, value, file)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    file = read_mysetting_file(path)
    return file[key]


def _read_mysetting(key, value):
    return _read_setting("mysetting", key, value)


def _read_mysetting2(key, value):
    return _read_setting("mysetting2", key, value)


def _read_djmysetting(key, value):
    return _read_setting("djmmysetting", key, value)


def _get_values(type_, key):
    root = os.path.join(TEST_ROOT, "mysettings", type_, key)
    return os.listdir(root)


def get_mysetting_values(key):
    return _get_values("mysetting", key)


def get_mysetting2_values(key):
    return _get_values("mysetting2", key)


def get_djmmysetting_values(key):
    return _get_values("djmmysetting", key)


# -- MySetting -------------------------------------------------------------------------


def test_mysetting_on_air_display():
    key = "on_air_display"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_lcd_brightness():
    key = "lcd_brightness"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_quantize():
    key = "quantize"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_auto_cue_level():
    key = "auto_cue_level"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_language():
    key = "language"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_jog_ring_brightness():
    key = "jog_ring_brightness"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_jog_ring_indicator():
    key = "jog_ring_indicator"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_slip_flashing():
    key = "slip_flashing"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_eject_lock():
    key = "eject_lock"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_disc_slot_illumination():
    key = "disc_slot_illumination"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_sync():
    key = "sync"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_play_mode():
    key = "play_mode"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_quantize_beat_value():
    key = "quantize_beat_value"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_hotcue_autoload():
    key = "hotcue_autoload"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_hotcue_color():
    key = "hotcue_color"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_needle_lock():
    key = "needle_lock"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_time_mode():
    key = "time_mode"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_jog_mode():
    key = "jog_mode"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_auto_cue():
    key = "auto_cue"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_master_tempo():
    key = "master_tempo"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_tempo_range():
    key = "tempo_range"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


def test_mysetting_phase_meter():
    key = "phase_meter"
    for expected in get_mysetting_values(key):
        assert _read_mysetting(key, expected) == expected


# -- MySetting2 ------------------------------------------------------------------------


def test_mysetting2_vinyl_speed_adjust():
    key = "vinyl_speed_adjust"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


def test_mysetting2_jog_display_mode():
    key = "jog_display_mode"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


def test_mysetting2_pad_button_brightness():
    key = "pad_button_brightness"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


def test_mysetting2_jog_lcd_brightness():
    key = "jog_lcd_brightness"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


def test_mysetting2_waveform_divisions():
    key = "waveform_divisions"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


def test_mysetting2_waveform():
    key = "waveform"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


def test_mysetting2_beat_jump_beat_value():
    key = "beat_jump_beat_value"
    for expected in get_mysetting2_values(key):
        assert _read_mysetting2(key, expected) == expected


# -- DjmMySetting ----------------------------------------------------------------------


def test_mysetting2_channel_fader_curve():
    key = "channel_fader_curve"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_crossfader_curve():
    key = "cross_fader_curve"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_headphones_pre_eq():
    key = "headphones_pre_eq"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_headphones_mono_split():
    key = "headphones_mono_split"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_beat_fx_quantize():
    key = "beat_fx_quantize"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_mic_low_cut():
    key = "mic_low_cut"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_talk_over_mode():
    key = "talk_over_mode"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_talk_over_level():
    key = "talk_over_level"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_midi_channel():
    key = "midi_channel"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_midi_button_type():
    key = "midi_button_type"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_display_brightness():
    key = "display_brightness"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_indicator_brightness():
    key = "indicator_brightness"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


def test_mysetting2_channel_fader_curve_long():
    key = "channel_fader_curve_long"
    for expected in get_djmmysetting_values(key):
        assert _read_djmysetting(key, expected) == expected


# ======================================================================================


def test_mysetting_checksum():
    file_types = "MYSETTING.DAT", "MYSETTING2.DAT", "DJMMYSETTING.DAT"

    root = os.path.join(TEST_ROOT, f"rekordbox {6}", "mysettings")
    for root, _, files in os.walk(root):
        for name in files:
            if name not in file_types:
                continue
            path = os.path.join(root, name)
            sett = read_mysetting_file(path)
            data = sett.build()
            checksum = compute_checksum(data, sett.struct)
            assert checksum == sett.parsed.checksum


def test_default_build():
    file_types = "MYSETTING.DAT", "MYSETTING2.DAT", "DJMMYSETTING.DAT"
    for key in file_types:
        obj = FILES[key]()
        data = obj.build()
        # See if data is parsable
        obj.parse(data)
