# XML Database Format

The Rekordbox XML format is well documented by Pioneer in [^footnote-1] and [^footnote-2].

The first entry of the XML file should be displayed as follows:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
```

```{warning}
In order to save playlists and their information to Rekordbox, all rows from the
second row and beyond must follow a format which rekordbox supports.
```

## General structure

The general structure of the Rekordbox XML file is as follows:

```xml
<?xml version="1.0" encoding="UTF-8" ?>

<DJ_PLAYLISTS Version="1.0.0">
        <PRODUCT Name="rekordbox" Version="5.4.3" Company="Pioneer DJ"/>
        <COLLECTION Entries="1234">
                <TRACK TrackID="1" Name="NOISE" Artist="" Composer="" Album="" Grouping=""
                           Genre="" Kind="WAV File" Size="1382226" TotalTime="5" DiscNumber="0"
                           TrackNumber="0" Year="0" AverageBpm="0.00" DateAdded="2017-09-07"
                           BitRate="2116" SampleRate="44100" Comments="" PlayCount="0" Rating="0"
                           Location="file://localhost/C:/Users/user/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/NOISE.wav"
                           Remixer="" Tonality="" Label="" Mix=""/>
                <TRACK TrackID="2" Name="SINEWAVE" Artist="" Composer="" Album="" Grouping=""
                           Genre="" Kind="WAV File" Size="1515258" TotalTime="5" DiscNumber="0"
                           TrackNumber="0" Year="0" AverageBpm="0.00" DateAdded="2017-09-07"
                           BitRate="2116" SampleRate="44100" Comments="" PlayCount="0" Rating="0"
                           Location="file://localhost/C:/Users/user/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/SINEWAVE.wav"
                           Remixer="" Tonality="" Label="" Mix="">
                        <TEMPO Inizio="0.232" Bpm="172.00" Metro="4/4" Battito="1"/>
                        <POSITION_MARK Name="" Type="0" Start="0.232" Num="-1"/>
                        ...
                </TRACK>
                ...
        </COLLECTION>
        <PLAYLISTS>
                <NODE Type="0" Name="ROOT" Count="11">
                        <NODE Name="Favourites" Type="1" KeyType="0" Entries="56">
                                <TRACK Key="1"/>
                                <TRACK Key="2"/>
                                ...
                        </NODE>
                </NODE>
                ...
        </PLAYLISTS>
