# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

r"""Rekordbox XML database file handler."""

import logging
import os.path
import urllib.parse
import xml.etree.cElementTree as xml
from abc import abstractmethod
from collections import abc
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Set, Union

import bidict

from .utils import pretty_xml

logger = logging.getLogger(__name__)


URL_PREFIX = "file://localhost/"
POSMARK_TYPE_MAPPING = bidict.bidict(
    {
        "0": "cue",
        "1": "fadein",
        "2": "fadeout",
        "3": "load",
        "4": "loop",
    }
)
RATING_MAPPING = bidict.bidict({"0": 0, "51": 1, "102": 2, "153": 3, "204": 4, "255": 5})
NODE_KEYTYPE_MAPPING = bidict.bidict({"0": "TrackID", "1": "Location"})


class XmlElementNotInitializedError(Exception):
    """Raised when an XML element is not initialized."""

    def __init__(self, name: str) -> None:
        super().__init__(f"XML element {name} is not initialized!")


class RootNodeNotInitializedError(Exception):
    """Raised when the root paylist node is not initialized."""

    def __init__(self) -> None:
        super().__init__("Playlist root node is not initialized!")


class XmlDuplicateError(Exception):
    """Raised when a track already exists in the XML database."""

    def __init__(self, key_type: str, key: str) -> None:
        super().__init__(f"XML database already contains a track with {key_type}={key}")


class XmlAttributeKeyError(Exception):
    def __init__(self, cls: Any, key: str, attributes: List[str]) -> None:
        super().__init__(
            f"{key} is not a valid key for {cls.__name__}! Valid attribs:\n{attributes}"
        )


def encode_path(path: Union[str, Path]) -> str:
    r"""Encodes a file path as URI string.

    Parameters
    ----------
    path : str or Path
        The file path to encode.

    Returns
    -------
    url : str
        The encoded file path as URI string.

    Examples
    --------
    >>> s = r"C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3"  # noqa: W605
    >>> encode_path(s)
    file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3

    """
    url_path = urllib.parse.quote(str(path), safe=":/\\")
    url = URL_PREFIX + url_path.replace("\\", "/")
    return url


def decode_path(url: str) -> str:
    r"""Decodes an as URI string encoded file path.

    Parameters
    ----------
    url : str
        The encoded file path to decode.

    Returns
    -------
    path : str
        The decoded file path.

    Examples
    --------
    >>> s = r"file://localhost/C:/Music/PioneerDJ/Demo%20Tracks/Demo%20Track%201.mp3"
    >>> decode_path(s)
    C:\Music\PioneerDJ\Demo Tracks\Demo Track 1.mp3  # noqa: W605

    """
    path = urllib.parse.unquote(url)
    path = path.replace(URL_PREFIX, "")
    return os.path.normpath(path)


class AbstractElement(abc.Mapping):  # type: ignore[type-arg]
    """Abstract base class for Rekordbox XML elements.

    Implements attribute getters and setters for an XML element
    """

    TAG: str
    """str: Name of the XML element"""

    ATTRIBS: List[str]
    """list[str]: List of all attribute keys of the XML element"""

    GETTERS: Dict[str, Callable[[Any], Any]] = dict()
    """dict[str, Callable]: Dictionary of attribute getter conversion methods.

    See Also
    --------
    AbstractElement.get
    """
    SETTERS: Dict[str, Callable[[Any], Any]] = dict()
    """dict[str, Callable]: Dictionary of attribute setter conversion methods.

    See Also
    --------
    AbstractElement.set
    """

    def __init__(self, element: xml.Element = None, *args: Any, **kwargs: Any):
        self._element: Union[xml.Element, None] = element
        if element is None:
            self._init(*args, **kwargs)
        else:
            self._load_subelements()

    @abstractmethod
    def _init(self, *args: Any, **kwargs: Any) -> None:
        """Initializes a new XML element."""
        pass

    def _load_subelements(self) -> None:
        """Loads the sub-elements of an existing XML element."""
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Returns the value of an attribute of the XML element.

        The type of the attribute value is converted if a conversion method is specified
        in the ``GETTERS`` class attribute. If no conversion method is found the value
        is returned unconverted as the default type ``str``.

        Parameters
        ----------
        key : str
            The key of the attribute.
        default : Any, optional
            The default value returned if the attribute does not exist.

        Returns
        -------
        value : Any
            The value of the atttribute. The type of the attribute is converted
            acccording to the data of the field.

        Raises
        ------
        XmlAttributeKeyError:
            Raised if `key` is not a valid attribute key.
        """
        if key not in self.ATTRIBS:
            raise XmlAttributeKeyError(self.__class__, key, self.ATTRIBS)
        if self._element is None:
            raise XmlElementNotInitializedError("_element")

        value = self._element.attrib.get(key, default)
        if value == default:
            return default
        try:
            # Apply callback
            value = self.GETTERS[key](value)
        except KeyError:
            pass
        return value

    def set(self, key: str, value: Any) -> None:
        """Sets the value of an attribute of the XML element.

        The type of the given value is converted before updating the attribute if a
        conversion method is specified in the ``SETTERS`` class attribute.
        If no conversion method is found the value updated set as given.

        Parameters
        ----------
        key : str
            The key of the attribute.
        value : Any
            The value for updating the attribute. The type conversion is handled
            automatically.

        Raises
        ------
        XmlAttributeKeyError:
            Raised if `key` is not a valid attribute key.
        """
        if key not in self.ATTRIBS:
            raise XmlAttributeKeyError(self.__class__, key, self.ATTRIBS)
        if self._element is None:
            raise XmlElementNotInitializedError("_element")
        try:
            # Apply callback
            value = self.SETTERS[key](value)
        except KeyError:
            # Convert to str just in case
            value = str(value)
        self._element.attrib[key] = value

    def __len__(self) -> int:
        """int: The number of attributes of the XML element."""
        if self._element is None:
            raise XmlElementNotInitializedError("_element")
        return len(self._element.attrib)

    def __iter__(self) -> Iterator[str]:
        """Iterable: An iterator of the attribute keys of the XML element."""
        if self._element is None:
            raise XmlElementNotInitializedError("_element")
        return iter(self._element.attrib.keys())

    def __getitem__(self, key: str) -> Any:
        """Returns the raw value of an attribute of the XML element.

        Parameters
        ----------
        key : str
            The key of the attribute.

        Returns
        -------
        value : Any
            The raw value of the attribute.
        """
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Sets the raw value of an attribute of the XML element.

        Parameters
        ----------
        key : str
            The key of the attribute.
        value : Any
            The raw value for updating the attribute.
        """
        self.set(key, value)

    def __getattr__(self, key: str) -> Any:
        """Returns the raw value of an attribute of the XML element (same as `get`)."""
        return self.get(key)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}()>"


