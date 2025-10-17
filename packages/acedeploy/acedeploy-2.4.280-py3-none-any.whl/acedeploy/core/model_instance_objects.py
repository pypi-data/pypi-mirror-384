import json
import logging
import re
import regex
from abc import ABC
from typing import Dict, List

import aceutils.dict_and_list_util as dict_and_list_util
import aceutils.misc_utils as misc_utils
import aceutils.string_util as string_util
from acedeploy.core.model_configuration import ObjectOption
from acedeploy.core.model_database_object import DatabaseObject
from acedeploy.core.model_sql_entities import DbObjectType, PolicyType
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class ColumnInstance(object):
    """
    Database object type Table-, DynamicTable-, or View- Column
    """

    def __init__(self, metadata_query_result: Dict):
        self.database_name = metadata_query_result["DATABASE_NAME"]
        self.object_schema = metadata_query_result["TABLE_SCHEMA"]
        self.object_name = metadata_query_result["TABLE_NAME"]
        self.column_name = metadata_query_result["COLUMN_NAME"]
        self.ordinal_position = metadata_query_result["ORDINAL_POSITION"]
        column_default_raw = metadata_query_result.get("COLUMN_DEFAULT")
        if (
            column_default_raw
            and column_default_raw.endswith(
                ".NEXTVAL"
            )  # if the default is a nextval, the result will contain the database name, which must be removed for comparisons to work
            and column_default_raw.startswith(
                f"{self.database_name}."
            )  # only remove database name if the sequence is in the same database
        ):
            self.column_default = string_util.remove_prefix(
                column_default_raw, f"{self.database_name}."
            )
        else:
            self.column_default = column_default_raw
        self.is_nullable = metadata_query_result.get("IS_NULLABLE") # IS_NULLABLE is not set for DynamicTable-Columns, because it is not supported in the DDL of a DynamicTable and is only inherited from underlying objects
        self.data_type = metadata_query_result["DATA_TYPE"]
        self.character_maximum_length = metadata_query_result.get(
            "CHARACTER_MAXIMUM_LENGTH"
        )
        self.character_octet_length = metadata_query_result.get(
            "CHARACTER_OCTET_LENGTH"
        )
        self.numeric_precision = metadata_query_result.get("NUMERIC_PRECISION")
        self.numeric_precision_radix = metadata_query_result.get(
            "NUMERIC_PRECISION_RADIX"
        )
        self.numeric_scale = metadata_query_result.get("NUMERIC_SCALE")
        self.datetime_precision = metadata_query_result.get("DATETIME_PRECISION")
        self.interval_type = metadata_query_result.get("INTERVAL_TYPE")
        self.interval_precision = metadata_query_result.get("INTERVAL_PRECISION")
        self.character_set_catalog = metadata_query_result.get("CHARACTER_SET_CATALOG")
        self.character_set_schema = metadata_query_result.get("CHARACTER_SET_SCHEMA")
        self.character_set_name = metadata_query_result.get("CHARACTER_SET_NAME")
        self.collation_catalog = metadata_query_result.get("COLLATION_CATALOG")
        self.collation_schema = metadata_query_result.get("COLLATION_SCHEMA")
        self.collation_name = metadata_query_result.get("COLLATION_NAME")
        self.domain_catalog = metadata_query_result.get("DOMAIN_CATALOG")
        self.domain_schema = metadata_query_result.get("DOMAIN_SCHEMA")
        self.domain_name = metadata_query_result.get("DOMAIN_NAME")
        self.udt_catalog = metadata_query_result.get("UDT_CATALOG")
        self.udt_schema = metadata_query_result.get("UDT_SCHEMA")
        self.udt_name = metadata_query_result.get("UDT_NAME")
        self.scope_catalog = metadata_query_result.get("SCOPE_CATALOG")
        self.scope_schema = metadata_query_result.get("SCOPE_SCHEMA")
        self.scope_name = metadata_query_result.get("SCOPE_NAME")
        self.maximum_cardinality = metadata_query_result.get("MAXIMUM_CARDINALITY")
        self.dtd_identifier = metadata_query_result.get("DTD_IDENTIFIER")
        self.is_self_referencing = metadata_query_result["IS_SELF_REFERENCING"]
        self.is_identity = metadata_query_result["IS_IDENTITY"]
        self.identity_generation = metadata_query_result.get("IDENTITY_GENERATION")
        self.identity_start = metadata_query_result.get("IDENTITY_START")
        self.identity_increment = metadata_query_result.get("IDENTITY_INCREMENT")
        self.identity_maximum = metadata_query_result.get("IDENTITY_MAXIMUM")
        self.identity_minimum = metadata_query_result.get("IDENTITY_MINIMUM")
        self.identity_cycle = metadata_query_result.get("IDENTITY_CYCLE")
        self.comment = metadata_query_result.get("COMMENT")
        self.tags = metadata_query_result.get("tags", {})

    def __eq__(self, other):
        """
        Test if two Column objects are identical.
        Tests for all properties, except ordinal_position and database_name.
        """
        return (
            self.object_schema == other.object_schema
            and self.object_name == other.object_name
            and self.column_name == other.column_name
            and self.column_default == other.column_default
            and self.is_nullable == other.is_nullable
            and self.data_type == other.data_type
            and self.character_maximum_length == other.character_maximum_length
            and self.character_octet_length == other.character_octet_length
            and self.numeric_precision == other.numeric_precision
            and self.numeric_precision_radix == other.numeric_precision_radix
            and self.numeric_scale == other.numeric_scale
            and self.datetime_precision == other.datetime_precision
            and self.interval_type == other.interval_type
            and self.interval_precision == other.interval_precision
            and self.character_set_catalog == other.character_set_catalog
            and self.character_set_schema == other.character_set_schema
            and self.character_set_name == other.character_set_name
            and self.collation_catalog == other.collation_catalog
            and self.collation_schema == other.collation_schema
            and self.collation_name == other.collation_name
            and self.domain_catalog == other.domain_catalog
            and self.domain_schema == other.domain_schema
            and self.domain_name == other.domain_name
            and self.udt_catalog == other.udt_catalog
            and self.udt_schema == other.udt_schema
            and self.udt_name == other.udt_name
            and self.scope_catalog == other.scope_catalog
            and self.scope_schema == other.scope_schema
            and self.scope_name == other.scope_name
            and self.maximum_cardinality == other.maximum_cardinality
            and self.dtd_identifier == other.dtd_identifier
            and self.is_self_referencing == other.is_self_referencing
            and self.is_identity == other.is_identity
            and self.identity_generation == other.identity_generation
            and self.identity_start == other.identity_start
            and self.identity_increment == other.identity_increment
            and self.identity_maximum == other.identity_maximum
            and self.identity_minimum == other.identity_minimum
            and self.identity_cycle == other.identity_cycle
            and self.tags == other.tags
            and (self.comment if self.comment else "")
            == (
                other.comment if other.comment else ""
            )  # comment can be None, treat as empty string for comparison
        )

    @staticmethod
    def get_differences(column1, column2):
        column1_dict = column1.__dict__.copy()
        column2_dict = column2.__dict__.copy()
        column1_dict["comment"] = (
            column1_dict["comment"] if column1_dict["comment"] else ""
        )  # comment can be None, treat as empty string for comparison
        column2_dict["comment"] = (
            column2_dict["comment"] if column2_dict["comment"] else ""
        )
        only_in_column1, only_in_column2 = dict_and_list_util.compare_nested_dicts(
            column1_dict, column2_dict
        )
        only_in_column1.pop("ordinal_position", 0)
        only_in_column1.pop("database_name", "")
        only_in_column2.pop("ordinal_position", 0)
        only_in_column2.pop("database_name", "")
        return only_in_column1, only_in_column2


