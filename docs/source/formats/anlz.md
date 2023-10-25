# Analysis Files Format

This document explains the file format of the Rekordbox ANLZ analysis files, which come
with the extionsions `.DAT`, `.EXT` and `.2EX`.

The following information was mainly taken from the excellent reverse engineering
work [^footnote-1] of the people behind DeepSymmetry's [crate-digger].
All figures were taken or modified from there as well.

## File Header

The file starts with the four-character code PMAI that identifies its format.
This file format identifier is followed a four-byte value, len_header (at bytes 04-07)
that specifies the length of the file header in bytes. This is followed by another
four-byte value, len_file, at bytes 08-0b that specifies the length of the whole
file in bytes:

```{figure} /_static/images/anlz_file.svg
:align: center
:scale: 100

File structure.
```

The header seems to usually be 1c bytes long, though we do not yet know the purpose
of the header values that come after len_file. After the header, the file
consists of a series of tagged sections, each with their own four-character code
identifying the section type, followed by a header and the section content.
This overall structure is illustrated in the above diagram, and the structure of the
known tag types is described next.

## Tagged File Sections

The structure of each tagged section has an “envelope” that can be understood even
if the internal structure of the section is unknown, making it easy to navigate
through the file looking for the section you need. This structure is very similar
to the file itself, and is illustrated below.

```{figure} /_static/images/anlz_tag.svg
:align: center
:scale: 100

Tagged section structure.
```

Every section begins with a four-character code, fourcc, identifying its specific
structure and content, as described in the sections below. This is followed by a
four-byte value, len_header, which specifies how many bytes there are in the section
header, and another four-byte value, len_tag, which specifies the length of the entire
tagged section (including the header), in bytes. This value can be added to the address
of the start of the tag to find the start of the next tag.

The order of the tags in the corresponding files is usually something like:

- `.DAT`: PPTH, PVBR, PQTZ, PWAV, PWV2, PCOB, PCOB
- `.EXT`: PPTH, PCOB, PCOB, PCO2, PCO2, PQT2, PWV3, PWV4, PWV5, PSSI
- `.2EX`: PPTH, PWV6, PWV7, PWVC

### PQTZ: Beat Grid Tag

Seen in `.DAT` analysis files. This kind of section holds a list of all beats found
within the track, recording their bar position, the time at which they occur,
and the tempo at that point. It has the structure shown below:

```{figure} /_static/images/anlz_pqtz.svg
:align: center
:scale: 100

Beat grid tag.
```

`len_header` is 24, while `unknown2` seems to always be `0x00800000`.
`len_beats` specifies the number of entries that will be present in this section.
The beat entries each have the following structure:

```{figure} /_static/images/anlz_beat.svg
:align: center
:scale: 100

Beat grid entry.
```

`beat_number` is a two-byte number specifies where the beat falls within its measure,
so the value is always 1, 2, 3 or 4. Next comes a two-byte `tempo` value, which records
the track tempo at the point of the beat. The tempo is given in beats per minute
multiplied by 100 to allow a precision of 0.01 BPM. Finally, there is a four-byte
`time` value, which specifies the time at which this beat would occur (in milliseconds).

### PQT2: Extended (nxs2) Beat Grid Tag

Seen in `.EXT` analysis files. There isn't much documentation on the structure or
purpose of this tag, but it seems like it always contains two beat grid entries.
It has the structure shown below:

```{figure} /_static/images/anlz_pqt2_2.svg
:align: center
:scale: 100

Extended beat grid tag.
```

`len_header` is 56. The first four bytes after `len_tag` are zero.
`unknown1` seems to always be `0x01000002`. Maybe this is another hint at the following
two beat grid entries. The format of the entries is the same as described in
the previous PQTZ tag.

After the two beat grid entries there is `entry_count`, which specifies the
number of entries. This number is almost always the same as the number of
entries in the PQTZ tag. The end of the header are three unknown
values.

The main entries of the Extended Beat Grid Tag are two bytes long. The format
of the entries is not yet known, but the first byte seems to always have a value between
0 and 3, so maybe this is an index for a beat?

