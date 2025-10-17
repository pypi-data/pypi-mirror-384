from typing import List

from acedeploy.core.model_database_object import DatabaseObject
from acedeploy.core.model_sql_entities import DbObjectType


class DbStatement(DatabaseObject):
    """
    Models atomic sql statement execution
    With target object name and sql statement to execute
    """

    def __init__(
        self, name: str, schema: str, statement: str, object_type: DbObjectType
    ):
        super().__init__(schema=schema, name=name, object_type=object_type)
        self.statement = statement

    def __eq__(self, other):
        return (
            self.schema == other.schema
            and self.name == other.name
            and self.statement == other.statement
            and self.object_type == other.object_type
        )

    def __str__(self):
        return f"DbStatement: {self.id}"

    def __repr__(self):
        return f"DbStatement: {self.id}"


class ParametersObjectStatement(DbStatement):
    """
    DbStatements for objects with parameters
    """

    def __init__(
        self,
        name: str,
        schema: str,
        statement: str,
        object_type: DbObjectType,
        parameters: List[str],
    ):
        super().__init__(
            name=name, schema=schema, statement=statement, object_type=object_type
        )
        self.parameters = parameters

    @property
    def id(self):
        return f"{super().id} {self.parameters_string.upper()}"

    @property
    def full_name(self):
        return f"{super().full_name} {self.parameters_string.upper()}"

    @property
    def parameters_string(self):
        return f"({', '.join([s for s in self.parameters])})"

    def __str__(self):
        return f"ParametersObjectStatement: {self.id}"

    def __repr__(self):
        return f"ParametersObjectStatement: {self.id}"