class ConstraintColumn(object):
    def __init__(self, key_sequence: int, column_name: str) -> None:
        self.key_sequence = key_sequence
        self.column_name = column_name

    def __eq__(self, other: "ConstraintColumn") -> bool:
        return (
            self.key_sequence == other.key_sequence
            and self.column_name == other.column_name
        )


class ConstraintColumnForeignKey(ConstraintColumn):
    def __init__(
        self, key_sequence: int, column_name: str, pk_column_name: str
    ) -> None:
        super().__init__(key_sequence, column_name)
        self.pk_column_name = pk_column_name

    def __eq__(self, other: "ConstraintColumnForeignKey") -> bool:
        return super().__eq__(other) and self.pk_column_name == other.pk_column_name


class InstanceConstraint(ABC):
    def __init__(self, metadata: List[Dict]):
        if len(metadata) == 0:
            raise ValueError("Cannot create object without metadata")
        self.schema_name = metadata[0]["schema_name"]
        if any(m["schema_name"] != self.schema_name for m in metadata):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table"
            )
        self.table_name = metadata[0]["table_name"]
        if any(m["table_name"] != self.table_name for m in metadata):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table"
            )
        self.constraint_name = metadata[0]["constraint_name"]
        if any(m["constraint_name"] != self.constraint_name for m in metadata):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table"
            )
        self.comment = metadata[0]["comment"]
        if any(m["comment"] != self.comment for m in metadata):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table"
            )
        self.columns = self._get_columns(metadata)

    @staticmethod
    def _get_columns(metadata: List[Dict]) -> List[ConstraintColumn]:
        return [ConstraintColumn(m["key_sequence"], m["column_name"]) for m in metadata]

    @staticmethod
    def factory(
        metadata_query_result: List[Dict], constraint_type: str
    ) -> "InstanceConstraint":
        mapping = {
            "foreign_key": {
                "class": InstanceConstraintForeignKey,
                "constraint_name_key": "fk_name",
            },
            "primary_key": {
                "class": InstanceConstraintPrimaryKey,
                "constraint_name_key": "constraint_name",
            },
            "unique_key": {
                "class": InstanceConstraintUniqueKey,
                "constraint_name_key": "constraint_name",
            },
        }
        constraint_objects = []
        constraint_names = set(
            [
                m[mapping[constraint_type]["constraint_name_key"]]
                for m in metadata_query_result
            ]
        )
        for constraint_name in constraint_names:
            metadata = [
                m
                for m in metadata_query_result
                if m[mapping[constraint_type]["constraint_name_key"]] == constraint_name
            ]
            constraint_objects.append(mapping[constraint_type]["class"](metadata))
        return constraint_objects

    def __eq__(self, other: "InstanceConstraint") -> bool:
        self_name = (
            "system_assigned"
            if self._is_system_assigned_name(self.constraint_name)
            else self.constraint_name
        )
        other_name = (
            "system_assigned"
            if self._is_system_assigned_name(other.constraint_name)
            else other.constraint_name
        )
        return (
            self.schema_name == other.schema_name
            and self.table_name == other.table_name
            and self_name == other_name
            and self.comment == other.comment
            and self.columns == other.columns
        )

    @staticmethod
    def _is_system_assigned_name(name: str) -> str:
        """
        Test if the given string is a system assigned constraint name.
        """
        if re.match(
            r"^SYS_CONSTRAINT_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
            name,
        ):
            return True
        else:
            return False


class InstanceConstraintPrimaryKey(InstanceConstraint):
    pass


class InstanceConstraintUniqueKey(InstanceConstraint):
    pass


class InstanceConstraintForeignKey(InstanceConstraint):
    def __init__(self, metadata: List[Dict]) -> None:
        metadata_copy = [m.copy() for m in metadata]
        # need to rename metadata entries to match expected key names in InstanceConstraint
        for m in metadata_copy:
            m["schema_name"] = m.pop("fk_schema_name")
            m["table_name"] = m.pop("fk_table_name")
            m["constraint_name"] = m.pop("fk_name")
        super().__init__(metadata_copy)
        self.pk_schema_name = metadata_copy[0]["pk_schema_name"]
        if any(m["pk_schema_name"] != self.pk_schema_name for m in metadata_copy):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table referencing a single pk"
            )
        self.pk_table_name = metadata_copy[0]["pk_table_name"]
        if any(m["pk_table_name"] != self.pk_table_name for m in metadata_copy):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table referencing a single pk"
            )
        self.pk_name = metadata_copy[0]["pk_name"]
        if any(m["pk_name"] != self.pk_name for m in metadata_copy):
            raise ValueError(
                "Metadata must refer to a single constraint on a single table referencing a single pk"
            )

    @property
    def fk_schema_name(self):
        return self.schema_name

    @property
    def fk_table_name(self):
        return self.table_name

    @property
    def fk_name(self):
        return self.constraint_name

    @staticmethod
    def _get_columns(metadata):
        return [
            ConstraintColumnForeignKey(
                m["key_sequence"], m["fk_column_name"], m["pk_column_name"]
            )
            for m in metadata
        ]

    def __eq__(self, other: "InstanceConstraintForeignKey") -> bool:
        self_pk_name = (
            "system_assigned"
            if self._is_system_assigned_name(self.pk_name)
            else self.pk_name
        )
        other_pk_name = (
            "system_assigned"
            if self._is_system_assigned_name(other.pk_name)
            else other.pk_name
        )
        return (
            super().__eq__(other)
            and self.pk_schema_name == other.pk_schema_name
            and self.pk_table_name == other.pk_table_name
            and self_pk_name == other_pk_name
        )


