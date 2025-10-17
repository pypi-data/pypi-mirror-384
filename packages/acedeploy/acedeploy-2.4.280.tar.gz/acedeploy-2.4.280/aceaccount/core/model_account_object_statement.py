from aceaccount.core.model_account_object import AccountObject
from aceaccount.core.model_account_object_sql_entities import AccountObjectType

class AccountObjectStatement(AccountObject):
    """
    Models atomic sql statement execution
    With target object name and sql statement to execute
    """

    def __init__(self, name: str, statement: str, object_type: AccountObjectType):
        super().__init__(name=name, object_type=object_type)
        self.statement = statement

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.statement == other.statement
            and self.object_type == other.object_type
        )

    def __str__(self):
        return f"AccountObjectStatement: {self.id}"

    def __repr__(self):
        return f"AccountObjectStatement: {self.id}"