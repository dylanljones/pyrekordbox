# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

"""Rekordbox XML database file interface."""

import logging
import os.path
from xml.dom import minidom
import xml.etree.cElementTree as xml

logger = logging.getLogger(__name__)


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


# ======================================================================================
# XML elements
# ======================================================================================


class AbstractElement:
    """Abstract base class for Rekordbox XML elements."""

    TAG: str

    def __init__(self, element):
        self.element = element

    @property
    def attrib(self):
        return self.element.attrib

    def __repr__(self):
        return f"{self.__class__.__name__}({self.attrib})"


# -- Collection elements ---------------------------------------------------------------


class Tempo(AbstractElement):
    """Rekordbox XML Tempo element for storing tempo and beat grid data of a track."""

    TAG = "TEMPO"

    def __init__(self, element):
        super().__init__(element)

    @classmethod
    def new(cls, track_element, inizio, bpm, metro, battito):
        """Create a new Tempo element

        Parameters
        ----------
        track_element: xml.etree.ElementTree.Element
            Parent track xml-element
        inizio: float
            Start position of BeatGrid
        bpm: float
            Value of BPM
        metro: str
            Kind of musical meter
        battito: int
            Beat number in the bar

        Returns
        -------
        temp: Tempo
        """
        attrib = {
            "Inizio": str(inizio),
            "Bpm": str(bpm),
            "Metro": metro,
            "Battito": str(battito),
        }
        return cls(xml.SubElement(track_element, cls.TAG, attrib=attrib))

    @property
    def inizio(self):
        """float: Start position of BeatGrid."""
        return float(self.element.get("Inizio"))

    @property
    def bpm(self):
        """float: Value of BPM."""
        return float(self.element.get("Bpm"))

    @property
    def metro(self):
        """str: Kind of musical meter."""
        return self.element.attrib.get("Metro")

    @property
    def battito(self):
        """int: Beat number in the bar."""
        return int(self.element.attrib.get("Battito"))


class PositionMark(AbstractElement):
    """Rekordbox XML Position element for storing position markers like cue points."""

    TAG = "POSITION_MARK"

    CUE = 0
    FADE_IN = 1
    FADE_OUT = 2
    LOAD = 3
    LOOP = 4

    def __init__(self, element):
        super().__init__(element)

    @classmethod
    def new(cls, track_element, name, marker_type, start, end, num):
        """Create a new PositionMark element

        Parameters
        ----------
        track_element : xml.etree.ElementTree.Element
            Parent track xml-element.
        name : str
            Name of position mark.
        marker_type : int
            Type of position mark.
        start : float
            Start position of position mark.
        end : float
            End position of position mark.
        num : int
            Number for identification of the position mark.

        Returns
        -------
        mark : PositionMark
            The new ``PositionMark`` instance.
        """
        attrib = {
            "Name": name,
            "Type": str(marker_type),
            "Start": str(start),
            "End": str(end),
            "Num": str(num),
        }
        return cls(xml.SubElement(track_element, cls.TAG, attrib=attrib))

    @property
    def name(self):
        """str: Name of position mark."""
        return self.element.attrib.get("Name")

    @property
    def type(self):
        """int: Type of position mark (Cue=0, Fade-In=1, Fade-Out=2, Load=3, Loop=4)."""
        return int(self.element.attrib.get("Type"))

    @property
    def start(self):
        """float: Start position of position mark."""
        return float(self.element.attrib.get("Start"))

    @property
    def end(self):
        """float: End position of position mark."""
        val = self.element.attrib.get("End")
        return float(val) if val is not None else None

    @property
    def num(self):
        """int: Number for identification of the position mark.

        Hot-Cue: 0, 1, 2, ...; Memory: -1.
        """
        return int(self.element.attrib.get("Num"))


