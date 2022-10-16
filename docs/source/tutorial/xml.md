# XML Database

We will use the Rekordbox 6 database from the test data as an example:

```python
import os
path = os.path.join(".testdata", "rekordbox 5", "database.xml")
```

An existing XML database can be parsed by passing the file path to the ``RekordboxXml``
constructor:
```python
from pyrekordbox import RekordboxXml
xml = RekordboxXml(path)
print(xml.tostring())
```

Printing the contents results in the following output:
```xml
<?xml version="1.0" encoding="utf-8"?>
<DJ_PLAYLISTS Version="1.0.0">
    <PRODUCT Name="rekordbox" Version="6.6.2" Company="AlphaTheta"/>
    <COLLECTION Entries="6">
        <TRACK TrackID="253529738" Name="Demo Track 1" Artist="Loopmasters" Composer="" Album="" Grouping="" Genre="" Kind="Mp3-Datei " Size="6899624" TotalTime="172" DiscNumber="0" TrackNumber="0" Year="0" AverageBpm="128.00" DateAdded="2022-04-09" BitRate="320" SampleRate="44100" Comments="Tracks by www.loopmasters.com" PlayCount="0" Rating="0" Location="file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3" Remixer="" Tonality="Fm" Label="Loopmasters" Mix="">
            <TEMPO Inizio="0.025" Bpm="128.00" Metro="4/4" Battito="1"/>
        </TRACK>
        <TRACK TrackID="17109519" Name="Demo Track 2" Artist="Loopmasters" Composer="" Album="" Grouping="" Genre="" Kind="Mp3-Datei " Size="5124342" TotalTime="128" DiscNumber="0" TrackNumber="0" Year="0" AverageBpm="120.00" DateAdded="2022-04-09" BitRate="320" SampleRate="44100" Comments="Tracks by www.loopmasters.com" PlayCount="0" Rating="0" Location="file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%202.mp3" Remixer="" Tonality="Fm" Label="Loopmasters" Mix="">
            <TEMPO Inizio="0.025" Bpm="120.00" Metro="4/4" Battito="1"/>
            <TEMPO Inizio="48.026" Bpm="120.00" Metro="4/4" Battito="1"/>
            <TEMPO Inizio="48.525" Bpm="120.00" Metro="4/4" Battito="2"/>
            <TEMPO Inizio="49.026" Bpm="120.00" Metro="4/4" Battito="3"/>
            <TEMPO Inizio="49.525" Bpm="120.00" Metro="4/4" Battito="4"/>
            <TEMPO Inizio="50.026" Bpm="120.00" Metro="4/4" Battito="1"/>
            <TEMPO Inizio="50.525" Bpm="120.00" Metro="4/4" Battito="2"/>
            <TEMPO Inizio="51.026" Bpm="120.00" Metro="4/4" Battito="3"/>
            <TEMPO Inizio="51.525" Bpm="120.00" Metro="4/4" Battito="4"/>
            <TEMPO Inizio="52.026" Bpm="120.00" Metro="4/4" Battito="1"/>
        </TRACK>
        <TRACK TrackID="49557014" Name="HORN" Artist="" Composer="" Album="" Grouping="" Genre="" Kind="Wav-Datei " Size="2010816" TotalTime="7" DiscNumber="0" TrackNumber="0" Year="0" AverageBpm="0.00" DateAdded="2022-04-09" BitRate="2116" SampleRate="44100" Comments="" PlayCount="0" Rating="0" Location="file://localhost/C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/HORN.wav" Remixer="" Tonality="" Label="" Mix=""/>
        <TRACK TrackID="209873516" Name="NOISE" Artist="" Composer="" Album="" Grouping="" Genre="" Kind="Wav-Datei " Size="1382226" TotalTime="5" DiscNumber="0" TrackNumber="0" Year="0" AverageBpm="0.00" DateAdded="2022-04-09" BitRate="2116" SampleRate="44100" Comments="" PlayCount="0" Rating="0" Location="file://localhost/C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/NOISE.wav" Remixer="" Tonality="" Label="" Mix=""/>
        <TRACK TrackID="55231398" Name="SINEWAVE" Artist="" Composer="" Album="" Grouping="" Genre="" Kind="Wav-Datei " Size="1515258" TotalTime="5" DiscNumber="0" TrackNumber="0" Year="0" AverageBpm="0.00" DateAdded="2022-04-09" BitRate="2116" SampleRate="44100" Comments="" PlayCount="0" Rating="0" Location="file://localhost/C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/SINEWAVE.wav" Remixer="" Tonality="" Label="" Mix=""/>
        <TRACK TrackID="92396897" Name="SIREN" Artist="" Composer="" Album="" Grouping="" Genre="" Kind="Wav-Datei " Size="1941204" TotalTime="7" DiscNumber="0" TrackNumber="0" Year="0" AverageBpm="0.00" DateAdded="2022-04-09" BitRate="2116" SampleRate="44100" Comments="" PlayCount="0" Rating="0" Location="file://localhost/C:/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/SIREN.wav" Remixer="" Tonality="" Label="" Mix=""/>
    </COLLECTION>
    <PLAYLISTS>
        <NODE Type="0" Name="ROOT" Count="1">
            <NODE Name="Trial playlist - Cloud Library Sync" Type="1" KeyType="0" Entries="0"/>
        </NODE>
    </PLAYLISTS>
</DJ_PLAYLISTS>
```

## Tracks

Individual tracks in the collection can be fetched by supplying an index
````
>>> xml.get_track(0)
<Track(Location=C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3)>
````
or the `TrackID`:
````
>>> xml.get_track(TrackID=253529738)
<Track(Location=C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3)>
````

All items in the collection can be fetched via
````
>>> tracks = xml.get_tracks()
>>> tracks[0]
<Track(Location=C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3)>
````

The XML attributes of a `Track` element are accessable as an attribute of the ``Track``
object or via a dict-interface:
````python
>>> track = xml.get_track(0)
>>> track.Name
Demo Track 1

>>> track["Name"]
Demo Track 1
````

Each track can contain a ``Tempo`` or ``PositionMark`` element. The ``Tempo`` element
stores the beat grid information:
````python
>>> track = xml.get_track(0)
>>> tempo = track.tempos[0]
>>> tempo.Bpm
128.0
````

and the ``PositionMark`` element stores the cue points of a track (not included in the XML example above):
````python
>>> track = xml.get_track(0)
>>> mark = track.marks[0]
>>> mark.Type
cue

>>> mark.Start
0.0

>>> mark.Num
-1
````

```{seealso}
See the {ref}`XML Database Format<XML Database Format>` documentation for a list of valid
attributes. All XML attributes start with a capital letter.
```


## Playlists

Playlists or playlist folders can be accessed by supplying the path:
````python
folder = xml.get_playlist("Folder")
paylist = xml.get_playlist("Folder", "Sub Playlist")
````
Content in a playlist is stored as a key, which can either be the ``TrackID`` or the
``Location`` (file path):
````python
>>> playlist.key_type
TrackID
````

The keys can be retrieved by calling
````python
keys = playlist.get_tracks()
````

A new track can be added to a playlist by specifying the corresponding key:
````python
playlist.add_track(track_key)
````

A new sub-folder or -playlist can be added by supplying the name:
````python
folder.add_playlist("Playlist")
folder.add_playlist_folder("Folder")
````
