from abc import ABC, abstractmethod

from aceaccount.core.model_account_object_sql_entities import AccountObjectType

class AccountObject(ABC):
    def __init__(self, name: str, object_type: AccountObjectType):
        self.name = name
        self.object_type = object_type

    @abstractmethod
    def __str__(self):
        pass

    @property
    def id(self):
        return f"{str(self.object_type)} {self.name.upper()}"

    @property
    def name(self):
        return self._name.replace('"', "").upper()

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def full_name(self):
        return f"{self.name}"

    @property
    def object_type(self):
        return self._object_type

    @object_type.setter
    def object_type(self, value):
        if not isinstance(value, AccountObjectType):
            raise TypeError("Incorrect datatype. Allowed: AccountObjectType")
        self._object_type = value

    def compare_full_name(self, full_name_to_compare):
        """
        Test if name_to_compare matches the full name of this AccountObject.

        Returns true if full names match, else false.
        Ignores double quotes around the names.
        """
        return self.full_name == full_name_to_compare.upper().replace('"', "")

    def compare_id(self, id_to_compare):
        """
        Test if id_to_compare matches the id of this AccountObject.

        Returns true if names match, else false.
        Ignores double quotes around the names.
        """
        return self.id == id_to_compare.replace('"', "")
