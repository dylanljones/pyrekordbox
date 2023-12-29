# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-12-13

import xml.etree.cElementTree as xml
from enum import StrEnum, IntEnum
from typing import List, Union
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import or_, and_, not_, select
from sqlalchemy.sql.elements import BooleanClauseList
from dateutil.relativedelta import relativedelta  # noqa

from .tables import DjmdContent, DjmdSongMyTag, DjmdMyTag

__all__ = [
    "LogicalOperator",
    "Operator",
    "Condition",
    "SmartList",
]


class LogicalOperator(IntEnum):
    ALL = 1
    ANY = 2


class Operator(IntEnum):
    EQUAL = 1
    NOT_EQUAL = 2
    GREATER = 3
    LESS = 4
    IN_RANGE = 5
    IN_LAST = 6
    NOT_IN_LAST = 7
    CONTAINS = 8
    NOT_CONTAINS = 9
    STARTS_WITH = 10
    ENDS_WITH = 11


class Property(StrEnum):
    ARTIST = "artist"
    ALBUM = "album"
    ALBUM_ARTIST = "albumartist"
    ORIGINAL_ARTIST = "originalartist"
    BPM = "bpm"
    GROUPING = "grouping"
    COMMENTS = "comments"
    PRODUCER = "producer"
    STOCK_DATE = "stockdate"
    DATE_CREATED = "datecreated"
    COUNTER = "counter"
    FILENAME = "filename"
    GENRE = "genre"
    KEY = "key"
    LABEL = "label"
    MIX_NAME = "mixname"
    MYTAG = "mytag"
    RATING = "rating"
    DATE_RELEASED = "datereleased"
    REMIXED_BY = "remixedby"
    DURATION = "duration"
    NAME = "name"
    YEAR = "year"


STR_OPS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.CONTAINS,
    Operator.NOT_CONTAINS,
    Operator.STARTS_WITH,
    Operator.ENDS_WITH,
]

NUM_OPS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.GREATER,
    Operator.LESS,
    Operator.IN_RANGE,
]

DATE_OPS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.GREATER,
    Operator.LESS,
    Operator.IN_RANGE,
    Operator.IN_LAST,
    Operator.NOT_IN_LAST,
]


PROPERTY_MAP = {
    "artist": "ArtistName",
    "album": "AlbumName",
    "albumArtist": "AlbumArtist",
    "originalArtist": "OrgArtist",
    "bpm": "BPM",
    "grouping": "ColorID",
    "comments": "Commnt",
    "producer": "ComposerName",
    "stockDate": "StockDate",
    "dateCreated": "created_at",
    "counter": "DJPlayCount",
    "fileName": "FileNameL",
    "genre": "GenreName",
    "key": "Key",
    "label": "LabelName",
    "mixName": "",
    "myTag": "myTag",
    "rating": "Rating",
    "dateReleased": "ReleaseDate",
    "remixedBy": "RemixerName",
    "duration": "Length",
    "name": "Title",
    "year": "ReleaseYear",
}


VALID_OPS = {
    "artist": STR_OPS,
    "album": STR_OPS,
    "albumArtist": STR_OPS,
    "originalArtist": STR_OPS,
    "bpm": NUM_OPS,
    "grouping": [Operator.EQUAL, Operator.NOT_EQUAL],
    "comments": STR_OPS,
    "producer": STR_OPS,
    "stockDate": DATE_OPS,
    "dateCreated": DATE_OPS,
    "counter": NUM_OPS,
    "fileName": STR_OPS,
    "genre": STR_OPS,
    "key": STR_OPS,
    "label": STR_OPS,
    "mixName": STR_OPS,
    "myTag": [Operator.CONTAINS, Operator.NOT_CONTAINS],
    "rating": NUM_OPS,
    "dateReleased": DATE_OPS,
    "remixedBy": STR_OPS,
    "duration": NUM_OPS,
    "name": STR_OPS,
    "year": NUM_OPS,
}

