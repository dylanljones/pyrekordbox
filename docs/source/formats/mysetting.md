# My-Setting Files Format

This document explains the file format of the following Rekordbox My-Setting files:

- `DEVSETTING.DAT`
- `DJMMYSETTING.DAT`
- `MYSETTING.DAT`
- `MYSETTING2.DAT`

## My-Setting File Structure

The My-Setting files of Rekordbox are made up of a file header, a body structure
containing the main data and a file footer. In contrast to the analysis files the
My-Setting files use little endian data types.

The files start with a single byte `len_strings` specifying the combined size of the
string data fields (should be always 96). The next 3 bytes are always zero.
The first 4 bytes can also be interpreted as a little endian 32-bit integer.
After that the My-Setting files contain three 32 byte long ASCII strings.
The first 32 byte field `brand` contains the name of the brand. The value seems to
depend on the file:

| File               | Value        |
|--------------------|--------------|
| `DEVSETTING.DAT`   | `PIONEER DJ` |
| `DJMMYSETTING.DAT` | `PioneerDJ`  |
| `MYSETTING.DAT`    | `PIONEER`    |
| `MYSETTING2.DAT`   | `PIONEER`    |

The next 32 byte long field `software` describes the name of the software. The value
seems to always be "rekordbox". The last string in the file header is `version`,
which describes some kind of version number.
The last value of the header is `len_data`, which describes
the size of the `data` data in bytes. The total length of the header is 104 bytes.

The My-Setting files end with an 4 byte long file footer, which contain a 2 byte checksum
and an 2 byte unknown value, which seems to always be `0x00`. The checksum is calculated
over the contents of the `data` field, except for `DJMSETTING.DAT` files where
the checksum is calculated over all preceding bytes including the length fields and
uses the CRC16 XMODEM algorithm [^footnote-1].

## My-Settings File Body

After the file header of the My-Settings files the main data begins. The format depends
on the kind of file. All settings are stored as enums, starting at the value
`0x80 = 129`. Note that even integers are not stored directly but mapped to the enum
values, for example `0x80` -> 1, `0x81` -> 2, etc. Sometimes the enum values are
shifted by one: `0x81` -> 1, `0x82` -> 2, etc.

### MySetting Body

