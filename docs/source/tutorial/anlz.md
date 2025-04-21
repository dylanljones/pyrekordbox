# Analysis Files

Rekordbox stores analysis information of the tracks in the collection in specific files,
which also get exported to decives used by Pioneer professional DJ equipment. The files
have names like `ANLZ0000` and come with the extensions `.DAT`, `.EXT` or `.2EX`.
They include waveforms, beat grids (information about the precise time at which
each beat occurs), time indices to allow efficient seeking to specific positions
inside variable bit-rate audio streams, and lists of memory cues and loop points.

```{seealso}
See the {ref}`Analysis Files Format<Analysis Files Format>` documentation for more information.
```

## Reading and writing ANLZ Files

To read an ANLZ file, you can use the `AnlzFile.parse_file` method:

```python
from pyrekordbox import AnlzFile

# Read a single ANLZ file
anlz = AnlzFile.parse_file("path/to/ANLZXXXX.DAT")
```

You can also read multiple ANLZ files for a single track using the `read_anlz_files` function.
It takes the root directory of the files as argument:

```python
from pyrekordbox import read_anlz_files

# Read all ANLZ files for a track
files = read_anlz_files("path/to/anlz_directory")
```

After modifiying the contents of a ANLZ file, it can be saved via
```python
# Save the ANLZ file contents
anlz.save("path/to/ANLZXXXX.DAT")
```


To find the ANLZ files corresponding to a specific track in the Rekordbox collection,
the database handler includes a method that returnes the directory containing the ANLZ files:
```python
>>> from pyrekordbox import Rekordbox6Database
>>> db = Rekordbox6Database()
>>> content = db.get_content().first()
>>> db.get_anlz_dir(content)
C:\Users\user\AppData\Roaming\Pioneer\rekordbox\share\PIONEER\USBANLZ\0e8\0d4cc-06a6-4574-ba18-1c2301ea9924
```

Alternatively, a dictionary containing the paths of the ANLZ files can be found via
```python
>>> db.get_anlz_paths(content)
{
    'DAT': 'C:/Users/user/AppData/Roaming/Pioneer/rekordbox/share/PIONEER/USBANLZ/0e8/0d4cc-06a6-4574-ba18-1c2301ea9924/ANLZ0000.DAT',
    'EXT': 'C:/Users/user/AppData/Roaming/Pioneer/rekordbox/share/PIONEER/USBANLZ/0e8/0d4cc-06a6-4574-ba18-1c2301ea9924/ANLZ0000.EXT',
    '2EX': None
}
```
In this example, the analysis data of the track is stored in only two ANLZ files, `ANLZ0000.DAT` and `ANLZ0000.EXT`.
Instead of returning the paths of the analysis files, they can also be read directly via
```python
db.read_anlz_files(content)
```


## Accessing ANLZ Data

The `AnlzFile` object implements a dictionary-like interface. You can access tags by their type code or name:

```python
# Check if a tag exists
if "beat_grid" in anlz:
    print("Beat grid found")

# Get the first tag of a specific type
beat_grid = anlz.get_tag("PQTZ")
# or by name
beat_grid = anlz.get_tag("beat_grid")

# Get all tags of a specific type
all_cues = anlz.getall_tags("PCOB")
```

```{note}
More coming soon!
```
