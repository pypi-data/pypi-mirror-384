import logging
import os
import re
from typing import Dict, List, Tuple

import git

import aceutils.file_util as file_util
import aceutils.misc_utils as misc_utils
import aceutils.string_util as string_util
from acedeploy.core.model_database_object import DatabaseObject
from acedeploy.core.model_sql_entities import DbFunctionType, DbObjectType
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class SolutionObject(DatabaseObject):
    """
    Abstract class for solution objects (i.e. files in the solution root directory)
    """

    def __init__(
        self,
        schema,
        name,
        path: str,
        content: str,
        object_type: DbObjectType,
        git_change_type: git.DiffIndex.change_type = None,
    ):
        self.path = path
        self.git_change_type = git_change_type
        self.content = content
        super().__init__(schema, name, object_type)

    @staticmethod
    def factory(
        filepath: str,
        git_change_type: git.DiffIndex.change_type = None,
        string_replace_dict: Dict[str, str] = None,
    ) -> "SolutionObject":
        object_list = [
            SolutionSchema,
            SolutionTable,
            SolutionExternalTable,
            SolutionView,
            SolutionMaterializedView,
            SolutionFunction,
            SolutionProcedure,
            SolutionStage,
            SolutionFileformat,
            SolutionStream,
            SolutionTask,
            SolutionPipe,
            SolutionSequence,
            SolutionMaskingPolicy,
            SolutionRowAccessPolicy,
            SolutionDynamicTable,
            SolutionNetworkRule,
            SolutionTag,
        ]
        if string_replace_dict is None:
            string_replace_dict = {}
        content = SolutionObject._load_sql_file(filepath)
        content = string_util.string_replace_by_dict(content, string_replace_dict)
        for obj in object_list:
            schema, name = SolutionObject._regex_get_object_name(
                obj.pattern, string_util.remove_comment(content)
            )
            if (schema is not None) and (name is not None):
                log.debug(
                    f"MATCH file [ '{filepath}' ] as object TYPE [ '{obj.__name__}' ] with FULL NAME [ '{schema}.{name}' ]"
                )
                return obj(filepath, content, git_change_type)
        log.warning(f"COULD NOT DETERMINE TYPE FOR FILE [ '{filepath}' ]")

    @staticmethod
    def _regex_get_object_name(pattern: str, content: str) -> Tuple[str, str]:
        """
        Given a regex pattern, find the object name from the content.
        Return (None, None) if no match.
        Return ('<schema name>', '<object name>') if match.
        """
        m = re.match(pattern, content, re.I)
        if m:
            return m.group("schema"), m.group("name")
        else:
            return None, None

    @staticmethod
    def _get_full_name_from_filepath(filepath: str) -> str:
        """
        Return the name of an object based on the filename (can be path including folders):
            - <schema> for schemas.
            - <schema>.<object> for all other types.
        Returned value will be uppercase.
        """
        return os.path.basename(filepath).upper().replace(".SQL", "")

    @staticmethod
    def _get_object_name_from_name(name):
        """
        Get the object name of an object the complete name (<schema>.<object>).
        """
        split_name = name.split(".")
        if len(split_name) != 2:
            raise ValueError(
                f"Name [ '{name}' ] is not a valid object name with pattern [ 'schema_name.object_name' ]"
            )
        return split_name[1].strip()

    @staticmethod
    def _get_schema_name_from_name(name):
        """
        Get the schema name of an object the complete name (<schema>.<object>).
        """
        split_name = name.split(".")
        if len(split_name) != 2:
            raise ValueError(
                f"Name [ '{name}' ] is not a valid object name with pattern [ 'schema_name.object_name' ]"
            )
        return split_name[0].strip()

    @staticmethod
    def _load_sql_file(file_path: str, allow_multiple_statements: bool = False) -> str:
        """
        Load a sql file from a given file path.
        Optionally raise error if it contains multiple statements in a single file.
        """
        content = file_util.load(file_path)
        if (
            not allow_multiple_statements
        ) and SolutionObject._ddl_contains_multiple_statements(content):
            raise Exception(f"MULTIPLE STATEMENTS in file [ '{file_path}' ].")
        return string_util.remove_comment_after_statement(content)

    @staticmethod
    def _ddl_contains_multiple_statements(ddl: str) -> bool:
        """
        Test if the given string contains more than one statement, return true if more than one.
        """
        ddl_without_comments = string_util.remove_comment(ddl)
        ddl_without_quoted_values = re.sub(
            r"('.*?')|(`.*?`)|(\$\$.*?\$\$)", "", ddl_without_comments, 0, re.DOTALL
        )
        return (
            ddl_without_quoted_values.count(";") > 1
        )  # at this point, there should be only the closing semicolon in the ddl