TYPE_CONVERSION = {
    "bpm": int,
    "stockDate": lambda x: datetime.strptime(x, "%Y-%m-%d"),
    "dateCreated": lambda x: datetime.strptime(x, "%Y-%m-%d"),
    "counter": int,
    "rating": int,
    "dateReleased": lambda x: datetime.strptime(x, "%Y-%m-%d"),
    "duration": int,
    "year": int,
}


@dataclass
class Condition:
    """Dataclass for a smart playlist condition."""

    property: str
    operator: int
    unit: str
    value_left: Union[str, int]
    value_right: Union[str, int]

    def __post_init__(self):
        if self.property not in VALID_OPS:
            raise ValueError(
                f"Invalid property: '{self.property}'! "
                f"Supported properties: {list(PROPERTY_MAP.keys())}"
            )

        valid_ops = VALID_OPS[self.property]
        if self.operator not in valid_ops:
            raise ValueError(
                f"Invalid operator '{self.operator}' for '{self.property}', "
                f"must be one of {valid_ops}"
            )

        if self.operator == Operator.IN_RANGE:
            if not self.value_right:
                raise ValueError(f"Operator '{self.operator}' requires `value_right`")


def _get_condition_values(cond):
    val_left = cond.value_left
    val_right = cond.value_right
    func = None
    if cond.operator in (Operator.IN_LAST, Operator.NOT_IN_LAST):
        func = int
    elif cond.property in TYPE_CONVERSION:
        func = TYPE_CONVERSION[cond.property]

    if func is not None:
        if val_left != "":
            val_left = func(val_left)
        if val_right != "":
            try:
                val_right = func(val_right)
            except ValueError:
                pass
    return val_left, val_right