The payload of the `MYSETTING.DAT` file is 40 bytes long and contains the main
settings for Pioneer audio players (CDJ's).

```{eval-rst}
.. list-table:: `MYSETTING.DAT` data body
   :widths: 13 25 120
   :header-rows: 1

   * - Byte
     - Name
     - Description
   * - 1-8
     -
     - Usually ``b"xV4\x12\x02\x00\x00\x00"``
   * - 9
     - `on_air_display`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 10
     - `lcd_brightness`
     - ``0x81`` = `one`, ``0x82`` = `two`, ..., ``0x85`` = `five`
   * - 11
     - `quantize`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 12
     - `auto_cue_level`
     - See encodings section
   * - 13
     - `language`
     - See encodings section
   * - 14
     -
     - Usually ``b"\x01"``
   * - 15
     - `jog_ring_brightness`
     - ``0x80`` = `off`, ``0x81`` = `dark`, ``0x82`` = `bright`
   * - 16
     - `jog_ring_indicator`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 17
     - `slip_flashing`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 18-20
     -
     - Usually ``b"\x01\x01\x01"``
   * - 21
     - `disc_slot_illumination`
     - ``0x80`` = `off`, ``0x81`` = `dark`, ``0x82`` = `bright`
   * - 22
     - `eject_lock`
     - ``0x80`` = `unlock`, ``0x81`` = `lock`
   * - 23
     - `sync`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 24
     - `play_mode`
     - ``0x80`` = `continue`, ``0x81`` = `single`
   * - 25
     - `quantize_beat_value`
     - ``0x80`` = `one`, ``0x81`` = `half`, ..., ``0x83`` = `eighth`
   * - 26
     - `hotcue_autoload`
     - ``0x80`` = `off`, ``0x81`` = `on`, ``0x83`` = `rekordbox`
   * - 27
     - `hotcue_color`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 28-29
     -
     - Always ``0``
   * - 30
     - `needle_lock`
     - ``0x80`` = `unlock`, ``0x81`` = `lock`
   * - 31-32
     -
     - Always ``0``
   * - 33
     - `time_mode`
     - ``0x80`` = `elapsed`, ``0x81`` = `remain`
   * - 34
     - `jog_mode`
     - ``0x80`` = `cdj`, ``0x81`` = `vinyl`
   * - 35
     - `auto_cue`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 36
     - `master_tempo`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 37
     - `tempo_range`
     - ``0x80`` = `six`, ``0x81`` = `ten`, ``0x82`` = `sixteen`, ``0x83`` = `wide`
   * - 38
     - `phase_meter`
     - ``0x80`` = `type1`, ``0x81`` = `type2`
   * - 39-40
     -
     - Always ``0``

```

### MySetting2 Body

The payload of the `MYSETTING2.DAT` file is 40 bytes long and contains additional
settings for Pioneer audio players (CDJ).

```{eval-rst}
.. list-table:: `MYSETTING2.DAT` data body
   :widths: 13 25 120
   :header-rows: 1

   * - Byte
     - Name
     - Description
   * - 1
     - `vinyl_speed_adjust`
     - ``0x80`` = `touch_release`, ``0x81`` = `touch`, ``0x82`` = `release`
   * - 2
     - `jog_display_mode`
     - ``0x80`` = `auto`, ``0x81`` = `info`, ``0x82`` = `simple`, ``0x83`` = `artwork`
   * - 3
     - `pad_button_brightness`
     - ``0x81`` = `one`, ``0x82`` = `two`, ..., ``0x84`` = `four`
   * - 4
     - `jog_lcd_brightness`
     - ``0x81`` = `one`, ``0x82`` = `two`, ..., ``0x85`` = `five`
   * - 5
     - `waveform_divisions`
     - ``0x80`` = `time_scale`, ``0x81`` = `phrase`
   * - 6-10
     -
     - Always ``0``
   * - 11
     - `waveform`
     - ``0x80`` = `waveform`, ``0x81`` = `phase_meter`
   * - 12
     -
     - Usually ``b"\x81"``
   * - 13
     - `beat_jump_beat_value`
     - See encodings section
   * - 14-30
     -
     - Always ``0``

```

### DjmMySetting Body

The payload of the `DJMMYSETTING.DAT` file is 52 bytes long and contains the main
settings for Pioneer mixers (DJM).

```{eval-rst}
.. list-table:: `DJMMYSETTING.DAT` data body
   :widths: 13 25 100
   :header-rows: 1

   * - Byte
     - Name
     - Description
   * - 1-12
     -
     - Usually ``b"xV4\x12\x01\x00\x00\x00 \x00\x00\x00"``
   * - 13
     - `channel_fader_curve`
     - ``0x80`` = `steep_top`, ``0x81`` = `linear`, ``0x82`` = `steep_bottom`
   * - 14
     - `cross_fader_curve`
     - ``0x80`` = `constant`, ``0x81`` = `slow_cut`, ``0x82`` = `fast_cut`
   * - 15
     - `headphones_pre_eq`
     - ``0x80`` = `post_eq`, ``0x81`` = `pre_eq`
   * - 16
     - `headphones_mono_split`
     - ``0x80`` = `stereo`, ``0x81`` = `mono_split`
   * - 17
     - `beat_fx_quantize`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 18
     - `mic_low_cut`
     - ``0x80`` = `off`, ``0x81`` = `on`
   * - 19
     - `talk_over_mode`
     - ``0x80`` = `advanced`, ``0x81`` = `normal`
   * - 20
     - `talk_over_level`
     - See encodings section
   * - 21
     - `midi_channel`
     - ``0x80`` = `one`, ``0x81`` = `two`, ..., ``0x8F`` = `sixteen`
   * - 22
     - `midi_button_type`
     - ``0x80`` = `toggle`, ``0x81`` = `trigger`
   * - 23
     - `display_brightness`
     - ``0x80`` = `white`, ``0x81`` = `one`, ..., ``0x85`` = `five`
   * - 24
     - `indicator_brightness`
     - ``0x80`` = `one`, ``0x81`` = `two`, ``0x82`` = `three`
   * - 25
     - `channel_fader_curve_long`
     - ``0x80`` = `exponential`, ``0x81`` = `smooth`, ``0x82`` = `linear`
   * - 26-52
     -
     - Always ``0``

```

### DevSetting Body

The `DEVSETTING.DAT` file is not yet understood well. Its payload is 32 bytes long.

## Encodings

The auto-cue levels in the `MYSETTING.DAT` files are encoded as follows:

```{eval-rst}
.. list-table:: Auto-cue level encodings
   :widths: 25 75
   :header-rows: 1

   * - Value
     - Name
   * - ``0x80``
     - `minus_36db`
   * - ``0x81``
     - `minus_42db`
   * - ``0x82``
     - `minus_48db`
   * - ``0x83``
     - `minus_54db`
   * - ``0x84``
     - `minus_60db`
   * - ``0x85``
     - `minus_66db`
   * - ``0x86``
     - `minus_72db`
   * - ``0x87``
     - `minus_78db`
   * - ``0x88``
     - `memory`

```

The languages in the `MYSETTING.DAT` files are encoded as follows:

```{eval-rst}
.. list-table:: Language encodings
   :widths: 25 75
   :header-rows: 1

   * - Value
     - Name
   * - ``0x80``
     - `english`
   * - ``0x81``
     - `french`
   * - ``0x82``
     - `english`
   * - ``0x83``
     - `german`
   * - ``0x84``
     - `italian`
   * - ``0x85``
     - `dutch`
   * - ``0x86``
     - `spanish`
   * - ``0x87``
     - `russian`
   * - ``0x88``
     - `korean`
   * - ``0x89``
     - `chinese_simplified`
   * - ``0x8A``
     - `chinese_traditional`
   * - ``0x8B``
     - `japanese`
   * - ``0x8C``
     - `portuguese`
   * - ``0x8D``
     - `swedish`
   * - ``0x8E``
     - `czech`
   * - ``0x8F``
     - `hungarian`
   * - ``0x90``
     - `danish`
   * - ``0x91``
     - `greek`
   * - ``0x92``
     - `turkish`
```

The beat jump beat value in the `MYSETTING2.DAT` files are encoded as follows:

```{eval-rst}
.. list-table:: Beat jump beat value encodings
   :widths: 25 75
   :header-rows: 1

   * - Value
     - Name
   * - ``0x80``
     - `half`
   * - ``0x81``
     - `one`
   * - ``0x82``
     - `two`
   * - ``0x83``
     - `four`
   * - ``0x84``
     - `eight`
   * - ``0x85``
     - `sixteen`
   * - ``0x86``
     - `thirtytwo`
   * - ``0x87``
     - `sixtyfour`
```

The talk-over level in the `DJMMYSETTING.DAT` files are encoded as follows:

```{eval-rst}
.. list-table:: Talk-over level encodings
   :widths: 25 75
   :header-rows: 1

   * - Value
     - Name
   * - ``0x80``
     - `minus_24db`
   * - ``0x81``
     - `minus_18db`
   * - ``0x82``
     - `minus_12db`
   * - ``0x83``
     - `minus_6db`

```

## References

[^footnote-1]: Jan Holthuis. rekordcrate. Module setting
    <https://holzhaus.github.io/rekordcrate/rekordcrate/setting/struct.Setting.html>