class Track(AbstractElement):
    """Rekordbox XML Track element for storing the metadata of a track."""

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

    def __init__(self, element):
        super().__init__(element)
        self.tempos = list()
        self.marks = list()
        self.load_subelements()

    def load_subelements(self):
        tempo_elements = self.element.findall(f"{Tempo.TAG}")
        if tempo_elements is not None:
            self.tempos = [Tempo(el) for el in tempo_elements]
        mark_elements = self.element.findall(f".//{PositionMark.TAG}")
        if mark_elements is not None:
            self.marks = [PositionMark(el) for el in mark_elements]

    @property
    def attrib(self):
        return self.element.attrib

    @property
    def id(self):
        """int: Identification of track."""
        return int(self.element.attrib.get("TrackID"))

    @id.setter
    def id(self, value):
        """int: Identification of track."""
        self.element.attrib.update({"TrackID": str(value)})

    @property
    def name(self):
        """str: Name of track."""
        return self.element.attrib.get("Name")

    @name.setter
    def name(self, value):
        """str: Name of track."""
        self.element.attrib.update({"Name": value})

    @property
    def artist(self):
        """str: Name of artist."""
        return self.element.attrib.get("Artist")

    @artist.setter
    def artist(self, value):
        """str: Name of artist."""
        self.element.attrib.update({"Artist": value})

    @property
    def composer(self):
        """str: Name of composer (or producer)."""
        return self.element.attrib.get("Composer")

    @composer.setter
    def composer(self, value):
        """str: Name of composer (or producer)"""
        self.element.attrib.update({"Composer": value})

    @property
    def album(self):
        """str: Name of album."""
        return self.element.attrib.get("Album")

    @album.setter
    def album(self, value):
        """str: Name of album."""
        self.element.attrib.update({"Album": value})

    @property
    def grouping(self):
        """str: Name of group."""
        return self.element.attrib.get("Grouping")

    @grouping.setter
    def grouping(self, value):
        """str: Name of group."""
        self.element.attrib.update({"Grouping": value})

    @property
    def genre(self):
        """str: Name of genre."""
        return self.element.attrib.get("Genre")

    @genre.setter
    def genre(self, value):
        """str: Name of genre."""
        self.element.attrib.update({"Genre": value})

    @property
    def kind(self):
        """str: Type of audio file."""
        return self.element.attrib.get("Kind")

    @kind.setter
    def kind(self, value):
        """str: Type of audio file."""
        self.element.attrib.update({"Kind": value})

    @property
    def size(self):
        """int: Size of audio file."""
        return int(self.element.attrib.get("Size"))

    @size.setter
    def size(self, value):
        """int: Size of audio file."""
        self.element.attrib.update({"Size": str(value)})

    @property
    def total_time(self):
        """float: Duration of track (in seconds)."""
        return float(self.element.attrib.get("TotalTime"))

    @total_time.setter
    def total_time(self, value):
        """float: Duration of track (in seconds)."""
        self.element.attrib.update({"TotalTime": str(value)})

    @property
    def disc_num(self):
        """int: Order number of the disc of the album."""
        return int(self.element.attrib.get("DiscNumber"))

    @disc_num.setter
    def disc_num(self, value):
        """int: Order number of the disc of the album."""
        self.element.attrib.update({"DiscNumber": value})

    @property
    def track_num(self):
        """int: Order number of the track on the album."""
        return int(self.element.attrib.get("TrackNumber"))

    @track_num.setter
    def track_num(self, value):
        """int: Order number of the track on the album."""
        self.element.attrib.update({"TrackNumber": value})

    @property
    def year(self):
        """str: Year of release."""
        return self.element.attrib.get("Year")

    @year.setter
    def year(self, value):
        """str: Year of release."""
        self.element.attrib.update({"Year": value})

    @property
    def bpm(self):
        """float Value of average BPM."""
        return float(self.element.attrib.get("AverageBPM"))

    @bpm.setter
    def bpm(self, value):
        """float Value of average BPM."""
        self.element.attrib.update({"AverageBPM": str(value)})

    @property
    def date_modified(self):
        """str: Date of last modification (Format: yyyy-mm-dd)."""
        return self.element.attrib.get("DateModified")

    @date_modified.setter
    def date_modified(self, value):
        """str: Date of last modification (Format: yyyy-mm-dd)."""
        self.element.attrib.update({"DateModified": value})

    @property
    def date_added(self):
        """str: Date of addition (Format: yyyy-mm-dd)."""
        return self.element.attrib.get("DateAdded")

    @date_added.setter
    def date_added(self, value):
        """str: Date of addition (Format: yyyy-mm-dd)."""
        self.element.attrib.update({"DateAdded": value})

    @property
    def bit_rate(self):
        """int: Encoding bit rate."""
        return int(self.element.attrib.get("BitRate"))

    @bit_rate.setter
    def bit_rate(self, value):
        """int: Encoding bit rate."""
        self.element.attrib.update({"BitRate": str(value)})

    @property
    def sample_rate(self):
        """int: Frequency of sampling."""
        return int(self.element.attrib.get("SampleRate"))

    @sample_rate.setter
    def sample_rate(self, value):
        """int: Frequency of sampling."""
        self.element.attrib.update({"SampleRate": str(value)})

    @property
    def comments(self):
        """str: Comments of track."""
        return self.element.attrib.get("Comments")

    @comments.setter
    def comments(self, value):
        """str: Comments of track."""
        self.element.attrib.update({"Comments": value})

    @property
    def play_count(self):
        """int: Play count of the track."""
        return int(self.element.attrib.get("PlayCount"))

    @play_count.setter
    def play_count(self, value):
        """int: Play count of the track."""
        self.element.attrib.update({"PlayCount": str(value)})

    @property
    def last_played(self):
        """str: Date of last playing (Format: yyyy-mm-dd)."""
        return self.element.attrib.get("LastPlayed")

    @last_played.setter
    def last_played(self, value):
        """str: Date of last playing (Format: yyyy-mm-dd)."""
        self.element.attrib.update({"LastPlayed": value})

    @property
    def rating(self):
        """int: Rating of the track.

        0 star=0, 1 star=51, 2 stars=102, 3 stars=153, 4 stars=204, 5 stars=255.
        """
        return int(self.element.attrib.get("Rating"))

    @rating.setter
    def rating(self, value):
        """int: Rating of the track.

        0 star=0, 1 star=51, 2 stars=102, 3 stars=153, 4 stars=204, 5 stars=255.
        """
        self.element.attrib.update({"Rating": str(value)})

    @property
    def location(self):
        """str: Location of the file."""
        return self.element.attrib.get("Location")

    @location.setter
    def location(self, value):
        """str: Location of the file."""
        self.element.attrib.update({"Location": value})

    @property
    def remixer(self):
        """str: Name of remixer."""
        return self.element.attrib.get("Remixer")

    @remixer.setter
    def remixer(self, value):
        """str: Name of remixer."""
        self.element.attrib.update({"Remixer": value})

    @property
    def key(self):
        """str: Tonality (Kind of musical key)."""
        return self.element.attrib.get("Tonality")

    @key.setter
    def key(self, value):
        """str: Tonality (Kind of musical key)."""
        self.element.attrib.update({"Tonality": value})

    @property
    def label(self):
        """str: Name of the record label."""
        return self.element.attrib.get("Label")

    @label.setter
    def label(self, value):
        """str: Name of the record label."""
        self.element.attrib.update({"Label": value})

    @property
    def mix(self):
        """str: Name of mix."""
        return self.element.attrib.get("Mix")

    @mix.setter
    def mix(self, value):
        """str: Name of mix."""
        self.element.attrib.update({"Mix": value})

    @property
    def color(self):
        """str: Colour for track grouping."""
        return self.element.attrib.get("Colour")

    @color.setter
    def color(self, value):
        """str: Colour for track grouping."""
        self.element.attrib.update({"Colour": value})

    def sort_markers(self):
        self.marks.sort(key=lambda x: x.start)

    def cue_points(self):
        return [m for m in self.marks if m.type == PositionMark.CUE]

    def to_string(self):
        string = "TRACK:\n"
        for key, value in self.attrib.items():
            string += f"{key:<13}{value}\n"
        return string

    def __repr__(self):
        track_id = self.id
        name = self.name
        return f"{self.__class__.__name__}(ID={track_id}, Name={name})"


