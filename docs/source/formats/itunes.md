# Itunes XML Format

The Itunes XML format is used by Apple's Itunes software to store information about tracks, playlists, and other data.
The format is based on XML and is human-readable. The format is used by Rekordbox to import playlists from Itunes.

````{note}
Not all features of the Itunes XML format are supported,
only the elements and attributes used by Rekordbox.
````


The first lines of the XML file should be displayed as follows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
```

## General structure

The general structure of the Rekordbox XML file is as follows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Major Version</key><integer>1</integer>
	<key>Minor Version</key><integer>1</integer>
	<key>Application Version</key><string>12.11.3.17</string>
	<key>Date</key><date>2024-01-07T03:30:56</date>
	<key>Features</key><integer>5</integer>
	<key>Show Content Ratings</key><true />
	<key>Library Persistent ID</key><string>E116CD8C3BA8AC5D</string>
	<key>Tracks</key>
	<dict>
		<key>1</key>
		<dict>
			<key>Track ID</key><integer>1</integer>
			<key>Persistent ID</key><string>746809D638F42895</string>
			<key>Location</key><string>file://localhost/C:/Users/user/Music/PioneerDJ/Sampler/OSC_SAMPLER/PRESET%20ONESHOT/NOISE.wav</string>
			<key>Name</key><string>NOISE</string>
		</dict>
	</dict>
	<key>Playlists</key>
	<array>
		<dict>
			<key>Master</key><true />
			<key>Playlist ID</key><integer>1</integer>
			<key>Playlist Persistent ID</key><string>EF98A43F1B09E435</string>
			<key>All Items</key><true />
			<key>Visible</key><false />
			<key>Name</key><string>Library</string>
			<key>Playlist Items</key>
			<array>
				<dict>
					<key>Track ID</key><integer>1</integer>
				</dict>
			</array>
		</dict>
		<dict>
			<key>Playlist ID</key><integer>1</integer>
			<key>Playlist Persistent ID</key><string>B323CD428E351B3C</string>
			<key>Name</key><string>Test Playlist</string>
			<key>All Items</key><true />
			<key>Playlist Items</key>
			<array>
				<dict>
					<key>Track ID</key><integer>1</integer>
				</dict>
			</array>
		</dict>
	</array>
	<key>Music Folder</key><string>file://localhost/C:/Users/user/Music/iTunes/iTunes%20Media</string>
</dict>
</plist>
```

Attributes are stored as key-value pairs in a dictionary with the type as the XML tag
of the value item, for example:
```xml
<key>Name</key><string>NOISE</string>
<key>Play Count</key><integer>1</integer>
```

One exception are boolean types, where the value is stored as the XML tag:
```xml
<key>Compilation</key><true/>
<key>Clean</key><false/>
```


## Supported Elements and Attributes

### Tracks


```{eval-rst}
.. list-table:: Supported Track elements
   :widths: 1 1 1 1
   :header-rows: 1

   * - Element
     - Type
     - Description
     - Notes
   * - Track ID
     - integer
     - Track ID
     - required
   * - Persistent ID
     - string
     - Persistent ID
     - required
   * - Location
     - string
     - File location
     - encoded as utf-8 (URI), required
   * - Album
     - string
     - Album name
     -
   * - Album Artist
     - string
     - Album artist name
     -
   * - Artist
     - string
     - Artist name
     -
   * - Artwork Count
     - integer
     - Number of artworks
     -
   * - BPM
     - integer
     - Beats per minute
     -
   * - Bit Rate
     - integer
     - Bit rate in kbps
     -
   * - Clean
     - bool
     - Is the track clean
     -
   * - Comments
     - string
     - Comments
     -
   * - Compilation
     - bool
     - Is the track a compilation
     -
   * - Composer
     - string
     - Composer name
     -
   * - Date Added
     - date
     - Date added
     -
   * - Date Modified
     - date
     - Date modified
     -
   * - Disc Count
     - integer
     - Number of discs
     -
   * - Disc Number
     - integer
     - Disc number
     -
   * - File Folder Count
     - integer
     - Number of file folders
     -
   * - Genre
     - string
     - Genre name
     -
   * - Grouping
     - string
     - Grouping name
     -
   * - Has Video
     - bool
     - Does the track have a video
     -
   * - Kind
     - string
     - File type
     -
   * - Library Folder Count
     - integer
     - Number of library folders
     -
   * - Loved
     - bool
     - Is the track loved
     -
   * - Name
     - string
     - Track title
     -
   * - Part Of Gapless Album
     - bool
     - Is the track part of a gapless album
     -
   * - Play Count
     - integer
     - Play count
     -
   * - Play Date
     - date
     - Play date
     -
   * - Play Date UTC
     - date
     - Play date UTC
     -
   * - Purchased
     - bool
     - Is the track purchased
     -
   * - Release Date
     - date
     - Release date
     -
   * - Sample Rate
     - integer
     - Sample rate in Hz
     -
   * - Size
     - integer
     - File size in bytes
     -
   * - Skip Count
     - integer
     - Skip count
     -
   * - Skip Date
     - date
     - Skip date
     -
   * - Sort Album
     - string
     - Sort album name
     -
   * - Sort Album Artist
     - string
     - Sort album artist name
     -
   * - Sort Artist
     - string
     - Sort artist name
     -
   * - Sort Composer
     - string
     - Sort composer name
     -
   * - Sort Name
     - string
     - Sort track title
     -
   * - Total Time
     - integer
     - Total time in milliseconds
     -
   * - Track Count
     - integer
     - Number of tracks
     -
   * - Track Number
     - integer
     - Track number
     -
   * - Track Type
     - string
     - Track type
     -
   * - Volume Adjustment
     - integer
     - Volume adjustment in dB
     -
   * - Work
     - string
     - Label name
     -
   * - Year
     - integer
     - Year
     -
```

### Playlists

```{note}
The Master playlist is the main playlist of the library and contains *all* tracks.
```

Playlists are stored in the `Playlists` array.
Each playlist is a dictionary with some information and the `Playlist Items` array,
which contains the tracks of the playlist as a list of dictionaries with the `Track ID` of the track.

```xml
<key>Playlist Items</key>
<array>
  <dict>
    <key>Track ID</key><integer>1</integer>
  </dict>
</array>
```

Playlists can have the following attributes:
```{eval-rst}
.. list-table:: Supported Playlist elements
   :widths: 1 1 1 1
   :header-rows: 1

   * - Element
     - Type
     - Description
     - Notes
   * - Playlist ID
     - integer
     - Playlist ID
     - required
   * - Playlist Persistent ID
     - string
     - Persistent ID
     - required
   * - Parent Persistent ID
     - string
     - Persistent ID of parent
     - required
   * - Playlist Items
     - array
     - Items in the playlist
     -
   * - All Items
     - bool
     - ?
     - usually true
   * - Name
     - string
     - Playlist name
     -
```

The Master playlist additionally has a ``Visible`` attribute, which is set to ``false``.

There are more playlist attributes, but they are not relevant for Rekordbox.
