from enum import Enum


class DbActionType(Enum):
    """
    Enum for valid database operations
    """

    ALTER = "ALTER"
    DROP = "DROP"
    ADD = "ADD"
    DROPOVERLOADED = "DROPOVERLOADED"


class DbObjectType(Enum):
    """
    Enum for valid database objects
    """

    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    EXTERNALTABLE = "EXTERNALTABLE"
    VIEW = "VIEW"
    MATERIALIZEDVIEW = "MATERIALIZEDVIEW"
    FUNCTION = "FUNCTION"
    PROCEDURE = "PROCEDURE"
    STAGE = "STAGE"
    FILEFORMAT = "FILEFORMAT"
    STREAM = "STREAM"
    TASK = "TASK"
    PIPE = "PIPE"
    SEQUENCE = "SEQUENCE"
    MASKINGPOLICY = "MASKINGPOLICY"
    ROWACCESSPOLICY = "ROWACCESSPOLICY"
    DYNAMICTABLE = "DYNAMICTABLE"
    NETWORKRULE = "NETWORKRULE"
    TAG = "TAG"

    @staticmethod
    def get_sql_object_type(db_object) -> str:
        """
        Get SQL identifier for DbObjectType.
        Example: get_sql_object_type(DbObjectType.MATERIALIZEDVIEW) returns "MATERIALIZED VIEW"
        """
        if db_object == DbObjectType.SCHEMA:
            return "SCHEMA"
        if db_object == DbObjectType.TABLE:
            return "TABLE"
        if db_object == DbObjectType.EXTERNALTABLE:
            return "EXTERNAL TABLE"
        if db_object == DbObjectType.VIEW:
            return "VIEW"
        if db_object == DbObjectType.MATERIALIZEDVIEW:
            return "MATERIALIZED VIEW"
        if db_object == DbObjectType.FUNCTION:
            return "FUNCTION"
        if db_object == DbObjectType.PROCEDURE:
            return "PROCEDURE"
        if db_object == DbObjectType.STAGE:
            return "STAGE"
        if db_object == DbObjectType.FILEFORMAT:
            return "FILE FORMAT"
        if db_object == DbObjectType.STREAM:
            return "STREAM"
        if db_object == DbObjectType.TASK:
            return "TASK"
        if db_object == DbObjectType.PIPE:
            return "PIPE"
        if db_object == DbObjectType.SEQUENCE:
            return "SEQUENCE"
        if db_object == DbObjectType.MASKINGPOLICY:
            return "MASKING POLICY"
        if db_object == DbObjectType.ROWACCESSPOLICY:
            return "ROW ACCESS POLICY"
        if db_object == DbObjectType.DYNAMICTABLE:
            return "DYNAMIC TABLE"
        if db_object == DbObjectType.NETWORKRULE:
            return "NETWORK RULE"
        if db_object == DbObjectType.TAG:
            return "TAG"
        else:
            raise ValueError("Given DbObjectType not recognized.")

    @staticmethod
    def get_object_type_for_show(db_object) -> str:
        """
        Get SQL text identifier for use in SHOW commands. https://docs.snowflake.com/en/sql-reference/sql/show.html
        Example: get_object_type_for_show(DbObjectType.MATERIALIZEDVIEW) returns "MATERIALIZED VIEWS"
        """
        if db_object == DbObjectType.SCHEMA:
            return "SCHEMAS"
        if db_object == DbObjectType.TABLE:
            return "TABLES"
        if db_object == DbObjectType.EXTERNALTABLE:
            return "EXTERNAL TABLES"
        if db_object == DbObjectType.VIEW:
            return "VIEWS"
        if db_object == DbObjectType.MATERIALIZEDVIEW:
            return "MATERIALIZED VIEWS"
        if db_object == DbObjectType.FUNCTION:
            return "FUNCTIONS"
        if db_object == DbObjectType.PROCEDURE:
            return "PROCEDURES"
        if db_object == DbObjectType.STAGE:
            return "STAGES"
        if db_object == DbObjectType.FILEFORMAT:
            return "FILE FORMATS"
        if db_object == DbObjectType.STREAM:
            return "STREAMS"
        if db_object == DbObjectType.TASK:
            return "TASKS"
        if db_object == DbObjectType.PIPE:
            return "PIPES"
        if db_object == DbObjectType.SEQUENCE:
            return "SEQUENCES"
        if db_object == DbObjectType.MASKINGPOLICY:
            return "MASKING POLICIES"
        if db_object == DbObjectType.ROWACCESSPOLICY:
            return "ROW ACCESS POLICIES"
        if db_object == DbObjectType.DYNAMICTABLE:
            return "DYNAMIC TABLES"
        if db_object == DbObjectType.NETWORKRULE:
            return "NETWORK RULES"
        if db_object == DbObjectType.TAG:
            return "TAGS"
        else:
            raise ValueError("Given DbObjectType not recognized.")

    @staticmethod
    def get_object_type_for_get_ddl(db_object) -> str:
        """
        Get SQL text identifier for use in GET_DDL(). https://docs.snowflake.com/en/sql-reference/functions/get_ddl.html
        Example: get_object_type_for_get_ddl(DbObjectType.MATERIALIZEDVIEW) returns "VIEW"
        """
        if db_object == DbObjectType.SCHEMA:
            return "SCHEMA"
        if db_object == DbObjectType.TABLE:
            return "TABLE"
        if db_object == DbObjectType.EXTERNALTABLE:
            return "TABLE"
        if db_object == DbObjectType.VIEW:
            return "VIEW"
        if db_object == DbObjectType.MATERIALIZEDVIEW:
            return "VIEW"
        if db_object == DbObjectType.FUNCTION:
            return "FUNCTION"
        if db_object == DbObjectType.PROCEDURE:
            return "PROCEDURE"
        if db_object == DbObjectType.STAGE:
            raise ValueError("Object of type STAGE cannot be used in GET_DDL()")
        if db_object == DbObjectType.FILEFORMAT:
            return "FILE_FORMAT"
        if db_object == DbObjectType.STREAM:
            return "STREAM"
        if db_object == DbObjectType.TASK:
            return "TASK"
        if db_object == DbObjectType.PIPE:
            return "PIPE"
        if db_object == DbObjectType.SEQUENCE:
            return "SEQUENCE"
        if db_object == DbObjectType.MASKINGPOLICY:
            return "POLICY"
        if db_object == DbObjectType.ROWACCESSPOLICY:
            return "POLICY"
        if db_object == DbObjectType.DYNAMICTABLE:
            return "TABLE"
        if db_object == DbObjectType.NETWORKRULE:
            raise ValueError("Object of type NETWORK_RULE cannot be used in GET_DDL()")
        if db_object == DbObjectType.TAG:
            return "TAG"
        else:
            raise ValueError("Given DbObjectType not recognized.")
        
    @staticmethod
    def get_object_domain_from_object_type_for_tag_references(object_type) -> str:
        """
        Get Snowflake object domain by object type.
        """
        mapping_object_type_object_domain = {
            DbObjectType.TABLE: "TABLE",
            DbObjectType.VIEW: "TABLE",
            DbObjectType.MATERIALIZEDVIEW: "TABLE",
            DbObjectType.EXTERNALTABLE: "TABLE",
            DbObjectType.DYNAMICTABLE: "TABLE"
        }

        object_domain = mapping_object_type_object_domain[object_type]

        return object_domain
    
    @staticmethod
    def get_object_domain_from_object_type_for_alter_tags(object_type) -> str:
        """
        Get Snowflake object domain by object type.
        """
        mapping_object_type_object_domain = {
            DbObjectType.TABLE: "TABLE",
            DbObjectType.VIEW: "VIEW",
            DbObjectType.MATERIALIZEDVIEW: "VIEW",
            DbObjectType.EXTERNALTABLE: "EXTERNAL TABLE",
            DbObjectType.DYNAMICTABLE: "DYNAMIC TABLE"
        }

        object_domain = mapping_object_type_object_domain[object_type]

        return object_domain
    
    @staticmethod
    def get_object_type_for_policy_references(ref_entity_domain: str) -> 'DbObjectType':
        """
        Get Snowflake object type by string.
        """
        mapping = {
            "TABLE": DbObjectType.TABLE,
            "VIEW": DbObjectType.VIEW,
        }
        return mapping[ref_entity_domain]


class DbFunctionType(Enum):
    """
    Enum for valid function types
    """

    SQL = "SQL"
    JAVASCRIPT = "JAVASCRIPT"


class PolicyType(Enum):
    """
    Valid policy types
    """

    ROWACCESS = "ROWACCESS"
    MASKING = "MASKING"