class InstanceObject(DatabaseObject):
    """
    Base object for storing basic information about a database object
    Only for inherit usage
    """

    def __init__(self, result, object_type: DbObjectType, object_options: ObjectOption=None):
        """
            inits a new instance
        Args:
            result: any - resultset entry for this entity
        """
        super().__init__(result["SCHEMA_NAME"], result["OBJECT_NAME"], object_type)
        self.database_name = result["DATABASE_NAME"].upper()
        self.object_options = object_options

    def __eq__(self, other: "InstanceObject") -> bool:
        return (
            self.object_type == other.object_type
            and self.schema == other.schema
            and self.name == other.name
        )

    @staticmethod
    def factory(
        object_type: DbObjectType,
        metadata_query_result: Dict,
        object_options: ObjectOption=None,
        **kwargs
    ):
        mapping = {
            DbObjectType.TABLE: InstanceTable,
            DbObjectType.EXTERNALTABLE: InstanceExternalTable,
            DbObjectType.VIEW: InstanceView,
            DbObjectType.MATERIALIZEDVIEW: InstanceMaterializedView,
            DbObjectType.FUNCTION: InstanceFunction,
            DbObjectType.PROCEDURE: InstanceProcedure,
            DbObjectType.STAGE: InstanceStage,
            DbObjectType.FILEFORMAT: InstanceFileformat,
            DbObjectType.SCHEMA: InstanceSchema,
            DbObjectType.STREAM: InstanceStream,
            DbObjectType.TASK: InstanceTask,
            DbObjectType.PIPE: InstancePipe,
            DbObjectType.SEQUENCE: InstanceSequence,
            DbObjectType.MASKINGPOLICY: InstanceMaskingPolicy,
            DbObjectType.ROWACCESSPOLICY: InstanceRowAccessPolicy,
            DbObjectType.DYNAMICTABLE: InstanceDynamicTable,
            DbObjectType.NETWORKRULE: InstanceNetworkRule,
            DbObjectType.TAG: InstanceTag,
        }
        return mapping[object_type](
            metadata_query_result=metadata_query_result,
            object_options=object_options,
            **kwargs,
        )


class InstanceTableLike(InstanceObject):
    """
    Database object type Table or View
    """

    def __init__(
        self,
        metadata_query_result: Dict,
        object_type: DbObjectType,
        object_options: ObjectOption=None,
        ignore_column_order: bool = False,
    ):
        super().__init__(metadata_query_result, object_type, object_options)
        self.table_type = metadata_query_result["TABLE_TYPE"]
        clustering_key_raw = metadata_query_result["CLUSTERING_KEY"]
        self.clustering_key = (
            clustering_key_raw.upper() if clustering_key_raw else clustering_key_raw
        )
        self.ignore_column_order = ignore_column_order
        self.table_columns = sorted(
            [ColumnInstance(column)for column in metadata_query_result["COLUMN_DETAILS"]],
            key=lambda c: c.ordinal_position,
        )

    def __eq__(self, other: "InstanceTableLike") -> bool:
        """
        Test if two Table objects are identical.
        Tests for all properties, except database_name.
        """
        clustering_key_self = (
            self.clustering_key.replace(" ", "").replace("\n", "").replace("\t", "")
            if isinstance(self.clustering_key, str)
            else self.clustering_key
        )  # clustering key can be, e.g. LINEAR(a,b) or LINEAR(a, b)
        clustering_key_other = (
            other.clustering_key.replace(" ", "").replace("\n", "").replace("\t", "")
            if isinstance(other.clustering_key, str)
            else other.clustering_key
        )
        if (
            (not super().__eq__(other))
            or self.table_type != other.table_type
            or clustering_key_self != clustering_key_other
        ):
            return False

        if len(self.table_columns) != len(other.table_columns):
            return False

        if self.ignore_column_order:
            if not InstanceTableLike._compare_columns_ignore_order(
                self.table_columns, other.table_columns
            ):
                return False
        else:
            if not InstanceTableLike._compare_columns_with_order(
                self.table_columns, other.table_columns
            ):
                return False

        return True

    @staticmethod
    def _compare_columns_with_order(columns_self, columns_other):
        for column_self, column_other in zip(columns_self, columns_other):
            if column_self != column_other:
                return False
        return True

    @staticmethod
    def _compare_columns_ignore_order(columns_self, columns_other):
        comparison = InstanceTableLike._compare_columns(columns_self, columns_other)
        return comparison == {
            "columns_not_in_both": {"only_in_table1": [], "only_in_table2": []},
            "property_differences": {"table1": {}, "table2": {}},
        }

    @staticmethod
    def generate_diff_description(table1, table2):
        nested_result_dict = InstanceTableLike._get_diffs(table1, table2)
        return json.dumps(
            dict_and_list_util.strip_nested_dict(nested_result_dict), indent=4
        )

    @staticmethod
    def _get_diffs(table1, table2):
        table1_dict = table1.__dict__.copy()
        table1_dict.pop("database_name")
        table1_dict.pop("table_columns")
        table1_dict.pop("ignore_column_order")
        table2_dict = table2.__dict__.copy()
        table2_dict.pop("database_name")
        table2_dict.pop("table_columns")
        table2_dict.pop("ignore_column_order")

        x = table1_dict.pop(
            "constraints_foreign_key", None
        )  # TODO: implement getting diff on constraints
        table1_dict.pop("constraints_primary_key", None)
        table1_dict.pop("constraints_unique_key", None)
        table2_dict.pop("constraints_foreign_key", None)
        table2_dict.pop("constraints_primary_key", None)
        table2_dict.pop("constraints_unique_key", None)

        only_in_table1, only_in_table2 = dict_and_list_util.compare_nested_dicts(
            table1_dict, table2_dict
        )
        column_differences = InstanceTableLike._compare_columns(
            table1.table_columns, table2.table_columns
        )

        result = {}
        result["property_differences"] = {
            "table1": only_in_table1,
            "table2": only_in_table2,
        }
        result["column_differences"] = column_differences
        if x is not None:  # TODO: implement getting diff on constraints
            result[
                "constraint_differences"
            ] = "currently not implemented, check manually"
        return result

    @staticmethod
    def _compare_columns(column_list1, column_list2):

        columns_only_in_1 = [
            c.column_name
            for c in column_list1
            if c.column_name not in [cn.column_name for cn in column_list2]
        ]
        columns_only_in_2 = [
            c.column_name
            for c in column_list2
            if c.column_name not in [cn.column_name for cn in column_list1]
        ]

        result = {}
        result["columns_not_in_both"] = {
            "only_in_table1": columns_only_in_1,
            "only_in_table2": columns_only_in_2,
        }
        result["property_differences"] = {"table1": {}, "table2": {}}

        column_names_in_both = [
            c.column_name
            for c in column_list1
            if c.column_name in [cn.column_name for cn in column_list2]
        ]
        for column_name in column_names_in_both:
            column1 = next(
                c
                for c in column_list1
                if c.column_name.casefold() == column_name.casefold()
            )
            column2 = next(
                c
                for c in column_list2
                if c.column_name.casefold() == column_name.casefold()
            )
            only_in_column1, only_in_column2 = ColumnInstance.get_differences(
                column1, column2
            )
            if len(only_in_column1) > 0:
                result["property_differences"]["table1"][column_name] = only_in_column1
            if len(only_in_column2) > 0:
                result["property_differences"]["table2"][column_name] = only_in_column2

        return result


