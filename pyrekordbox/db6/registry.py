# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones


class RekordboxAgentRegistry:

    __update_sequence__ = list()
    __update_history__ = list()
    __enabled__ = True

    def __init__(self, db):
        self.db = db

    @classmethod
    def on_update(cls, instance, key, value):
        if cls.__enabled__:
            cls.__update_sequence__.append((instance, "update", key, value))

    @classmethod
    def on_create(cls, instance):
        if cls.__enabled__:
            cls.__update_sequence__.append((instance, "create", "", ""))

    @classmethod
    def on_delete(cls, instance):
        if cls.__enabled__:
            cls.__update_sequence__.append((instance, "delete", "", ""))

    @classmethod
    def clear_buffer(cls):
        cls.__update_history__.extend(cls.__update_sequence__)
        cls.__update_sequence__.clear()

    @classmethod
    def enable_tracking(cls):
        cls.__enabled__ = True

    @classmethod
    def disable_tracking(cls):
        cls.__enabled__ = False

    def get_registries(self):
        return self.db.get_agent_registry()

    def get_registry(self, key):
        return self.db.get_agent_registry(registry_id=key)

    def get_string(self, key):
        return self.db.get_agent_registry(registry_id=key).str_1

    def get_text(self, key):
        return self.db.get_agent_registry(registry_id=key).text_1

    def get_int(self, key):
        return self.db.get_agent_registry(registry_id=key).int_1

    def get_date(self, key, value):
        self.db.get_agent_registry(registry_id=key).date_1 = value

    def set_string(self, key, value):
        self.db.get_agent_registry(registry_id=key).str_1 = value

    def set_text(self, key, value):
        self.db.get_agent_registry(registry_id=key).text_1 = value

    def set_int(self, key, value):
        self.db.get_agent_registry(registry_id=key).int_1 = value

    def set_date(self, key, value):
        self.db.get_agent_registry(registry_id=key).date_1 = value

    def get_local_update_count(self):
        reg = self.db.get_agent_registry(registry_id="localUpdateCount")
        return reg.int_1

    def set_local_update_count(self, value):
        reg = self.db.get_agent_registry(registry_id="localUpdateCount")
        reg.int_1 = value

    def increment_local_update_count(self, num=1):
        if not isinstance(num, int) or num < 1:
            raise ValueError("The USN can only be increment by a positive integer!")
        reg = self.db.get_agent_registry(registry_id="localUpdateCount")
        reg.int_1 = reg.int_1 + num
        return reg.int_1

    def autoincrement_local_update_count(self, set_row_usn=True):
        reg = self.db.get_agent_registry(registry_id="localUpdateCount")
        usn = reg.int_1

        with self.db.session.no_autoflush:
            for instance, op, _, _ in self.__update_sequence__.copy():
                usn += 1
                if set_row_usn and op != "delete" and hasattr(instance, "rb_local_usn"):
                    instance.rb_local_usn = usn
            reg.int_1 = usn

        self.clear_buffer()

        return usn
