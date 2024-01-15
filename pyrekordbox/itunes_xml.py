# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2024-01-03

import os
import secrets
from datetime import datetime
from abc import ABC
from collections import OrderedDict
from collections.abc import MutableMapping
import xml.etree.cElementTree as xml
import bidict
from .utils import (
    XmlFile,
    XmlAttributeKeyError,
    XmlDuplicateError,
    decode_xml_path,
    encode_xml_path,
)

DOCTYPE_LINE = (
    '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" '
    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
)

DATE_FRMT = "%Y-%m-%dT%H:%M:%S%z"

INT_TYPE = "integer"
STR_TYPE = "string"
DATE_TYPE = "date"

TYPES = {
    str: STR_TYPE,
    int: INT_TYPE,
    datetime: DATE_TYPE,
}
DTYPE_GETTERS = {
    STR_TYPE: str,
    INT_TYPE: int,
    DATE_TYPE: lambda s: datetime.strptime(s, DATE_FRMT),
}
DTYPE_SETTERS = {
    DATE_TYPE: lambda d: d.strftime(DATE_FRMT),
}


def _dict_item_string(key_element, value_element, encoding="utf-8"):
    key_str = xml.tostring(key_element, encoding=encoding)
    val_str = xml.tostring(value_element, encoding=encoding)
    return (key_str + val_str).decode().rstrip("\n\t")


def itunes_xml_string(root, indent=None):
    if indent is None:
        indent = "\t"
    indent2 = 2 * indent
    indent3 = 3 * indent
    indent4 = 4 * indent
    indent5 = 5 * indent

    s = '<?xml version="1.0" encoding="UTF-8"?>\n' + DOCTYPE_LINE + "\n"
    s += '<plist version="1.0">\n<dict>\n'

    main_dict = root.find("dict")
    tracks_dict, playlists_arr = None, None
    music_folder = None, None

    # Main dict
    for key, val in zip(main_dict[::2], main_dict[1::2]):
        if key.text == "Tracks":
            tracks_dict = val
        elif key.text == "Playlists":
            playlists_arr = val
        elif key.text == "Music Folder":
            music_folder = key, val
        else:
            s += indent + _dict_item_string(key, val) + "\n"

    # Tracks
    s += indent + "<key>Tracks</key>\n" + indent + "<dict>\n"
    for key, val in zip(tracks_dict[::2], tracks_dict[1::2]):
        track_id = key.text
        s += indent2 + f"<key>{track_id}</key>\n"
        s += indent2 + "<dict>\n"
        for k, v in zip(val[::2], val[1::2]):
            s += indent3 + _dict_item_string(k, v) + "\n"
        s += indent2 + "</dict>\n"
    s += indent + "</dict>\n"

    # Playlists
    s += indent + "<key>Playlists</key>\n" + indent + "<array>\n"
    for playlist in playlists_arr:
        s += indent2 + "<dict>\n"
        # Info
        arr = None
        for key, val in zip(playlist[::2], playlist[1::2]):
            if key.text == "Playlist Items":
                arr = val
            else:
                s += indent3 + _dict_item_string(key, val) + "\n"
        # Playlist items
        s += indent3 + "<key>Playlist Items</key>\n"
        s += indent3 + "<array>\n"
        for item in arr:
            s += indent4 + "<dict>\n"
            s += indent5 + _dict_item_string(item[0], item[1]) + "\n"
            s += indent4 + "</dict>\n"
        s += indent3 + "</array>\n" + indent2 + "</dict>\n"

    s += indent + "</array>\n"

    # Music folder at end
    s += indent + _dict_item_string(*music_folder) + "\n"
    s += "</dict>\n</plist>\n"
    return s


def _generate_persistent_id(existing_ids: set = None):
    if existing_ids is None:
        existing_ids = set()
    max_tries = 10_000
    for _ in range(max_tries):
        persist_id = secrets.token_hex(8).upper()
        if persist_id not in existing_ids:
            return persist_id
    raise RuntimeError("Could not generate unique persistent ID.")