class SmartList:
    """Rekordbox smart playlist XML handler."""

    def __init__(
        self,
        playlist_id: Union[int, str] = None,
        logical_operator: int = None,
        auto_update: int = 1,
    ):
        self.playlist_id: Union[int, str] = playlist_id
        self.logical_operator: int = logical_operator
        self.auto_update: int = auto_update
        self.conditions: List[Condition] = list()

    def parse(self, source: str) -> None:
        """Parse the XML source of a smart playlist."""
        tree = xml.ElementTree(xml.fromstring(source))
        root = tree.getroot()
        conditions = list()
        for child in root.findall("CONDITION"):
            condition = Condition(
                property=child.attrib["PropertyName"],
                operator=int(child.attrib["Operator"]),
                unit=child.attrib["ValueUnit"],
                value_left=child.attrib["ValueLeft"],
                value_right=child.attrib["ValueRight"],
            )
            conditions.append(condition)

        self.playlist_id = int(root.attrib["Id"])
        self.logical_operator = int(root.attrib["LogicalOperator"])
        self.auto_update = int(root.attrib["AutomaticUpdate"])
        self.conditions = conditions

    def to_xml(self) -> str:
        """Convert the smart playlist conditions to XML."""
        attrib = {
            "Id": str(self.playlist_id),
            "LogicalOperator": str(self.logical_operator),
            "AutomaticUpdate": str(self.auto_update),
        }
        root = xml.Element("NODE", attrib=attrib)
        for cond in self.conditions:
            attrib = {
                "PropertyName": str(cond.property),
                "Operator": str(cond.operator),
                "ValueUnit": str(cond.unit),
                "ValueLeft": str(cond.value_left),
                "ValueRight": str(cond.value_right),
            }
            xml.SubElement(root, "CONDITION", attrib=attrib)
        return xml.tostring(root).decode("utf-8").replace(" /", "/")

    def add_condition(
        self,
        prop: str,
        operator: int,
        value_left: str,
        value_right: str = "",
        unit: str = "",
    ) -> None:
        """Add a condition to the smart playlist.

        Parameters
        ----------
        prop : str
            The property to filter on.
        operator : {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11} int
            The operator to use. Must be in the range of 1-11
        value_left : str
            The left value to use.
        value_right : str, optional
            The right value to use, by default "".
        unit : str, optional
            The unit to use, by default "".
        """
        cond = Condition(prop, operator, unit, value_left, value_right)
        self.conditions.append(cond)

    def filter_clause(self, db) -> BooleanClauseList:
        """Return a SQLAlchemy filter clause matching the content of the smart playlist.

        Parameters
        ----------
        db : Rekorbox6Database
            The database instance. This is required for chained conditions (like MyTag).

        Returns
        -------
        BooleanClauseList
            A filter list macthing the contents of the smart playlist.
        """
        logical_op = and_ if self.logical_operator == LogicalOperator.ALL else or_

        comps = list()
        for cond in self.conditions:
            colum_name = PROPERTY_MAP[cond.property]
            val_left, val_right = _get_condition_values(cond)

            if colum_name == "MyTag":
                # MyTag is a special case, as it requires a subquery to get
                # the MyTagID from the MyTag name, and then another subquery
                # to get the ContentID from the MyTagID.
                sub_query = db.query(DjmdMyTag.ID).filter(DjmdMyTag.Name == val_left)
                sub_query = db.query(DjmdSongMyTag.ContentID).filter(
                    DjmdSongMyTag.MyTagID.in_(select(sub_query.scalar_subquery()))
                )
                if cond.operator == Operator.CONTAINS:
                    comp = DjmdContent.ID.in_(select(sub_query.subquery()))

                elif cond.operator == Operator.NOT_CONTAINS:
                    comp = DjmdContent.ID.notin_(select(sub_query.subquery()))

                else:
                    raise ValueError(
                        f"Operator '{cond.operator}' is not supported for MyTag"
                    )

            else:
                if cond.operator == Operator.EQUAL:
                    comp = getattr(DjmdContent, colum_name) == val_left

                elif cond.operator == Operator.NOT_EQUAL:
                    comp = getattr(DjmdContent, colum_name) != val_left

                elif cond.operator == Operator.GREATER:
                    comp = getattr(DjmdContent, colum_name) > val_left

                elif cond.operator == Operator.LESS:
                    comp = getattr(DjmdContent, colum_name) < val_left

                elif cond.operator == Operator.IN_RANGE:
                    comp = getattr(DjmdContent, colum_name).between(val_left, val_right)

                elif cond.operator == Operator.CONTAINS:
                    comp = getattr(DjmdContent, colum_name).contains(val_left)

                elif cond.operator == Operator.NOT_CONTAINS:
                    comp = not_(getattr(DjmdContent, colum_name).contains(val_left))

                elif cond.operator == Operator.STARTS_WITH:
                    comp = getattr(DjmdContent, colum_name).startswith(val_left)

                elif cond.operator == Operator.ENDS_WITH:
                    comp = getattr(DjmdContent, colum_name).endswith(val_left)

                elif cond.operator == Operator.IN_LAST:
                    now = datetime.now()
                    if cond.unit == "day":
                        t0 = now - relativedelta(days=val_left)
                        comp = getattr(DjmdContent, colum_name) > t0
                    elif cond.unit == "month":
                        t0 = now - relativedelta(months=val_left)
                        comp = getattr(DjmdContent, colum_name).month > t0
                    else:
                        raise ValueError(f"Unknown unit '{cond.unit}'")

                elif cond.operator == Operator.NOT_IN_LAST:
                    now = datetime.now()
                    if cond.unit == "day":
                        t0 = now - relativedelta(days=val_left)
                        comp = getattr(DjmdContent, colum_name) < t0
                    elif cond.unit == "month":
                        t0 = now - relativedelta(months=val_left)
                        comp = getattr(DjmdContent, colum_name).month < t0
                    else:
                        raise ValueError(f"Unknown unit '{cond.unit}'")

                else:
                    raise ValueError(f"Unknown operator '{cond.operator}'")

            comps.append(comp)
        return logical_op(*comps)
