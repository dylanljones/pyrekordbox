# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

import os
import pytest
from pyrekordbox.mysettings import (
    read_mysetting_file,
    MySettingFile,
    MySetting2File,
    DjmMySettingFile,
)
from pyrekordbox.mysettings.file import compute_checksum

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testdata")

MYSETTING_KEYS = [
    "on_air_display",
    "lcd_brightness",
    "quantize",
    "auto_cue_level",
    "language",
    "jog_ring_brightness",
    "jog_ring_indicator",
    "slip_flashing",
    "eject_lock",
    "disc_slot_illumination",
    "sync",
    "play_mode",
    "quantize_beat_value",
    "hotcue_autoload",
    "hotcue_color",
    "needle_lock",
    "time_mode",
    "jog_mode",
    "auto_cue",
    "master_tempo",
    "tempo_range",
    "phase_meter",
]

MYSETTING2_KEYS = [
    "vinyl_speed_adjust",
    "jog_display_mode",
    "pad_button_brightness",
    "jog_lcd_brightness",
    "waveform_divisions",
    "waveform",
    "beat_jump_beat_value",
]

DJMMYSETTING_KEYS = [
    "channel_fader_curve",
    "cross_fader_curve",
    "headphones_pre_eq",
    "headphones_mono_split",
    "beat_fx_quantize",
    "mic_low_cut",
    "talk_over_mode",
    "talk_over_level",
    "midi_channel",
    "midi_button_type",
    "display_brightness",
    "indicator_brightness",
    "channel_fader_curve_long",
]


def _read_setting_file(type_, key, value):
    file = type_.upper() + ".DAT"
    root = os.path.join(TEST_ROOT, "mysettings", type_)
    path = os.path.join(root, key, value, file)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return read_mysetting_file(path)


def _read_default_setting_file(type_):
    file = type_.upper() + ".DAT"
    root = os.path.join(TEST_ROOT, "mysettings")
    path = os.path.join(root, file)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return read_mysetting_file(path)


def _get_values(type_, key):
    root = os.path.join(TEST_ROOT, "mysettings", type_, key)
    return os.listdir(root)


# -- MySetting -------------------------------------------------------------------------


@pytest.mark.parametrize("key", MYSETTING_KEYS)
def test_get_mysetting(key):
    for expected in _get_values("mysetting", key):
        file = _read_setting_file("mysetting", key, expected)
        assert file[key] == expected


def test_mysetting_defaults():
    file_default = _read_default_setting_file("mysetting")
    file = MySettingFile()
    for key in MYSETTING_KEYS:
        assert file[key] == file_default[key]


@pytest.mark.parametrize("key", MYSETTING_KEYS)
def test_set_mysetting(key):
    type_ = "mysetting"
    for val in _get_values(type_, key):
        # Read value file
        file_ref = _read_setting_file(type_, key, val)
        # Read default file and update value
        file = _read_default_setting_file(type_)
        file[key] = val
        # Check values are identical
        assert file[key] == file_ref[key]
        # Check binary data is identical
        assert file.build() == file_ref.build()


# -- MySetting2 ------------------------------------------------------------------------


@pytest.mark.parametrize("key", MYSETTING2_KEYS)
def test_get_mysetting2(key):
    for expected in _get_values("mysetting2", key):
        file = _read_setting_file("mysetting2", key, expected)
        assert file[key] == expected


def test_mysetting2_defaults():
    file_default = _read_default_setting_file("mysetting2")
    file = MySetting2File()
    for key in MYSETTING2_KEYS:
        assert file[key] == file_default[key]


@pytest.mark.parametrize("key", MYSETTING2_KEYS)
def test_set_mysetting2(key):
    type_ = "mysetting2"
    for val in _get_values(type_, key):
        # Read value file
        file_ref = _read_setting_file(type_, key, val)
        # Read default file and update value
        file = _read_default_setting_file(type_)
        file[key] = val
        # Check values are identical
        assert file[key] == file_ref[key]
        # Check binary data is identical
        assert file.build() == file_ref.build()


# -- DjmMySetting ----------------------------------------------------------------------


@pytest.mark.parametrize("key", DJMMYSETTING_KEYS)
def test_get_djmmysetting(key):
    for expected in _get_values("djmmysetting", key):
        file = _read_setting_file("djmmysetting", key, expected)
        assert file[key] == expected


def test_djmmysetting_defaults():
    file_default = _read_default_setting_file("djmmysetting")
    file = DjmMySettingFile()
    for key in DJMMYSETTING_KEYS:
        assert file[key] == file_default[key]


@pytest.mark.parametrize("key", DJMMYSETTING_KEYS)
def test_set_djmmysetting(key):
    type_ = "djmmysetting"
    for val in _get_values(type_, key):
        # Read value file
        file_ref = _read_setting_file(type_, key, val)
        # Read default file and update value
        file = _read_default_setting_file(type_)
        file[key] = val
        # Check values are identical
        assert file[key] == file_ref[key]
        # Check binary data is identical
        assert file.build() == file_ref.build()


# ======================================================================================


def test_mysetting_checksum():
    file_types = "MYSETTING.DAT", "MYSETTING2.DAT", "DJMMYSETTING.DAT"

    root = os.path.join(TEST_ROOT, "mysettings")
    for root, _, files in os.walk(root):
        for name in files:
            if name not in file_types:
                continue
            path = os.path.join(root, name)
            sett = read_mysetting_file(path)
            data = sett.build()
            checksum = compute_checksum(data, sett.struct)
            assert checksum == sett.parsed.checksum
