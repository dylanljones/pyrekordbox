# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-09-10

from pathlib import Path
from datetime import datetime
import xml.etree.cElementTree as xml
from ..config import get_config
from ..xml import pretty_xml


class MasterPlaylistXml:
    """Rekordbox v6 masterPlaylists6.xml file handler.

    Rekordbox stores some playlist information in the masterPlaylists6.xml file.
    Each playlist is represented by a <PLAYLIST> element, containing the following
    attributes:
    - Id: The playlist ID in hexadecimal format.
    - ParentId: The parent playlist ID in hexadecimal format. The root playlist has
    - Attributes: The type of playlist. 0 = normal, 1 = folder, 4 = smart playlist.
    - Timestamp: The last time the playlist was updated.
    - Lib_Type: ? (0 for palylists/folders)
    - CheckType: ? (always 0)
    """

    KEYS = ["Id", "ParentId", "Attributes", "Timestamp", "Lib_Type", "CheckType"]

    def __init__(self, path=None, db_dir=None):
        if path is None:
            if db_dir is None:
                db_dir = get_config("rekordbox6", "db_dir")
            path = Path(db_dir) / "masterPlaylists6.xml"

        tree = xml.parse(str(path))
        self.path = path
        self.root = tree.getroot()
        self.product = self.root.find("PRODUCT")
        self.playlists = self.root.find("PLAYLISTS")
        self._changed = False

    @property
    def version(self):
        return self.root.attrib["Version"]

    @property
    def automatic_sync(self):
        return self.root.attrib["AutomaticSync"]

    @property
    def rekordbox_version(self):
        return self.product.attrib["Version"]

    @property
    def modified(self):
        return self._changed

    def get_playlists(self):
        """Returns a list of the attributes of all playlist elements."""
        items = list()
        for playlist in self.playlists:
            items.append(playlist.attrib)
        return items

    def get(self, playlist_id):
        """Returns element attribs with the PlaylistID used in the `master.db` database.

        Parameters
        ----------
        playlist_id : str or int
            The playlist ID used in the main `master.db` database. This id is converted
            to hexadecimal format before searching.

        Returns
        -------
        playlist : dict
        """
        hex_id = f"{int(playlist_id):X}"
        element = self.playlists.find(f'.//NODE[@Id="{hex_id}"]')
        if element is None:
            return None
        attribs = dict(element.attrib)
        attribs["Attribute"] = int(attribs["Attribute"])
        attribs["Timestamp"] = datetime.fromtimestamp(int(attribs["Timestamp"]) / 1000)
        attribs["Lib_Type"] = int(attribs["Lib_Type"])
        attribs["CheckType"] = int(attribs["CheckType"])
        return attribs

    def add(
        self,
        playlist_id: str,
        parent_id: str,
        attribute: int,
        updated_at: datetime,
        lib_type: int = 0,
        check_type: int = 0,
    ):
        """Adds a new element with the PlaylistID used in the `master.db` database.

        Parameters
        ----------
        playlist_id : str or int
            The playlist ID used in the main `master.db` database. This id is converted
            to hexadecimal format before searching.
        parent_id : str or int, optional
            The parent playlist ID used in the main `master.db` database. This id is
            converted to hexadecimal format.
        attribute : int, optional
            The type of playlist. 0 = normal, 1 = folder, 4 = smart playlist.
        updated_at : datetime, optional
            The last time the playlist was updated.
        lib_type : int, optional
            The libarray type. It seems to be always 0 for playlists.
        check_type : int, optional
            The check type. It seems to be always 0.

        Returns
        -------
        element : xml.Element
            The newly created element.
        """
        hex_id = f"{int(playlist_id):X}"
        parent_id = f"{int(parent_id):X}" if parent_id != "root" else "0"
        timestamp = int(updated_at.timestamp() * 1000)
        attrib = {
            "Id": hex_id,
            "ParentId": parent_id,
            "Attribute": str(attribute),
            "Timestamp": str(timestamp),
            "Lib_Type": str(lib_type),
            "CheckType": str(check_type),
        }
        element = xml.SubElement(self.playlists, "NODE", attrib=attrib)
        self._changed = True
        return element

    def remove(self, playlist_id):
        """Removes the element with the PlaylistID used in the `master.db` database.

        Parameters
        ----------
        playlist_id : str or int
            The playlist ID used in the main `master.db` database. This id is converted
            to hexadecimal format before searching.
        """
        hex_id = f"{int(playlist_id):X}"
        element = self.playlists.find(f'.//NODE[@Id="{hex_id}"]')
        if element is None:
            raise ValueError(f"Playlist with ID {playlist_id} ({hex_id}) not found.")
        self.playlists.remove(element)
        self._changed = True

    def update(
        self,
        playlist_id: str,
        parent_id: str = None,
        attribute: int = None,
        updated_at: datetime = None,
        lib_type: int = None,
        check_type: int = None,
    ):
        """Updates the element with the PlaylistID used in the `master.db` database.

        Parameters
        ----------
        playlist_id : str or int
            The playlist ID used in the main `master.db` database. This id is converted
            to hexadecimal format before searching.
        parent_id : str or int, optional
            The parent playlist ID used in the main `master.db` database. This id is
            converted to hexadecimal format.
        attribute : int, optional
            The type of playlist. 0 = normal, 1 = folder, 4 = smart playlist.
        updated_at : datetime, optional
            The last time the playlist was updated.
        lib_type : int, optional
            The libarray type. It seems to be always 0 for playlists.
        check_type : int, optional
            The check type. It seems to be always 0.
        """
        hex_id = f"{int(playlist_id):X}"
        element = self.playlists.find(f'.//NODE[@Id="{hex_id}"]')
        if element is None:
            raise ValueError(f"Playlist with ID {playlist_id} ({hex_id}) not found.")

        attribs = dict()
        if parent_id is not None:
            attribs["ParentId"] = f"{int(parent_id):X}" if parent_id != "root" else "0"
        if attribute is not None:
            attribs["Attribute"] = str(attribute)
        if updated_at is not None:
            attribs["Timestamp"] = str(int(updated_at.timestamp() * 1000))
        if lib_type is not None:
            attribs["Lib_Type"] = str(lib_type)
        if check_type is not None:
            attribs["CheckType"] = str(check_type)

        element.attrib.update(attribs)
        self._changed = True

    def to_string(self, indent=None):
        return pretty_xml(self.root, indent, encoding="utf-8")

    def save(self, path=None, indent=None):
        if path is None:
            path = self.path
        path = str(path)

        string = self.to_string(indent)
        with open(path, "w") as fh:
            fh.write(string)
        self._changed = False