class InstanceTable(InstanceTableLike):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None, ignore_column_order: bool = False):
        super().__init__(metadata_query_result, DbObjectType.TABLE, object_options, ignore_column_order)
        self.row_count = metadata_query_result["ROW_COUNT"] # should not be used for comparsions
        self.bytes = metadata_query_result["BYTES"] # should not be used for comparsions
        self.retention_time = metadata_query_result["RETENTION_TIME"]
        self.schema_retention_time = metadata_query_result["SCHEMA_RETENTION_TIME"]
        self.comment = metadata_query_result["COMMENT"]
        self.constraints_foreign_key = InstanceConstraint.factory(
            metadata_query_result["constraint_foreign_keys"], "foreign_key"
        )
        self.constraints_primary_key = InstanceConstraint.factory(
            metadata_query_result["constraint_primary_keys"], "primary_key"
        )
        self.constraints_unique_key = InstanceConstraint.factory(
            metadata_query_result["constraint_unique_keys"], "unique_key"
        )
        self.tags = metadata_query_result.get("tags", {})

        pr_factory = PolicyReferenceFactory()
        policy_references = [
                pr_factory.factory(ref) for ref in metadata_query_result.get("policy_references", [])
            ]
        self.row_access_policy_references = [
            ref for ref in policy_references if ref.policy_type == PolicyType.ROWACCESS
        ]
        self.masking_policy_references = [
            ref for ref in policy_references if ref.policy_type == PolicyType.MASKING
        ]

    def __str__(self):
        return f"InstanceTable: {self.id}"

    def __repr__(self):
        return f"InstanceTable: {self.id}"

    def __eq__(self, other: "InstanceTable") -> bool:
        if not (
            super().__eq__(other)
            and self.retention_time == other.retention_time
            and self.schema_retention_time == other.schema_retention_time
            and self.comment == other.comment
            and self.constraints_foreign_key == other.constraints_foreign_key
            and self.constraints_primary_key == other.constraints_primary_key
            and self.constraints_unique_key == other.constraints_unique_key
            and self.tags == other.tags
        ):
            return False
    
        if set(self.row_access_policy_references) != set(other.row_access_policy_references):
            return False
        
        if set(self.masking_policy_references) != set(other.masking_policy_references):
            return False

        return True


class InstanceView(InstanceTableLike):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None, ignore_column_order: bool = False):
        super().__init__(metadata_query_result, DbObjectType.VIEW, object_options, ignore_column_order)
        self.view_definition = metadata_query_result["VIEW_DEFINITION"]
        self.is_secure = metadata_query_result["IS_SECURE"]
        self.comment = metadata_query_result["COMMENT"]
        applied_policies_metadata_legacy = metadata_query_result.get(
            "APPLIED_POLICIES_LEGACY", []
        )  # applied policies property is optional
        self.applied_policies_legacy = [
            AppliedPolicyLegacy.factory(apm) for apm in applied_policies_metadata_legacy
        ]
        self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"InstanceView: {self.id}"

    def __repr__(self):
        return f"InstanceView: {self.id}"

    def __eq__(self, other: "InstanceView") -> bool:
        return (
            super().__eq__(other)
            and string_util.compare_strings_ignore_whitespace_and_case(
                string_util.add_copy_grants(string_util.add_create_or_replace(self.view_definition)),
                string_util.add_copy_grants(string_util.add_create_or_replace(other.view_definition))
                )
            # and self.comment == other.comment #TODO -> comments on views are currently (10.04.2024) ignored by the MetadataService (view_definition in the information_schema.views does not include comments on views)
            and self.is_secure == other.is_secure
            and self.tags == other.tags
        )
    

class InstanceMaterializedView(InstanceTableLike):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None, ignore_column_order: bool = False,):
        super().__init__(
            metadata_query_result, DbObjectType.MATERIALIZEDVIEW, object_options, ignore_column_order
        )
        self.comment = metadata_query_result["COMMENT"]
        self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"InstanceMaterializedView: {self.id}"

    def __repr__(self):
        return f"InstanceMaterializedView: {self.id}"

    def __eq__(self, other: "InstanceMaterializedView") -> bool:
        return (
            super().__eq__(other) 
            and self.comment == other.comment 
            and self.tags == other.tags
        )


class InstanceExternalTable(InstanceTableLike):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None, ignore_column_order: bool = False):
        super().__init__(
            metadata_query_result, DbObjectType.EXTERNALTABLE, object_options, ignore_column_order
        )
        self.comment = metadata_query_result["COMMENT"]
        self.location = metadata_query_result["LOCATION"]
        self.file_format_name = metadata_query_result["FILE_FORMAT_NAME"]
        self.file_format_type = metadata_query_result["FILE_FORMAT_TYPE"]
        self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"InstanceExternalTable: {self.id}"

    def __repr__(self):
        return f"InstanceExternalTable: {self.id}"

    def __eq__(self, other: "InstanceExternalTable") -> bool:
        return (
            super().__eq__(other)
            and self.comment == other.comment
            and self.location == other.location
            and self.file_format_name == other.file_format_name
            and self.file_format_type == other.file_format_type
            and self.tags == other.tags
        )