class SolutionTable(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:TRANSIENT\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.TABLE, git_change_type
        )

    def __str__(self):
        return f"SolutionTable: {self.id}"

    def __repr__(self):
        return f"SolutionTable: {self.id}"


class SolutionExternalTable(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?EXTERNAL\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.EXTERNALTABLE, git_change_type
        )

    def __str__(self):
        return f"SolutionExternalTable: {self.id}"

    def __repr__(self):
        return f"SolutionExternalTable: {self.id}"


class SolutionView(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(?:RECURSIVE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.VIEW, git_change_type
        )

    def __str__(self):
        return f"SolutionView: {self.id}"

    def __repr__(self):
        return f"SolutionView: {self.id}"


class SolutionMaterializedView(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?MATERIALIZED\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.MATERIALIZEDVIEW, git_change_type
        )

    def __str__(self):
        return f"SolutionMaterializedView: {self.id}"

    def __repr__(self):
        return f"SolutionMaterializedView: {self.id}"


class SolutionStage(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?STAGE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.STAGE, git_change_type
        )

    def __str__(self):
        return f"SolutionStage: {self.id}"

    def __repr__(self):
        return f"SolutionStage: {self.id}"


class SolutionFileformat(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?FILE\s+FORMAT\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.FILEFORMAT, git_change_type
        )

    def __str__(self):
        return f"SolutionFileformat: {self.id}"

    def __repr__(self):
        return f"SolutionFileformat: {self.id}"


class SolutionStream(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?STREAM\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.STREAM, git_change_type
        )

    def __str__(self):
        return f"SolutionStream: {self.id}"

    def __repr__(self):
        return f"SolutionStream: {self.id}"


class SolutionTask(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?TASK\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.TASK, git_change_type
        )

    def __str__(self):
        return f"SolutionTask: {self.id}"

    def __repr__(self):
        return f"SolutionTask: {self.id}"


class SolutionPipe(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?PIPE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.PIPE, git_change_type
        )

    def __str__(self):
        return f"SolutionPipe: {self.id}"

    def __repr__(self):
        return f"SolutionPipe: {self.id}"


class SolutionSequence(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?SEQUENCE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.SEQUENCE, git_change_type
        )

    def __str__(self):
        return f"SolutionSequence: {self.id}"

    def __repr__(self):
        return f"SolutionSequence: {self.id}"


class SolutionMaskingPolicy(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?MASKING\s+POLICY\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.MASKINGPOLICY, git_change_type
        )

    def __str__(self):
        return f"SolutionMaskingPolicy: {self.id}"

    def __repr__(self):
        return f"SolutionMaskingPolicy: {self.id}"


class SolutionRowAccessPolicy(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?ROW\s+ACCESS\s+POLICY\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.ROWACCESSPOLICY, git_change_type
        )

    def __str__(self):
        return f"SolutionRowAccessPolicy: {self.id}"

    def __repr__(self):
        return f"SolutionRowAccessPolicy: {self.id}"

class SolutionDynamicTable(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?DYNAMIC\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.DYNAMICTABLE, git_change_type
        )

    def __str__(self):
        return f"SolutionDynamicTable: {self.id}"

    def __repr__(self):
        return f"SolutionDynamicTable: {self.id}"
    
class SolutionNetworkRule(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?NETWORK\s+RULE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.NETWORKRULE, git_change_type
        )

    def __str__(self):
        return f"SolutionNetworkRule: {self.id}"

    def __repr__(self):
        return f"SolutionNetworkRule: {self.id}"

class SolutionParametersObject(SolutionObject):
    def __init__(
        self,
        name,
        schema,
        path: str,
        content: str,
        object_type: DbObjectType,
        git_change_type: git.DiffIndex.change_type = None,
    ):
        super().__init__(name, schema, path, content, object_type, git_change_type)
        try:
            parameters = self._get_parameters_from_ddl(self.content)
        except Exception as err:
            raise Exception(
                f"Unable to parse parameters for file [ '{path}' ]. Check if parameter list is valid."
            ) from err
        self.parameters = [
            misc_utils.map_datatype_name_to_default(p) for p in parameters
        ]

    @staticmethod
    def _get_parameters_from_ddl(ddl: str) -> List[str]:
        """
            Get parameters from a function or procedure ddl.

            Limited support for default values.
                Allowed:
                    - insert_mode string default 'APPEND'
                    - truncate_stage boolean default false
                    - ts timestamp default current_timestamp()
                Not allowed:
                    - my_param string default substr(upper('my five is cool'), 4, 4))   --> default value with nested brackets not allowed
        Args:
            ddl: str - function or procedure ddl (can contain comments)
        Returns:
            string containing the parameter types to be used to reference the function or procedure
            Example:
                input: "CREATE OR REPLACE FUNCTION MYSCHEMA.MYFUNCTION (A VARCHAR, B INT, C INT)"
                output: ["VARCHAR", "INT", "INT")]
        """
        ddl_without_comment = string_util.remove_comment(ddl)
        ddl_without_type_sizes = re.sub(
            r"\(\s*\d+(\s*,\s*\d+)?\s*\)", "", ddl_without_comment
        )  # need to remove numbers from types to be able to get parameters list, e.g. VARCHAR(10) becomes VARCHAR; DECIMAL(38, 5) becomes DECIMAL
        result = re.search(
            r"CREATE\s*(?:OR\s+REPLACE)?\s*(?:PROCEDURE|FUNCTION)\s+\"?[a-z0-9_#$]+\"?\.\"?[a-z0-9_#$]+\"?\s*\((?P<parameters>(?:[^\(\)]|\(\))*)\)",
            ddl_without_type_sizes,
            re.IGNORECASE,
        )
        types = []
        parameters = result.group("parameters").strip().upper()
        if parameters == "":
            return []
        parameter_list = SolutionParametersObject._split_parameters(parameters)
        for parameter in parameter_list:
            types.append(
                re.search(
                    r"[\"a-z0-9_#$]+\s+(?P<type>[a-z0-9_#$]+)(?:\s+default\s+)?", parameter, re.IGNORECASE
                ).group("type")
            )
        return types

    @staticmethod
    def _split_parameters(parameters: str) -> List[str]:
        """
            Given a string of parameters, split into a list of parameters.

            This also supports parameters that contain commas as part of the default values, e.g.
            "PARAM1" VARCHAR DEFAULT \'BK_WHL_ITEM_NO\', "PARAM2" VARCHAR DEFAULT \'VAL1,VAL2,VAL3\'
        """
        return re.split(",(?=(?:[^']*'[^']*')*[^']*$)", parameters.replace(r"\'", ""), flags=re.DOTALL)

    @property
    def id(self):
        return f"{super().id} {self.parameters_string.upper()}"

    @property
    def full_name(self):
        return f"{super().full_name} {self.parameters_string.upper()}"

    @property
    def parameters_string(self):
        return f"({', '.join([s for s in self.parameters])})"

    @property
    def name_without_params(self):
        return super().full_name

    def compare_name_without_params(self, name_without_params_to_compare):
        """
        Test if name_without_params_to_compare matches the name_without_params of this DatabaseObject.

        Returns true if name_without_params match, else false.
        Ignores double quotes around the names.
        """
        return (
            self.name_without_params
            == name_without_params_to_compare.upper().replace('"', "")
        )


class SolutionFunction(SolutionParametersObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?FUNCTION\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.FUNCTION, git_change_type
        )

    def __str__(self):
        return f"SolutionFunction: {self.id}"

    def __repr__(self):
        return f"SolutionFunction: {self.id}"

    @property
    def function_type(self):
        return self.get_function_type(self.content)

    @staticmethod
    def get_function_type(statement: str) -> DbFunctionType:
        """
        Given a function DDL statement, return the function type.
        """
        statement = string_util.remove_comment(statement)
        if re.match(
            f"{SolutionFunction.pattern}.*\\s+LANGUAGE\\s+JAVASCRIPT\\s+.*AS",
            statement,
            re.IGNORECASE | re.DOTALL,
        ):
            return DbFunctionType.JAVASCRIPT
        else:
            return DbFunctionType.SQL  # SQL is the default if no language is defined


class SolutionProcedure(SolutionParametersObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.PROCEDURE, git_change_type
        )

    def __str__(self):
        return f"SolutionProcedure: {self.id}"

    def __repr__(self):
        return f"SolutionProcedure: {self.id}"


class SolutionSchema(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?SCHEMA\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+)\b)(?!\.)(?P<name>)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, __ = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        self.schema = schema
        self.name = schema
        self.object_type = DbObjectType.SCHEMA
        self.path = path
        self.git_change_type = git_change_type
        self.content = content

    def __str__(self):
        return f"SolutionSchema: {self.id}"

    def __repr__(self):
        return f"SolutionSchema: {self.id}"

    @property
    def id(self):
        return f"{self.object_type} {self.schema.upper()}"

    @property
    def full_name(self):
        return self.schema.upper()
    

class SolutionTag(SolutionObject):
    pattern = r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?TAG\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>(\"\w+\")|(\w+))\.(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

    def __init__(
        self, path: str, content: str, git_change_type: git.DiffIndex.change_type = None
    ):
        schema, name = super()._regex_get_object_name(
            self.pattern, string_util.remove_comment(content)
        )
        super().__init__(
            schema, name, path, content, DbObjectType.TAG, git_change_type
        )

    def __str__(self):
        return f"SolutionTag: {self.id}"

    def __repr__(self):
        return f"SolutionTag: {self.id}"