# -- Playlist elements -----------------------------------------------------------------


class Node(AbstractElement):
    """Rekordbox XML Node element used for storing playlist folders and playlists."""

    TAG = "NODE"

    FOLDER = 0
    PLAYLIST = 1

    TRACKID = 0
    LOCATION = 1

    def __init__(self, element):
        super().__init__(element)

    @classmethod
    def folder(cls, parent_element, name):
        attrib = {"Name": name, "Type": str(cls.FOLDER), "Count": "0"}
        return cls(xml.SubElement(parent_element, cls.TAG, attrib=attrib))

    @classmethod
    def playlist(cls, parent_element, name, keytype=TRACKID):
        attrib = {
            "Name": name,
            "Type": str(cls.PLAYLIST),
            "KeyType": str(keytype),
            "Entries": "0",
        }
        return cls(xml.SubElement(parent_element, cls.TAG, attrib=attrib))

    @property
    def parent(self):
        return self.element.parent

    @property
    def name(self):
        """str: Name of Node."""
        return self.element.attrib.get("Name")

    @property
    def type(self):
        """int: Type of Node (0=folder or 1=playlist)."""
        return int(self.element.attrib.get("Type"))

    @property
    def count(self):
        """int: Number of Node's in the Node."""
        return int(self.element.attrib.get("Count", 0))

    @property
    def entries(self):
        """int: Number of Track's in Playlist."""
        return int(self.element.attrib.get("Entries", 0))

    @property
    def keytype(self):
        """int: Kind of identification (0=TrackID or 1=Location)."""
        return int(self.element.attrib.get("KeyType"))

    @property
    def keys(self):
        """list of Track: TrackID's of the playlist-content (if playlist-Node)."""
        keys = list()
        for el in self.element.findall(f".//{Track.TAG}"):
            val = el.attrib["Key"]
            keys.append(int(val) if self.keytype == self.TRACKID else val)
        return keys

    @property
    def nodes(self):
        """list of Node: Sub-Nodes (in case of a folder-Node)."""
        return [Node(el) for el in self.element.findall(f"{Node.TAG}")]

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
        return Node(self.element.findall(f"{Node.TAG}[{i}]"))

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
        return Node(self.element.find(f'.//{Node.TAG}[@Name="{name}"]'))

    def add_folder_node(self, name):
        node = Node.folder(self.element, name)
        self.element.attrib["Count"] = str(self.count + 1)
        return node

    def add_playlist_node(self, name, keytype=TRACKID):
        node = Node.playlist(self.element, name, keytype)
        self.element.attrib["Count"] = str(self.count + 1)
        return node

    def get_track(self, idx):
        if self.type == self.FOLDER:
            return None
        el = self.element.findall(f".//{Track.TAG}[{idx}]")
        return int(el.attrib["Key"])

    def add_track(self, key):
        """Add a track to the current node.

        Parameters
        ----------
        key : int or str
            Track identification.
        """
        el = xml.SubElement(self.element, Track.TAG, attrib={"Key": str(key)})
        self.element.attrib["Entries"] = str(self.entries + 1)
        return el

    def print_tree(self, lvl=0, indent=4):
        space = indent * lvl * " "
        if self.type == self.PLAYLIST:
            print(space + f"Playlist: {self.name} ({self.entries} Tracks)")
        elif self.type == self.FOLDER:
            print(space + f"Folder: {self.name}")
            for node in self.nodes:
                node.print_tree(lvl + 1, indent)

    def __repr__(self):
        string = f"Node(Name={self.name}, type={self.type}, "
        if self.type == self.FOLDER:
            string += f"Count={self.count}"
        else:
            string += f"Entries={self.entries}, KeyType={self.keytype}"
        return string + ")"