class InstanceStage(InstanceObject):
    """
    Database object typ Stage
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        metadata_query_result["DATABASE_NAME"] = metadata_query_result["database_name"]
        metadata_query_result["SCHEMA_NAME"] = metadata_query_result["schema_name"]
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, DbObjectType.STAGE, object_options)
        # self.url = metadata_query_result['url'] # also appears in dict as STAGE_LOCATION
        self.has_credentials = metadata_query_result["has_credentials"]
        self.has_encryption_key = metadata_query_result["has_encryption_key"]
        self.comment = metadata_query_result["comment"]
        # self.region = metadata_query_result['region'] # do not use this attribute. snowflake sometimes does not return a value for this. region does not add value anyways, because it is part of stage_location anyways.
        self.type = metadata_query_result["type"]
        self.cloud = metadata_query_result["cloud"]
        # self.storage_integration = metadata_query_result['storage_integration'] # also appears in dict as STAGE_INTEGRATION
        self.stage_file_format = metadata_query_result["STAGE_FILE_FORMAT"]  # dict
        self.stage_copy_options = metadata_query_result["STAGE_COPY_OPTIONS"]  # dict
        self.stage_location = metadata_query_result["STAGE_LOCATION"]  # dict
        self.stage_integration = metadata_query_result["STAGE_INTEGRATION"]  # dict
        self.directory = metadata_query_result["DIRECTORY"]  # dict
        self.directory.pop("LAST_REFRESHED_ON", None) # not relevant for metadata comparison

    def __str__(self):
        return f"InstanceStage: {self.id}"

    def __repr__(self):
        return f"InstanceStage: {self.id}"

    def __eq__(self, other: "InstanceStage") -> bool:
        return (
            super().__eq__(other)
            # and self.url == other.url
            and self.has_credentials == other.has_credentials
            and self.has_encryption_key == other.has_encryption_key
            and self.comment == other.comment
            # and self.region == other.region # do not compare this attribute. snowflake sometimes does not return a value for this. region does not add value anyways, because it is part of stage_location anyways.
            and self.type == other.type
            and self.cloud == other.cloud
            # and self.storage_integration == other.storage_integration
            and self.stage_file_format == other.stage_file_format
            and self.stage_copy_options == other.stage_copy_options
            and self.stage_location == other.stage_location
            and self.stage_integration == other.stage_integration
            and self.directory == other.directory
        )


class InstanceFileformat(InstanceObject):
    """
    Database object typ File format
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        metadata_query_result["DATABASE_NAME"] = metadata_query_result["database_name"]
        metadata_query_result["SCHEMA_NAME"] = metadata_query_result["schema_name"]
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, DbObjectType.FILEFORMAT, object_options)
        self.file_format_type = metadata_query_result["type"]
        self.format_options = self._convert_options_json_to_dict(
            metadata_query_result["format_options"]
        )
        self.comment = metadata_query_result["comment"]

    def __str__(self):
        return f"InstanceFileformat: {self.id}"

    def __repr__(self):
        return f"InstanceFileformat: {self.id}"

    def __eq__(self, other: "InstanceFileformat") -> bool:
        return (
            super().__eq__(other)
            and self.file_format_type == other.file_format_type
            and self.format_options == other.format_options
            and self.comment == other.comment
        )

    @staticmethod
    def _convert_options_json_to_dict(s: str) -> dict:
        d = json.loads(s)
        d.pop("TYPE")
        return d


class InstanceStream(InstanceObject):
    """
    Database object type Stream
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        metadata_query_result["DATABASE_NAME"] = metadata_query_result["database_name"]
        metadata_query_result["SCHEMA_NAME"] = metadata_query_result["schema_name"]
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, DbObjectType.STREAM, object_options)
        self.comment = metadata_query_result["comment"]
        self.table_name = self._remove_database_from_table_name(
            metadata_query_result["table_name"]
        )
        self.type = metadata_query_result["type"]
        self.stale = metadata_query_result["stale"]
        self.mode = metadata_query_result["mode"]

    def __eq__(self, other: "InstanceStream") -> bool:
        return (
            super().__eq__(other)
            and self.comment == other.comment
            and self.table_name == other.table_name
            and self.type == other.type
            and self.mode == other.mode
        )

    def __str__(self):
        return f"InstanceStream: {self.id}"

    def __repr__(self):
        return f"InstanceStream: {self.id}"

    @staticmethod
    def _remove_database_from_table_name(table_name):
        m = re.match(r"^\"?\w+\"?\.(?P<name>\"?\w+\"?\.\"?\w+\"?)$", table_name)
        if m:
            return m.group("name")
        else:
            return table_name


class InstanceTask(InstanceObject):
    """
    Database object typ File format
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        metadata_query_result["DATABASE_NAME"] = metadata_query_result["database_name"]
        metadata_query_result["SCHEMA_NAME"] = metadata_query_result["schema_name"]
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, DbObjectType.TASK, object_options)
        self.comment = metadata_query_result["comment"]
        self.warehouse = metadata_query_result["warehouse"]
        self.schedule = metadata_query_result["schedule"]
        self.predecessors = self._parse_predecessors(
            metadata_query_result["predecessors"], self.database_name
        )
        self.state = metadata_query_result["state"]
        self.definition = metadata_query_result["definition"]
        self.condition = metadata_query_result["condition"]
        self.allow_overlapping_execution = metadata_query_result[
            "allow_overlapping_execution"
        ]

    def __str__(self):
        return f"InstanceTask: {self.id}"

    def __repr__(self):
        return f"InstanceTask: {self.id}"

    def __eq__(self, other: "InstanceTask") -> bool:
        return (
            super().__eq__(other)
            and self.comment == other.comment
            and self.warehouse == other.warehouse
            and self.schedule == other.schedule
            and self.predecessors == other.predecessors
            and self.state == other.state
            and self.definition == other.definition
            and self.condition == other.condition
            and self.allow_overlapping_execution == other.allow_overlapping_execution
        )

    @staticmethod
    def _parse_predecessors(metadata: str, database_name) -> List[str]:
        """
        Parse the metadata for predecessors.

        This function works both for accounts where behavior change 2022_03 is active and not active.
        https://community.snowflake.com/s/article/SHOW-TASKS-Command-and-TASK-DEPENDENTS-Function-PREDECESSORS-PREDECESSOR-Column
        """
        if metadata is None:  # pre bundle 2022_03 (no predecessor)
            return []
        elif metadata.startswith("["):  # post bundle 2022_03
            predecessor_list = json.loads(metadata)
            return [
                string_util.remove_prefix(p, f"{database_name}.")
                for p in predecessor_list
            ]
        else:  # pre bundle 2022_03 (with predecessor)
            return [string_util.remove_prefix(metadata, f"{database_name}.")]