</DJ_PLAYLISTS>
```

## Supported Elements and Attributes

```{eval-rst}
.. list-table:: Supported Rekordbox XML elements and attributes
   :widths: 1 1 1 1
   :header-rows: 1

   * - Element
     - Description
     - Type
     - Notes
   * - **DJ_PLAYLIST**
     -
     -
     -
   * - *Version*
     - Version of XML format
     - utf-8
     - The latest version is 1.0.0
   * - **PRODUCT**
     -
     -
     -
   * - *Name*
     - Name of product
     - utf-8
     - This name will be displayed in each application software.
   * - *Version*
     - Version of application
     - utf-8
     -
   * - *Company*
     - Name of company
     - utf-8
     -
   * - **COLLECTION**
     -
     -
     -
   * - *Entries*
     - Number of TRACK in COLLECTION
     - sint32
     -
   * - **TRACK**
     -
     -
     - "Location" is essential for each track
   * - *TrackID*
     - Identification of track
     - utf-8
     -
   * - *Name*
     - Name of track
     - utf-8
     -
   * - *Artist*
     - Name of artist
     - utf-8
     -
   * - *Composer*
     - Name of composer (or producer)
     - utf-8
     -
   * - *Album*
     - Name of album
     - utf-8
     -
   * - *Grouping*
     - Name of group
     - utf-8
     -
   * - *Genre*
     - Name of genre
     - utf-8
     -
   * - *Kind*
     - Type of audio file
     - utf-8
     -
   * - *Size*
     - Size of audio file
     - sint64
     - Unit: Octet
   * - *TotalTime*
     - Duration of track
     - float64
     - Unit: Second (without decimal numbers)
   * - *DiscNumber*
     - Number of the disc of the album
     - sint32
     -
   * - *TrackNumber*
     - Number of the track of the album
     - sint32
     -
   * - *Year*
     - Year of release
     - sint32
     -
   * - *AverageBpm*
     - Value of average BPM
     - float64
     - Unit: Second (with decimal numbers)
   * - *DateModified*
     - Date of last modification
     - utf-8
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - *DateAdded*
     - Date of addition
     - utf-8
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - *BitRate*
     - Encoding bit rate
     - sint32
     - Unit: Kbps
   * - *SampleRate*
     - Frequency of sampling
     - float64
     - Unit: Hertz
   * - *Comments*
     - Comments
     - utf-8
     -
   * - *PlayCount*
     - Play count of the track
     - sint32
     -
   * - *LastPlayed*
     - Date of last playing
     - utf-8
     - Format: yyyy-mm-dd; ex.: 2010-08-21
   * - *Rating*
     - Rating of the track
     - sint32
     - 0="0", 1="51", 2="102", 3="153", 4="204", 5="255"
   * - *Location*
     - Location of the file
     - utf-8 (URI)
     - includes the file name
   * - *Remixer*
     - Name of remixer
     - utf-8
     -
   * - *Tonality*
     - Tonality (Kind of musical key)
     - utf-8
     -
   * - *Label*
     - Name of record label
     - utf-8
     -
   * - *Mix*
     - Name of mix
     - utf-8
     -
   * - *Colour*
     - Colour for track grouping
     - utf-8
     - RGB format (3 bytes)
   * - **TEMPO**
     -
     -
     - BeatGrid; More than two "TEMPO" can exist for each track
   * - *Inizio*
     - Start position of BeatGrid
     - float64
     - Unit: Second (with decimal numbers)
   * - *Bpm*
     - Value of BPM
     - float64
     - Unit: Second (with decimal numbers)
   * - *Metro*
     - Kind of musical meter
     - utf-8
     - ex. 3/4, 4/4, 7/8 ...
   * - *Battito*
     - Beat number in the bar
     - sint32
     - If "Metro" is 4/4, the value should be 1, 2, 3 or 4
   * - **POSITION_MARK**
     -
     -
     - More than two "POSITION MARK" can exist for each track
   * - *Name*
     - Name of position mark
     - utf-8
     -
   * - *Type*
     - Type of position mark
     - sint32
     - Cue="0", Fade-In="1", Fade-Out="2", Load="3", Loop="4"
   * - *Start*
     - Start position of position mark
     - float64
     - Unit: Second (with decimal numbers)
   * - *End*
     - End position of position mark
     - float64
     - Unit: Second (with decimal numbers)
   * - *Num*
     - Number of the position mark
     - sint32
     - Hot Cue: A="0", B="1", C="2"; Memory Cue: "-1"

```

Playlists are a bit more complex since they are nested:

```{eval-rst}
.. list-table:: Supported Rekordbox XML playlist elements and attributes
   :widths: 1 1 1 1
   :header-rows: 1

   * - Element
     - Description
     - Type
     - Notes
   * - **NODE**
     -
     -
     -
   * - *Type*
     - Type of NODE
     - sint32
     - "0" (FOLDER)
   * - *Name*
     - Name of NODE
     - utf-8
     - ("ROOT")
   * - *Count*
     - Number of items in the NODE
     - sint32
     -
   * - **NODE**
     -
     -
     -
   * - *Type*
     - Type of NODE
     - sint32
     - "0" (FOLDER)
   * - *Name*
     - Name of NODE
     - utf-8
     - ("ROOT")
   * - (if "Type" == "1")
     -
     -
     - Node is a PLAYLIST
   * - *Entries*
     - Number of TRACK in PLAYLIST
     - sint32
     -
   * - *KeyType*
     - Kind of identification
     - sint32
     - "0" (Track ID) or "1"(Location)
   * - **TRACK**
     -
     -
     -
   * - *Key*
     - Identification of track
     - sint32/utf-8
     -
   * - (if "Type" == "0")
     -
     -
     - Node is a FOLDER
   * - *Count*
     - Number of items in the NODE
     - sint32
     -

```

Rekordbox track colors:

```{eval-rst}
.. list-table:: Rekordbox group colors
   :widths: 1 1 1
   :header-rows: 1

   * - Name
     - Hex
     - RGB
   * - Rose
     - 0xFF007F
     - 255, 0, 127
   * - Red
     - 0xFF0000
     - 255, 0, 0
   * - Orange
     - 0xFFA500
     - 255, 165, 0
   * - Lemon
     - 0xFFFF00
     - 255, 255, 0
   * - Green
     - 0x00FF00
     - 0, 255, 0
   * - Turquoise
     - 0x25FDE9
     - 37, 253, 233
   * - Blue
     - 0x0000FF
     - 0, 0, 255
   * - Violet
     - 0x660099
     - 102, 0, 153

```

## References

[^footnote-1]: Rekordbox for developers.
    <https://rekordbox.com/en/support/developer/>

[^footnote-2]: Rekordbox XML format
    <https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf>