# -- Collection elements ---------------------------------------------------------------


# noinspection PyPep8Naming,PyUnresolvedReferences
class Tempo(AbstractElement):
    """Tempo element representing the beat grid of a track.

    Attributes
    ----------
    Inizio : float
        The start position of the beat grid item.
    Bpm : float
        The BPM value of the beat grid item.
    Metro : str
        The kind of musical meter, for example '4/4'. The default is '4/4'.
    Battito : int
        The beat number in the bar. If `metro` is '4/4', the value can be 1, 2, 3 or 4.
    """

    TAG = "TEMPO"
    ATTRIBS = ["Inizio", "Bpm", "Metro", "Battito"]
    GETTERS = {"Inizio": float, "Bpm": float, "Battito": int}

    def __init__(
        self,
        parent: xml.Element = None,
        Inizio: float = 0.0,
        Bpm: float = 0.0,
        Metro: str = "4/4",
        Battito: int = 1,
        element: xml.Element = None,
    ):
        super().__init__(element, parent, Inizio, Bpm, Metro, Battito)

    def _init(
        self, parent: xml.Element, inizio: float, bpm: float, metro: str, battito: int
    ) -> None:
        attrib = {
            "Inizio": str(inizio),
            "Bpm": str(bpm),
            "Metro": str(metro),
            "Battito": str(battito),
        }
        self._element = xml.SubElement(parent, self.TAG, attrib=attrib)

    def __repr__(self) -> str:
        args = ", ".join(
            [
                f"Inizio={self.Inizio}",
                f"Bpm={self.Bpm}",
                f"Metro={self.Metro}",
                f"Battito={self.Battito}",
            ]
        )
        return f"<{self.__class__.__name__}({args})>"


# noinspection PyPep8Naming,PyUnresolvedReferences
class PositionMark(AbstractElement):
    """Position element for storing position markers like cue points of a track.

    Attributes
    ----------
    Name : str
        The name of the position mark.
    Type : str
        The type of position mark. Can be 'cue', 'fadein', 'fadeout', 'load' or 'loop'.
    Start : float
        Start position of the position mark in seconds.
    End : float, optionl
        End position of the position mark in seconds.
    Num : int, optional
        Charakter for identification of the position mark (for hot cues). For memory
        cues this is always -1.
    """

    TAG = "POSITION_MARK"
    ATTRIBS = ["Name", "Type", "Start", "End", "Num"]

    GETTERS = {
        "Type": POSMARK_TYPE_MAPPING.get,
        "Start": float,
        "End": float,
        "Num": int,
    }
    SETTERS = {"Type": POSMARK_TYPE_MAPPING.inv.get}  # noqa

    def __init__(
        self,
        parent: xml.Element = None,
        Name: str = "",
        Type: str = "cue",
        Start: float = 0.0,
        End: float = None,
        Num: int = -1,
        element: xml.Element = None,
    ):
        super().__init__(element, parent, Name, Type, Start, End, Num)

    def _init(
        self, parent: xml.Element, name: str, type_: str, start: float, end: float, num: int
    ) -> None:
        if type_ not in POSMARK_TYPE_MAPPING.inv:
            raise ValueError(f"Type '{type_}' is not supported!")
        attrib = {
            "Name": name,
            "Type": POSMARK_TYPE_MAPPING.inv.get(type_, "cue"),
            "Start": str(start),
            "Num": str(num),
        }
        if end is not None:
            attrib["End"] = str(end)
        self._element = xml.SubElement(parent, self.TAG, attrib=attrib)

    def __repr__(self) -> str:
        args = ", ".join(
            [
                f"Name={self.Name}",
                f"Type={self.Type}",
                f"Start={self.Start}",
                f"End={self.End}",
                f"Num={self.Num}",
            ]
        )
        return f"<{self.__class__.__name__}({args})>"


