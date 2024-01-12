# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2024-01-03

import os
import secrets
from datetime import datetime
from abc import abstractmethod
from collections import OrderedDict
from collections.abc import MutableMapping
import xml.etree.cElementTree as xml
from .utils import encode_xml_path, decode_xml_path

DATE_FRMT = "%Y-%m-%dT%H:%M:%S%z"

VALID_VALUE_TAGS = "string", "integer", "date", "true", "false", "dict", "array", "data"
PATH_VALUES = "Music Folder", "Location"

TYPES = {
    str: "string",
    int: "integer",
    datetime: "date",
}
DTYPE_GETTERS = {
    "string": str,
    "integer": int,
    "date": lambda s: datetime.strptime(s, DATE_FRMT),
}
DTYPE_SETTERS = {
    "date": lambda d: d.strftime(DATE_FRMT),
}


def _iter_dict_element_contents(element):
    n_childs = len(element)
    for i in range(0, n_childs, 2):
        key_element = element[i]
        value_element = element[i + 1]
        assert key_element.tag == "key"
        assert value_element.tag in VALID_VALUE_TAGS
        yield key_element, value_element


def _parse_value(key_element, value_element):
    dtype = value_element.tag
    if dtype == "true":
        value = True
    elif dtype == "false":
        value = False
    elif dtype == "data":
        value = value_element.text
    else:
        value = DTYPE_GETTERS[dtype](value_element.text)
    if key_element.text in PATH_VALUES:
        value = decode_xml_path(value)
    return value


def _generate_persistent_id(existing_ids):
    max_tries = 10_000
    for _ in range(max_tries):
        persist_id = secrets.token_hex(8).upper()
        if persist_id not in existing_ids:
            return persist_id
    raise RuntimeError("Could not generate unique persistent ID.")


class KeyValueElement:
    """Represents a key-value pair in an iTunes XML file."""

    def __init__(
        self,
        parent=None,
        key=None,
        dtype=None,
        value=None,
        key_element=None,
        value_element=None,
    ):
        if parent is not None:
            key_element = xml.SubElement(parent, "key")
            key_element.text = key
            value_element = xml.SubElement(parent, dtype)
            if value is not None:
                value_element.text = str(value)
        self._key_element = key_element
        self._value_element = value_element

    @classmethod
    def integer(cls, parent, key, value):
        return cls(parent=parent, key=key, dtype="integer", value=value)

    @classmethod
    def string(cls, parent, key, value):
        return cls(parent=parent, key=key, dtype="string", value=value)

    @classmethod
    def date(cls, parent, key, value):
        valstr = DTYPE_SETTERS["date"](value)
        return cls(parent=parent, key=key, dtype="date", value=valstr)

    @classmethod
    def bool(cls, parent, key, value):
        return cls(parent=parent, key=key, dtype="true" if value else "false")

    @property
    def key(self):
        return self._key_element.text

    @property
    def value(self):
        return _parse_value(self._key_element, self._value_element)

    @value.setter
    def value(self, value):
        self._value_element.text = str(value)

    def tostring(self, encoding="utf-8"):
        key_str = xml.tostring(self._key_element, encoding=encoding)
        val_str = xml.tostring(self._value_element, encoding=encoding)
        return (key_str + val_str).decode().rstrip("\n\t")


