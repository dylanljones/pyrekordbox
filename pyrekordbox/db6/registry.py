# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-08-07

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterator, List, Tuple, Type

from sqlalchemy.orm.exc import ObjectDeletedError

if TYPE_CHECKING:
    from .database import Rekordbox6Database
    from .tables import AgentRegistry


Instances = Any
RegistryUpdateItem = Tuple[Instances, str, str, Any]

logger = logging.getLogger(__name__)


class RekordboxAgentRegistry:
    """Rekordbox Agent Registry handler.

    The Rekordbox Agent Registry handler is responsible for tracking changes to the
    Rekordbox database. It is used to keep track of changes to the database,
    provide a history of changes and to update the global and individual
    USN (unique sequence number) values of the database entries.

    This object should *not* be instantiated directly. It is used by the
    :class:`RekordboxDatabase` class to track changes to the database.

    Parameters
    ----------
    db : RekordboxDatabase
        The Rekordbox database instance.
    """

    __update_sequence__: List[RegistryUpdateItem] = list()
    __update_history__: List[RegistryUpdateItem] = list()
    __enabled__ = True

    def __init__(self, db: "Rekordbox6Database") -> None:
        self.db = db

    @classmethod
    def on_update(cls, instance: Instances, key: str, value: Any) -> None:
        """Called when an instance of a database model is updated.

        Parameters
        ----------
        instance : tables.Base
            The table entry instance.
        key : str
            The name of the updated column.
        value : Any
            The new value of the updated column.
        """
        if cls.__enabled__:
            logger.debug("On update: %s, %s, %s", instance, key, value)
            cls.__update_sequence__.append((instance, "update", key, value))

    @classmethod
    def on_create(cls, instance: Instances) -> None:
        """Called when an instance of a database model is created.

        Parameters
        ----------
        instance : tables.Base
            The table entry instance.
        """
        if cls.__enabled__:
            logger.debug("On create: %s", instance)
            cls.__update_sequence__.append((instance, "create", "", ""))

    @classmethod
    def on_delete(cls, instance: Instances) -> None:
        """Called when an instance of a database model is deleted.

        Parameters
        ----------
        instance : tables.Base
            The table entry instance.
        """
        if cls.__enabled__:
            try:
                s = str(instance)
                logger.debug("On delete: %s", s)
            except ObjectDeletedError:
                instance = []

            cls.__update_sequence__.append((instance, "delete", "", ""))

    @classmethod
    def on_move(cls, instances: Instances) -> None:
        """Called when instanced of a database model are moved.

        Parameters
        ----------
        instances : list[tables.Base]
            The table entry instance.
        """
        if cls.__enabled__:
            logger.debug("On move: %s", instances)
            cls.__update_sequence__.append((instances, "move", "", ""))

    @classmethod
    def clear_buffer(cls) -> None:
        """Clears the update buffer and update history."""
        cls.__update_history__.extend(cls.__update_sequence__)
        cls.__update_sequence__.clear()

    @classmethod
    def enable_tracking(cls) -> None:
        """Enables the tracking of database changes."""
        cls.__enabled__ = True

    @classmethod
    def disable_tracking(cls) -> None:
        """Disables the tracking of database changes."""
        cls.__enabled__ = False

    @classmethod
    @contextmanager
    def disabled(cls) -> Iterator[Type["RekordboxAgentRegistry"]]:
        """Context manager to temporarily disable the tracking of database changes.

        Examples
        --------
        >>> registry = RekordboxAgentRegistry(db)  # noqa
        >>> registry.__enabled__
        True

        >>> with registry.disabled():
        ...     print(registry.__enabled__)
        False
        """
        enabled = cls.__enabled__
        cls.disable_tracking()
        yield cls
        if enabled:
            cls.enable_tracking()

    def get_registries(self) -> Any:
        """Returns all agent registries.

        Returns
        -------
        registries : list[tables.AgentRegistry]
        """
        return self.db.get_agent_registry()

    def get_registry(self, key: str) -> Any:
        """Returns the agent registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).

        Returns
        -------
        registry : tables.AgentRegistry
        """
        return self.db.get_agent_registry(registry_id=key)

    def get_string(self, key: str) -> str:
        """Returns the string value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).

        Returns
        -------
        value : str
        """
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id=key)
        return reg.str_1

    def get_text(self, key: str) -> str:
        """Returns the text value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).

        Returns
        -------
        value : str
        """
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id=key)
        return reg.text_1

    def get_int(self, key: str) -> int:
        """Returns the integer value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).

        Returns
        -------
        value : int
        """
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id=key)
        return reg.int_1

    def get_date(self, key: str) -> datetime:
        """Returns the date value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).

        Returns
        -------
        value : datetime.datetime
        """
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id=key)
        return reg.date_1

    def set_string(self, key: str, value: str) -> None:
        """Sets the string value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).
        value : str
            The new value.
        """
        self.db.get_agent_registry(registry_id=key).str_1 = value

    def set_text(self, key: str, value: str) -> None:
        """Sets the text value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).
        value : str
            The new value.
        """
        self.db.get_agent_registry(registry_id=key).text_1 = value

    def set_int(self, key: str, value: int) -> None:
        """Sets the integer value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).
        value : int
            The new value.
        """
        self.db.get_agent_registry(registry_id=key).int_1 = value

    def set_date(self, key: str, value: datetime) -> None:
        """Sets the date value of the registry with the given key.

        Parameters
        ----------
        key : str
            The registry identifier (`registry_id`).
        value : datetime.datetime
            The new value.
        """
        self.db.get_agent_registry(registry_id=key).date_1 = value

    def get_local_update_count(self) -> int:
        """Returns the current global local USN (unique sequence number)."""
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id="localUpdateCount")
        return reg.int_1

    def set_local_update_count(self, value: int) -> None:
        """Sets the global local USN (unique sequence number).

        Parameters
        ----------
        value : int
            The new USN value.
        """
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id="localUpdateCount")
        reg.int_1 = value

    def increment_local_update_count(self, num: int = 1) -> int:
        """Increments the global local USN (unique sequence number) by the given number.

        Parameters
        ----------
        num : int, optional
            The number to increment the USN by. The default is 1.

        Returns
        -------
        usn: int
            The new global local USN.
        """
        if not isinstance(num, int) or num < 1:
            raise ValueError("The USN can only be increment by a positive integer!")
        reg: "AgentRegistry" = self.db.get_agent_registry(registry_id="localUpdateCount")
        reg.int_1 = reg.int_1 + num
        return reg.int_1

    def autoincrement_local_update_count(self, set_row_usn: bool = True) -> int:
        """Auto-increments the global local USN (unique sequence number).

        The number of changes in the update buffer is used to determine the
        number to increment the USN by. After the update the buffer is cleared.

        Parameters
        ----------
        set_row_usn : bool, optional
            If True the local USN of each database entry is updated with the
            corresponding value in the order the changes were made.

        Returns
        -------
        usn: int
            The new global local USN.
        """
        reg = self.db.get_agent_registry(registry_id="localUpdateCount")
        usn: int = reg.int_1
        self.disable_tracking()
        self.db.flush()
        with self.db.no_autoflush:
            for instances, op, _, _ in self.__update_sequence__.copy():
                usn += 1
                if set_row_usn:
                    # All instances in a list get the same USN
                    if not isinstance(instances, list):
                        instances = [instances]
                    for instance in instances:
                        if hasattr(instance, "rb_local_usn"):
                            instance.rb_local_usn = usn
            reg.int_1 = usn

        self.clear_buffer()
        self.db.flush()
        self.enable_tracking()
        return usn