class InstancePipe(InstanceObject):
    """
    Database object typ File format
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.PIPE, object_options)
        self.definition = metadata_query_result["DEFINITION"]
        self.is_autoingest_enabled = metadata_query_result["IS_AUTOINGEST_ENABLED"]
        self.notification_channel_name = metadata_query_result[
            "NOTIFICATION_CHANNEL_NAME"
        ]
        self.comment = metadata_query_result["COMMENT"]
        self.pattern = metadata_query_result["PATTERN"]
        self.integration = metadata_query_result["integration"]
        self.execution_state = metadata_query_result[
            "execution_state"
        ]  # RUNNING or PAUSED (or some error). Is set outside of deployment and does not need to be compared in __eq__()

    def __str__(self):
        return f"InstancePipe: {self.id}"

    def __repr__(self):
        return f"InstancePipe: {self.id}"

    def __eq__(self, other: "InstancePipe") -> bool:
        return (
            super().__eq__(other)
            and self.definition == other.definition
            and self.is_autoingest_enabled == other.is_autoingest_enabled
            and self.notification_channel_name == other.notification_channel_name
            and self.comment == other.comment
            and self.pattern == other.pattern
            and self.integration == other.integration
        )


class InstanceSequence(InstanceObject):
    """
    Database object type Sequence
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.SEQUENCE, object_options)
        self.data_type = metadata_query_result["DATA_TYPE"]
        self.numeric_precision = metadata_query_result["NUMERIC_PRECISION"]
        self.numeric_precision_radix = metadata_query_result["NUMERIC_PRECISION_RADIX"]
        self.numeric_scale = metadata_query_result["NUMERIC_SCALE"]
        self.start_value = metadata_query_result["START_VALUE"]
        self.increment = metadata_query_result["INCREMENT"]
        self.comment = metadata_query_result["COMMENT"]

    def __eq__(self, other: "InstanceSequence") -> bool:
        return (
            super().__eq__(other)
            and self.data_type == other.data_type
            and self.numeric_precision == other.numeric_precision
            and self.numeric_precision_radix == other.numeric_precision_radix
            and self.numeric_scale == other.numeric_scale
            and self.start_value == other.start_value
            and self.increment == other.increment
            and (self.comment if self.comment else "")
            == (
                other.comment if other.comment else ""
            )  # comment can be None, treat as empty string for comparison
        )

    def __str__(self):
        return f"InstanceSequence: {self.id}"

    def __repr__(self):
        return f"InstanceSequence: {self.id}"


class InstanceParameterObject(InstanceObject):
    """
    Database object type Function or Procedure
    """

    def __init__(self, metadata_query_result: Dict, object_type: DbObjectType, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, object_type, object_options)
        parameters = self.parse_parameters(metadata_query_result["SIGNATURE"])
        self.parameters = [
            misc_utils.map_datatype_name_to_default(p) for p in parameters
        ]
        self.data_type = metadata_query_result["DATA_TYPE"]
        self.character_maximum_length = metadata_query_result[
            "CHARACTER_MAXIMUM_LENGTH"
        ]
        self.character_octet_length = metadata_query_result["CHARACTER_OCTET_LENGTH"]
        self.numeric_precision = metadata_query_result["NUMERIC_PRECISION"]
        self.numeric_precision_radix = metadata_query_result["NUMERIC_PRECISION_RADIX"]
        self.numeric_scale = metadata_query_result["NUMERIC_SCALE"]
        self.language = metadata_query_result["LANGUAGE"]
        self.definition = metadata_query_result["DEFINITION"]

    def __eq__(self, other: "InstanceParameterObject") -> bool:
        return (
            super().__eq__(other)
            and self.parameters == other.parameters
            and self.data_type == other.data_type
            and self.character_maximum_length == other.character_maximum_length
            and self.character_octet_length == other.character_octet_length
            and self.numeric_precision == other.numeric_precision
            and self.numeric_precision_radix == other.numeric_precision_radix
            and self.numeric_scale == other.numeric_scale
            and self.language == other.language
            and self.definition == other.definition
        )

    @property
    def id(self):
        return f"{super().id} {self.parameters_string.upper()}"

    @property
    def full_name(self):
        return f"{super().full_name} {self.parameters_string.upper()}"

    @property
    def parameters_string(self):
        return f"({', '.join([s for s in self.parameters])})"

    @staticmethod
    def parse_parameters(signature: str) -> List[str]:
        """
            parses the snowflake parameter signature into valid tokens for snowflake connector
        Args:
            signature : str - snowflake parameter signature from query result set
        Raises:
            ValueError - if signature can not be parsed
        Returns:
            Data types from signature
        """
        if signature is None:
            raise ValueError("Signature can not be of type None.")

        output = []
        __argument_list = signature.replace("(", "").replace(")", "")
        if len(__argument_list) > 0:
            tokens = []
            if __argument_list.find(",") != -1:
                split_tokens = __argument_list.split(", ")
                for split_token in split_tokens:
                    tokens.append(split_token)
            else:
                tokens.append(__argument_list)

            for token in tokens:
                token_split = token.split(" ")
                if len(token_split) > 1:
                    output.append(token_split[1])
                else:
                    raise ValueError("Parameter token list not valid.")
        return output


class InstanceFunction(InstanceParameterObject):
    """
    Database object type Function
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.FUNCTION, object_options)
        self.is_external = metadata_query_result["IS_EXTERNAL"]
        self.is_secure = metadata_query_result["IS_SECURE"]
        self.volatility = metadata_query_result["VOLATILITY"]
        self.is_null_call = metadata_query_result["IS_NULL_CALL"]
        self.comment = metadata_query_result["COMMENT"]
        self.is_external = metadata_query_result["IS_EXTERNAL"]
        self.api_integration = metadata_query_result["API_INTEGRATION"]
        self.context_headers = metadata_query_result["CONTEXT_HEADERS"]
        self.max_batch_rows = metadata_query_result["MAX_BATCH_ROWS"]
        self.compression = metadata_query_result["COMPRESSION"]
        # the metadata that we currently query does not include information on Java functions, e.g. HANDLER
        # therefore, we can currently not use this class alone to determine if function instances are identical

    def __str__(self):
        return f"InstanceFunction: {self.id}"

    def __repr__(self):
        return f"InstanceFunction: {self.id}"

    def __eq__(self, other: "InstanceFunction") -> bool:
        return (
            super().__eq__(other)
            and self.is_external == other.is_external
            and self.is_secure == other.is_secure
            and self.volatility == other.volatility
            and self.is_null_call == other.is_null_call
            and self.comment == other.comment
            and self.is_external == other.is_external
            and self.api_integration == other.api_integration
            and self.context_headers == other.context_headers
            and self.max_batch_rows == other.max_batch_rows
            and self.compression == other.compression
        )


class InstanceProcedure(InstanceParameterObject):
    """
    Database object type Procedure
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.PROCEDURE, object_options)
        self.comment = metadata_query_result["COMMENT"]
        # the metadata that we currently query does not include information on EXECUTE AS
        # therefore, we can currently not use this class alone to determine if procedure instances are identical

    def __str__(self):
        return f"InstanceProcedure: {self.id}"

    def __repr__(self):
        return f"InstanceProcedure: {self.id}"

    def __eq__(self, other: "InstanceProcedure") -> bool:
        return super().__eq__(other) and self.comment == other.comment