class ItunesXmlElement(MutableMapping):
    ATTRIBS = []  # List of valid attribute names
    GETTERS = {}  # Dict of callbacks to apply when getting an attribute
    SETTERS = {}  # Dict of callbacks to apply when setting an attribute

    def __init__(
        self, parent_element, element=None, id_=None, persist_id=None, **kwargs
    ):
        self._parent_element = parent_element
        self._data = OrderedDict()
        if element is not None:
            self._parse(element)
        else:
            self._init(parent_element, id_, persist_id, **kwargs)

    @abstractmethod
    def _parse(self, element):
        pass

    @abstractmethod
    def _init(self, parent_element, id_, persist_id, **kwargs):
        pass

    def get(self, key, default=None):
        if key not in self.ATTRIBS:
            raise KeyError(key)

        item = self._data.get(key, None)
        if item is None:
            return default

        value = item.value
        try:
            # Apply callback
            value = self.GETTERS[key](value)
        except KeyError:
            pass
        return value

    def set(self, key, value):
        if key not in self.ATTRIBS:
            raise KeyError(key)
        if isinstance(value, bool):
            dtype = "true" if value else "false"
            value = None
        else:
            dtype = TYPES[type(value)]
            try:
                # Apply callback
                value = self.SETTERS[key](value)
            except KeyError:
                # Convert to str just in case
                value = str(value)

        item = self._data.get(key, None)
        if item is None:
            item = KeyValueElement(
                self._parent_element, key=key, dtype=dtype, value=value
            )
            self._data[item.key] = item
        else:
            item.value = value

    def __len__(self):
        """int: The number of attributes of the XML element."""
        return len(self._data)

    def __iter__(self):
        """Iterable: An iterator of the attribute keys of the XML element."""
        return iter(self._data)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        if key not in self.ATTRIBS:
            raise KeyError(key)
        del self._data[key]

    def to_dict(self):
        return {k: self.get(k, None) for k, v in self._data.items()}

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
    SETTERS = {"Location": encode_xml_path}

    def __init__(
        self,
        parent_element,
        element=None,
        id_=None,
        persist_id=None,
        location=None,
        **kwargs,
    ):
        super().__init__(
            parent_element, element, id_, persist_id, location=location, **kwargs
        )

    def _parse(self, element):
        for key_el, value_el in _iter_dict_element_contents(element):
            item = KeyValueElement(key_element=key_el, value_element=value_el)
            self._data[item.key] = item

    def _init(self, parent_element, id_, persist_id, **kwargs):
        self.set("Track ID", id_)
        self.set("Persistent ID", persist_id)
        self.set("Location", kwargs.pop("location", None))
        for key, value in kwargs.items():
            self.set(key, value)

    def tostring(self, indent=""):
        lines = list()
        trackid = self.get("Track ID")
        lines.append(2 * indent + f"<key>{trackid}</key>")
        lines.append(2 * indent + "<dict>")
        for key, value in self._data.items():
            lines.append(3 * indent + value.tostring())
        lines.append(2 * indent + "</dict>")
        return "\n".join(lines)


class BasePlaylist(ItunesXmlElement):
    def __init__(
        self, parent_element, element=None, id_=None, persist_id=None, **kwargs
    ):
        self._contents = list()
        super().__init__(parent_element, element, id_, persist_id, **kwargs)

    @property
    def contents(self):
        return self._contents

    def _parse(self, element):
        items = None
        for key_el, value_el in _iter_dict_element_contents(element):
            if key_el.text == "Playlist Items":
                items = value_el
            else:
                item = KeyValueElement(key_element=key_el, value_element=value_el)
                self._data[item.key] = item

        if items is not None:
            for item_dict in items:
                key_el, value_el = item_dict
                assert key_el.text == "Track ID"
                self._contents.append(int(value_el.text))

    def contains_track(self, track):
        return track["Track ID"] in self._contents

    def add_track(self, track):
        self._contents.append(track["Track ID"])

    def clear_tracks(self):
        self._contents.clear()

    def tostring(self, indent=""):
        lines = list()
        lines.append(2 * indent + "<dict>")
        for key, value in self._data.items():
            lines.append(3 * indent + value.tostring())

        lines.append(3 * indent + "<key>Playlist Items</key>")
        lines.append(3 * indent + "<array>")
        for id_ in self._contents:
            lines.append(4 * indent + "<dict>")
            lines.append(5 * indent + f"<key>Track ID</key><integer>{id_}</integer>")
            lines.append(4 * indent + "</dict>")
        lines.append(3 * indent + "</array>")
        lines.append(2 * indent + "</dict>")
        return "\n".join(lines)


