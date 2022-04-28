# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

"""Rekordbox XML database file interface."""

import logging
import os.path
import urllib.parse
from collections import abc
from xml.dom import minidom
import xml.etree.cElementTree as xml
import bidict

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


RATING_MAPPING = bidict.bidict(
    {"0": 0, "51": 1, "102": 2, "153": 3, "204": 4, "255": 5}
)


NODE_KEYTYPE_MAPPING = bidict.bidict({"0": "TrackID", "1": "Location"})


def pretty_xml(element, indent=None, encoding="utf-8"):
    """Generates a formatted string of an XML element.

    Parameters
    ----------
    element : xml.etree.cElementTree.Element
        The input XML element.
    indent : str, optional
        The indentation used for formatting the XML element. The default is 3 spaces.
    encoding : str, optional
        The encoding used for formatting the XML element. The default is `utf-8`.

    Returns
    -------
    xml_string : str
        The formatted string of the XML element.
    """
    # Build pretty xml-string
    if indent is None:
        indent = "    "
    if encoding is None:
        encoding = "utf-8"
    rough_string = xml.tostring(element, encoding)
    reparsed = minidom.parseString(rough_string)
    string = reparsed.toprettyxml(indent=indent, encoding=encoding).decode()
    # Remove annoying empty lines
    string = "\n".join([line for line in string.splitlines() if line.strip()])
    return string


def encode_path(path):
    """Encodes a file path as URI string.

    Parameters
    ----------
    path : str
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
    url_path = urllib.parse.quote(path, safe=":/\\")
    url = URL_PREFIX + url_path.replace("\\", "/")
    return url


def decode_path(url):
    """Decodes an as URI string encoded file path.

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


class AbstractElement(abc.Mapping):
    """Abstract base class for Rekordbox XML elements."""

    TAG: str
    ATTRIBS: list

    SETTERS = dict()
    GETTERS = dict()

    def __init__(self, element=None, *args, **kwargs):
        self._element = element
        if element is None:
            self._init(*args, **kwargs)
        else:
            self._load_subelements()

    def _init(self, *args, **kwargs):
        pass

    def _load_subelements(self):
        pass

    def get(self, key, default=None):
        if key not in self.ATTRIBS:
            raise KeyError(f"{key} is not a valid key for {self.__class__.__name__}!")
        value = self._element.attrib.get(key, default)
        if value == default:
            return default
        try:
            # Apply callback
            value = self.GETTERS[key](value)
        except KeyError:
            pass
        return value

    def set(self, key, value):
        if key not in self.ATTRIBS:
            raise KeyError(f"{key} is not a valid key for {self.__class__.__name__}!")
        try:
            # Apply callback
            value = self.SETTERS[key](value)
        except KeyError:
            # Convert to str just in case
            value = str(value)
        self._element.attrib.set(key, value)

    def __len__(self):
        return len(self._element.attrib)

    def __iter__(self):
        return iter(self._element.attrib.keys())

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getattr__(self, key):
        return self.get(key)

    def __repr__(self):
        return f"<{self.__class__.__name__}()>"


# -- Collection elements ---------------------------------------------------------------


# noinspection PyPep8Naming
class Tempo(AbstractElement):
    """Tempo element representing the beat grid.

    Attributes
    ----------
    Inizio : float
        The start position of the beat grid item.
    Bpm : float
        The BPM value of the beat grid item.
    Metro : str, optional
        The kind of musical meter, for example '4/4'. The default is '4/4'.
    Battito : int
        The beat number in the bar. If `metro` is '4/4', the value can be 1, 2, 3 or 4.
    """

    TAG = "TEMPO"
    ATTRIBS = ["Inizio", "Bpm", "Metro", "Battito"]
    GETTERS = {"Inizio": float, "Bpm": float, "Battito": int}

    def __init__(
        self, parent=None, Inizio=0.0, Bpm=0.0, Metro="4/4", Battito=1, element=None
    ):
        super().__init__(element, parent, Inizio, Bpm, Metro, Battito)

    def _init(self, parent, inizio, bpm, metro, battito):
        attrib = {
            "Inizio": str(inizio),
            "Bpm": str(bpm),
            "Metro": str(metro),
            "Battito": str(battito),
        }
        self._element = xml.SubElement(parent, self.TAG, attrib=attrib)

    def __repr__(self):
        args = ", ".join(
            [
                f"Inizio={self.Inizio}",
                f"Bpm={self.Bpm}",
                f"Metro={self.Metro}",
                f"Battito={self.Battito}",
            ]
        )
        return f"<{self.__class__.__name__}({args})>"


