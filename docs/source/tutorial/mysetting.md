# My-Settings


Rekordbox stores the user settings in ``*SETTING.DAT`` files, which get exported
to USB devices. These files are located in the ``PIONEER`` directory of a USB drive
(device exports), but are also present on local installations of Rekordbox 6.
The setting files store the settings found on the "DJ System" > "My Settings" page
of the Rekordbox preferences. These include language, LCD brightness,
tempo fader range, crossfader curve and other settings for Pioneer professional
DJ equipment.

```{seealso}
See the {ref}`My-Setting Files Format<My-Setting Files Format>` documentation for more information.
```

Pyrekordbox includes a file handler for each of the four My-Settings files.
To read any of the four files, use
````python
from pyrekordbox import read_mysetting_file

file = read_mysetting_file("MYSETTING.DAT")
````

My-Settings files can also be parsed manually:
````python
from pyrekordbox import MySettingFile, MySetting2File, DjmMySettingFile, DevSettingFile

file1 = MySettingFile.parse_file("MYSETTING.DAT")
file2 = MySetting2File.parse_file("MYSETTING2.DAT")
file3 = DjmMySettingFile.parse_file("DJMMYSETTING.DAT")
file4 = DevSettingFile.parse_file("DEVSETTING.DAT")
````

To find the My-Settings files, the database handler includes a method that returnes the
paths of all four files:
````python
>>> from pyrekordbox import Rekordbox6Database
>>> db = Rekordbox6Database()
>>> db.get_mysetting_paths()
[
    'C:/Users/user/AppData/Roaming/Pioneer/rekordbox/DEVSETTING.DAT',
    'C:/Users/user/AppData/Roaming/Pioneer/rekordbox/DJMMYSETTING.DAT',
    'C:/Users/user/AppData/Roaming/Pioneer/rekordbox/MYSETTING.DAT',
    'C:/Users/user/AppData/Roaming/Pioneer/rekordbox/MYSETTING2.DAT'
]
````


After parsing a My-Setting file, the settings can be accessed as dictionary:
````python
>>> file = read_mysetting_file("MYSETTING.DAT")
>>> file["quantize"]
on

>>> file["quantize"] = "off"
````

To save the updated contents of a My-Settings file, use
````python
>>> file.save("MYSETTING.DAT")
````

## MySetting Files

The ``MYSETTING.DAT`` files store the main settings for Pioneers CDJ players.

````python
>>> file = read_mysetting_file("MYSETTING.DAT")
>>> for setting, value in file.items():
...     print(f"{setting:<25} {value}")
auto_cue                  on
auto_cue_level            memory
disc_slot_illumination    bright
eject_lock                unlock
hotcue_autoload           on
hotcue_color              off
jog_mode                  vinyl
jog_ring_brightness       bright
jog_ring_indicator        on
language                  english
lcd_brightness            three
master_tempo              off
needle_lock               lock
on_air_display            on
phase_meter               type1
play_mode                 single
quantize                  on
quantize_beat_value       one
slip_flashing             on
sync                      off
tempo_range               ten
time_mode                 remain
````


## MySetting2 Files

The ``MYSETTING2.DAT`` files store additional settings for Pioneers CDJ players.

````python
>>> file = read_mysetting_file("MYSETTING2.DAT")
>>> for setting, value in file.items():
...     print(f"{setting:<25} {value}")
vinyl_speed_adjust        touch
jog_display_mode          auto
pad_button_brightness     three
jog_lcd_brightness        three
waveform_divisions        phrase
waveform                  waveform
beat_jump_beat_value      sixteen
````


## DjmMySetting Files

The ``DJMMYSETTING.DAT`` files store the settings for Pioneers DJMD mixers.

````python
>>> file = read_mysetting_file("DJMMYSETTING.DAT")
>>> for setting, value in file.items():
...     print(f"{setting:<25} {value}")
channel_fader_curve       linear
cross_fader_curve         fast_cut
headphones_pre_eq         post_eq
headphones_mono_split     stereo
beat_fx_quantize          on
mic_low_cut               on
talk_over_mode            advanced
talk_over_level           minus_18db
midi_channel              one
midi_button_type          toggle
display_brightness        five
indicator_brightness      three
channel_fader_curve_long  exponential
````


## DevSetting Files

The ``DEVSETTING.DAT`` files are not supported.