class MasterPlaylist(BasePlaylist):
    ATTRIBS = [
        "Master",
        "Playlist ID",
        "Playlist Persistent ID",
        "All Items",
        "Visible",
        "Name",
    ]

    def _init(self, parent_element, id_, persist_id, **kwargs):
        xml.SubElement(parent_element, "key").text = str(id_)
        xml.SubElement(parent_element, "dict")

        self.set("Master", True)
        self.set("Playlist ID", id_)
        self.set("Playlist Persistent ID", persist_id)
        self.set("All Items", True)
        self.set("Visible", False)
        self.set("Name", "Library")


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

    def _init(self, parent_element, id_, persist_id, **kwargs):
        self.set("Playlist ID", id_)
        self.set("Playlist Persistent ID", persist_id)
        for key, val in kwargs.items():
            self.set(key, val)


class ItunesXml:
    ROOT_TAG = "plist"

    def __init__(self, path=None, **kwargs):
        self._root = None
        self._tracks_dict = None
        self._playlists_arr = None

        self._info = OrderedDict()
        self._tracks = OrderedDict()
        self._master_playlist = None
        self._playlists = OrderedDict()

        self._track_ids = set()
        self._track_persist_ids = set()
        self._locations = set()
        self._playlist_ids = set()
        self._playlist_persist_ids = set()

        if path is not None:
            self._parse(path)
        else:
            self._init(**kwargs)

    @property
    def major_version(self):
        return self._info["Major Version"].value

    @property
    def minor_version(self):
        return self._info["Minor Version"].value

    @property
    def application_version(self):
        return self._info["Application Version"].value

    @property
    def date(self):
        return self._info["Date"].value

    @property
    def features(self):
        return self._info["Features"].value

    @property
    def show_content_ratings(self):
        return self._info["Show Content Ratings"].value

    @property
    def library_persistent_id(self):
        return self._info["Library Persistent ID"].value

    @property
    def music_folder(self):
        return self._info["Music Folder"].value

    @property
    def tracks(self):
        return list(self._tracks.values())

    @property
    def playlists(self):
        return list(self._playlists.values())

    def _parse(self, path):
        tree = xml.parse(str(path))
        self._root = tree.getroot()

        # Parse info
        plist_dict = self._root.find("dict")
        for key_el, value_el in _iter_dict_element_contents(plist_dict):
            if key_el.text == "Tracks":
                self._tracks_dict = value_el
            elif key_el.text == "Playlists":
                self._playlists_arr = value_el
            else:
                keyval = KeyValueElement(key_element=key_el, value_element=value_el)
                key = key_el.text
                self._info[key] = keyval

        # Parse tracks
        for key_el, value_el in _iter_dict_element_contents(self._tracks_dict):
            track_id = int(key_el.text)
            track = Track(self._tracks_dict, element=value_el)
            self._tracks[track_id] = track

        # Parse playlists
        master_pl = MasterPlaylist(self._playlists_arr, element=self._playlists_arr[0])
        self._master_playlist = master_pl
        for pl_dict in self._playlists_arr[1:]:
            pl = Playlist(self._playlists_arr, element=pl_dict)
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
        plist_dict = xml.SubElement(self._root, "dict")

        # Info
        item = KeyValueElement.integer(plist_dict, "Major Version", 1)
        self._info[item.key] = item
        item = KeyValueElement.integer(plist_dict, "Minor Version", 1)
        self._info[item.key] = item
        item = KeyValueElement.string(plist_dict, "Application Version", app_version)
        self._info[item.key] = item
        item = KeyValueElement.date(plist_dict, "Date", date)
        self._info[item.key] = item
        item = KeyValueElement.integer(plist_dict, "Features", 5)
        self._info[item.key] = item
        item = KeyValueElement.bool(plist_dict, "Show Content Ratings", True)
        self._info[item.key] = item
        item = KeyValueElement.string(plist_dict, "Library Persistent ID", persist_id)
        self._info[item.key] = item
        # Tracks dict
        xml.SubElement(plist_dict, "key").text = "Tracks"
        self._tracks_dict = xml.SubElement(plist_dict, "dict")
        # Playlists array
        xml.SubElement(plist_dict, "key").text = "Playlists"
        self._playlists_arr = xml.SubElement(plist_dict, "array")
        # Music folder
        item = KeyValueElement.string(
            plist_dict, "Music Folder", encode_xml_path(music_folder)
        )
        self._info[item.key] = item

        persist_id = _generate_persistent_id(set())
        self._master_playlist = MasterPlaylist(
            self._playlists_arr, id_=1, persist_id=persist_id
        )

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

    def get_track(self, track_id):
        return self._tracks[track_id]

    def add_track(self, location, **kwargs):
        id_ = max(self._tracks.keys()) + 1 if self._tracks else 1
        persist_id = _generate_persistent_id(self._track_persist_ids)
        if os.path.normpath(location) in self._locations:
            raise ValueError(f"Track with Location {location} already in database")
        if id_ in self._track_ids:
            raise ValueError(f"Track ID {id_} already in use")

        track = Track(
            self._tracks_dict,
            location=location,
            id_=id_,
            persist_id=persist_id,
            **kwargs,
        )
        self._tracks[track["Track ID"]] = track
        self._add_track_cache(track)
        return track

    def get_playlist(self, persist_id):
        return self._playlists[persist_id]

    def add_playlist(self, name, parent=None, all_items=True, **kwargs):
        id_ = max(self._playlists.keys()) + 1 if self._playlists else 1
        persist_id = _generate_persistent_id(self._playlist_persist_ids)
        if id_ in self._playlist_ids:
            raise ValueError(f"Playlist ID {id_} already in use")

        attribs = {
            "Name": name,
            "All Items": all_items,
        }
        if parent is not None:
            attribs["Parent Persistent ID"] = parent["Playlist Persistent ID"]
        attribs.update(kwargs)
        pl = Playlist(self._playlists_arr, id_=id_, persist_id=persist_id, **attribs)
        self._playlists[pl["Playlist ID"]] = pl
        self._add_playlist_cache(pl)
        return pl

    def tostring(self, indent=None, char_replacements=None):
        if not self.tracks:
            raise ValueError("No tracks in library")
        if char_replacements is None:
            char_replacements = {"\u200b": ""}

        self._update_master_playlist()

        if indent is None:
            indent = "\t"

        lines = list()
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append(
            '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        )
        lines.append('<plist version="1.0">')
        lines.append("<dict>")
        for info in self._info.values():
            if info.key == "Music Folder":
                continue
            lines.append(indent + info.tostring())
        # Tracks
        lines.append(indent + "<key>Tracks</key>")
        lines.append(indent + "<dict>")
        for track in self.tracks:
            lines.append(track.tostring(indent=indent))
        lines.append(indent + "</dict>")
        # Playlists
        lines.append(indent + "<key>Playlists</key>")
        lines.append(indent + "<array>")
        lines.append(self._master_playlist.tostring(indent=indent))
        for pl in self.playlists:
            lines.append(pl.tostring(indent=indent))
        lines.append(indent + "</array>")
        # Music folder at end
        lines.append(indent + self._info["Music Folder"].tostring())

        lines.append("</dict>")
        lines.append("</plist>")
        string = "\n".join(lines)
        for char, replacement in char_replacements.items():
            string = string.replace(char, replacement)
        return string

    def save(self, path="", indent=None):
        """Saves the contents to an XML file.

        Parameters
        ----------
        path : str or Path, optional
            The path for saving the XML file. The default is the original file.
        indent : str, optional
            The indentation used for formatting the XML element.
            The default is 3 spaces.
        """
        data = self.tostring(indent).encode("utf-8")
        with open(path, "wb") as fh:
            fh.write(data)