class InstancePolicy(InstanceObject):
    """
    Database object type policy (masking or row access)
    """

    def __init__(self, metadata_query_result: Dict, object_type: DbObjectType, object_options: ObjectOption=None,):
        metadata_query_result["DATABASE_NAME"] = metadata_query_result["database_name"]
        metadata_query_result["SCHEMA_NAME"] = metadata_query_result["schema_name"]
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, object_type, object_options)
        self.kind = metadata_query_result["kind"]
        self.comment = metadata_query_result["comment"]
        self.signature = metadata_query_result["signature"]
        self.return_type = metadata_query_result["return_type"]
        self.body = metadata_query_result["body"]

    def __eq__(self, other: "InstancePolicy") -> bool:
        return (
            super().__eq__(other)
            and self.kind == other.kind
            and self.comment == other.comment
            and self.signature == other.signature
            and misc_utils.compare_datatype_ignore_varchar_maximum_length(self.return_type, other.return_type)
            and self.body == other.body
        )


class InstanceMaskingPolicy(InstancePolicy):
    """
    Database object type masking policy
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.MASKINGPOLICY, object_options)

    def __str__(self):
        return f"InstanceMaskingPolicy: {self.id}"

    def __repr__(self):
        return f"InstanceMaskingPolicy: {self.id}"


class InstanceRowAccessPolicy(InstancePolicy):
    """
    Database object type masking policy
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.ROWACCESSPOLICY, object_options)

    def __str__(self):
        return f"InstanceRowAccessPolicy: {self.id}"

    def __repr__(self):
        return f"InstanceRowAccessPolicy: {self.id}"


class InstanceSchema(InstanceObject):
    """
    Database object schema
    """

    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        self.database_name = metadata_query_result["DATABASE_NAME"]
        self.schema = metadata_query_result["SCHEMA_NAME"]
        self.name = self.schema
        self.object_type = DbObjectType.SCHEMA
        # self.is_managed_access = metadata_query_result["IS_MANAGED_ACCESS"]
        self.is_transient = metadata_query_result["IS_TRANSIENT"]
        self.retention_time = metadata_query_result["RETENTION_TIME"]
        self.database_retention_time = metadata_query_result["DATABASE_RETENTION_TIME"]
        self.comment = metadata_query_result["COMMENT"]
        self.object_options = object_options

    def __str__(self):
        return f"InstanceSchema: {self.id}"

    def __repr__(self):
        return f"InstanceSchema: {self.id}"

    def __eq__(self, other: "InstanceSchema") -> bool:
        return (
            self.object_type == other.object_type
            and self.schema == other.schema
            and self.name == other.name
            # and self.is_managed_access == other.is_managed_access
            and self.is_transient == other.is_transient
            and self.retention_time == other.retention_time
            and self.database_retention_time == other.database_retention_time
            and self.comment == other.comment
        )

    @property
    def full_name(self):
        return self.schema.upper()

    @property
    def id(self):
        return f"{self.object_type} {self.schema.upper()}"


class AppliedPolicyLegacy(object):
    """
    Hold information on which policy is applied to an object
    """

    def __init__(self, metadata, policy_type: PolicyType):
        self.policy_type = policy_type
        self.policy_db = metadata["POLICY_DB"]
        self.policy_schema = metadata["POLICY_SCHEMA"]
        self.policy_name = metadata["POLICY_NAME"]
        self.policy_kind = metadata["POLICY_KIND"]
        self.ref_database_name = metadata["REF_DATABASE_NAME"]
        self.ref_schema_name = metadata["REF_SCHEMA_NAME"]
        self.ref_entity_name = metadata["REF_ENTITY_NAME"]
        self.ref_entity_domain = metadata["REF_ENTITY_DOMAIN"]

    @property
    def full_name(self):
        "Full name including database and schema"
        return f"{self.policy_db}.{self.policy_schema}.{self.policy_name}"

    @property
    def full_name_quoted(self):
        "Full name including database and schema with quoted identifiers"
        return f'"{self.policy_db}"."{self.policy_schema}"."{self.policy_name}"'

    @staticmethod
    def factory(metadata):
        if metadata["POLICY_KIND"] == "ROW_ACCESS_POLICY":
            return AppliedRowAccessPolicyLegacy(metadata)
        elif metadata["POLICY_KIND"] == "MASKING_POLICY":
            return AppliedMaskingPolicyLegacy(metadata)
        else:
            raise ValueError(
                f"Metadata for POLICY_KIND [ '{metadata['POLICY_KIND']}' ] cannot be parsed"
            )

class InstanceDynamicTable(InstanceTableLike):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None, ignore_column_order: bool = False):
        super().__init__(metadata_query_result, DbObjectType.DYNAMICTABLE, object_options, ignore_column_order)
        self.query_text = metadata_query_result["QUERY_TEXT"]
        self.refresh_mode = metadata_query_result["REFRESH_MODE"]
        self.target_lag = metadata_query_result["TARGET_LAG"]
        self.warehouse = metadata_query_result["WAREHOUSE"]
        self.retention_time = metadata_query_result["RETENTION_TIME"]
        self.schema_retention_time = metadata_query_result["SCHEMA_RETENTION_TIME"]
        self.comment = metadata_query_result["COMMENT"]
        self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"InstanceDynamicTable: {self.id}"

    def __repr__(self):
        return f"InstanceDynamicTable: {self.id}"

    def __eq__(self, other: "InstanceDynamicTable") -> bool:
        return (
            super().__eq__(other)
            and self.query_text == other.query_text
            and self.refresh_mode == other.refresh_mode
            and self.target_lag == other.target_lag
            and self.warehouse == other.warehouse
            and self.retention_time == other.retention_time
            and self.schema_retention_time == self.schema_retention_time
            and self.comment == other.comment
            and self.tags == other.tags
        )