# noinspection PyPep8Naming,PyUnresolvedReferences
class Track(AbstractElement):
    """Track element for storing the metadata of a track.

    Attributes
    ----------
    TrackID : int
        Identification of the track.
    Name: str
        The name of the track.
    Artist : str
        The name of the artist.
    Composer : str
        The name of the composer (or producer).
    Album : str
        The name of the album.
    Grouping : str
        The name of the grouping.
    Genre : str
        The name of the genre.
    Kind : str
        The kind of the audio file, for example 'WAV File' or 'MP3 File'.
    Size : int
        The size of the audio file.
    TotalTime : int
        The duration of the track in seconds.
    DiscNumber : int
        The number of the disc of the album.
    TrackNumber : int
        The Number of the track of the album.
    Year : int
        The year of release.
    AverageBpm : float
        The average BPM of the track.
    DateModified : str
        The date of last modification in the format 'yyyy-mm-dd'.
    DateAdded : str
        The date of addition modification in the format 'yyyy-mm-dd'.
    BitRate : int
        The encoding bit rate.
    SampleRate : float
        The frequency of sampling.
    Comments : str
        The comments of the track.
    PlayCount : int
        The play count of the track.
    LastPlayed : str
        The date of last playing in the format 'yyyy-mm-dd'.
    Rating : int
        The rating of the track using the mapping 0=0, 1=51, 2=102, 3=153, 4=204, 5=255.
    Location : str
        The location of the file encoded as URI string. This value is essential for
        each track.
    Remixer : str
        The name of the remixer.
    Tonality : str
        The tonality or kind of musical key.
    Label : str
        The name of the record label.
    Mix : str
        The name of the mix.
    Colour : str
        The color for track grouping in RGB format.
    tempos : list
        The `Tempo` elements of the track.
    marks : list
        The `PositionMark` elements of the track.

    Raises
    ------
    XmlAttributeKeyError:
        Raised if initialized with invalid key in attributes.
    """

    TAG = "TRACK"
    ATTRIBS = [
        "TrackID",
        "Name",
        "Artist",
        "Composer",
        "Album",
        "Grouping",
        "Genre",
        "Kind",
        "Size",
        "TotalTime",
        "DiscNumber",
        "TrackNumber",
        "Year",
        "AverageBpm",
        "DateModified",
        "DateAdded",
        "BitRate",
        "SampleRate",
        "Comments",
        "PlayCount",
        "LastPlayed",
        "Rating",
        "Location",
        "Remixer",
        "Tonality",
        "Label",
        "Mix",
        "Colour",
    ]

    GETTERS = {
        "TrackID": int,
        "Size": int,
        "TotalTime": int,
        "DiscNumber": int,
        "TrackNumber": int,
        "Year": int,
        "AverageBpm": float,
        "BitRate": int,
        "SampleRate": float,
        "PlayCount": int,
        "Rating": RATING_MAPPING.get,
        "Location": decode_path,
    }

    SETTERS = {"Rating": RATING_MAPPING.inv.get, "Location": encode_path}  # noqa

    def __init__(
        self,
        parent: xml.Element = None,
        Location: Union[str, Path] = "",
        element: xml.Element = None,
        **kwargs: Any,
    ):
        self.tempos: List[Tempo] = list()
        self.marks: List[PositionMark] = list()
        super().__init__(element, parent, Location, **kwargs)

    def _init(self, parent: xml.Element, Location: Union[str, Path] = "", **kwargs: Any) -> None:
        attrib = {"Location": encode_path(Location)}
        for key, val in kwargs.items():
            if key not in self.ATTRIBS:
                raise XmlAttributeKeyError(self.__class__, key, self.ATTRIBS)
            attrib[key] = str(val)
        element = xml.SubElement(parent, self.TAG, attrib=attrib)
        if element is None:
            raise RuntimeError("XML element is not initialized!")
        self._element = element

    def _load_subelements(self) -> None:
        if self._element is None:
            raise XmlElementNotInitializedError("_element")
        tempo_elements = self._element.findall(f"{Tempo.TAG}")
        if tempo_elements is not None:
            self.tempos = [Tempo(element=el) for el in tempo_elements]
        mark_elements = self._element.findall(f".//{PositionMark.TAG}")
        if mark_elements is not None:
            self.marks = [PositionMark(element=el) for el in mark_elements]

    def add_tempo(self, Inizio: float, Bpm: float, Metro: str, Battito: int) -> Tempo:
        """Adds a new ``Tempo`` XML element to the track element.

        Parameters
        ----------
        Inizio : float
            The start position of the beat grid item.
        Bpm : float
            The BPM value of the beat grid item.
        Metro : str, optional
            The kind of musical meter, for example '4/4'. The default is '4/4'.
        Battito : int
            The beat number in the bar. If `metro` is '4/4', the value can be 1, 2, 3
            or 4.

        Returns
        -------
        tempo : Tempo
            The newly created tempo XML element.

        See Also
        --------
        Tempo: Beat grid XML element handler
        """
        tempo = Tempo(self._element, Inizio, Bpm, Metro, Battito)
        self.tempos.append(tempo)
        return tempo

    def add_mark(
        self,
        Name: str = "",
        Type: str = "cue",
        Start: float = 0.0,
        End: float = None,
        Num: int = -1,
    ) -> PositionMark:
        """Adds a new ``PositionMark`` XML element to the track element.

        Parameters
        ----------
        Name : str
            The name of the position mark.
        Type : str
            The type of position mark. Can be 'cue', 'fadein', 'fadeout', 'load' or
            'loop'.
        Start : float
            Start position of the position mark in seconds.
        End : float or None, optionl
            End position of the position mark in seconds.
        Num : int, optional
            Charakter for identification of the position mark (for hot cues). For memory
            cues this is always -1.

        Returns
        -------
        position_mark : PositionMark
            The newly created position mark XML element.

        See Also
        --------
        PositionMark: Position mark XML element handler
        """
        mark = PositionMark(self._element, Name, Type, Start, End, Num)
        self.marks.append(mark)
        return mark

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(Location={self.Location})>"