class ItunesXmlElement(MutableMapping, ABC):
    """Base class for Track and Playlist items."""

    ATTRIBS: list
    """list[str]: List of all attribute keys of the XML element"""
    ATTRIB_MAP = bidict.bidict()
    """bidict[str, str]: Bidirectional map of attribute names

    Used to unify the attribute names of the Itunes and Rekordbox XML format.
    """
    GETTERS = dict()
    """dict[str, Callable]: Dictionary of attribute getter conversion methods.

    See Also
    --------
    AbstractElement.get
    """
    SETTERS = dict()
    """dict[str, Callable]: Dictionary of attribute setter conversion methods.

    See Also
    --------
    AbstractElement.set
    """

    def __init__(self, dict_element):
        self._dict_element = dict_element
        self._elements = OrderedDict()

    def get(self, key, default=None):
        if key in self.ATTRIB_MAP:
            key = self.ATTRIB_MAP[key]
        if key not in self.ATTRIBS:
            raise XmlAttributeKeyError(self.__class__, key, self.ATTRIBS)

        element = self._elements.get(key, None)
        if element is None:
            return default

        if element.tag == "true":
            return True
        elif element.tag == "false":
            return False

        value = element.text
        try:
            # Apply callback
            value = self.GETTERS[key](value)
        except KeyError:
            dtype = element.tag
            func = DTYPE_GETTERS.get(dtype, None)
            if func is not None:
                value = func(value)
        return value

    def set(self, key, value):
        if key in self.ATTRIB_MAP:
            key = self.ATTRIB_MAP[key]

        if key not in self.ATTRIBS:
            raise XmlAttributeKeyError(self.__class__, key, self.ATTRIBS)

        if isinstance(value, bool):
            dtype = "true" if value else "false"
            value = None
        else:
            dtype = TYPES[type(value)]
            try:
                # Apply callback
                value = self.SETTERS[key](value)
            except KeyError:
                func = DTYPE_SETTERS.get(type(value), None)
                if func is not None:
                    value = func(value)
                # Convert to str just in case
                value = str(value)

        element = self._elements.get(key, None)
        if element is None:
            xml.SubElement(self._dict_element, "key").text = key
            element = xml.SubElement(self._dict_element, dtype)
            if value is not None:
                element.text = value
            self._elements[key] = element
        else:
            element.text = value
            element.tag = dtype

    def delete(self, key):
        if key not in self.ATTRIBS:
            raise XmlAttributeKeyError(self.__class__, key, self.ATTRIBS)
        raise NotImplementedError()

    def __len__(self):
        """int: The number of attributes of the XML element."""
        return len(self._elements)

    def __iter__(self):
        """Iterable: An iterator of the attribute keys of the XML element."""
        return iter(self._elements)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def to_dict(self):
        return {k: self.get(k, None) for k, v in self._elements.items()}

    def tostring(self, indent=""):
        pass


