# DJ Profile Format

A stick exported by Rekordbox carries one more file beside the analysis files and the databases:
`PIONEER/djprofile.nxs`. It holds the player name the deck shows, and it is 160 bytes.

## Structure

| Offset | Size | Meaning |
|--------|------|---------|
| `0x00` | 4 | a header word, the same on every profile measured so far |
| `0x04` | 4 | a second header word |
| `0x08` | 4 | a third |
| `0x0c` | 16 | zero |
| `0x1c` | 4 | an id the deck writes once and then carries along |
| `0x20` | 32 | the player name, single byte characters, zero padded |
| `0x40` | 96 | zero |

Only the name is understood well enough to change. The three header words and the id were never explained
by a measurement, so they are kept as they were read rather than guessed at: saving a profile writes the
name into its field and leaves every other byte alone.

## Reading and writing

````python
from pyrekordbox import DjProfile

profile = DjProfile.load("PIONEER/djprofile.nxs")
print(profile.name)

profile.name = "Radek Temp"
profile.save("PIONEER/djprofile.nxs")
````

A profile that is read and saved without touching the name is the same file byte for byte. A name longer
than the 32 byte field raises instead of being truncated, and a file that is not 160 bytes is refused.