# ======================================================================================
# XML File
# ======================================================================================


class RekordboxXml:
    """Rekordbox XML database file object."""

    ROOT = "DJ_PLAYLISTS"
    PRDT_TAG = "PRODUCT"
    PLST_TAG = "PLAYLISTS"
    COLL_TAG = "COLLECTION"

    def __init__(self, path="", name=None, version=None, company=None):
        self.path = path
        self._root = None
        self._product = None
        self._collection = None
        self._playlists = None
        self._root_node = None

        self.collection = None

        if os.path.exists(path):
            self.parse(self.path)
        else:
            self.init(name, version, company)

    @property
    def frmt_version(self):
        return self._root.attrib["Version"]

    @property
    def product_name(self):
        return self._product.attrib.get("Name")

    @property
    def product_version(self):
        return self._product.attrib.get("Version")

    @property
    def product_company(self):
        return self._product.attrib.get("Company")

    @property
    def num_tracks(self):
        return int(self._collection.attrib.get("Entries"))

    def init(self, name=None, version=None, company=None, frmt_version=None):
        frmt_version = frmt_version or "1.0.0"
        name = name or "pyRekordbox"
        version = version or "0.0.1"
        company = company or "None"

        # Initialize root element
        self._root = xml.Element(self.ROOT, attrib={"Version": frmt_version})
        # Initialize product element
        attrib = {"Name": name, "Version": version, "Company": company}
        self._product = xml.SubElement(self._root, self.PRDT_TAG, attrib=attrib)
        # Initialize collection element
        attrib = {"Entries": "0"}
        self._collection = xml.SubElement(self._root, self.COLL_TAG, attrib=attrib)
        # Initialize playlist element
        self._playlists = xml.SubElement(self._root, self.PLST_TAG)
        self._root_node = Node.folder(self._playlists, "ROOT")

    def parse(self, path):
        self.path = path

        tree = xml.parse(path)
        self._root = tree.getroot()
        self._product = self._root.find(self.PRDT_TAG)
        self._collection = self._root.find(self.COLL_TAG)
        self._playlists = self._root.find(self.PLST_TAG)
        self._root_node = Node(self._playlists.find(Node.TAG))

    def get_tracks(self):
        return [Track(el) for el in self._collection.findall(f".//{Track.TAG}")]

    def get_track_ids(self):
        return [Track(el).id for el in self._collection.findall(f".//{Track.TAG}")]

    def get_track(self, track_id):
        element = self._collection.find(f'.//{Track.TAG}[@TrackID="{track_id}"]')
        if element is None:
            return None
        return Track(element)

    def update_track_count(self):
        num_tracks = len(self._collection.findall(f".//{Track.TAG}"))
        self._collection.attrib["Entries"] = num_tracks

    def get_playlist(self, *names):
        node = self._root_node
        for name in names:
            node = node.get_node_by_name(name)
        return node

    def print_playlist_tree(self):
        self._root_node.print_tree()

    def tostring(self, indent=None):
        return pretty_xml(self._root, indent, encoding="utf-8")

    def save(self, path="", indent=None):
        if not path:
            path = self.path
        string = self.tostring(indent)
        with open(path, "w") as fh:
            fh.write(string)

    def __repr__(self):
        path = self.path
        name = self.product_name
        v = self.product_version
        company = self.product_company
        tracks = self.num_tracks

        cls = self.__class__.__name__
        s = f"{cls}('{path}', tracks={tracks}, info={name} {company} v{v})"
        return s
