# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-12-13

import logging
import xml.etree.cElementTree as xml
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, Tuple, Union

from dateutil.relativedelta import relativedelta  # noqa
from sqlalchemy import and_, not_, or_
from sqlalchemy.sql.elements import ColumnElement

from .tables import DjmdContent

logger = logging.getLogger(__name__)

__all__ = [
    "LogicalOperator",
    "Property",
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


class Property(str, Enum):
    ARTIST = "artist"
    ALBUM = "album"
    ALBUM_ARTIST = "albumArtist"
    ORIGINAL_ARTIST = "originalArtist"
    BPM = "bpm"
    GROUPING = "grouping"
    COMMENTS = "comments"
    PRODUCER = "producer"
    STOCK_DATE = "stockDate"
    DATE_CREATED = "dateCreated"
    COUNTER = "counter"
    FILENAME = "fileName"
    GENRE = "genre"
    KEY = "key"
    LABEL = "label"
    MIX_NAME = "mixName"
    MYTAG = "myTag"
    RATING = "rating"
    DATE_RELEASED = "dateReleased"
    REMIXED_BY = "remixedBy"
    DURATION = "duration"
    NAME = "name"
    YEAR = "year"


_STR_OPS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.CONTAINS,
    Operator.NOT_CONTAINS,
    Operator.STARTS_WITH,
    Operator.ENDS_WITH,
]

_NUM_OPS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.GREATER,
    Operator.LESS,
    Operator.IN_RANGE,
]

_DATE_OPS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.GREATER,
    Operator.LESS,
    Operator.IN_RANGE,
    Operator.IN_LAST,
    Operator.NOT_IN_LAST,
]

# Defines the valid operators for each property
VALID_OPS: Dict[str, Any] = {
    Property.ARTIST: _STR_OPS,
    Property.ALBUM: _STR_OPS,
    Property.ALBUM_ARTIST: _STR_OPS,
    Property.ORIGINAL_ARTIST: _STR_OPS,
    Property.BPM: _NUM_OPS,
    Property.GROUPING: [Operator.EQUAL, Operator.NOT_EQUAL],
    Property.COMMENTS: _STR_OPS,
    Property.PRODUCER: _STR_OPS,
    Property.STOCK_DATE: _DATE_OPS,
    Property.DATE_CREATED: _DATE_OPS,
    Property.COUNTER: _NUM_OPS,
    Property.FILENAME: _STR_OPS,
    Property.GENRE: _STR_OPS,
    Property.KEY: _STR_OPS,
    Property.LABEL: _STR_OPS,
    Property.MIX_NAME: _STR_OPS,
    Property.MYTAG: [Operator.CONTAINS, Operator.NOT_CONTAINS],
    Property.RATING: _NUM_OPS,
    Property.DATE_RELEASED: _DATE_OPS,
    Property.REMIXED_BY: _STR_OPS,
    Property.DURATION: _NUM_OPS,
    Property.NAME: _STR_OPS,
    Property.YEAR: _NUM_OPS,
}

# Defines the column names in the DB for properties that are directly mapped
PROPERTY_COLUMN_MAP: Dict[str, str] = {
    Property.ARTIST: "ArtistName",
    Property.ALBUM: "AlbumName",
    Property.ALBUM_ARTIST: "AlbumArtistName",
    Property.ORIGINAL_ARTIST: "OrgArtistName",
    Property.BPM: "BPM",
    Property.GROUPING: "ColorID",
    Property.COMMENTS: "Commnt",
    Property.PRODUCER: "ComposerName",
    Property.STOCK_DATE: "StockDate",
    Property.DATE_CREATED: "created_at",
    Property.COUNTER: "DJPlayCount",
    Property.FILENAME: "FileNameL",
    Property.GENRE: "GenreName",
    Property.KEY: "KeyName",
    Property.LABEL: "LabelName",
    # Property.MIX_NAME don't know what this maps to
    Property.MYTAG: "MyTagIDs",
    Property.RATING: "Rating",
    Property.DATE_RELEASED: "ReleaseDate",
    Property.REMIXED_BY: "RemixerName",
    Property.DURATION: "Length",
    Property.NAME: "Title",
    Property.YEAR: "ReleaseYear",
}

TYPE_CONVERSION: Dict[str, Any] = {
    Property.BPM: int,
    Property.STOCK_DATE: lambda x: datetime.strptime(x, "%Y-%m-%d"),
    Property.DATE_CREATED: lambda x: datetime.strptime(x, "%Y-%m-%d"),
    Property.COUNTER: int,
    Property.RATING: int,
    Property.DATE_RELEASED: lambda x: datetime.strptime(x, "%Y-%m-%d"),
    Property.DURATION: int,
    Property.YEAR: int,
}

PROPERTIES = [str(p.value) for p in list(Property)]  # noqa


@dataclass
class Condition:
    """Dataclass for a smart playlist condition."""

    property: str
    operator: int
    unit: str
    value_left: Union[str, int]
    value_right: Union[str, int]

    def __post_init__(self) -> None:
        if self.property not in PROPERTIES:
            raise ValueError(
                f"Invalid property: '{self.property}'! Supported properties: {PROPERTIES}"
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


def left_bitshift(x: int, nbit: int = 32) -> int:
    """Left shifts an N bit integer with sign change."""
    return int(x - 2**nbit)


def right_bitshift(x: int, nbit: int = 32) -> int:
    """Right shifts an N bit integer with sign change."""
    return int(x + 2**nbit)


def _get_condition_values(cond: Condition) -> Tuple[Any, Any]:
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

    if val_left == "":
        val_left = None  # type: ignore

    return val_left, val_right


class SmartList:
    """Rekordbox smart playlist XML handler."""

    def __init__(self, logical_operator: int = LogicalOperator.ALL, auto_update: int = 0):
        self.playlist_id: Union[int, str] = ""
        self.logical_operator: int = int(logical_operator)
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

        self.playlist_id = str(right_bitshift(int(root.attrib["Id"])))
        self.logical_operator = int(root.attrib["LogicalOperator"])
        self.auto_update = int(root.attrib["AutomaticUpdate"])
        self.conditions = conditions

    def to_xml(self) -> str:
        """Convert the smart playlist conditions to XML."""
        attrib = {
            "Id": str(left_bitshift(int(self.playlist_id))),
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
        if isinstance(prop, Property):
            prop = str(prop.value)
        cond = Condition(prop, int(operator), unit, value_left, value_right)
        self.conditions.append(cond)

    def filter_clause(self) -> ColumnElement[bool]:
        """Return a SQLAlchemy filter clause matching the content of the smart playlist.

        Returns
        -------
        ColumnElement[bool]
            A filter list macthing the contents of the smart playlist.
        """
        logical_op = and_ if self.logical_operator == LogicalOperator.ALL else or_

        comps = list()
        for cond in self.conditions:
            val_left, val_right = _get_condition_values(cond)
            # val_left = str(-abs(int(val_left))) if val_left is not None else ""
            if cond.property in PROPERTY_COLUMN_MAP:
                colum_name = PROPERTY_COLUMN_MAP[cond.property]
                if cond.property == Property.MYTAG:
                    if int(val_left) < 0:
                        val_left = str(right_bitshift(int(val_left)))

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

            else:
                logger.warning(f"Unsupported property '{cond.property}'")

        return logical_op(*comps)