# -- Playlist elements -----------------------------------------------------------------


class Node:
    """Node element used for representing playlist folders and playlists.

    A node configured as playlist folder can store other nodes as well as tracks, a node
    configured as playlist can only store tracks. The tracks in playlists are stored via
    a key depending on the key type of the playlist. The key type can either be the
    ID of the track in the XML database ('TrackID') or the file path of the track
    ('Location').
    """

    TAG = "NODE"
    """str: Name of the XML element"""

    FOLDER = 0
    PLAYLIST = 1

    def __init__(self, parent: xml.Element = None, element: xml.Element = None, **attribs: Any):
        if element is None:
            if parent is None:
                raise ValueError("Either parent or element must be given!")
            element = xml.SubElement(parent, self.TAG, attrib=attribs)
        self._parent = parent
        self._element = element

    @classmethod
    def folder(cls, parent: xml.Element, name: str) -> "Node":
        """Initializes a playlist folder node XML element.

        Parameters
        ----------
        parent : Node
            The parent node XML element of the new playlist folder node.
        name : str
            The name of the playlist folder node.
        """
        attrib = {"Name": name, "Type": str(cls.FOLDER), "Count": "0"}
        return cls(parent, None, **attrib)

    @classmethod
    def playlist(cls, parent: xml.Element, name: str, keytype: str = "TrackID") -> "Node":
        """Initializes a playlist node XML element.

        Parameters
        ----------
        parent : xml.Element
            The parent node XML element of the new playlist node.
        name : str
            The name of the playlist node.
        keytype : str, optional
            The key type used by the playlist node. Can be 'TrackID' or 'Location'
            (file path of the track).
        """
        if keytype not in NODE_KEYTYPE_MAPPING.inv:
            raise ValueError(f"Key type '{keytype}' is not supported!")
        attrib = {
            "Name": name,
            "Type": str(cls.PLAYLIST),
            "KeyType": NODE_KEYTYPE_MAPPING.inv.get(keytype, "TrackID"),
            "Entries": "0",
        }
        return cls(parent, None, **attrib)

    @property
    def parent(self) -> Union[xml.Element, None]:
        """xml.Element: The parent of the node."""
        return self._parent

    @property
    def name(self) -> str:
        """str: The name of the node."""
        value = self._element.attrib.get("Name")
        if value is None:
            raise ValueError("Name element has no value")
        return value

    @property
    def type(self) -> int:
        """int: The type of the node (0=folder or 1=playlist)."""
        type_ = self._element.attrib.get("Type")
        if type_ is None:
            raise ValueError("Type element has no value")
        return int(type_)

    @property
    def count(self) -> int:
        """int: The number of attributes of the XML element."""
        return int(self._element.attrib.get("Count", 0))

    @property
    def entries(self) -> int:
        """int: The number of entries of the node."""
        return int(self._element.attrib.get("Entries", 0))

    @property
    def key_type(self) -> str:
        """str: The type of key used by the playlist node."""
        keytype: str = NODE_KEYTYPE_MAPPING[self._element.attrib.get("KeyType", "0")]
        return keytype

    @property
    def is_folder(self) -> bool:
        """bool: True if the node is a playlist folder, false if otherwise."""
        return self.type == self.FOLDER

    @property
    def is_playlist(self) -> bool:
        """bool: True if the node is a playlist, false if otherwise."""
        return self.type == self.PLAYLIST

    def _update_count(self) -> None:
        self._element.attrib["Count"] = str(len(self._element))

    def _update_entries(self) -> None:
        self._element.attrib["Entries"] = str(len(self._element))

    def get_node(self, i: int) -> "Node":
        """Returns the i-th sub-Node of the current node.

        Parameters
        ----------
        i : int
            Index of sub-Node

        Returns
        -------
        subnode : Node
        """
        return Node(self._element, element=self._element.find(f"{self.TAG}[{i + 1}]"))

    def get_playlist(self, name: str) -> "Node":
        """Returns the sub-Node with the given name.

        Parameters
        ----------
        name : str
            Name of the sub-Node

        Returns
        -------
        subnode : Node
        """
        return Node(self._element, element=self._element.find(f'.//{self.TAG}[@Name="{name}"]'))

    def get_playlists(self) -> List["Node"]:
        """Returns all sub-nodes that are playlists.

        Returns
        -------
        playlists : list[Node]
            The playlist nodes in the current node.
        """
        return [Node(self._element, element=el) for el in self._element]

    def add_playlist_folder(self, name: str) -> "Node":
        """Add a new playlist folder as child to this node.

        Parameters
        ----------
        name : str
            The name of the new playlist folder.

        Returns
        -------
        folder_node : Node
            The newly created playlist folder node.

        Raises
        ------
        ValueError:
            Raised if called on a playlist node.
        """
        if self.is_playlist:
            raise ValueError("Sub-elements can only be added to a folder node!")

        node = Node.folder(self._element, name)
        self._update_count()
        return node

    def add_playlist(self, name: str, keytype: str = "TrackID") -> "Node":
        """Add a new playlist as child to this node.

        Parameters
        ----------
        name : str
            The name of the new playlist.
        keytype : {'TrackID', 'Location'} str
            The type of key the playlist uses to store the tracks. Can either be
            'TrackID' or 'Location'.

        Returns
        -------
        playlist_node : Node
            The newly created playlist node.

        Raises
        ------
        ValueError:
            Raised if called on a playlist node.
        """
        if self.is_playlist:
            raise ValueError("Sub-elements can only be added to a folder node!")

        node = Node.playlist(self._element, name, keytype)
        self._update_count()
        return node

    def remove_playlist(self, name: str) -> None:
        """Removes a playlist from the playlist folder node.

        Parameters
        ----------
        name : str
            The name of the playlist to remove.
        """
        item = self.get_playlist(name)
        self._element.remove(item._element)  # noqa
        self._update_count()
        self._update_entries()

    def add_track(self, key: Union[int, str]) -> xml.Element:
        """Adds a new track to the playlist node.

        Parameters
        ----------
        key : int or str
            The key of the track to add, depending on the `type` of the playlist node.

        Returns
        -------
        el : xml.SubElement
            The newly created playlist track element.
        """
        el = xml.SubElement(self._element, Track.TAG, attrib={"Key": str(key)})
        if el is None:
            raise RuntimeError("XML element is not initialized!")
        self._update_entries()
        return el

    def remove_track(self, key: Union[int, str]) -> xml.Element:
        """Removes a track from the playlist node.

        Parameters
        ----------
        key : int or str
            The key of the track to remove, depending on the `type` attribute of the
            playlist node.
        """
        el = self._element.find(f'{Track.TAG}[@Key="{key}"]')
        if el is None:
            raise ValueError(f"Track key {key} not found.")
        self._element.remove(el)
        self._update_entries()
        return el

    def get_tracks(self) -> List[Union[int, str]]:
        """Returns the keys of all tracks contained in the playlist node.

        Returns
        -------
        keys : list
            The keys of the tracks in the playlist. The format depends on the `type`
            attribute of the playlist node.
        """
        if self.type == self.FOLDER:
            return list()
        elements = self._element.findall(f".//{Track.TAG}")
        items = list()
        for el in elements:
            val: Union[int, str] = el.attrib["Key"]
            if self.key_type == "TrackID":
                val = int(val)
            items.append(val)
        return items

    def get_track(self, key: str) -> Union[int, str]:
        """Returns the formatted key of the track."""
        el = self._element.find(f'{Track.TAG}[@Key="{key}"]')
        if el is None:
            raise ValueError(f"Track key {key} not found.")
        val: Union[int, str] = el.attrib["Key"]
        if self.key_type == "TrackID":
            val = int(val)
        return val

    def treestr(self, indent: int = 4, lvl: int = 0) -> str:
        """returns a formatted string of the node tree strucutre.

        Parameters
        ----------
        indent : int, optional
            Number of spaces used for indenting.
        lvl : int, optional
            Internal parameter for recursion, don't use!

        Returns
        -------
        s : str
            The formatted tree string.
        """
        space = indent * lvl * " "
        string = ""
        if self.type == self.PLAYLIST:
            string += space + f"Playlist: {self.name} ({self.entries} Tracks)\n"
        elif self.type == self.FOLDER:
            string += space + f"Folder: {self.name}\n"
            for node in self.get_playlists():
                string += node.treestr(indent, lvl + 1)
        return string

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Node):
            raise NotImplementedError()
        return self.parent == other.parent and self.name == other.name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"