class Track(ItunesXmlElement):
    ATTRIBS = [
        "Compilation",
        "Album Artist",
        "Persistent ID",
        "Track Number",
        "Grouping",
        "Composer",
        "Year",
        "Sort Name",
        "Skip Count",
        "Size",
        "Track ID",
        "Bit Rate",
        "Sort Artist",
        "Work",
        "Location",
        "Purchased",
        "Track Type",
        "Kind",
        "Release Date",
        "BPM",
        "Clean",
        "Has Video",
        "Artist",
        "Sort Album",
        "Sort Composer",
        "Album",
        "Disc Number",
        "Library Folder Count",
        "Comments",
        "Track Count",
        "Date Added",
        "Skip Date",
        "Date Modified",
        "Loved",
        "Play Date UTC",
        "Disc Count",
        "Artwork Count",
        "Play Date",
        "Volume Adjustment",
        "Genre",
        "Sort Album Artist",
        "Name",
        "Part Of Gapless Album",
        "Sample Rate",
        "Total Time",
        "File Folder Count",
        "Play Count",
    ]
    ATTRIB_MAP = bidict.bidict(
        {
            "TrackID": "Track ID",
            "TotalTime": "Total Time",
            "DiscNumber": "Disc Number",
            "TrackNumber": "Track Number",
            "AverageBpm": "BPM",
            "DateModified": "Date Modified",
            "DateAdded": "Date Added",
            "Bitrate": "Bit Rate",
            "SampleRate": "Sample Rate",
            "PlayCount": "Play Count",
            "LastPlayed": "Play Date UTC",
            "Label": "Work",
        }
    )
    GETTERS = {
        "Location": decode_xml_path,
    }
    SETTERS = {
        "Location": encode_xml_path,
    }

    def __init__(self, key_element, dict_element):
        self._key_element = key_element
        super().__init__(dict_element)
        for key, val in zip(self._dict_element[::2], self._dict_element[1::2]):
            self._elements[key.text] = val


class BasePlaylist(ItunesXmlElement):
    def __init__(self, dict_element):
        self._contents = OrderedDict()
        self._array_element = None
        super().__init__(dict_element)
        for key, val in zip(self._dict_element[::2], self._dict_element[1::2]):
            if key.text == "Playlist Items":
                self._array_element = val
            else:
                self._elements[key.text] = val

    def init(self):
        xml.SubElement(self._dict_element, "key").text = "Playlist Items"
        self._array_element = xml.SubElement(self._dict_element, "array")

    @property
    def tracks(self):
        return list(self._contents.values())

    def contains_track(self, track):
        return track["Track ID"] in self._contents

    def add_track(self, track):
        id_ = track["Track ID"]
        dict_element = xml.SubElement(self._array_element, "dict")
        xml.SubElement(dict_element, "key").text = "Track ID"
        xml.SubElement(dict_element, "integer").text = str(id_)
        self._contents[id_] = dict_element

    def remove_track(self, track):
        id_ = track["Track ID"]
        dict_element = self._contents.pop(id_)
        self._array_element.remove(dict_element)

    def clear_tracks(self):
        self._contents.clear()
        self._array_element.clear()


class MasterPlaylist(BasePlaylist):
    ATTRIBS = [
        "Master",
        "Playlist ID",
        "Playlist Persistent ID",
        "All Items",
        "Visible",
        "Name",
    ]


class Playlist(BasePlaylist):
    ATTRIBS = [
        "Playlist ID",
        "Playlist Persistent ID",
        "Parent Persistent ID",
        "Audiobooks",
        "All Items",
        "Distinguished Kind",
        "Name",
        "Smart Info",
        "Smart Criteria",
        "TV Shows",
        "Folder",
        "Music",
        "Movies",
        "Podcasts",
    ]