# noinspection PyPep8Naming
class PositionMark(AbstractElement):
    """Position element for storing position markers like cue points.

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
        parent=None,
        Name="",
        Type="cue",
        Start=0.0,
        End=None,
        Num=-1,
        element=None,
    ):
        super().__init__(element, parent, Name, Type, Start, End, Num)

    def _init(self, parent, name, type_, start, end, num):
        attrib = {
            "Name": name,
            "Type": POSMARK_TYPE_MAPPING.inv.get(type_),  # noqa
            "Start": str(start),
            "Num": str(num),
        }
        if end is not None:
            attrib["End"] = str(end)
        self._element = xml.SubElement(parent, self.TAG, attrib=attrib)

    def __repr__(self):
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


# noinspection PyPep8Naming
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

    def __init__(self, parent=None, Location="", element=None, **kwargs):
        self.tempos = list()
        self.marks = list()
        super().__init__(element, parent, Location, **kwargs)

    def _init(self, parent, Location, **kwargs):
        attrib = {"Location": encode_path(Location)}
        for key, val in kwargs:
            if key not in self.ATTRIBS:
                raise KeyError(
                    f"{key} is not a valid key for {self.__class__.__name__}!"
                )
            attrib[key] = str(val)
        self._element = xml.SubElement(parent, self.TAG, attrib=attrib)

    def _load_subelements(self):
        tempo_elements = self._element.findall(f"{Tempo.TAG}")
        if tempo_elements is not None:
            self.tempos = [Tempo(element=el) for el in tempo_elements]
        mark_elements = self._element.findall(f".//{PositionMark.TAG}")
        if mark_elements is not None:
            self.marks = [PositionMark(element=el) for el in mark_elements]

    def add_tempo(self, Inizio=0.0, Bpm=0.0, Metro="4/4", Battito=1):
        return Tempo(self, Inizio, Bpm, Metro, Battito)

    def add_mark(self, Name="", Type="cue", Start=0.0, End=None, Num=-1):
        return PositionMark(self, Name, Type, Start, End, Num)

    def __repr__(self):
        return f"<{self.__class__.__name__}(Location={self.Location})>"


# -- Playlist elements -----------------------------------------------------------------


class Node:
    """Node element used for storing playlist folders and playlists."""

    TAG = "NODE"

    FOLDER = 0
    PLAYLIST = 1

    def __init__(self, parent=None, element=None, **attribs):
        self._parent = parent
        self._element = element
        if element is None:
            self._element = xml.SubElement(parent, self.TAG, attrib=attribs)

    @classmethod
    def folder(cls, parent, name):
        attrib = {"Name": name, "Type": str(cls.FOLDER), "Count": "0"}
        return cls(parent, **attrib)

    @classmethod
    def playlist(cls, parent, name, keytype="TrackID"):
        attrib = {
            "Name": name,
            "Type": str(cls.PLAYLIST),
            "KeyType": NODE_KEYTYPE_MAPPING.inv[keytype],  # noqa
            "Entries": "0",
        }
        return cls(parent, **attrib)

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        """str: Name of Node."""
        return self._element.attrib.get("Name")

    @property
    def type(self):
        """int: Type of Node (0=folder or 1=playlist)."""
        return int(self._element.attrib.get("Type"))

    @property
    def count(self):
        return int(self._element.attrib.get("Count", 0))

    @property
    def entries(self):
        return int(self._element.attrib.get("Entries", 0))

    @property
    def key_type(self):
        return NODE_KEYTYPE_MAPPING.get(self._element.attrib.get("KeyType"))

    @property
    def is_folder(self):
        return self.key_type == self.FOLDER

    @property
    def is_playlist(self):
        return self.key_type == self.PLAYLIST

    @property
    def nodes(self):
        """list of Node: Sub-Nodes (in case of a folder-Node)."""
        return [Node(self, element=el) for el in self._element.findall(f"{self.TAG}")]

    def get_node(self, i):
        """Returns the i-th sub-Node of the current node.

        Parameters
        ----------
        i : int
            Index of sub-Node

        Returns
        -------
        subnode : Node
        """
        return Node(self, element=self._element.findall(f"{self.TAG}[{i + 1}]"))

    def get_node_by_name(self, name):
        """Returns the sub-Node with the given name.

        Parameters
        ----------
        name : str
            Name of the sub-Node

        Returns
        -------
        subnode : Node
        """
        return Node(self, element=self._element.find(f'.//{self.TAG}[@Name="{name}"]'))

    def get_tracks(self):
        if self.type == self.FOLDER:
            return list()
        elements = self._element.findall(f".//{Track.TAG}")
        return [int(el.attrib["Key"]) for el in elements]

    def _update_count(self):
        self._element.attrib["Count"] = str(len(self._element))

    def _update_entries(self):
        self._element.attrib["Entries"] = str(len(self._element))

    def add_folder_node(self, name):
        node = Node.folder(self._element, name)
        self._update_count()
        return node

    def add_playlist_node(self, name, keytype="TrackID"):
        node = Node.playlist(self._element, name, keytype)
        self._update_count()
        return node

    def add_track(self, key):
        el = xml.SubElement(self._element, Track.TAG, attrib={"Key": str(key)})
        self._update_entries()
        return el

    def treestr(self, lvl=0, indent=4):
        space = indent * lvl * " "
        string = ""
        if self.type == self.PLAYLIST:
            string += space + f"Playlist: {self.name} ({self.entries} Tracks)\n"
        elif self.type == self.FOLDER:
            string += space + f"Folder: {self.name}\n"
            for node in self.nodes:
                string += node.treestr(lvl + 1, indent)
        return string

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name})>"


# -- Main XML object -------------------------------------------------------------------


# noinspection PyPep8Naming
class RekordboxXml:
    """Rekordbox XML database object.

    The XML database contains the tracks and playlists in the Rekordbox collection. By
    importing the databse, new tracks and items can be added to the Rekordbox
    collection.
    The Rekordbox XML file can be created in Rekordbox 5/6 in the application menu
    'File>Export collection in xml format'. It can be imported by setting the file path
    in 'File>Preferences>Advanced>rekordbox xml>Imported Libary'.

    If a file path is passed to the constructor of the `RekordboxXml` object, the file
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

    >>> file = RekordboxXml(os.path.join(".testdata", "rekordbox 6", "database.xml"))

    Create new XML file

    >>> file = RekordboxXml()

    """

    ROOT_TAG = "DJ_PLAYLISTS"
    PRDT_TAG = "PRODUCT"
    PLST_TAG = "PLAYLISTS"
    COLL_TAG = "COLLECTION"

    def __init__(self, path="", name=None, version=None, company=None):
        self._root = None
        self._product = None
        self._collection = None
        self._playlists = None
        self._root_node = None
        if path:
            self._parse(path)
        else:
            self._init(name, version, company)

    @property
    def frmt_version(self):
        """str : The version of the Rekordbox XML format."""
        return self._root.attrib["Version"]

    @property
    def product_name(self):
        """str : The product name that will be displayed in the software."""
        return self._product.attrib.get("Name")

    @property
    def product_version(self):
        """str : The product version."""
        return self._product.attrib.get("Version")

    @property
    def product_company(self):
        """str : The company name."""
        return self._product.attrib.get("Company")

    @property
    def num_tracks(self):
        """str : The number of tracks in the collection."""
        return int(self._collection.attrib.get("Entries"))

    def _parse(self, path):
        """Parse an existing XML file."""
        tree = xml.parse(path)
        self._root = tree.getroot()
        self._product = self._root.find(self.PRDT_TAG)
        self._collection = self._root.find(self.COLL_TAG)
        self._playlists = self._root.find(self.PLST_TAG)
        self._root_node = Node(element=self._playlists.find(Node.TAG))

    def _init(self, name=None, version=None, company=None, frmt_version=None):
        """Initialize a new XML file."""
        frmt_version = frmt_version or "1.0.0"
        name = name or "pyrekordbox"
        version = version or "0.0.1"
        company = company or "None"

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

    def get_tracks(self):
        """Returns the tracks in the collection of the XML file.

        Returns
        -------
        tracks : list of Track
            A list of the track objects in the collection.
        """
        elements = self._collection.findall(f".//{Track.TAG}")
        return [Track(element=el) for el in elements]

    def get_track(self, index=None, TrackID=None):
        """Get a track in the collection of the XML file.

        Parameters
        ----------
        index : int, optional
            If `index` is given, the track with this index in the collection is
            returned.
        TrackID : int, optional
            If `TrackID` is given, the track with this ID in the collection is
            returned.

        Returns
        -------
        track : Track
            The track object.
        """
        if index is None and TrackID is None:
            raise ValueError("Either index or TrackID has to be specified!")

        if TrackID is not None:
            el = self._collection.find(f'.//{Track.TAG}[@TrackID="{TrackID}"]')
        else:
            el = self._collection.find(f".//{Track.TAG}[{index + 1}]")
        return Track(element=el)

    def get_track_ids(self):
        """Returns the `TrackID` of all tracks in the collection of the XML file.

        Returns
        -------
        ids : list of int
            The ID's of all tracks.
        """
        elements = self._collection.findall(f".//{Track.TAG}")
        return [int(el.attrib["TrackID"]) for el in elements]

    def get_playlist(self, *names):
        node = self._root_node
        if not names:
            return node
        for name in names:
            node = node.get_node_by_name(name)
        return node

    def _update_track_count(self):
        num_tracks = len(self._collection.findall(f".//{Track.TAG}"))
        self._collection.attrib["Entries"] = num_tracks

    def add_track(self, location, **kwargs):
        track = Track(self, location, **kwargs)
        self._update_track_count()
        return track

    def add_playlist_folder(self, name):
        return self._root_node.add_folder_node(name)

    def add_playlist_node(self, name, keytype="TrackID"):
        return self._root_node.add_folder_node(name, keytype)

    def tostring(self, indent=None):
        """Returns the contents of the XML file as a string.

        Parameters
        ----------
        indent : str, optional
            The indentation used for formatting the XML file. The default is 3 spaces.

        Returns
        -------
        s : str
            The contents of the XML file
        """
        return pretty_xml(self._root, indent, encoding="utf-8")

    def save(self, path="", indent=None):
        """Writes the contents of the XML file to disk.

        Parameters
        ----------
        path : str, optional
            The path for saving the XML file. The default is the original file.
        indent : str, optional
            The indentation used for formatting the XML element.
            The default is 3 spaces.
        """
        string = self.tostring(indent)
        with open(path, "w") as fh:
            fh.write(string)

    def __repr__(self):
        name = self.product_name
        v = self.product_version
        company = self.product_company
        tracks = self.num_tracks

        cls = self.__class__.__name__
        s = f"{cls}(tracks={tracks}, info={name}, {company}, v{v})"
        return s
