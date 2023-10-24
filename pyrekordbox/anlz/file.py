# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-02-01

import logging
from collections import abc
from pathlib import Path
from typing import Union
from .tags import TAGS
from . import structs
from construct import Int16ub

logger = logging.getLogger(__name__)


class BuildFileLengthError(Exception):
    def __init__(self, struct, len_data):
        super().__init__(
            f"`len_file` ({struct.len_file}) of '{struct.type}' does not "
            f"match the data-length ({len_data})!"
        )


class AnlzFile(abc.Mapping):
    """Rekordbox `ANLZnnnn.xxx` binary file handler."""

    def __init__(self):
        self._path = ""
        self.file_header = None
        self.tags = list()

    @property
    def num_tags(self):
        return len(self.tags)

    @property
    def tag_types(self):
        return [tag.type for tag in self.tags]

    @property
    def path(self):
        return self._path

    @classmethod
    def parse(cls, data: bytes):
        """Parses the in-memory data of a Rekordbox analysis binary file.

        Parameters
        ----------
        data : bytes
            The in-memory binary contents of a Rekordbox analysis file.

        Returns
        -------
        self : AnlzFile
            The new instance with the parsed file content.
        """
        self = cls()
        self._parse(data)
        return self

    @classmethod
    def parse_file(cls, path: Union[str, Path]):
        """Reads and parses a Rekordbox analysis binary file.

        Parameters
        ----------
        path : str or Path
            The path of a Rekordbox analysis file which is used to read
            the file contents before parsing the binary data.

        Returns
        -------
        self : AnlzFile
            The new instance with the parsed file content.

        See Also
        --------
        AnlzFile.parse: Parses the data of a Rekordbox analysis file.
        """
        path = Path(path)
        ext = path.suffix.upper()
        if ext not in (".DAT", ".EXT", ".2EX"):
            raise ValueError(f"File type '{ext}' not supported!")

        logger.debug(f"Reading file {path.name}")
        with open(path, "rb") as fh:
            data = fh.read()

        self = cls.parse(data)
        self._path = path
        return self

    def _parse(self, data: bytes):
        file_header = structs.AnlzFileHeader.parse(data)
        tag_type = file_header.type
        assert tag_type == "PMAI"

        tags = list()
        i = file_header.len_header
        while i < file_header.len_file:
            # Get data starting from struct
            tag_data = data[i:]
            # Get the four byte struct type
            tag_type = tag_data[:4].decode("ascii")
            
            if tag_type == 'PSSI':
                # deobfuscate tag_data[18:] using xor with verysecretcode+len_entries
                verysecretcode = bytearray.fromhex("CB E1 EE FA E5 EE AD EE E9 D2 E9 EB E1 E9 F3 E8 E9 F4 E1")
                len_entries = Int16ub.parse(tag_data[16:])
                tag_data = bytearray(data[i:i+len(tag_data)])
                for x in range(len(tag_data[18:])):
                    decryptmask = verysecretcode[x%len(verysecretcode)]+len_entries
                    if decryptmask > 255 :
                        decryptmask -= 256
                    tag_data[x+18] = tag_data[x+18] ^ decryptmask

            try:
                # Parse the struct
                tag = TAGS[tag_type](tag_data)
                tags.append(tag)
                len_header = tag.struct.len_header
                len_tag = tag.struct.len_tag
                logger.debug(
                    "Parsed struct '%s' (len_header=%s, len_tag=%s)",
                    tag_type,
                    len_header,
                    len_tag,
                )
            except KeyError:
                logger.warning("Tag '%s' not supported!", tag_type)
                tag = structs.AnlzTag.parse(tag_data)
                len_tag = tag.len_tag
            i += len_tag

        self.file_header = file_header
        self.tags = tags

    def update_len(self):
        # Update struct lengths
        tags_len = 0
        for tag in self.tags:
            tag.update_len()
            tags_len += tag.struct.len_tag
        # Update file length
        len_file = self.file_header.len_header + tags_len
        self.file_header.len_file = len_file

    def build(self):
        self.update_len()
        header_data = structs.AnlzFileHeader.build(self.file_header)
        section_data = b"".join(tag.build() for tag in self.tags)
        data = header_data + section_data
        # Check `len_file`
        len_file = self.file_header.len_file
        len_data = len(data)
        if len_file != len_data:
            raise BuildFileLengthError(self.file_header, len_file)

        return data

    def save(self, path=""):
        path = path or self._path

        data = self.build()
        with open(path, "wb") as fh:
            fh.write(data)

    def get_tag(self, key):
        return self.__getitem__(key)[0]

    def getall_tags(self, key):
        return self.__getitem__(key)

    def get(self, key):
        return self.__getitem__(key)[0].get()

    def getall(self, key):
        return [tag.get() for tag in self.__getitem__(key)]

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(set(tag.type for tag in self.tags))

    def __getitem__(self, item):
        if item.isupper() and len(item) == 4:
            return [tag for tag in self.tags if tag.type == item]
        else:
            return [tag for tag in self.tags if tag.name == item]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.tag_types})"

    def set_path(self, path):
        tag = self.get_tag("PPTH")
        tag.set(path)
