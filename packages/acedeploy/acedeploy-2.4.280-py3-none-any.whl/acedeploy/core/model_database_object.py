from abc import ABC, abstractmethod

from acedeploy.core.model_sql_entities import DbObjectType


class DatabaseObject(ABC):
    def __init__(self, schema: str, name: str, object_type: DbObjectType):
        self.schema = schema
        self.name = name
        self.object_type = object_type

    @abstractmethod
    def __str__(self):
        pass

    @property
    def id(self):
        return f"{str(self.object_type)} {self.schema.upper()}.{self.name.upper()}"

    @property
    def schema(self):
        return self._schema.replace('"', "").upper()

    @schema.setter
    def schema(self, value):
        self._schema = value

    @property
    def name(self):
        return self._name.replace('"', "").upper()

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def full_name(self):
        return f"{self.schema}.{self.name}"

    @property
    def object_type(self):
        return self._object_type

    @object_type.setter
    def object_type(self, value):
        if not isinstance(value, DbObjectType):
            raise TypeError("Incorrect datatype. Allowed: DbObjectType")
        self._object_type = value

    def compare_full_name(self, full_name_to_compare):
        """
        Test if name_to_compare matches the full name of this DatabaseObject.

        Returns true if full names match, else false.
        Ignores double quotes around the names.
        """
        return self.full_name == full_name_to_compare.upper().replace('"', "")

    def compare_id(self, id_to_compare):
        """
        Test if id_to_compare matches the id of this DatabaseObject.

        Returns true if names match, else false.
        Ignores double quotes around the names.
        """
        return self.id == id_to_compare.replace('"', "")