# -- Main XML object -------------------------------------------------------------------


# noinspection PyPep8Naming,PyUnresolvedReferences
class RekordboxXml:
    """Rekordbox XML database object.

    The XML database contains the tracks and playlists in the Rekordbox collection. By
    importing the database, new tracks and items can be added to the Rekordbox
    collection.

    If a file path is passed to the constructor of the ``RekordboxXml`` object, the file
    is opened and parsed. Otherwise, an empty file is created with the given arguments.
    Creating an importable XML file requires a product name, xml database version and
    company name.

    Attributes
    ----------
    path : str, optional
        The file path to

    Examples
    --------
    Open Rekordbox XML file

    >>> file = RekordboxXml(Path(".testdata", "rekordbox 6", "database.xml"))

    Create new XML file

    >>> file = RekordboxXml()

    """

    ROOT_TAG = "DJ_PLAYLISTS"
    PRDT_TAG = "PRODUCT"
    PLST_TAG = "PLAYLISTS"
    COLL_TAG = "COLLECTION"

    def __init__(
        self,
        path: Union[str, Path] = None,
        name: str = None,
        version: str = None,
        company: str = None,
    ):
        self._root: Union[xml.Element, None] = None
        self._product: Union[xml.Element, None] = None
        self._collection: Union[xml.Element, None] = None
        self._playlists: Union[xml.Element, None] = None
        self._root_node: Union[Node, None] = None

        self._last_id = 0
        # Used for fast duplicate check
        self._locations: Set[str] = set()
        self._ids: Set[int] = set()

        if path is not None:
            self._parse(path)
        else:
            self._init(name, version, company)

    @property
    def frmt_version(self) -> str:
        """str : The version of the Rekordbox XML format."""
        if self._root is None:
            raise XmlElementNotInitializedError("_root")
        return self._root.attrib.get("Version", "")

    @property
    def product_name(self) -> str:
        """str : The product name that will be displayed in the software."""
        if self._product is None:
            raise XmlElementNotInitializedError("_product")
        return self._product.attrib.get("Name", "")

    @property
    def product_version(self) -> str:
        """str : The product version."""
        if self._product is None:
            raise XmlElementNotInitializedError("_product")
        return self._product.attrib.get("Version", "")

    @property
    def product_company(self) -> str:
        """str : The company name."""
        if self._product is None:
            raise XmlElementNotInitializedError("_product")
        return self._product.attrib.get("Company", "")

    @property
    def num_tracks(self) -> int:
        """int : The number of tracks in the collection."""
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        return int(self._collection.attrib.get("Entries", "0"))

    @property
    def root_playlist_folder(self) -> Node:
        """Node: The node of the root playlist folder containing all other nodes."""
        if self._root_node is None:
            raise RootNodeNotInitializedError()
        return self._root_node

    def _parse(self, path: Union[str, Path]) -> None:
        """Parse an existing XML file.

        Parameters
        ----------
        path : str or Path
            The path to the XML file to parse.
        """
        tree = xml.parse(str(path))
        self._root = tree.getroot()

        product = self._root.find(self.PRDT_TAG)
        collection = self._root.find(self.COLL_TAG)
        playlists = self._root.find(self.PLST_TAG)
        if product is None:
            raise RuntimeError(f"No product found in {path}")
        if collection is None:
            raise RuntimeError(f"No collection found in {path}")
        if playlists is None:
            raise RuntimeError(f"No playlists found in {path}")

        self._product = product
        self._collection = collection
        self._playlists = playlists
        self._root_node = Node(element=self._playlists.find(Node.TAG))
        self._update_cache()

    def _init(
        self, name: str = None, version: str = None, company: str = None, frmt_version: str = None
    ) -> None:
        """Initialize a new XML file."""
        frmt_version = frmt_version or "1.0.0"
        name = name or "pyrekordbox"
        version = version or "0.0.1"
        company = company or ""

        # Initialize root element
        self._root = xml.Element(self.ROOT_TAG, attrib={"Version": frmt_version})
        # Initialize product element
        attrib = {"Name": name, "Version": version, "Company": company}
        self._product = xml.SubElement(self._root, self.PRDT_TAG, attrib=attrib)
        # Initialize collection element
        attrib = {"Entries": "0"}
        self._collection = xml.SubElement(self._root, self.COLL_TAG, attrib=attrib)
        # Initialize playlist element
        self._playlists = xml.SubElement(self._root, self.PLST_TAG)
        self._root_node = Node.folder(self._playlists, "ROOT")

        track_ids = self.get_track_ids()
        if track_ids:
            self._last_id = max(track_ids)

    def get_tracks(self) -> List[Track]:
        """Returns the tracks in the collection of the XML file.

        Returns
        -------
        tracks : list of Track
            A list of the track objects in the collection.
        """
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        elements = self._collection.findall(f".//{Track.TAG}")
        return [Track(element=el) for el in elements]

    def get_track(
        self, index: int = None, TrackID: Union[int, str] = None, Location: str = None
    ) -> Track:
        """Get a track in the collection of the XML file.

        Parameters
        ----------
        index : int, optional
            If `index` is given, the track with this index in the collection is
            returned.
        TrackID : int or str, optional
            If `TrackID` is given, the track with this ID in the collection is
            returned.
        Location : str, optional
            If `Location` is given, the track with this file path in the collection is
            returned.

        Returns
        -------
        track : Track
            The XML track element.

        Raises
        ------
        ValueError:
            Raised if neither the index of the track id is specified.

        Examples
        --------
        Get track by index

        >>> file = RekordboxXml("database.xml")
        >>> track = file.get_track(0)

        or by ``TrackID``

        >>> track = file.get_track(TrackID=1)

        """
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        if TrackID is not None:
            el = self._collection.find(f'.//{Track.TAG}[@TrackID="{TrackID}"]')
        elif Location is not None:
            encoded = encode_path(Location)
            el = self._collection.find(f'.//{Track.TAG}[@Location="{encoded}"]')
        elif index is not None:
            el = self._collection.find(f".//{Track.TAG}[{index + 1}]")
        else:
            raise ValueError("Either index, TrackID or Location has to be specified!")
        return Track(element=el)

    def get_track_ids(self) -> List[int]:
        """Returns the `TrackID` of all tracks in the collection of the XML file.

        Returns
        -------
        ids : list of int
            The ID's of all tracks.
        """
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        elements = self._collection.findall(f".//{Track.TAG}")
        return [int(el.attrib["TrackID"]) for el in elements]

    def get_playlist(self, *names: str) -> Node:
        """Returns a playlist or playlist folder with the given path.

        Parameters
        ----------
        *names : str
            Names in the path. If no names are given the root playlist folder is
            returned.

        Returns
        -------
        node : Node
            The playlist or playlist folder node.

        Examples
        --------
        >>> file = RekordboxXml("database.xml")
        >>> playlist = file.get_playlist("Folder", "Sub Playlist")

        """
        if self._root_node is None:
            raise RootNodeNotInitializedError()
        node = self._root_node
        if not names:
            return node
        for name in names:
            node = node.get_playlist(name)
        return node

    # def _update_track_count(self):
    #     """Updates the track count element."""
    #     num_tracks = len(self._collection.findall(f".//{Track.TAG}"))
    #     self._collection.attrib["Entries"] = str(num_tracks)

    def _increment_track_count(self) -> None:
        """Increment the track count element."""
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        old = int(self._collection.attrib["Entries"])
        self._collection.attrib["Entries"] = str(old + 1)

    def _decrement_track_count(self) -> None:
        """Decrement the track count element."""
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        old = int(self._collection.attrib["Entries"])
        self._collection.attrib["Entries"] = str(old - 1)

    def _add_cache(self, track: Track) -> None:
        """Add the TrackID and Location to the cache."""
        self._locations.add(track.Location)
        self._ids.add(track.TrackID)

    def _remove_cache(self, track: Track) -> None:
        """Remove the TrackID and Location from the cache."""
        self._locations.remove(track.Location)
        self._ids.remove(track.TrackID)

    def _update_cache(self) -> None:
        """Update the cache with the current tracks in the collection."""
        self._locations.clear()
        self._ids.clear()
        for track in self.get_tracks():
            self._add_cache(track)

    def add_track(self, location: Union[str, Path], **kwargs: Any) -> Track:
        """Add a new track element to the Rekordbox XML collection.

        Parameters
        ----------
        location : str or Path
            The file path of the track.
        kwargs :
            Keyword arguments which are used to fill the track attributes. If no
            argument for ``TrackID`` is given the ID is auto-incremented.

        Returns
        -------
        track : Track
            The newly created XML track element.

        Raises
        ------
        ValueError:
            Raised if the database already contains a track with the track-id
            or file path.

        Examples
        --------
        >>> file = RekordboxXml("database.xml")
        >>> _ = file.add_track("path/to/track.wav")
        """
        if "TrackID" not in kwargs:
            kwargs["TrackID"] = self._last_id + 1

        # Check that Location and TrackID are unique
        track_id = kwargs["TrackID"]
        if os.path.normpath(location) in self._locations:
            raise XmlDuplicateError("Location", str(location))
        if track_id in self._ids:
            raise XmlDuplicateError("TrackID", track_id)

        # Create track and add it to the collection
        track = Track(self._collection, location, **kwargs)
        self._last_id = int(track["TrackID"])
        self._increment_track_count()
        self._add_cache(track)
        return track

    def remove_track(self, track: Track) -> None:
        """Remove a track element from the Rekordbox XML collection.

        Parameters
        ----------
        track : Track
            The XML track element to remove.

        Examples
        --------
        >>> file = RekordboxXml("database.xml")
        >>> t = file.get_track(0)
        >>> file.remove_track(t)

        """
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        if track._element is None:  # noqa
            raise XmlElementNotInitializedError("track._element")
        self._collection.remove(track._element)  # noqa
        self._decrement_track_count()
        self._remove_cache(track)

    def add_playlist_folder(self, name: str) -> Node:
        """Add a new top-level playlist folder to the XML collection.

        Parameters
        ----------
        name : str
            The name of the new playlist folder.

        Returns
        -------
        folder_node : Node
            The newly created playlist folder node.

        See Also
        --------
        Node.add_playlist_folder

        Examples
        --------
        >>> file = RekordboxXml("database.xml")
        >>> file.add_playlist_folder("New Folder")
        """
        if self._root_node is None:
            raise RootNodeNotInitializedError()
        return self._root_node.add_playlist_folder(name)

    def add_playlist(self, name: str, keytype: str = "TrackID") -> Node:
        """Adds a new top-level playlist to the XML collection.

        Parameters
        ----------
        name : str
            The name of the new playlist.
        keytype : {'TrackID', 'Location'} str
            The type of key the playlist uses to store the tracks. Can either be
            'TrackID' or 'Location'.

        Returns
        -------
        playlist_node : Node
            The newly created playlist node.

        See Also
        --------
        Node.add_playlist

        Examples
        --------
        Create playlist using the track ID as keys

        >>> file = RekordboxXml("database.xml")
        >>> file.add_playlist("New Playlist", keytype="TrackID")

        Create playlist using the file paths as keys

        >>> file.add_playlist("New Playlist 2", keytype="Location")
        """
        if self._root_node is None:
            raise RootNodeNotInitializedError()
        return self._root_node.add_playlist(name, keytype)

    def tostring(self, indent: str = None, encoding: str = "utf-8") -> str:
        r"""Returns the contents of the XML file as a string.

        Parameters
        ----------
        indent : str, optional
            The indentation used for formatting the XML file. The default is '\t'.
        encoding : str, optional
            The encoding used for the XML file. The default is 'utf-8'.

        Returns
        -------
        s : str
            The contents of the XML file
        """
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        if self._root is None:
            raise XmlElementNotInitializedError("_root")

        # Check track count is valid
        num_tracks = len(self._collection.findall(f".//{Track.TAG}"))
        n = int(self._collection.attrib["Entries"])
        if n != num_tracks:
            raise ValueError(f"Track count {num_tracks} does not match number of elements {n}")

        space = "\t" if indent is None else indent
        text: str
        data: bytes
        try:
            tree = xml.ElementTree(self._root)
            xml.indent(tree, space=space, level=0)
            data = xml.tostring(self._root, encoding=encoding, xml_declaration=True)
            text = data.decode(encoding)
        except AttributeError:
            # For Python < 3.9
            try:
                text = pretty_xml(self._root, space, encoding=encoding)
            except Exception:  # noqa
                # If the pretty_xml function fails, use unformatted XML
                data = xml.tostring(self._root, encoding=encoding, xml_declaration=True)
                text = data.decode(encoding)
        return text

    def save(
        self, path: Union[str, Path] = "", indent: str = None, encoding: str = "utf-8"
    ) -> None:
        r"""Saves the contents to an XML file.

        Parameters
        ----------
        path : str or Path, optional
            The path for saving the XML file. The default is the original file.
        indent : str, optional
            The indentation used for formatting the XML file. The default is '\t'.
        encoding : str, optional
            The encoding used for the XML file. The default is 'utf-8'.
        """
        if self._collection is None:
            raise XmlElementNotInitializedError("_collection")
        if self._root is None:
            raise XmlElementNotInitializedError("_root")

        # Check track count is valid
        num_tracks = len(self._collection.findall(f".//{Track.TAG}"))
        n = int(self._collection.attrib["Entries"])
        if n != num_tracks:
            raise ValueError(f"Track count {num_tracks} does not match number of elements {n}")

        space = "\t" if indent is None else indent
        try:
            tree = xml.ElementTree(self._root)
            xml.indent(tree, space=space, level=0)
            tree.write(path, encoding=encoding, xml_declaration=True)
        except AttributeError:
            # For Python < 3.9
            try:
                data: str = pretty_xml(self._root, space, encoding=encoding)
                with open(path, "w", encoding=encoding) as fh:
                    fh.write(data)
            except Exception:  # noqa
                # If the pretty_xml function fails, write the XML unformatted
                text: bytes = xml.tostring(self._root, encoding=encoding, xml_declaration=True)
                with open(path, "wb") as fh:
                    fh.write(text)

    def __repr__(self) -> str:
        name = self.product_name
        v = self.product_version
        company = self.product_company
        tracks = self.num_tracks

        cls = self.__class__.__name__
        s = f"{cls}(tracks={tracks}, info={name}, {company}, v{v})"
        return s