class ItunesXml(XmlFile):
    ROOT_TAG = "plist"

    def __init__(self, path=None, **kwargs):
        # Main container elements
        self._tracks_dict = None
        self._playlists_arr = None

        # Data in the XML file
        self._info = OrderedDict()
        self._tracks = OrderedDict()
        self._master_playlist = None
        self._playlists = OrderedDict()

        # Used to check for duplicates
        self._track_ids = set()
        self._track_persist_ids = set()
        self._locations = set()
        self._playlist_ids = set()
        self._playlist_persist_ids = set()

        super().__init__(path, **kwargs)

    @property
    def version(self):
        major = self._info["Major Version"].text
        minor = self._info["Minor Version"].text
        return f"{major}.{minor}"

    @property
    def application_version(self):
        return self._info["Application Version"].text

    @property
    def date(self):
        return datetime.strptime(self._info["Date"].text, DATE_FRMT)

    @property
    def features(self):
        return int(self._info["Features"].text)

    @property
    def show_content_ratings(self):
        return self._info["Show Content Ratings"].tag == "true"

    @property
    def library_persistent_id(self):
        return self._info["Library Persistent ID"].text

    @property
    def music_folder(self):
        return decode_xml_path(self._info["Music Folder"].text)

    @property
    def tracks(self):
        return list(self._tracks.values())

    @property
    def playlists(self):
        return list(self._playlists.values())

    def _add_track_cache(self, track):
        """Add the TrackID and Location to the cache."""
        self._locations.add(track["Location"])
        self._track_ids.add(track["Track ID"])
        self._track_persist_ids.add(track["Persistent ID"])

    def _remove_track_cache(self, track):
        """Remove the TrackID and Location from the cache."""
        self._locations.remove(track["Location"])
        self._track_ids.remove(track["Track ID"])
        self._track_persist_ids.remove(track["Persistent ID"])

    def _add_playlist_cache(self, playlist):
        """Add the TrackID and Location to the cache."""
        self._playlist_ids.add(playlist["Playlist ID"])
        self._playlist_persist_ids.add(playlist["Playlist Persistent ID"])

    def _remove_playlist_cache(self, playlist):
        """Remove the TrackID and Location from the cache."""
        self._playlist_ids.add(playlist["Playlist ID"])
        self._playlist_persist_ids.add(playlist["Playlist Persistent ID"])

    def _update_cache(self):
        """Update the cache with the current tracks in the collection."""
        self._locations.clear()
        self._track_ids.clear()
        self._track_persist_ids.clear()
        self._playlist_ids.clear()
        self._playlist_persist_ids.clear()

        for track in self.tracks:
            self._add_track_cache(track)
        for pl in self.playlists:
            self._add_playlist_cache(pl)

    def _update_master_playlist(self):
        for track in self.tracks:
            if not self._master_playlist.contains_track(track):
                self._master_playlist.add_track(track)

    def _parse(self, path):
        tree = xml.parse(str(path))
        self._root = tree.getroot()

        main_dict = self._root.find("dict")
        for key, val in zip(main_dict[::2], main_dict[1::2]):
            if key.text == "Tracks":
                self._tracks_dict = val
            elif key.text == "Playlists":
                self._playlists_arr = val
            else:
                self._info[key.text] = val

        # Parse tracks
        for key, val in zip(self._tracks_dict[::2], self._tracks_dict[1::2]):
            track = Track(key, val)
            assert int(key.text) == int(track["Track ID"])
            self._tracks[key.text] = track

        # Parse playlists
        self._master_playlist = MasterPlaylist(self._playlists_arr[0])
        for pl_dict in self._playlists_arr[1:]:
            pl = Playlist(pl_dict)
            persist_id = pl["Playlist Persistent ID"]
            self._playlists[persist_id] = pl

        self._update_cache()

    def _init(
        self,
        app_version="12.11.3.17",
        date=None,
        persist_id="E116CD8C3BA8AC5D",
        music_folder="C:/Users/dylan/Music/iTunes/iTunes Media",
    ):
        if date is None:
            date = datetime.now()

        self._root = xml.Element(self.ROOT_TAG, attrib={"Version": "1.0"})
        main_dict = xml.SubElement(self._root, "dict")

        # Info
        key = "Major Version"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, INT_TYPE)
        item.text = "1"
        self._info[key] = item

        key = "Minor Version"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, INT_TYPE)
        item.text = "1"
        self._info[key] = item

        key = "Application Version"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, STR_TYPE)
        item.text = app_version
        self._info[key] = item

        key = "Date"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, DATE_TYPE)
        item.text = date.strftime(DATE_FRMT) + "Z"
        self._info[key] = item

        key = "Features"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, INT_TYPE)
        item.text = "5"
        self._info[key] = item

        key = "Show Content Ratings"
        xml.SubElement(main_dict, "key").text = key
        self._info[key] = xml.SubElement(main_dict, "true")

        key = "Library Persistent ID"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, INT_TYPE)
        item.text = persist_id
        self._info[key] = item

        # Tracks
        xml.SubElement(main_dict, "key").text = "Tracks"
        self._tracks_dict = xml.SubElement(main_dict, "dict")

        # Playlists
        xml.SubElement(main_dict, "key").text = "Playlists"
        self._playlists_arr = xml.SubElement(main_dict, "array")

        # Music folder
        key = "Music Folder"
        xml.SubElement(main_dict, "key").text = key
        item = xml.SubElement(main_dict, STR_TYPE)
        item.text = encode_xml_path(music_folder)
        self._info[key] = item

        # Add the master Playlist
        id_ = 1
        persist_id = _generate_persistent_id()
        dict_element = xml.SubElement(self._playlists_arr, "dict")
        playlist = MasterPlaylist(dict_element)
        playlist.set("Master", True)
        playlist.set("Playlist ID", id_)
        playlist.set("Playlist Persistent ID", persist_id)
        playlist.set("All Items", True)
        playlist.set("Visible", False)
        playlist.set("Name", "Library")
        playlist.init()
        self._master_playlist = playlist

    def add_track(self, location, **kwargs):
        id_ = max(self._tracks.keys()) + 1 if self._tracks else 1
        persist_id = _generate_persistent_id(self._track_persist_ids)
        if os.path.normpath(location) in self._locations:
            raise XmlDuplicateError("Location", location)
        if id_ in self._track_ids:
            raise XmlDuplicateError("Track ID", id_)

        key_element = xml.SubElement(self._tracks_dict, "key")
        key_element.text = str(id_)
        dict_element = xml.SubElement(self._tracks_dict, "dict")

        track = Track(key_element, dict_element)
        track["Track ID"] = id_
        track["Persistent ID"] = persist_id
        track["Location"] = location
        track.update(kwargs)

        self._tracks[id_] = track
        self._add_track_cache(track)
        return track

    def get_track(self, id_):
        return self._tracks[id_]

    def remove_track(self, id_):
        track = self._tracks.pop(id_)
        # noinspection PyProtectedMember
        self._tracks_dict.remove(track._key_element)
        # noinspection PyProtectedMember
        self._tracks_dict.remove(track._dict_element)
        self._remove_track_cache(track)

    def add_playlist(self, name, parent=None, all_items=True, **kwargs):
        id_ = max(self._playlists.keys()) + 1 if self._playlists else 2
        persist_id = _generate_persistent_id(self._playlist_persist_ids)
        if id_ in self._playlist_ids:
            raise ValueError(f"Playlist ID {id_} already in use")
        if persist_id in self._playlist_persist_ids:
            raise ValueError(f"Playlist Persistent ID {persist_id} already in use")

        dict_element = xml.SubElement(self._playlists_arr, "dict")
        playlist = Playlist(dict_element)
        playlist["Playlist ID"] = id_
        if parent is not None:
            playlist["Parent Persistent ID"] = parent["Playlist Persistent ID"]
        playlist["Playlist Persistent ID"] = persist_id
        playlist["All Items"] = all_items
        playlist["Name"] = name
        for key, val in kwargs.items():
            playlist[key] = val
        playlist.init()

        self._playlists[persist_id] = playlist
        self._add_playlist_cache(playlist)
        return playlist

    def get_playlist(self, persist_id):
        return self._playlists[persist_id]

    def remove_playlist(self, persist_id):
        playlist = self._playlists.pop(persist_id)
        # noinspection PyProtectedMember
        self._tracks_dict.remove(playlist._dict_element)
        self._remove_playlist_cache(playlist)

    def tostring(self, indent=None, itunes_format=True):
        self._update_master_playlist()
        if itunes_format:
            return itunes_xml_string(self._root, indent)
        else:
            lines = super().tostring(indent).splitlines()
            lines.insert(1, DOCTYPE_LINE)
            return "\n".join(lines)