class InstanceNetworkRule(InstanceObject):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        super().__init__(metadata_query_result, DbObjectType.NETWORKRULE, object_options)
        self.type = metadata_query_result["TYPE"]
        self.value_list = metadata_query_result["VALUE_LIST"]
        self.mode = metadata_query_result["MODE"]
        self.comment = metadata_query_result["COMMENT"]

    def __str__(self):
        return f"InstanceNetworkRule: {self.id}"

    def __repr__(self):
        return f"InstanceNetworkRule: {self.id}"

    def __eq__(self, other: "InstanceNetworkRule") -> bool:
        return (
            super().__eq__(other)
            and self.type == other.type
            and self.value_list == other.value_list
            and self.mode == other.mode
            and self.comment == other.comment
        )

class AppliedRowAccessPolicyLegacy(AppliedPolicyLegacy):
    """
    Hold information on which row access policy is applied to an object
    """

    def __init__(self, metadata):
        super().__init__(metadata, PolicyType.ROWACCESS)
        self.ref_arg_column_names = json.loads(metadata["REF_ARG_COLUMN_NAMES"])

    @property
    def column_list_string(self):
        "String containing all columns (to be used in ALTER VIEW ADD POLICY). Example: '(COL1,COL2)'"
        return f"({','.join(self.ref_arg_column_names)})"


class AppliedMaskingPolicyLegacy(AppliedPolicyLegacy):
    """
    Hold information on which masking policy is applied to an object
    """

    def __init__(self, metadata):
        super().__init__(metadata, PolicyType.MASKING)
        self.ref_column_name = metadata["REF_COLUMN_NAME"]

class InstanceTag(InstanceObject):
    def __init__(self, metadata_query_result: Dict, object_options: ObjectOption=None,):
        self.object_type = DbObjectType.TAG
        self.object_options = object_options
        self.schema = metadata_query_result["schema_name"]
        self.name = metadata_query_result["name"]
        if metadata_query_result["allowed_values"]:
            self.allowed_values = metadata_query_result["allowed_values"][1:-1].replace('"','').split(',')
        else:
            self.allowed_values=[]

        self.comment = metadata_query_result["comment"]

    def __str__(self):
        return f"InstanceTag: {self.id}"

    def __repr__(self):
        return f"InstanceTag: {self.id}"

    def __eq__(self, other: "InstanceTag") -> bool:
        return (
            self.object_type == other.object_type
            and self.schema == other.schema
            and self.name == other.name
            and self.allowed_values == other.allowed_values
            and self.comment == other.comment
        )


class PolicyReference(object):
    def __init__(self, metadata_query_result: Dict, policy_type: PolicyType):
        # IDEA: use only relevant attributes here and move others to child classes
        self.policy_type = policy_type       
        self.policy_db = metadata_query_result['POLICY_DB']
        self.policy_schema = metadata_query_result['POLICY_SCHEMA']
        self.policy_name = metadata_query_result['POLICY_NAME']
        self.policy_kind = metadata_query_result['POLICY_KIND']
        self.ref_database_name = metadata_query_result['REF_DATABASE_NAME']
        self.ref_schema_name = metadata_query_result['REF_SCHEMA_NAME']
        self.ref_entity_name = metadata_query_result['REF_ENTITY_NAME']
        self.ref_entity_domain = metadata_query_result['REF_ENTITY_DOMAIN']
        self.ref_column_name = metadata_query_result['REF_COLUMN_NAME']
        self.ref_arg_column_names = metadata_query_result['REF_ARG_COLUMN_NAMES']
        self.ref_arg_column_names_dict = json.loads(metadata_query_result["REF_ARG_COLUMN_NAMES"] or "[]")
        self.tag_database = metadata_query_result['TAG_DATABASE']
        self.tag_schema = metadata_query_result['TAG_SCHEMA']
        self.tag_name = metadata_query_result['TAG_NAME']
        self.policy_status = metadata_query_result['POLICY_STATUS']
    
    def __eq__(self, other) -> bool:
        return (
            self.policy_schema == other.policy_schema
            and self.policy_name == other.policy_name
            and self.policy_kind == other.policy_kind
            and self.ref_schema_name == other.ref_schema_name
            and self.ref_entity_name == other.ref_entity_name
            and self.ref_entity_domain == other.ref_entity_domain
            and self.ref_column_name == other.ref_column_name
            and self.ref_arg_column_names == other.ref_arg_column_names
            and self.ref_arg_column_names_dict == other.ref_arg_column_names_dict
            and self.tag_database == other.tag_database
            and self.tag_schema == other.tag_schema
            and self.tag_name == other.tag_name
            and self.policy_status == other.policy_status
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.policy_schema,
                self.policy_name,
                self.policy_kind,
                self.ref_schema_name,
                self.ref_entity_name,
                self.ref_entity_domain,
                self.ref_column_name,
                self.ref_arg_column_names,
                self.tag_database,
                self.tag_schema,
                self.tag_name,
                self.policy_status,
            )
        )

class PolicyReferenceFactory(object):
    @staticmethod
    def factory(metadata_query_result: Dict) -> PolicyReference:
        mapping = {
            "ROW_ACCESS_POLICY": RowAccessPolicyReference,
            "MASKING_POLICY": MaskingPolicyReference,
        }
        return mapping[metadata_query_result["POLICY_KIND"]](metadata_query_result)


class RowAccessPolicyReference(PolicyReference):
    def __init__(self, metadata):
        super().__init__(metadata, PolicyType.ROWACCESS)

    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def ref_arg_columns_string(self):
        "String containing all columns (to be used in ALTER ... ADD POLICY). Example: '(COL1,COL2)'"
        return f"({','.join(self.ref_arg_column_names_dict)})"
    
    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other)
        )

class MaskingPolicyReference(PolicyReference):
    def __init__(self, metadata):
        super().__init__(metadata, PolicyType.MASKING)

    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def conditional_columns_string(self):
        "String containing all conditional columns (to be used in ALTER COLUMN ... ADD POLICY). Example: '(COL1,COL2)'"
        if len(self.ref_arg_column_names_dict) == 0:
            raise ValueError(f"Conditional columns string can only be generated for conditional masking policies. [ '{self.policy_schema}.{self.policy_name}' ] does not appear to be a conditional masking policy.")
        return f"({','.join([self.ref_column_name] + self.ref_arg_column_names_dict)})"