### PCOB: Cue List Tag

Seen in `.DAT` and `.EXT` analysis files. This kind of section holds either a
list of ordinary memory points and loops, or a list of hot cues and hot loops.

```{figure} /_static/images/anlz_pcob.svg
:align: center
:scale: 100

Cue list tag.
```

The value of `len_header` is 24. The `type` value determines whether this section
holds memory points (0) or hot cues (1). The number of cue entries present in the
section is reported in `len_cues`. The meaning of `unk` or `memory_count` is not
yet known.

The remainder of the section, from byte 18 through `len_tag`, holds the cue entries
themselves, with the following structure:

```{figure} /_static/images/anlz_pcpt.svg
:align: center
:scale: 100

Cue list entry.
```

Each cue entry is 38 bytes long. It is structured as its own miniature tag,
starting with the four-character code `PCPT`, and its own internal four-byte
`len_header` and `len_entry` values (1c and 38 respectively).

If the cue is an ordinary memory point, `hot_cue` at will be zero, otherwise it
identifies the number of the hot cue that this entry represents
(Hot Cue A is number 1, B is 2, and so on). The `status` value is an indicator of
active loops; if it is zero, the entry is a regular cue point or loop.
Active loops have the value 4 here.

The next four bytes have an unknown purpose, but seem to always have the
value `0x00100000`. They are followed by two two-byte values, which seem to be for
sorting the cues in the proper order in some strange way. `order_first` (labeled `O_first`)
has the value `ffff` for the first cue, `0000` for the second, then 2, 3 and on.
`order_last` at bytes (labeled `O_last`) has the value 1 for the first cue,
2 for the second, and so on, but ffff for the last.
It would seem that the cues could be perfectly well sorted by just one of these fields,
or indeed, by their time values.

The first “non-header” field is `type` (labeled `t`), and it specifies whether the
entry records a simple position (if it has the value 1) or a loop (if it has the value 2).
The next three bytes have an unknown purpose, but seem to always have the value `0003e8`,
or decimal 1000.

The value `time` records the position of the cue within the track, as a number
of milliseconds (representing when the cue would occur if the track is being played at
normal speed). If type is 2, meaning that this cue stores a loop, then `loop_time`
stores the track time in milliseconds at which the player should loop back to time.

### PCO2: Extended (nxs2) Cue List Tag

Seen in `.EXT` analysis files. This is a variation of the Cue List Tag just described
that was introduced with the Nexus 2 players to add support for more than three hot
cues with custom color assignments, as well as DJ-assigned comment text for each hot
cue and memory point. It also contains the information present in the standard
\[Cue List Tag\](#pcob-cue-list-tag), so you only need to read one set or the other.

Just like the older tag, this kind of section holds either a list of ordinary memory
points and loops, or a list of hot cues and hot loops:

```{figure} /_static/images/anlz_pco2.svg
:align: center
:scale: 100

Extended cue list tag.
```

The value of `len_header` is 20. The `type` value determines whether this section
holds memory points (0) or hot cues (1). The number of cue entries present in the
section is reported in `len_cues`. The meaning of the remaining two header bytes
is unknown.

The remainder of the section, from byte 14 through `len_tag`, holds the cue entries
themselves, with the following structure:

```{figure} /_static/images/anlz_pcp2.svg
:align: center
:scale: 100

Extended cue list entry.
```

### PPTH: Path Tag

Seen in all analysis files. This kind of section holds the file path of the audio file
for which the track analysis was performed:

```{figure} /_static/images/anlz_ppth.svg
:align: center
:scale: 100

Path tag.
```

`len_header` is 16. The length of the string is stored in `len_path`. The actual
string, encoded as a UTF-16 Big endian string with a trailing `NULL` (`0x0000`)
charakter, is stored in `path`.

### PVBR: VBR Tag

Seen in `.DAT` analysis files. This tag is believed to hold an index allowing rapid
seeking to particular times within variable-bit-rate tracks. What is known of the
structure is shown below:

```{figure} /_static/images/anlz_pvbr.svg
:align: center
:scale: 100

VBR tag.
```

`len_header` is 16. It appears as if `len_tag` is always 1620. The last 4 bytes of
the header are unknown. The entries of the section are unsigned 32-bit integers.
Finally, the tag ends with an unknown 4 byte value.

Since the tag length seems to always be 1620 the body of the tag consists of 400
integer values. It is believed that these values are the frame-indices of the
times  within variable-bit-rate tracks. However, in most of the cases the entries
of the tag are all `0`.

### PSSI: Song Structure Tag

Seen in `.EXT` analysis files. This kind of section was originally used only in
Rekordbox Performance Mode, but starting with Rekordbox version 6 it also gets
exported to external media so CDJ-3000 players can use it to control lighting looks.

```{note}
The version that Rekordbox 6 **exports** is garbled with an XOR mask to make it
more difficult to access the data. All bytes after `len_e` are XOR-masked with a
pattern that is generated by adding the value of `len_e` to each byte of the following
base pattern:

CB E1 EE FA E5 EE AD EE E9 D2 E9 EB E1 E9 F3 E8 E9 F4 E1
```

The section has the folowwing strcture:

```{figure} /_static/images/anlz_pssi.svg
:align: center
:scale: 100

Song structure tag.
```

`len_header` is 32. `len_entry_bytes` identifies how many bytes each phrase entry takes up;
so far it always has the value 24. `len_entries` (labeled `len_e`) specifies how many
entries are present in the tag. Each entry represents one recognized phrase.

The value `mood` specifies the overall type of phrase structure that rekordbox chose to
represent the song, based on its analysis of the audio.

The value 1 is a “high” mood where the phrase types consist of “Intro”, “Up”, “Down”,
“Chorus”, and “Outro”. Other values in each phrase entry cause the intro, chorus, and
outro phrases to have their labels subdivided into styes “1” or “2”
(for example, “Intro 1”), and “up” is subdivided into style “Up 1”, “Up 2”, or “Up 3”.
See the table below for an expanded version of this description.

The value 2 is a “mid” mood where the phrase types are labeled “Intro”, “Verse 1”
through “Verse 6”, “Chorus”, “Bridge”, and “Outro”.

And value 3 is a “low” mood where the phrase types are labeled “Intro”, “Verse 1”,
“Verse 2”, “Chorus”, “Bridge”, and “Outro”. There are three different phrase type
values for each of “Verse 1” and “Verse 2”, but rekordbox makes no distinction between
them.

`end_beat` (labeled `end` in the diagram) holds the beat number at which the
last recognized phrase ends. The track may continue beyond this, but will mostly be
silence from then on.

`bank` identifies the stylistic bank which has been assigned to the track by the user
in Lighting mode. The value zero means the user has made no assignment, and this is
treated the same as if “Cool” has been chosen. The values and their meanings are
listed in the table below.

Each phrase entry has the structure shown below:

```{figure} /_static/images/anlz_pssi_entry.svg
:align: center
:scale: 100

Song structure entry.
```

The first two bytes of each song structure entry hold `index`, which numbers each phrase,
starting at one and incrementing with each entry. That is followed by beat,
a two-byte value that specifies the beat at which this phrase begins in the track.
It continues until either the beat number of the next phrase, or the beat identified
by end in the tag header if this is the last entry.

`kind` specifies what kind of phrase rekordbox has identified here.
The interpretation depends on the value of mood in the tag header, as is detailed the
table below. In the case of the “high” mood, there are numbered variations for some
of the phrases displayed in rekordbox that are not reflected in kind, but depend on the
values of three flag bytes `k1` through `k3` in a complicated way shown in its own table.

We also noticed that when `mood`, `kind` and the `k` flags indicate a phrase of type
“Up 3”, additional beat numbers (which all fall within the phrase) are present in the
entry. These may indicate points within the phrase at which lighting changes would look good;
more investigation is required to make sense of them.
The number of beats that will be listed seems to depend on the value of the flag `b`:
if this has the value 0, there will be a single beat found in `beat2`, and if `b` has
the value 1 there will be three different beat numbers present, with increasing values,
in `beat2`, `beat3` and `beat4`.

`fill` is a flag that indicates whether there are fill (non-phrase) beats at the end of
the phrase. If it is non-zero, then ``beat fill`` holds the beat number at which the
fill begins. When fill-in is present, it is indicated in rekordbox by little dots on the
full waveform. The manual says:


    [Fill in] is a section that provides improvisational changes at the end of phrase.
    [Fill in] is detected at the end of Intro, Up, and Chorus (up to 4 beats).



```{eval-rst}
.. list-table:: Phrase labels in each mood.
   :header-rows: 1

   * - Phrase ID
     - Low Label
     - Mid Label
     - High Label
   * - 1
     - Intro
     - Intro
     - Intro n
   * - 2
     - Verse 1
     - Verse 1
     - Up n
   * - 3
     - Verse 1
     - Verse 2
     - Down
   * - 4
     - Verse 1
     - Verse 3
     -
   * - 5
     - Verse 2
     - Verse 4
     - Chorus n
   * - 6
     - Verse 2
     - Verse 5
     - Outro n
   * - 7
     - Verse 2
     - Verse 6
     -
   * - 8
     - Bridge
     - Bridge
     -
   * - 9
     - Chorus
     - Chorus
     -
   * - 10
     - Outro
     - Outro
     -
```

```{eval-rst}
.. list-table:: High mood phrase variants.
   :header-rows: 1

   * - Phrase ID
     - k1
     - k2
     - k3
     - Expanded Label
   * - 1
     - 1
     -
     -
     - Intro 1
   * - 1
     - 0
     -
     -
     - Intro 2
   * - 2
     -
     - 0
     - 0
     - Up 1
   * - 2
     -
     - 0
     - 1
     - Up 2
   * - 2
     -
     - 1
     - 0
     - Up 3
   * - 3
     -
     -
     -
     - Down 1
   * - 5
     - 1
     -
     -
     - Chorus 2
   * - 5
     - 0
     -
     -
     - Chorus 1
   * - 6
     - 1
     -
     -
     - Outro 1
   * - 6
     - 0
     -
     -
     - Outro 2
```

```{eval-rst}
.. list-table:: Track banks.
   :header-rows: 1

   * - Bank ID
     - Label
   * - 0
     - Default (treated as Cool)
   * - 1
     - Cool
   * - 2
     - Natural
   * - 3
     - Hot
   * - 4
     - Subtle
   * - 5
     - Warm
   * - 6
     - Vivid
   * - 7
     - Club 1
   * - 8
     - Club 2
```

### PWAV: Waveform Preview Tag

Seen in `.DAT` analysis files. This kind of section holds a fixed-width monochrome
preview of the track waveform, displayed above the touch strip on original
Nexus players, providing a birds-eye view of the current playback position,
and supporting direct needle jump to specific track sections.

```{figure} /_static/images/anlz_pwav.svg
:align: center
:scale: 100

Waveform preview tag.
```

`len_header` is 20. The purpose of `unknown` is not understood, it always seems to have
the value `0x00100000`. The waveform preview data is 400 (decimal) bytes long.
Each byte encodes one vertical pixel-wide column of the waveform preview.
The height of the column is represented by the five low-order bits of the byte
(so it can range from 0 to 31 pixels high), and the whiteness of the segment is
represented by the three high-order bits. Segments with higher values in these three
bits are drawn in a less saturated (whiter) shade of blue.

### PWV2: Tiny Waveform Preview Tag

Seen in `.DAT` analysis files. This kind of section holds an even smaller fixed-width
monochrome preview of the track waveform, which seems to be displayed on the CDJ-900.
It is identified by the four-character code `PWV2` but otherwise has the same structure
as the larger waveform preview tags {ref}`PWAV <PWAV: Waveform Preview Tag>`.

### PWV3: Waveform Detail Tag

Seen in `.EXT` analysis files. This kind of section holds a variable-width and much
larger monochrome rendition of the track waveform, which scrolls along while the
track plays, giving a detailed glimpse of the neighborhood of the current playback
position:

```{figure} /_static/images/anlz_pwv3.svg
:align: center
:scale: 100

Waveform detail tag.
```

`len_header` is 24. `len_entry_bytes` identifies how many bytes each waveform detail
entry takes up; for this kind of tag it always has the value 1. `len_entries` specifies
how many entries are present in the tag. Each entry represents one half-frame of audio
data, and there are 75 frames per second, so for each second of track audio there are
150 waveform detail entries. The purpose of the header `unknown` is not known yet;
they always seem to have the value `0x00960000`. The interpretation of each byte of the
entriesis the same as for {ref}`PWAV <PWAV: Waveform Preview Tag>`.

### PWV4: Waveform Color Preview Tag

Seen in `.EXT` analysis files. This kind of section holds a fixed-width color preview
of the track waveform, displayed above the touch strip on Nexus 2 players, providing
a birds-eye view of the current playback position, and supporting direct needle jump
to specific track sections. It is also used in rekordbox itself.

```{figure} /_static/images/anlz_pwv4.svg
:align: center
:scale: 100

Waveform color preview tag.
```

`len_header` is 24. `len_entry_bytes` identifies how many bytes each waveform preview
entry takes up; for this kind of tag it always has the value 6. `len_entries` specifies
how many entries are present in the tag. The purpose of `unknown` is unknown.
The waveform color preview data is 7,200 (decimal) bytes long, representing 1,200 columns
of waveform preview information.

The color waveform preview entries are the most complex of the waveform tags.

### PWV5: Waveform Color Detail Tag

Seen in `.EXT` analysis files. This kind of section holds a variable-width and much
larger color rendition of the track waveform, introduced with the nexus 2 line
(and also used in rekordbox), which scrolls along while the track plays, giving a
detailed glimpse of the neighborhood of the current playback position.

```{figure} /_static/images/anlz_pwv5.svg
:align: center
:scale: 100

Waveform color detail tag.
```

`len_header` is 24. `len_entry_bytes` identifies how many bytes each waveform preview
entry takes up; for this kind of tag it always has the value 6. `len_entries` specifies
how many entries are present in the tag. The purpose of `unknown` is unknown, but
it always has the value 960305. Each entry represents one half-frame of audio
data, and there are 75 frames per second, so for each second of track audio there are
150 waveform detail entries.

Color detail entries are much simpler than color preview entries. They consist of
three-bit red, green, and blue components and a five-bit height component packed into
the sixteen bits of the two entry bytes:

```{figure} /_static/images/anlz_pwv5_entry.svg
:align: center
:scale: 100

Waveform color detail entry bits.
```

### PWV6

Seen in `.2EX` analysis files.

```{figure} /_static/images/anlz_pwv6.svg
:align: center
:scale: 100

Waveform 6 tag.
```

`len_header` is 20. `len_entry_bytes` identifies how many bytes each waveform preview
entry takes up; for this kind of tag it always has the value 3. `len_entries` specifies
how many entries are present in the tag.

### PWV7

Seen in `.2EX` analysis files.

```{figure} /_static/images/anlz_pwv7.svg
:align: center
:scale: 100

PWV7 tag.
```

`len_header` is 24. `len_entry_bytes` identifies how many bytes each waveform preview
entry takes up; for this kind of tag it always has the value 6. `len_entries` specifies
how many entries are present in the tag. The purpose of `unknown` is unknown, but
it always has the value 9830400 or `0x00960000`.

### PWVC

Seen in `.2EX` analysis files.

```{figure} /_static/images/anlz_pwvc.svg
:align: center
:scale: 100

PWVC tag.
```

`len_header` is 14. The remaining two bytes of the header are unknown. The enries are
not understood either, but it seems like `len_tag` is always 20, so the
6 byte long entry data could be parsed to three 2-byte integers. Are
these maybe RBG values? But for what?

## References

[^footnote-1]: Rekordbox Export Structure Analysis: Analysis Files.
    <https://djl-analysis.deepsymmetry.org/rekordbox-export-analysis/anlz.html>.

[^footnote-2]: <https://github.com/Deep-Symmetry/crate-digger/issues/22>

[crate-digger]: https://github.com/Deep-Symmetry/crate-digger
