import copy
import re
import logging
from aceutils.logger import LoggingAdapter
from abc import abstractmethod
from typing import Dict, List, Tuple, Union

import aceutils.misc_utils as misc_utils
import aceutils.string_util as string_util
import aceutils.dict_and_list_util as dict_and_list_util
from acedeploy.core.model_configuration import TableCreateAndInsertOptionWarehouse, ObjectOption
from acedeploy.core.model_database_object import DatabaseObject
from acedeploy.core.model_db_statement import DbStatement, ParametersObjectStatement
from acedeploy.core.model_instance_objects import (
    ColumnInstance,
    ConstraintColumn,
    ConstraintColumnForeignKey,
    InstanceConstraintForeignKey,
    InstanceConstraintPrimaryKey,
    InstanceConstraintUniqueKey,
    InstanceObject,
    InstancePipe,
    InstancePolicy,
    InstanceSchema,
    InstanceSequence,
    InstanceStage,
    InstanceStream,
    InstanceTable,
    InstanceExternalTable,
    InstanceView,
    InstanceFileformat,
    InstanceDynamicTable,
    InstanceNetworkRule,
    InstanceTag,
    PolicyReference,
    RowAccessPolicyReference,
    MaskingPolicyReference,
)
from acedeploy.core.model_solution_entities import SolutionObject
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType, PolicyType
from aceservices.snowflake_service import SnowClient
from acedeploy.services.policy_service import PolicyService, PolicyAssignmentObjectTypes
from acedeploy.services.policy_service import get_policy_assignments_info_from_object,handle_policy_assignments_for_object_creation, handle_policy_assignments_for_alter_view_action, prepare_view_statement_comparison_independent_of_columns_string, handle_policy_assignments_for_alter_table_add_column_action

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)

class DbObjectAction(DatabaseObject):
    """
    Collects information about a database object and the action
    that will be applied to it (CREATE, ALTER, DROP).
    This object can create the statement object (DbStatement)
    that is used to perform the desired action.
    This is necessary since some actions cannot be performed using
    only the file content of the SQL DDL (e.g. ALTER TABLE statements)
    """

    def __init__(
        self,
        schema: str,
        name: str,
        object_type: DbObjectType,
        action: DbActionType,
        current_instance: InstanceObject = None,
        desired_instance: InstanceObject = None,
        file_content: str = None,
    ):
        super().__init__(schema, name, object_type)
        self.action = action
        self.current_instance = current_instance
        self.desired_instance = desired_instance
        self.file_content = file_content

        self.object_options: ObjectOption = self._get_object_options(
            current_instance=current_instance,
            desired_instance=desired_instance,
        )

        self.policy_assignments_info_from_object = {}

    @staticmethod
    def _get_object_options(
        current_instance: InstanceObject,
        desired_instance: InstanceObject,
    ) -> ObjectOption:
        if current_instance is None and desired_instance is None:
            return None
        if current_instance is not None:
            if desired_instance is not None:
                if current_instance.object_options != desired_instance.object_options:
                    raise ValueError("Object options for current_instance and desired_instance do not match")
            return current_instance.object_options
        return desired_instance.object_options

    @staticmethod
    def factory(
        schema: str,
        name: str,
        object_type: DbObjectType,
        action: DbActionType,
        **kwargs,
    ) -> "DbObjectAction":
        """
        Generate and return a DbObjectAction for the given parameters.
        """
        mapping = {
            DbObjectType.VIEW: ViewAction,
            DbObjectType.MATERIALIZEDVIEW: MaterializedViewAction,
            DbObjectType.FILEFORMAT: FileformatAction,
            DbObjectType.STAGE: StageAction,
            DbObjectType.FUNCTION: FunctionAction,
            DbObjectType.PROCEDURE: ProcedureAction,
            DbObjectType.TABLE: TableAction,
            DbObjectType.EXTERNALTABLE: ExternalTableAction,
            DbObjectType.SCHEMA: SchemaAction,
            DbObjectType.STREAM: StreamAction,
            DbObjectType.TASK: TaskAction,
            DbObjectType.PIPE: PipeAction,
            DbObjectType.SEQUENCE: SequenceAction,
            DbObjectType.MASKINGPOLICY: MaskingPolicyAction,
            DbObjectType.ROWACCESSPOLICY: RowAccessPolicyAction,
            DbObjectType.DYNAMICTABLE: DynamicTableAction,
            DbObjectType.NETWORKRULE: NetworkRuleAction,
            DbObjectType.TAG: TagAction,
        }
        return mapping[object_type](schema=schema, name=name, action=action, **kwargs)

    @staticmethod
    def factory_from_solution_object(
        solution_object: SolutionObject, action: DbActionType, desired_instance: InstanceObject = None, **kwargs
    ) -> "DbObjectAction":
        """
        Generate and return a DbObjectAction for the given a SolutionObject and DbActionType.
        """
        if (action == DbActionType.ALTER) and (
            solution_object.object_type == DbObjectType.TABLE
        ):
            raise ValueError(
                f"Action of type [ '{action}' ] and type [ '{solution_object.object_type}' ] can not be generated using this function. Use DbObjectAction.factory() instead."
            )

        return DbObjectAction.factory(
            name=solution_object.name,
            schema=solution_object.schema,
            file_content=solution_object.content,
            desired_instance=desired_instance,
            object_type=solution_object.object_type,
            parameters=getattr(solution_object, "parameters", None),
            action=action,
            **kwargs,
        )

    @staticmethod
    def factory_from_instance_object(
        instance_object: InstanceObject, action: DbActionType, **kwargs
    ) -> "DbObjectAction":
        """
        Generate and return a DbObjectAction for the given a InstanceObject and DbActionType.
        """
        if action != DbActionType.DROP and action != DbActionType.DROPOVERLOADED:
            raise ValueError(
                f"Action of type [ '{action}' ] can not be generated using this function. Use DbObjectAction.factory() instead."
            )
        return DbObjectAction.factory(
            name=instance_object.name,
            schema=instance_object.schema,
            object_type=instance_object.object_type,
            parameters=getattr(instance_object, "parameters", None),
            action=action,
            **kwargs,
        )

    @staticmethod
    def factory_from_instance_objects(
        current_instance: InstanceObject,
        desired_instance: InstanceObject,
        action: DbActionType,
        **kwargs,
    ) -> "DbObjectAction":
        """
        Generate and return a DbObjectAction for the given a current InstanceObject, a desired InstanceObject and DbActionType.
        """
        if action != DbActionType.ALTER:
            raise ValueError(
                f"Action of type [ '{action}' ] can not be generated using this function. Use DbObjectAction.factory() instead."
            )
        if str(current_instance) != str(desired_instance):
            raise ValueError(
                f"Name or type of current and desired instance do not match ( current: ['{str(current_instance)}'], desired: ['{str(desired_instance)}'] )"
            )
        return DbObjectAction.factory(
            name=current_instance.name,
            schema=current_instance.schema,
            object_type=current_instance.object_type,
            parameters=getattr(current_instance, "parameters", None),
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            **kwargs,
        )

    @abstractmethod
    def _generate_statement(self, **kwargs):
        pass

    def generate_statement_object(self, snow_client_meta: SnowClient = None, snow_client_target: SnowClient = None, policy_service: PolicyService = None) -> DbStatement:
        """
            Generate a DbStatement object, which contains the SQL code required
            to perform the desired action on the db object.
        Args:
            snow_client_meta: SnowClient - Connection to snowflake database containing the desired configuration (meta db)
            snow_client_target: SnowClient - Connection to snowflake database containing the target configuration (meta db)
        Returns:
            DbStatement - containing the SQL statement(s) to achieve the desired result.
        """

        if policy_service and policy_service.policy_assignments_info:
            self.policy_assignments_info_from_object = get_policy_assignments_info_from_object(
                object_schema=self.schema,
                object_name=self.name,
                object_type=self.object_type,
                action_type=self.action,
                policy_assignments_info=policy_service.policy_assignments_info)

        db_statement = DbStatement(
            schema=self.schema,
            name=self.name,
            statement=self._generate_statement(snow_client_meta=snow_client_meta, snow_client_target=snow_client_target),
            object_type=self.object_type,
        )

        if (
            policy_service
            and policy_service.policy_assignments_info
            and db_statement.object_type.value in policy_service.policy_assignments_info
            and (not db_statement.statement or "NOT_HANDLED" in self.policy_assignments_info_from_object)
        ):
            log.debug(f"++++++++++++++++++++ CASE 0 ++++++++++++++++++++++ {db_statement.full_name}")
            policy_service.policy_assignments_info[db_statement.object_type.value].pop(db_statement.full_name, None)
            log.debug(f"++++++++++++++++++++ policy_service.policy_assignments_info ++++++++++++++++++++++ {policy_service.policy_assignments_info}")

        return db_statement

    @staticmethod
    def _alter_statement_error_summary(
        updated_instance: InstanceObject,
        desired_instance: InstanceObject,
        properties_to_skip: List[str] = ("database_name",),
    ) -> str:
        """
        Given two instance objects, return a summary of all properties which differ.
        Optionally accepts a list of properties to skip.
        """
        try:
            messages = []
            updated_dict = updated_instance.__dict__
            desired_dict = desired_instance.__dict__
            for key in updated_dict:
                if not key.startswith("_") and key not in properties_to_skip:
                    if updated_dict[key] != desired_dict[key]:
                        messages.append(
                            f"property [ '{key}' ]: current value [ '{updated_dict[key]}' ], desired value [ '{desired_dict[key]}' ]"
                        )
            return "; ".join(messages)
        except:
            return "Could not determine differences."


    def _generate_settag_statement(self) -> str: # TODO: write tests for this function
        """
            Function to generate set-tag statements from database object instances to align the current state of a an database objects to the desired state.
        """
        object_domain=DbObjectType.get_object_domain_from_object_type_for_alter_tags(self.object_type)

        settag_statement=""
        set_tags=[]
        for tag, tag_value in self.desired_instance.tags.items():
            if not hasattr(self.current_instance, "tags") or tag.upper() not in {tag.upper() for tag in self.current_instance.tags} or tag_value != self.current_instance.tags[tag.upper()]:
                set_tags.append(f"{tag} = '{tag_value}'")
        set_tags = ", ".join(set_tags)
        if set_tags:
            settag_statement = f"ALTER {object_domain} {self.desired_instance.full_name} SET TAG {set_tags}"

        return settag_statement

    def _generate_unsettag_statement(self) -> str: # TODO: write tests for this function
        """
            Function to generate unset-tag statements from database object instances to align the current state of a an database objects to the desired state.
        """
        object_domain=DbObjectType.get_object_domain_from_object_type_for_alter_tags(self.object_type)

        unsettag_statement=''
        unset_tags=[]
        for tag, tag_value in self.current_instance.tags.items():
            if tag.upper() not in {tag.upper() for tag in self.desired_instance.tags} or not tag_value:
                unset_tags.append(tag)
        unset_tags = ", ".join(unset_tags)
        if unset_tags:
            unsettag_statement = f"ALTER {object_domain} {self.desired_instance.full_name} UNSET TAG {unset_tags}"

        return unsettag_statement

    @staticmethod
    def _generate_column_settag_statement(current_column: ColumnInstance, desired_column: ColumnInstance) -> str: # TODO: write tests for this function
        """
            Function to generate set-tag statements from column instances to align the current state of a an column to the desired state.
        """
        settag_statement=""
        set_tags=[]
        for tag, tag_value in desired_column.tags.items():
            if not hasattr(current_column, "tags") or tag.upper() not in {tag.upper() for tag in current_column.tags} or tag_value != current_column.tags[tag.upper()]:
                set_tags.append(f"{tag} = '{tag_value}'")
        set_tags = ", ".join(set_tags)
        if set_tags:
            settag_statement = f"ALTER COLUMN {current_column.column_name} SET TAG {set_tags}"

        return settag_statement

    @staticmethod
    def _generate_column_unsettag_statement(current_column: ColumnInstance, desired_column: ColumnInstance) -> str: # TODO: write tests for this function
        """
            Function to generate unset-tag statements from column instances to align the current state of a an column to the desired state.
        """
        unsettag_statement=''
        unset_tags=[]
        for tag, tag_value in current_column.tags.items():
            if tag.upper() not in {tag.upper() for tag in desired_column.tags} or not tag_value:
                unset_tags.append(tag)
        unset_tags = ", ".join(unset_tags)
        if unset_tags:
            unsettag_statement = f"ALTER COLUMN {current_column.column_name} UNSET TAG {unset_tags}"

        return unsettag_statement


class ViewAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceView = None,
        desired_instance: InstanceView = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.VIEW,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return self._generate_add_statement(self.file_content, self.desired_instance, self.policy_assignments_info_from_object)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance, self.policy_assignments_info_from_object
            )
        elif self.action == DbActionType.DROP:
            return f"DROP VIEW IF EXISTS {self.full_name}"

    def __str__(self):
        return f"ViewAction: {self.id}"

    def __repr__(self):
        return f"ViewAction: {self.id}"

    @staticmethod
    def _generate_add_statement(
        file_content: str, desired_instance: InstanceView, policy_assignments_info_from_object: dict= {}
    ) -> str:
        """
        Generate sql statement(s) for creating a new view based on the desired state. Handles policy assignments.
        """
        statements = []
        statements.append( string_util.remove_create_or_replace(file_content) )

        if policy_assignments_info_from_object:
            view_statement=statements[0]
            statements = handle_policy_assignments_for_object_creation(
                object_type= PolicyAssignmentObjectTypes.VIEW,
                object_statement=view_statement,
                columns=desired_instance.table_columns,
                policy_assignments_of_object=policy_assignments_info_from_object["assignments"]
            )

        return " ".join(statements)


    @staticmethod
    def _generate_alter_statement(
        current_instance: InstanceView, desired_instance: InstanceView, policy_assignments_info_from_object: dict= {}
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a stream to the desired state.
        """
        statements = []
        policy_statement_appended = False

        view_statement = string_util.add_create_or_replace(desired_instance.view_definition)

        view_statement = string_util.remove_comment(view_statement)

        statements.append(string_util.add_copy_grants(view_statement))

        (
            current_instance_view_definition,
            current_instance_view_definition_with_columns_string,
            current_instance_view_definition_without_columns_string
        ) = prepare_view_statement_comparison_independent_of_columns_string(
            view_definition = current_instance.view_definition,
            columns = current_instance.table_columns,
            comment = current_instance.comment,
            policy_assignments_info_from_object = policy_assignments_info_from_object
        )

        view_statement_with_policies = 'view statement with policies not defined'
        view_statement_with_policies_alternative = 'view statement with policies alternative not defined'
        view_statement_with_policies_without_db_reference = 'view statement with policies without database reference not defined'
        view_statement_with_policies_without_db_reference_alternative = 'view statement with policies alternative without database reference  not defined'

        if policy_assignments_info_from_object:

            (
                statements,
                view_statement_with_policies,
                view_statement_with_policies_alternative,
                view_statement_with_policies_without_db_reference,
                view_statement_with_policies_without_db_reference_alternative
            ) = handle_policy_assignments_for_alter_view_action(
                view_statement = view_statement,
                columns = desired_instance.table_columns,
                policy_assignments_info_from_object = policy_assignments_info_from_object
            )

        else:
            desired_column_names = [c.column_name for c in desired_instance.table_columns]
            for policy in current_instance.applied_policies_legacy:
                if policy.policy_type == PolicyType.ROWACCESS:
                    if not set(policy.ref_arg_column_names).issubset(
                        set(desired_column_names)
                    ):
                        raise ValueError(
                            f"UNABLE to apply ROW ACCESS POLICY [ '{policy.full_name_quoted}' ] on VIEW [ '{current_instance.full_name}' ]: After deployment, the view will have the columns [ '{desired_column_names}' ], but policy must be applied on columns [ '{policy.ref_arg_column_names}' ]"
                        )
                    policy_statement = f"ALTER VIEW {current_instance.full_name} ADD ROW ACCESS POLICY {policy.full_name_quoted} ON {policy.column_list_string};"
                if policy.policy_type == PolicyType.MASKING:
                    if not policy.ref_column_name in set(desired_column_names):
                        raise ValueError(
                            f"UNABLE to apply MASKING POLICY [ '{policy.full_name_quoted}' ] on VIEW [ '{current_instance.full_name}' ]: After deployment, the view will have the columns [ '{desired_column_names}' ], but policy must be applied on column [ '{policy.ref_column_name}' ]"
                        )
                    policy_statement = f"ALTER VIEW {current_instance.full_name} ALTER COLUMN {policy.ref_column_name} SET MASKING POLICY {policy.full_name_quoted};"

                statements.append(policy_statement)
                policy_statement_appended=True


        view_statement_equals_current_view_definition = ViewAction.compare_view_statement_with_current_instance(
            current_instance.full_name,
            policy_assignments_info_from_object,
            view_statement,
            current_instance_view_definition,
            current_instance_view_definition_with_columns_string,
            current_instance_view_definition_without_columns_string,
            view_statement_with_policies,
            view_statement_with_policies_alternative,
            view_statement_with_policies_without_db_reference,
            view_statement_with_policies_without_db_reference_alternative
        )

        current_instance_ = copy.deepcopy(current_instance)
        desired_instance_ = copy.deepcopy(desired_instance)
        desired_instance_.view_definition = 'CREATE VIEW DUMMY.DUMMY'
        current_instance_.view_definition = 'CREATE VIEW DUMMY.DUMMY'

        # No alter statements should be executed when the current_state and the desired state are the same and the view definitions only differ in whitespaces or case
        if (
            view_statement_equals_current_view_definition
            and current_instance_ == desired_instance_
            and not policy_statement_appended
        ):
            statements = []
            log.info(f"++++++++++++++++++++ ALTER VIEW ACTION ignored since current instance equals desired instance for: {current_instance.full_name}")

        return " ".join(statements)


    @staticmethod
    def compare_view_statement_with_current_instance(view_identifier, policy_assignments_info_from_object,view_statement, current_instance_view_definition, current_instance_view_definition_with_columns_string, current_instance_view_definition_without_columns_string, view_statement_with_policies, view_statement_with_policies_alternative, view_statement_with_policies_without_db_reference, view_statement_with_policies_without_db_reference_alternative):
        if policy_assignments_info_from_object:
            view_statement_equals_current_view_definition = (
                    string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition_with_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition_without_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies,current_instance_view_definition)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies,current_instance_view_definition_with_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies,current_instance_view_definition_without_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_alternative,current_instance_view_definition)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_alternative,current_instance_view_definition_with_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_alternative,current_instance_view_definition_without_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference,current_instance_view_definition)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference,current_instance_view_definition_with_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference,current_instance_view_definition_without_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference_alternative,current_instance_view_definition)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference_alternative,current_instance_view_definition_with_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference_alternative,current_instance_view_definition_without_columns_string)
                )
        else:
            #TODO similar to "current_instance_view_definition_without_columns_string" there should be a comparison with "current_instance_view_definition_without_with_tag" where the definition of tags on the view is ignored.
            # -> tags are part of the comparison between current_instance_ and desired_instance_
            view_statement_equals_current_view_definition = (
                    string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition_with_columns_string)
                    or string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition_without_columns_string)
            )

        if not view_statement_equals_current_view_definition:
            log.debug(f"++++++++++++++++++++ ALTER VIEW ACTION SUMMARY: {view_identifier} ++++++++++++++++++++++ ")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition_with_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement,current_instance_view_definition_without_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies,current_instance_view_definition)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies,current_instance_view_definition_with_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies,current_instance_view_definition_without_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_alternative,current_instance_view_definition)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_alternative,current_instance_view_definition_with_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_alternative,current_instance_view_definition_without_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference,current_instance_view_definition)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference,current_instance_view_definition_with_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference,current_instance_view_definition_without_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference_alternative,current_instance_view_definition)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference_alternative,current_instance_view_definition_with_columns_string)}")
            log.debug(f"{string_util.compare_strings_ignore_whitespace_and_case(view_statement_with_policies_without_db_reference_alternative,current_instance_view_definition_without_columns_string)}")
            log.debug(f"current_instance_view_definition: {current_instance_view_definition}")
            log.debug(f"current_instance_view_definition_with_columns_string: {current_instance_view_definition_with_columns_string}")
            log.debug(f"current_instance_view_definition_without_columns_string: {current_instance_view_definition_without_columns_string}")
            log.debug(f"view_statement: {view_statement}")
            log.debug(f"view_statement_with_policies: {view_statement_with_policies}")
            log.debug(f"view_statement_with_policies_alternative: {view_statement_with_policies_alternative}")
            log.debug(f"view_statement_with_policies_without_db_reference: {view_statement_with_policies_without_db_reference}")
            log.debug(f"view_statement_with_policies_without_db_reference_alternative: {view_statement_with_policies_without_db_reference_alternative}")
            log.debug(f"----------------------------------------------------------------------------")

        return view_statement_equals_current_view_definition


class MaterializedViewAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.MATERIALIZEDVIEW,
            action=action,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return string_util.add_create_or_replace(self.file_content)
        elif self.action == DbActionType.DROP:
            return f"DROP MATERIALIZED VIEW IF EXISTS {self.full_name}"

    def __str__(self):
        return f"MaterializedViewAction: {self.id}"

    def __repr__(self):
        return f"MaterializedViewAction: {self.id}"


class FileformatAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceFileformat = None,
        desired_instance: InstanceFileformat = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.FILEFORMAT,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            return f"DROP FILE FORMAT IF EXISTS {self.full_name}"

    def __str__(self):
        return f"FileformatAction: {self.id}"

    def __repr__(self):
        return f"FileformatAction: {self.id}"

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstanceFileformat, desired_instance: InstanceFileformat
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a stream to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        if updated_instance.file_format_type != desired_instance.file_format_type:
            raise ValueError(
                f"Required ALTER FILE FORMAT is not supported for {current_instance.full_name}: It is not possible to change the TYPE of a file format. (Consider replacing the existing file format using a predeployment script.)"
            )
            # TODO: might want to use a custom error type here

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER FILE FORMAT {current_instance.full_name} SET COMMENT = '';"
                )  # FILE FORMATS do not have UNSET COMMENT command
            else:
                comment = string_util.escape_string_for_snowflake(
                    desired_instance.comment
                )
                statements.append(
                    f"ALTER FILE FORMAT {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # format_options
        no_alter_list = ["VALIDATE_UTF8"]
        for prop, desired_value in desired_instance.format_options.items():
            if prop in no_alter_list:
                continue
            current_value = current_instance.format_options.get(prop, None)
            if current_value != desired_value:
                desired_value_formatted = (
                    string_util.convert_python_variable_to_snowflake_value(
                        desired_value
                    )
                )
                statements.append(
                    f"ALTER FILE FORMAT {current_instance.full_name} SET {prop} = {desired_value_formatted};"
                )
                updated_instance.format_options[prop] = desired_value
                # TODO: write tests for this part

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER FILE FORMAT is not supported for {current_instance.full_name} (for {property_error_message}), the framework only supports changes to COMMENT"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


class StageAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceStage = None,
        desired_instance: InstanceStage = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.STAGE,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            return f"DROP STAGE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"StageAction: {self.id}"

    def __repr__(self):
        return f"StageAction: {self.id}"

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstanceStage, desired_instance: InstanceStage
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a stream to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER STAGE {current_instance.full_name} SET COMMENT = '';"
                )  # STAGES do not have UNSET COMMENT command
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER STAGE {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # # stage_location # TODO: this part is commented out because it is currently untested
        # if updated_instance.stage_location != desired_instance.stage_location:
        #     # URL
        #     url = desired_instance.stage_location.get("URL", None)
        #     if url is not None:
        #         statements.append(
        #             f"ALTER STAGE {current_instance.full_name} SET URL = '{url}';"
        #         )
        #         updated_instance.stage_location["URL"] = desired_instance.stage_location["URL"]
        #     # TODO: implement other alter stage location statements

        # TODO: implement other alter statements

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER STAGE is not supported for {current_instance.full_name} (for {property_error_message}), the framework only supports changes to COMMENT"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


class ExternalTableAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceExternalTable = None,
        desired_instance: InstanceExternalTable = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.EXTERNALTABLE,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return string_util.add_create_or_replace(self.file_content)
        elif self.action == DbActionType.DROP:
            return f"DROP EXTERNAL TABLE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"ExternalTableAction: {self.id}"

    def __repr__(self):
        return f"ExternalTableAction: {self.id}"


class StreamAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceStream = None,
        desired_instance: InstanceStream = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.STREAM,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            return f"DROP STREAM IF EXISTS {self.full_name}"

    def __str__(self):
        return f"StreamAction: {self.id}"

    def __repr__(self):
        return f"StreamAction: {self.id}"

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstanceStream, desired_instance: InstanceStream
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a stream to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER STREAM {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER STREAM {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER STREAM is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-stream.html"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


class TaskAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        state_before_deployment: str = "unknown",
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.TASK,
            action=action,
            file_content=file_content,
        )
        self.state_before_deployment = state_before_deployment

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return string_util.add_create_or_replace(self.file_content)
        elif self.action == DbActionType.DROP:
            return f"DROP TASK IF EXISTS {self.full_name}"

    def __str__(self):
        return f"TaskAction: {self.id}"

    def __repr__(self):
        return f"TaskAction: {self.id}"

    def generate_resume_statement(self):
        if self.state_before_deployment == "started":
            return f"ALTER TASK {self.full_name} RESUME"
        else:
            return None


class PipeAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstancePipe = None,
        desired_instance: InstancePipe = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.PIPE,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance, self.file_content
            )
        elif self.action == DbActionType.DROP:
            return f"DROP PIPE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"PipeAction: {self.id}"

    def __repr__(self):
        return f"PipeAction: {self.id}"

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstancePipe,
        desired_instance: InstancePipe,
        file_content: str,
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a pipe to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER PIPE {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER PIPE {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # can object be changed with ALTER or do we need CREATE OR REPLACE?
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            # if we CREATE OR REPLACE, need to (https://docs.snowflake.com/en/user-guide/data-load-snowpipe-manage.html#recreating-pipes-for-automated-data-loads):
            # 1) pause the pipe (done in deploy_service)
            # 2) verify that the pending file count is 0 (done in deploy_service)
            # 3) CREATE OR REPLACE PIPE
            # 4) pause the pipe, if it was not running before 1)
            statements = []
            statements.append(string_util.add_create_or_replace(file_content))
            if current_instance.execution_state != "RUNNING":
                statements.append(
                    f"ALTER PIPE {current_instance.full_name} SET PIPE_EXECUTION_PAUSED = TRUE;"
                )
            return " ".join(statements)


class SequenceAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceSequence = None,
        desired_instance: InstanceSequence = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.SEQUENCE,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            return f"DROP SEQUENCE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"SequenceAction: {self.id}"

    def __repr__(self):
        return f"SequenceAction: {self.id}"

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstanceSequence, desired_instance: InstanceSequence
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a sequence to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER SEQUENCE {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER SEQUENCE {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # increment
        if updated_instance.increment != desired_instance.increment:
            increment = desired_instance.increment
            statements.append(
                f"ALTER SEQUENCE {current_instance.full_name} SET INCREMENT {increment};"
            )
            updated_instance.increment = desired_instance.increment

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER SEQUENCE is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-sequence.html"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


class ParametersObjectAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        object_type: DbObjectType,
        action: DbActionType,
        parameters: List[str],
        file_content: str = None,
    ):
        """
        parameters: either a list of parameter types, e.g. ['INT', 'VARCHAR'], or a string of parameters, e.g. '(INT, VARCHAR)'
        """
        super().__init__(
            schema=schema,
            name=name,
            object_type=object_type,
            action=action,
            file_content=file_content,
        )
        self.parameters = [
            misc_utils.map_datatype_name_to_default(p) for p in parameters
        ]

    def generate_statement_object(self, **kwargs) -> DbStatement:
        """
            Generate a DbStatement object, which contains the SQL code required
            to perform the desired action on the db object.
        Args:
            snow_client: SnowClient - Connection to snowflake database containing the desired configuration (meta db)
        Returns:
            DbStatement - containing the SQL statement(s) to achieve the desired result.
        """
        return ParametersObjectStatement(
            schema=self.schema,
            name=self.name,
            statement=self._generate_statement(**kwargs),
            object_type=self.object_type,
            parameters=self.parameters,
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


class FunctionAction(ParametersObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        parameters: Union[str, List[str]],
        file_content: str = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.FUNCTION,
            action=action,
            parameters=parameters,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return string_util.add_create_or_replace(self.file_content)
        elif self.action == DbActionType.DROP:
            return f"DROP FUNCTION IF EXISTS {self.full_name}"
        elif self.action == DbActionType.DROPOVERLOADED:
            return f"DROP FUNCTION IF EXISTS {self.full_name}"

    def __str__(self):
        return f"FunctionAction: {self.id}"

    def __repr__(self):
        return f"FunctionAction: {self.id}"


class ProcedureAction(ParametersObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        parameters: Union[str, List[str]],
        file_content: str = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.PROCEDURE,
            action=action,
            parameters=parameters,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return string_util.add_create_or_replace(self.file_content)
        elif self.action == DbActionType.DROP:
            return f"DROP PROCEDURE IF EXISTS {self.full_name}"
        elif self.action == DbActionType.DROPOVERLOADED:
            return f"DROP PROCEDURE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"ProcedureAction: {self.id}"

    def __repr__(self):
        return f"ProcedureAction: {self.id}"


class PolicyAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        object_type: DbObjectType,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstancePolicy = None,
        desired_instance: InstancePolicy = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=object_type,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            type_identifier = DbObjectType.get_sql_object_type(self.object_type)
            return f"DROP {type_identifier} IF EXISTS {self.full_name}"

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstancePolicy, desired_instance: InstancePolicy
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a sequence to the desired state.
        """
        type_identifier = DbObjectType.get_sql_object_type(current_instance.object_type)

        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER {type_identifier} {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER {type_identifier} {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # body
        if updated_instance.body != desired_instance.body:
            body = desired_instance.body
            statements.append(
                f"ALTER {type_identifier} {current_instance.full_name} SET BODY -> {body};"
            )
            updated_instance.body = desired_instance.body

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER {type_identifier} is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-masking-policy.html or https://docs.snowflake.com/en/sql-reference/sql/alter-row-access-policy.html"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


class MaskingPolicyAction(PolicyAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: "MaskingPolicyAction" = None,
        desired_instance: "MaskingPolicyAction" = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.MASKINGPOLICY,
            action=action,
            file_content=file_content,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )

    def __str__(self):
        return f"MaskingPolicyAction: {self.id}"

    def __repr__(self):
        return f"MaskingPolicyAction: {self.id}"


class RowAccessPolicyAction(PolicyAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: "RowAccessPolicyAction" = None,
        desired_instance: "RowAccessPolicyAction" = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.ROWACCESSPOLICY,
            action=action,
            file_content=file_content,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )

    def __str__(self):
        return f"RowAccessPolicyAction: {self.id}"

    def __repr__(self):
        return f"RowAccessPolicyAction: {self.id}"


class SchemaAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceSchema = None,
        desired_instance: InstanceSchema = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.SCHEMA,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )
        if schema != name:
            raise ValueError("schema and name must be identical")
        self.schema = schema
        self.name = name
        self.file_content = file_content
        self.action = action
        self.object_type = DbObjectType.SCHEMA

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return self.file_content
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            return f"DROP SCHEMA IF EXISTS {self.full_name}"

    def __str__(self):
        return f"SchemaAction: {self.id}"

    def __repr__(self):
        return f"SchemaAction: {self.id}"

    @property
    def id(self):
        return f"{self.object_type} {self.schema.upper()}"

    @property
    def full_name(self):
        return self.schema.upper()

    @staticmethod
    def _generate_alter_statement(
        current_instance: InstanceSchema, desired_instance: InstanceSchema
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a schema to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER SCHEMA {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER SCHEMA {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # data retention time
        if (updated_instance.retention_time != desired_instance.retention_time) or (
            updated_instance.database_retention_time
            != desired_instance.database_retention_time
        ):
            if (
                desired_instance.retention_time
                == desired_instance.database_retention_time
            ):
                statements.append(
                    f"ALTER SCHEMA {current_instance.full_name} UNSET DATA_RETENTION_TIME_IN_DAYS;"
                )
            else:
                statements.append(
                    f"ALTER SCHEMA {current_instance.full_name} SET DATA_RETENTION_TIME_IN_DAYS = {desired_instance.retention_time};"
                )
            updated_instance.retention_time = desired_instance.retention_time
            updated_instance.database_retention_time = (
                desired_instance.database_retention_time
            )

        # managed access
        # if updated_instance.is_managed_access != desired_instance.is_managed_access:
        #     if desired_instance.is_managed_access == "YES":
        #         statements.append(
        #             f"ALTER SCHEMA {current_instance.full_name} ENABLE MANAGED ACCESS;"
        #         )
        #     if desired_instance.is_managed_access == "NO":
        #         statements.append(
        #             f"ALTER SCHEMA {current_instance.full_name} DISABLE MANAGED ACCESS;"
        #         )
        #     updated_instance.is_managed_access = desired_instance.is_managed_access

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER SCHEMA is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-schema.html"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


class TableAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        current_instance: InstanceTable = None,
        desired_instance: InstanceTable = None,
        file_content: str = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.TABLE,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )
        if (self.desired_instance is not None) and (self.current_instance is not None):
            # these values are created here, so they can be used by other functions (e.g. to check for dataloss)
            (
                self.columns_to_add,
                self.columns_to_drop,
                self.columns_to_alter,
                self.columns_added_in_between,
            ) = self._get_column_diff()

    def _generate_statement(self, snow_client_meta: SnowClient = None, snow_client_target: SnowClient = None):
        if self.action == DbActionType.ADD:
            return self._generate_add_statement(self.file_content, self.desired_instance, self.policy_assignments_info_from_object)
        elif self.action == DbActionType.ALTER:
            if (not snow_client_meta) or (not snow_client_target):
                raise ValueError(
                    "SnowClients must be provided for TABLE ALTER statement generation"
                )
            if self._check_create_and_insert_required():
                return self._generate_create_and_insert_statement(snow_client_meta, snow_client_target)
            else:
                try:
                    return self._generate_alter_statement(snow_client_meta)
                except Exception as e:
                    if self.object_options.alterOptions.createAndInsert.useAsFallback:
                        log.info(f"FAILED to generate alter statements for TABLE [ '{self.full_name}' ]. Fallback method CREATE AND INSERT will be used.")
                        log.info(f"Original error message: {str(e)}")
                        return self._generate_create_and_insert_statement(snow_client_meta, snow_client_target)
                    else:
                        raise e
        elif self.action == DbActionType.DROP:
            return f"DROP TABLE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"TableAction: {self.id}"

    def __repr__(self):
        return f"TableAction: {self.id}"

    @staticmethod
    def _generate_add_statement(
        file_content: str, desired_instance: InstanceTable, policy_assignments_info_from_object: dict= {}
    ) -> str:
        """
        Generate sql statement(s) for creating a new table based on the desired state. Handles policy assignments.
        """
        statements = []
        statements.append(file_content)

        if policy_assignments_info_from_object:
            table_statement=statements[0]
            statements = handle_policy_assignments_for_object_creation(
                object_type= PolicyAssignmentObjectTypes.TABLE,
                object_statement=table_statement,
                columns=desired_instance.table_columns,
                policy_assignments_of_object=policy_assignments_info_from_object["assignments"]
            )

        return " ".join(statements)


    def _check_create_and_insert_required(self) -> bool:
        """
        Using the config, determine if the desired state can only be reached using
        create and insert.
        """
        result = False

        if (
            self.columns_added_in_between and
            self.object_options.alterOptions.keepColumnOrder
        ):
            log.info(f"TABLE [ '{self.full_name}' ] must be updated using createAndInsert (adds columns within the column list and TABLE.alterOptions.keepColumnOrder is true)")
            result = True

        return result


    def _generate_create_and_insert_statement(self, snow_client_meta: SnowClient, snow_client_target: SnowClient) -> str:
        """
        Generate sql statements to create the new (desired) table and insert the data
        from the old (current) table.
        """
        if not self.object_options.alterOptions.createAndInsert.enabled:
            raise ValueError("The option 'TABLE.alterOptions.createAndInsert.enabled' is not true.")

        statements = []

        temp_name = self.full_name + '_' + string_util.get_now_string()

        statements.append(
            self._generate_create_table_statement(
                snow_client_meta=snow_client_meta,
                snow_client_target=snow_client_target,
                old_table_name=self.full_name,
                new_table_name=temp_name,
                desired_columns=self.desired_instance.table_columns,
                option_update_autoincrement=self.object_options.alterOptions.createAndInsert.updateAutoincrement,
            )
        )

        statements.append(
            self._generate_use_warehouse_statement(
                warehouse_settings=self.object_options.alterOptions.createAndInsert.warehouses,
                table_bytes=self.current_instance.bytes,
                default_warehouse=snow_client_target._config.warehouse,
            )
        )

        statements.append(
            self._generate_insert_statement(
                current_cols=[c.column_name for c in self.current_instance.table_columns],
                desired_cols=[c.column_name for c in self.desired_instance.table_columns],
                source_table=self.full_name,
                target_table=temp_name,
            )
        )

        statements.append(f"ALTER TABLE {self.full_name} SWAP WITH {temp_name}")

        if self.object_options.alterOptions.createAndInsert.dropOldTable:
            statements.append(f"DROP TABLE {temp_name}")

        statements.append(
            self._generate_use_warehouse_statement(
                warehouse_settings=[],
                table_bytes=0,
                default_warehouse=snow_client_target._config.warehouse,
            )
        )

        return "; ".join(statements)


    @staticmethod
    def _generate_use_warehouse_statement(warehouse_settings: List[TableCreateAndInsertOptionWarehouse], table_bytes: int, default_warehouse: str) -> str:
        matching_warehouses = [wh for wh in warehouse_settings if wh.byteThreshold <= table_bytes]
        if not matching_warehouses:
            return f"USE WAREHOUSE {default_warehouse}"
        min_warehouse = max(matching_warehouses, key=lambda wh: wh.byteThreshold)
        return f"USE WAREHOUSE {min_warehouse.name}"


    @staticmethod
    def _generate_create_table_statement(snow_client_meta: SnowClient, snow_client_target: SnowClient, old_table_name: str, new_table_name: str, desired_columns: List[str], option_update_autoincrement: bool,) -> str:
        ddl = TableAction._get_table_ddl(snow_client_meta, old_table_name)
        ddl_updated_name = TableAction._update_table_name(ddl=ddl,new_table_name=new_table_name)
        ddl_without_mps = TableAction._remove_masking_policy_db_references(ddl=ddl_updated_name)
        ddl_without_raps = TableAction._remove_row_access_policy_db_references(ddl=ddl_without_mps)
        ddl_updated = ddl_without_raps.rstrip().rstrip(";")
        if not option_update_autoincrement:
            return ddl_updated
        else:
            return TableAction._update_ddl_autoincrement(
                ddl=ddl_updated,
                old_table_name=old_table_name,
                desired_columns=desired_columns,
                snow_client_target=snow_client_target,
            )


    @staticmethod
    def _get_table_ddl(snow_client_meta: SnowClient, table_name: str) -> str:
        query = f"SELECT GET_DDL('TABLE' , '{table_name}') AS COL_DEF"
        return snow_client_meta.execute_query(query)[0]["COL_DEF"]


    @staticmethod
    def _update_table_name(ddl: str, new_table_name: str) -> str:
        """
        Given the output of GET_DDL(), change the name of the table.

        Note that the input ddl should not contain the schema name.
        """
        ddl_with_new_name = re.sub(
            pattern="create\\s(or\\sreplace\\s)?table\\s\\w+\\s",
            repl=f"CREATE TABLE {new_table_name} ",
            string=ddl,
            count=1,
            flags=re.IGNORECASE,
        )
        if ddl_with_new_name == ddl:
            raise ValueError(f"The ddl for TABLE [ '{new_table_name}' ] could not be updated successfully")
        return ddl_with_new_name


    @staticmethod
    def _remove_masking_policy_db_references(ddl: str) -> str:
        """
        Remove the database references for masking policies in the ddl.
        """
        return re.sub(
            pattern="WITH MASKING POLICY \w+\.(\w+\.\w+)",
            repl="WITH MASKING POLICY \\1",
            string=ddl,
            flags=re.IGNORECASE,
        )


    @staticmethod
    def _remove_row_access_policy_db_references(ddl: str) -> str:
        """
        Remove the database references for row access policies in the ddl.
        """
        return re.sub(
            pattern="WITH ROW ACCESS POLICY \w+\.(\w+\.\w+)",
            repl="WITH ROW ACCESS POLICY \\1",
            string=ddl,
            flags=re.IGNORECASE,
        )
    

    @staticmethod
    def _update_ddl_autoincrement(ddl: str, old_table_name: str, desired_columns: List[str], snow_client_target: SnowClient) -> str:        
        updated_ddl = [ddl.splitlines()[0]]
        # columns start at the second line of the ddl
        # each line contains a column
        # after the columns, additional properties, like primary key, might appear
        # the ddl ends with a closing bracket
        for col, line in zip(desired_columns, ddl.splitlines()[1:len(desired_columns)+1]):
            updated_line = TableAction._generate_column_autoincrement(
                snow_client_target=snow_client_target,
                table_name=old_table_name,
                col=col,
                line=line,
            )
            updated_ddl.append(updated_line)
        updated_ddl.extend(ddl.splitlines()[len(desired_columns)+1:])
        return "\n".join(updated_ddl)
    

    @staticmethod
    def _generate_column_autoincrement(snow_client_target: SnowClient, table_name: str, col: ColumnInstance, line: str) -> str:
        """
        Given a column definition from GET_DDL(), generate a new autoincrement statement.

        Check if the column has a min/max value in the target table. If yes, use that
        value + the autoincrement value as the new start value.

        NOTE: This function assumes that the line is taken directly from GET_DDL.
              It might not work with other formats, e.g. AUTOINCREMENT(1,1) is not accepted.
        """
        if col.identity_start is None: # the column does not have autoincrement set
            return line
        if col.identity_increment > 0: # the autoincrement value is positive
            current_val = TableAction._get_max_column_value(
                snow_client_target=snow_client_target,
                table_name=table_name,
                column_name=col.column_name,
            )
        else: # the autoincrement value is negative
            current_val = TableAction._get_min_column_value(
                snow_client_target=snow_client_target,
                table_name=table_name,
                column_name=col.column_name,
            )
        if current_val is None: # there is no current max/min value (probably beacuse the column is empty)
            return line
        next_val = col.identity_increment + current_val
        return re.sub( # replace the start value with the determined next value
            pattern="\\sautoincrement\\sstart\\s\\d+\\s",
            repl=f" autoincrement start {next_val} ",
            string=line,
            count=1,
        )


    @staticmethod
    def _get_max_column_value(snow_client_target: SnowClient, table_name: str, column_name: str) -> any:
        """
        Get the max value of a table column in the target database.
        """
        result = snow_client_target.execute_query(f"SELECT MAX({column_name}) AS M FROM {table_name};")
        return result[0]["M"]


    @staticmethod
    def _get_min_column_value(snow_client_target: SnowClient, table_name: str, column_name: str) -> any:
        """
        Get the min value of a table column in the target database.
        """
        result = snow_client_target.execute_query(f"SELECT MIN({column_name}) AS M FROM {table_name};")
        return result[0]["M"]


    @staticmethod
    def _generate_insert_statement(
        current_cols: List[str],
        desired_cols: List[str],
        source_table: str,
        target_table: str
    ) -> str:
        """
        Generate an insert statement for the create and insert operation.

        Args:
            current_cols - List of column names in the current table
            desired_cols - List of column names in the desired table
            source_table - Name of the table that contains the data
            target_table - Name of the table into which data will be inserted
        """
        relevant_column_names = ", ".join([c for c in current_cols if c in desired_cols])
        return f"""
            INSERT INTO {target_table} (
                {relevant_column_names}
            ) SELECT
                {relevant_column_names}
            FROM
                {source_table}
        """


    def _generate_alter_statement(self, snow_client: SnowClient) -> str:
        """
            Generate SQL statements for this object action.
            If more than one statement is required, they will be returned as a single
            string, separated by semicolons.
        Args:
            snow_client: SnowClient - Connection to snowflake database containing the desired configuration (meta db)
        Returns:
            statement: str - SQL statements which will perform the action (separated by ;)
        """
        statements = []

        updated_instance = copy.deepcopy(self.current_instance)
        desired_instance = copy.deepcopy(self.desired_instance)

        if len(self.columns_to_add) > 0:
            column_definitions = self._get_column_definitions(snow_client)
        else:
            # In case there is no add-column action there is no need for policy handling
            self.policy_assignments_info_from_object = {"NOT_HANDLED":True}

        for column in self.columns_to_add:
            if self.policy_assignments_info_from_object:

                column_comment = next((column_.comment for column_ in desired_instance.table_columns if column_.column_name.casefold() == column), '')

                statements.extend(
                    handle_policy_assignments_for_alter_table_add_column_action(
                        table_identifier = self.full_name,
                        column = column,
                        column_comment = column_comment,
                        column_definition = column_definitions[column],
                        policy_assignments_info_from_object = self.policy_assignments_info_from_object
                    )
                )
            else:
                # TODO: Can this be done without using snow_client?
                statements.append(
                    self._generate_add_column_statement(
                        table_name=self.full_name,
                        column_definition=column_definitions[column],
                    )
                )

        for column in self.columns_to_alter:
            column_current = next(
                c
                for c in updated_instance.table_columns
                if c.column_name.casefold() == column.casefold()
            )
            column_desired = next(
                c
                for c in desired_instance.table_columns
                if c.column_name.casefold() == column.casefold()
            )
            statements.extend(
                self._generate_column_alter_statements(
                    table_name=self.full_name,
                    column_current=column_current,
                    column_desired=column_desired,
                )
            )


        if updated_instance.clustering_key != desired_instance.clustering_key:
            statements.append(
                self._generate_clustering_statement(
                    table_name=self.full_name,
                    clustering_key_desired=desired_instance.clustering_key,
                )
            )
            updated_instance.clustering_key = desired_instance.clustering_key

        if (
            updated_instance.constraints_primary_key
            != desired_instance.constraints_primary_key
        ):
            if updated_instance.constraints_primary_key:
                statements.append(
                    self._generate_drop_primary_key_statement(self.full_name)
                )
            updated_instance.constraints_primary_key = []

        if (
            updated_instance.constraints_foreign_key
            != desired_instance.constraints_foreign_key
        ):
            for i, constraint_foreign_key in enumerate(updated_instance.constraints_foreign_key):
                statements.append(
                    self._generate_drop_foreign_key_statement(
                        self.full_name, constraint_foreign_key.columns
                    )
                )
            updated_instance.constraints_foreign_key = []

        if (
            updated_instance.constraints_unique_key
            != desired_instance.constraints_unique_key
        ):
            for i, constraint_unique_key in enumerate(updated_instance.constraints_unique_key):
                statements.append(
                    self._generate_drop_unique_key_statement(
                        self.full_name, constraint_unique_key.columns
                    )
                )
            updated_instance.constraints_unique_key = []

        for column in self.columns_to_drop:
            statements.append(
                self._generate_drop_column_statement(
                    table_name=self.full_name, column_name=column
                )
            )

        # TODO: we should more closely consider if the correct columns have been added
        updated_instance.table_columns = desired_instance.table_columns # at this point, we have generated statements for add, alter and drop columns

        if (
            updated_instance.retention_time != desired_instance.retention_time
        ) or (
            updated_instance.schema_retention_time
            != desired_instance.schema_retention_time
        ):
            statements.append(
                self._generate_retention_time_statement(
                    self.full_name,
                    desired_instance.retention_time,
                    desired_instance.schema_retention_time,
                )
            )
            updated_instance.retention_time = desired_instance.retention_time
            updated_instance.schema_retention_time = desired_instance.schema_retention_time

        if updated_instance.comment != desired_instance.comment:
            statements.append(
                self._generate_comment_statement(
                    self.full_name, desired_instance.comment
                )
            )
            updated_instance.comment = desired_instance.comment

        if (
            updated_instance.constraints_foreign_key
            != desired_instance.constraints_foreign_key
        ):
            for constraint_foreign_key in desired_instance.constraints_foreign_key:
                statements.append(
                    self._generate_create_foreign_key_statement(
                        self.full_name, constraint_foreign_key
                    )
                )
            updated_instance.constraints_foreign_key = desired_instance.constraints_foreign_key

        if (
            updated_instance.constraints_primary_key
            != desired_instance.constraints_primary_key
        ):
            for constraint_primary_key in desired_instance.constraints_primary_key:
                statements.append(
                    self._generate_create_primary_key_statement(
                        self.full_name, constraint_primary_key
                    )
                )
            updated_instance.constraints_primary_key = desired_instance.constraints_primary_key

        if (
            updated_instance.constraints_unique_key
            != desired_instance.constraints_unique_key
        ):
            for constraint_unique_key in desired_instance.constraints_unique_key:
                statements.append(
                    self._generate_create_unique_key_statement(
                        self.full_name, constraint_unique_key
                    )
                )
            updated_instance.constraints_unique_key = desired_instance.constraints_unique_key

        if (
            updated_instance.tags
            != desired_instance.tags
        ):
            settag_statement=self._generate_settag_statement()
            if settag_statement:
                statements.append(settag_statement)
            unsettag_statement=self._generate_unsettag_statement()
            if unsettag_statement:
                statements.append(unsettag_statement)
            updated_instance.tags = desired_instance.tags

        if updated_instance.row_access_policy_references != desired_instance.row_access_policy_references:
            statements.extend(self._generate_alter_row_access_policy_assignment_statement(
                    object_type = self.object_type,
                    object_full_name = self.full_name,
                    desired_policy_references = desired_instance.row_access_policy_references,
                )
            )
            updated_instance.row_access_policy_references = desired_instance.row_access_policy_references

        if updated_instance.masking_policy_references != desired_instance.masking_policy_references:
            statements.extend(self._generate_alter_masking_policy_assignment_statement(
                    object_type = self.object_type,
                    object_full_name = self.full_name,
                    desired_policy_references = desired_instance.masking_policy_references,
                    desired_column_names = [c.column_name for c in desired_instance.table_columns],
                )
            )
            updated_instance.masking_policy_references = desired_instance.masking_policy_references

        if updated_instance != desired_instance:
            self._alter_statement_error_summary(updated_instance, desired_instance)
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER TABLE is not supported for {updated_instance.full_name} (for {property_error_message})"
            raise ValueError(error_message)

        return "; ".join(statements)

    @staticmethod
    def _generate_alter_row_access_policy_assignment_statement(
        object_type: DbObjectType,
        object_full_name: str,
        desired_policy_references: List[RowAccessPolicyReference],
    ) -> str:
        sql_object_type = DbObjectType.get_sql_object_type(object_type)
        statements = [f"ALTER {sql_object_type} {object_full_name} DROP ALL ROW ACCESS POLICIES"]
        for ref in desired_policy_references:
            statements.append(
                f"ALTER {sql_object_type} {object_full_name} ADD ROW ACCESS POLICY {ref.policy_schema}.{ref.policy_name} ON {ref.ref_arg_columns_string}"
            )
        return statements

    @staticmethod
    def _generate_alter_masking_policy_assignment_statement(
        object_type: DbObjectType,
        object_full_name: str,
        desired_policy_references: List[MaskingPolicyReference],
        desired_column_names: List[str],
    ) -> str:
        sql_object_type = DbObjectType.get_sql_object_type(object_type)
        statements = []

        # Remove masking policies from all columns.
        # This must be done before setting the masking policies, because a
        # column might need to be unmasked before it can be used as condition
        # for another column.
        for col_name in desired_column_names:
            statements.append(f"ALTER {sql_object_type} {object_full_name} ALTER COLUMN {col_name} UNSET MASKING POLICY")

        # set masking policies as desired
        for ref in desired_policy_references:
            if len(ref.ref_arg_column_names_dict) > 0:
                conditional_columns_string = f"USING {ref.conditional_columns_string}"
            else:
                conditional_columns_string = ""
            statements.append(f"ALTER {sql_object_type} {object_full_name} ALTER COLUMN {ref.ref_column_name} SET MASKING POLICY {ref.policy_schema}.{ref.policy_name} {conditional_columns_string} FORCE")

        return statements

    @staticmethod
    def _generate_clustering_statement(table_name, clustering_key_desired: str):
        """
            Generate a statement for altering the clustering key.
        Args:
            clustering_key_desired: str - desired clustering key, e.g. "LINEAR(MANDANT_ID,KJMO)" or "(MANDANT_ID,KJMO)"
        Note:
            snowflake output for clustering key depends on when table was created, see
            https://community.snowflake.com/s/article/LINEAR-keyword-missing-in-clustering-key-column-in-information-schema-table-table
        """
        if clustering_key_desired is None:
            cluster_statement = "DROP CLUSTERING KEY"
        else:
            m = re.match(
                r"(LINEAR)?\s*\((?P<key>.*)\)",
                clustering_key_desired,
                re.IGNORECASE + re.DOTALL,
            )
            cluster_statement = f"CLUSTER BY ({m.group('key')})"
        return f"ALTER TABLE {table_name} {cluster_statement}"

    @staticmethod
    def _generate_add_column_statement(table_name: str, column_definition: str) -> str:
        """
        Generate a statement to add a column.
        """
        return f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"

    @staticmethod
    def _generate_drop_column_statement(table_name: str, column_name: str) -> str:
        """
        Generate a statement to drop a column.
        """
        return f"ALTER TABLE {table_name} DROP COLUMN {column_name}"

    @staticmethod
    def _generate_retention_time_statement(
        table_name: str, retention_time: int, schema_retention_time: int
    ) -> str:
        """
        Generate a statement to alter the retention time.
        """
        if retention_time == schema_retention_time:
            return f"ALTER TABLE {table_name} UNSET DATA_RETENTION_TIME_IN_DAYS"
        else:
            return f"ALTER TABLE {table_name} SET DATA_RETENTION_TIME_IN_DAYS = {retention_time}"

    @staticmethod
    def _generate_comment_statement(table_name: str, comment: Union[str, None]) -> str:
        """
        Generate a statement to alter the comment.
        """
        if comment is None:
            return f"ALTER TABLE {table_name} UNSET COMMENT"
        else:
            return f"ALTER TABLE {table_name} SET COMMENT = '{comment}'"

    @staticmethod
    def _generate_drop_foreign_key_statement(
        table_name, columns: List[ConstraintColumnForeignKey]
    ) -> str:
        """
            Generate statement to drop a foreign key.
        Args:
            columns: List[ConstraintColumnForeignKey] - list of foreign key columns
        Note:
            Dropping is not done by key name, as this does not work for system generated key names.
        """
        constraint_columns = [
            c.column_name for c in sorted(columns, key=lambda x: x.key_sequence)
        ]
        return f"ALTER TABLE {table_name} DROP FOREIGN KEY ({', '.join(constraint_columns)})"

    @staticmethod
    def _generate_drop_primary_key_statement(table_name) -> str:
        """
            Generate statement to drop a primary key.
        Args:
            None (there can only be one primary key per table)
        Note:
            Dropping is not done by key name, as this does not work for system generated key names.
        """
        return f"ALTER TABLE {table_name} DROP PRIMARY KEY"

    @staticmethod
    def _generate_drop_unique_key_statement(
        table_name, columns: List[ConstraintColumn]
    ) -> str:
        """
            Generate statement to drop a unique key.
        Args:
            columns: List[ConstraintColumn] - list of key columns
        Note:
            Dropping is not done by key name, as this does not work for system generated key names.
        """
        constraint_columns = [
            c.column_name for c in sorted(columns, key=lambda x: x.key_sequence)
        ]
        return f"ALTER TABLE {table_name} DROP UNIQUE ({', '.join(constraint_columns)})"

    @staticmethod
    def _generate_create_foreign_key_statement(
        table_name, constraint_instance: InstanceConstraintForeignKey
    ) -> str:
        """
            Generate statement to create a foreign key.
        Args:
            constraint_instance: InstanceConstraintForeignKey
        """
        if InstanceConstraintPrimaryKey._is_system_assigned_name(
            constraint_instance.constraint_name
        ):
            constraint_name = ""
        else:
            constraint_name = f"CONSTRAINT {constraint_instance.constraint_name}"
        pk_column_names = [
            c.pk_column_name
            for c in sorted(constraint_instance.columns, key=lambda x: x.key_sequence)
        ]
        fk_column_names = [
            c.column_name
            for c in sorted(constraint_instance.columns, key=lambda x: x.key_sequence)
        ]
        pk_table_full_name = (
            f"{constraint_instance.pk_schema_name}.{constraint_instance.pk_table_name}"
        )
        comment = (
            f"COMMENT '{constraint_instance.comment}'"
            if constraint_instance.comment
            else ""
        )
        return f"ALTER TABLE {table_name} ADD {constraint_name} FOREIGN KEY ({', '.join(fk_column_names)}) REFERENCES {pk_table_full_name} ({', '.join(pk_column_names)}) {comment}"

    @staticmethod
    def _generate_create_primary_key_statement(
        table_name, constraint_instance: InstanceConstraintPrimaryKey
    ) -> str:
        """
            Generate statement to create a primary key.
        Args:
            constraint_instance: InstanceConstraintPrimaryKey
        """
        if InstanceConstraintPrimaryKey._is_system_assigned_name(
            constraint_instance.constraint_name
        ):
            constraint_name = ""
        else:
            constraint_name = f"CONSTRAINT {constraint_instance.constraint_name}"
        constraint_columns = [
            c.column_name
            for c in sorted(constraint_instance.columns, key=lambda x: x.key_sequence)
        ]
        comment = (
            f"COMMENT '{constraint_instance.comment}'"
            if constraint_instance.comment
            else ""
        )
        return f"ALTER TABLE {table_name} ADD {constraint_name} PRIMARY KEY ({', '.join(constraint_columns)}) {comment}"

    @staticmethod
    def _generate_create_unique_key_statement(
        table_name, constraint_instance: InstanceConstraintUniqueKey
    ) -> str:
        """
            Generate statement to create a unique key.
        Args:
            constraint_instance: InstanceConstraintUniqueKey
        """
        if InstanceConstraintUniqueKey._is_system_assigned_name(
            constraint_instance.constraint_name
        ):
            constraint_name = ""
        else:
            constraint_name = f"CONSTRAINT {constraint_instance.constraint_name}"
        constraint_columns = [
            c.column_name
            for c in sorted(constraint_instance.columns, key=lambda x: x.key_sequence)
        ]
        comment = (
            f"COMMENT '{constraint_instance.comment}'"
            if constraint_instance.comment
            else ""
        )
        return f"ALTER TABLE {table_name} ADD {constraint_name} UNIQUE ({', '.join(constraint_columns)}) {comment}"

    @staticmethod
    def _generate_column_alter_statements(
        table_name: str, column_current: ColumnInstance, column_desired: ColumnInstance
    ) -> List[str]:
        """
            Generate alter column statements. Supported cases:
            - change nullability of a column
            - change comment
            - change n in NUMBER(n, m)
            - increase n in VARCHAR(n)
            - drop default of a column
            List of cases supported by snowflake: https://docs.snowflake.com/en/sql-reference/sql/alter-table-column.html
        Args:
            table_name: str - full name of the table
            column_current: Column - current state of the column
            column_desired: Column - desired state of the column
        Returns:
            statements: List[str]
        """
        statements = []
        column = copy.deepcopy(
            column_current
        )  # variable used to track changes for which statements are added

        # comment
        if column.comment != column_desired.comment:
            comment = (
                column_desired.comment.replace("'", "''")
                if column_desired.comment is not None
                else ""
            )
            statements.append(f"ALTER {column.column_name} COMMENT '{comment}'")
            column.comment = column_desired.comment

        # nullability
        if column.is_nullable != column_desired.is_nullable:
            if column_desired.is_nullable == "NO":
                statements.append(f"ALTER {column.column_name} SET NOT NULL")
                column.is_nullable = "NO"
            if column_desired.is_nullable == "YES":
                statements.append(f"ALTER {column.column_name} DROP NOT NULL")
                column.is_nullable = "YES"

        # number precision
        if (
            (column.data_type == column_desired.data_type)
            and (column.data_type == "NUMBER")
            and (column.numeric_precision != column_desired.numeric_precision)
        ):
            statements.append(
                f"ALTER {column.column_name} SET DATA TYPE NUMBER({column_desired.numeric_precision},{column.numeric_scale})"
            )
            column.numeric_precision = column_desired.numeric_precision

        # varchar length
        if (
            (column.data_type == column_desired.data_type)
            and (column.data_type == "TEXT")
            and (
                column.character_maximum_length
                < column_desired.character_maximum_length
            )
            and (
                column.collation_name == column_desired.collation_name
            )  # collation must be identical https://docs.snowflake.com/en/sql-reference/collation.html#additional-considerations-for-using-collation
        ):
            collation_string = (
                f" COLLATE '{column.collation_name}'" if column.collation_name else ""
            )
            statements.append(
                f"ALTER {column.column_name} SET DATA TYPE VARCHAR({column_desired.character_maximum_length}){collation_string}"
            )
            column.character_maximum_length = column_desired.character_maximum_length
            column.character_octet_length = column_desired.character_octet_length

        # drop column default
        if (not column_desired.column_default) and column.column_default:
            statements.append(f"ALTER {column.column_name} DROP DEFAULT")
            column.column_default = column_desired.column_default

        # alter column default sequence
        if (
            column_desired.column_default != column.column_default
            and str(column_desired.column_default).endswith(".NEXTVAL")
            and str(column.column_default).endswith(".NEXTVAL")
        ):
            statements.append(
                f"ALTER {column.column_name} SET DEFAULT {column_desired.column_default}"
            )
            column.column_default = column_desired.column_default

        # alter tags on column
        if (
            column_desired.tags != column.tags
        ):
            column_settag_statement=DbObjectAction._generate_column_settag_statement(column, column_desired)
            if column_settag_statement:
                statements.append(column_settag_statement)
            column_unsettag_statement=DbObjectAction._generate_column_unsettag_statement(column, column_desired)
            if column_unsettag_statement:
                statements.append(column_unsettag_statement)
            column.tags = column_desired.tags

        # sucessful if all changes could be performed
        if column == column_desired:
            return [f"ALTER TABLE {table_name} {s}" for s in statements]
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                column, column_desired
            )
            error_message = (
                f"Required column alter is not supported for column {column.column_name} in table {column.object_schema}.{column.object_name}. Problems: {property_error_message}\n"
                "Supported column alter in Snowflake: https://docs.snowflake.com/en/sql-reference/sql/alter-table-column.html \n"
                "Out of those, the following are implemented in Acedeploy framework:\n"
                "- change nullability of a column\n"
                "- change comment\n"
                "- change n in NUMBER(n, m)\n"
                "- increase n in VARCHAR(n)\n"
                "- drop default of a column\n"
                "- change default from one sequence to another sequence"
            )
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here

    def _get_column_diff(self) -> Tuple[List[str], List[str], List[str], bool]:
        """
            Get differences between desired and current columns.
            Returns 3 lists with names of columns to add, drop or alter.
            List will contain column names in lowercase.
            Also returns a flag to see if any columns to add are in somewhere other than
            the end of the column list.
        Returns:
            columns_to_add, columns_to_drop, columns_to_alter, columns_added_in_between: (List[str], List[str], List[str], bool) - Lists of column names (3x) and flag to see if new columns are added in between existing columns
        """
        column_names_desired = [
            c.column_name.casefold() for c in sorted(self.desired_instance.table_columns, key=lambda tc: tc.ordinal_position)
        ]
        column_names_current = [
            c.column_name.casefold() for c in sorted(self.current_instance.table_columns, key=lambda tc: tc.ordinal_position)
        ]
        columns_to_add = [
            c.casefold() for c in column_names_desired if c not in column_names_current
        ]
        columns_to_drop = [
            c.casefold() for c in column_names_current if c not in column_names_desired
        ]
        columns_in_both = [
            c.casefold() for c in column_names_current if c in column_names_desired
        ]
        columns_to_alter = []
        for column_name in columns_in_both:
            column_desired = [
                c
                for c in self.desired_instance.table_columns
                if c.column_name.casefold() == column_name
            ][0]
            column_current = [
                c
                for c in self.current_instance.table_columns
                if c.column_name.casefold() == column_name
            ][0]
            if not column_desired == column_current:
                columns_to_alter.append(column_name)
        columns_added_at_end = dict_and_list_util.list_ends_with_list(column_names_desired, columns_to_add)
        columns_added_in_between = not columns_added_at_end
        return columns_to_add, columns_to_drop, columns_to_alter, columns_added_in_between

    def _get_column_definitions(self, snow_client: SnowClient) -> Dict[str, str]:
        """
            Get column definition from snowflake get_ddl function.

            Will also return all additional lines (such as semicolon or cluster keys) as columns.
            Those entries in the returned dict can be ignored.
        Args:
            snow_client: SnowClient - Connection to snowflake database containing the desired configuration (meta db)
        Returns:
            [Dict[str, str] - dict with format {column_name: column_definition}
        """
        # TODO: This function currently also returns all other lines (e.g. clustering keys, constraints) as dictionary: can this be solved in a nicer way?
        # TODO: This function also includes information on masking policies. Will this cause a problem somewhere?
        statement = f"SELECT GET_DDL('TABLE' , '{self.full_name}') AS COL_DEF"
        table_definition = snow_client.execute_query(statement)[0]["COL_DEF"]
        column_definitions = {}
        for line in table_definition.splitlines():
            cleaned_line = line.strip().rstrip(",")
            if not cleaned_line.startswith("create or replace"):
                column_name = cleaned_line.split()[0].casefold()
                column_definitions[column_name] = cleaned_line
        return column_definitions


class DynamicTableAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceDynamicTable = None,
        desired_instance: InstanceDynamicTable = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.DYNAMICTABLE,
            action=action,
            file_content=file_content,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )
        if (self.desired_instance is not None) and (self.current_instance is not None):
            # these values are created here, so they can be used by other functions (e.g. to check for dataloss)
            (
                self.columns_to_add,
                self.columns_to_drop,
                self.columns_to_alter,
            ) = self._get_column_diff()

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return self._generate_add_statement(self.file_content, self.desired_instance, self.policy_assignments_info_from_object)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement()
        elif self.action == DbActionType.DROP:
            return f"DROP DYNAMIC TABLE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"DynamicTableAction: {self.id}"

    def __repr__(self):
        return f"DynamicTableAction: {self.id}"

    @staticmethod
    def _generate_add_statement(
        file_content: str, desired_instance: InstanceDynamicTable, policy_assignments_info_from_object: dict= {}
    ) -> str:
        """
        Generate sql statement(s) for creating a new dynamic table based on the desired state. Handles policy assignments.
        """
        statements = []
        statements.append( string_util.remove_create_or_replace(file_content) )

        if policy_assignments_info_from_object:
            dynamictable_statement=statements[0]
            statements = handle_policy_assignments_for_object_creation(
                object_type= PolicyAssignmentObjectTypes.DYNAMICTABLE,
                object_statement=dynamictable_statement,
                columns=desired_instance.table_columns,
                policy_assignments_of_object=policy_assignments_info_from_object["assignments"]
            )

        return " ".join(statements)
    
    def _check_dynamic_table_alter_column_supported(
            self,
            columns_to_alter: List[str]
        ) -> bool:
        """
        Check if all alter Dynamic Table Column operations are supported.
        For the following differences the Dynamic Table will be re-created:
            - ordinal_position
            - data_type
            - is_nullable
            - column_default
        Currently only the following alter column operations are supported:
            - comment
            - tags
        All other column differences will be ignored.
        """
        dynamic_table_alter_column_supported = True

        for column in columns_to_alter:
            column_current = next(
                c
                for c in self.current_instance.table_columns
                if c.column_name.casefold() == column.casefold()
            )
            column_desired = next(
                c
                for c in self.desired_instance.table_columns
                if c.column_name.casefold() == column.casefold()
            )

            if (
                column_current.data_type != column_desired.data_type
                or column_current.is_nullable != column_desired.is_nullable
                or column_current.column_default != column_desired.column_default
                or column_current.ordinal_position != column_desired.ordinal_position
            ):
                dynamic_table_alter_column_supported = False

        return dynamic_table_alter_column_supported

    def _generate_alter_statement(self) -> str:
        """
            Generate SQL statements for this object action.
            If more than one statement is required, they will be returned as a single
            string, separated by semicolons.
        Returns:
            statement: str - SQL statements which will perform the action (separated by ;)
        """
        statements = []

        updated_instance = copy.deepcopy(
            self.current_instance
        )  # variable used to track changes for which statements are added

        
        if self.current_instance.table_columns != self.desired_instance.table_columns:
            dynamic_table_alter_column_supported = self._check_dynamic_table_alter_column_supported(
                columns_to_alter = self.columns_to_alter
            )
        else:
            dynamic_table_alter_column_supported = False

        # first check if the dynamic table needs to be altered with "create or replace"
        # check -> alter query_text 
        # check -> alter refresh_mode
        # check -> alter dynamic table columns
        if (
            self.current_instance.query_text != self.desired_instance.query_text 
            or self.current_instance.refresh_mode != self.desired_instance.refresh_mode
            or 
            (self.current_instance.table_columns != self.desired_instance.table_columns
             and not dynamic_table_alter_column_supported
             )
        ):
            statements.append(string_util.add_create_or_replace(self.file_content))
            if self.policy_assignments_info_from_object:
                dynamictable_statement=statements[0]
                statements = handle_policy_assignments_for_object_creation(
                    object_type= PolicyAssignmentObjectTypes.DYNAMICTABLE,
                    object_statement=dynamictable_statement,
                    columns=self.desired_instance.table_columns,
                    policy_assignments_of_object=self.policy_assignments_info_from_object["assignments"]
                )
            return " ".join(statements)
        else:
            # In case there is no change to the query_text or the refresh_mode there is no need for policy handling
            self.policy_assignments_info_from_object = {"NOT_HANDLED":True}

        # alter column
        # TODO add tests that cover the alter column functionality for dynamic tables
        if self.current_instance.table_columns != self.desired_instance.table_columns and dynamic_table_alter_column_supported:
            if len(self.columns_to_add) > 0:
                raise ValueError(f"Required ALTER DYNAMIC TABLE is not supported for {self.current_instance.full_name}, adding a column or renaming a column is just supported when the query_text is changed (Note: In this case the dynamic table gets altered with 'create or replace').")
            for column in self.columns_to_alter:
                column_current = next(
                    c
                    for c in self.current_instance.table_columns
                    if c.column_name.casefold() == column.casefold()
                )
                column_desired = next(
                    c
                    for c in self.desired_instance.table_columns
                    if c.column_name.casefold() == column.casefold()
                )

                if column_current.comment != column_desired.comment:
                    statements.append(
                        self._generate_dynamcic_table_alter_comment_on_column_statement(
                            dynamic_table_name=self.full_name,
                            column_current=column_current,
                            column_desired=column_desired
                        )
                    )

                if column_desired.tags != column_current.tags:  
                    alter_column_tags_statements = self._generate_dynamcic_table_alter_tags_on_column_statement( 
                            dynamic_table_name=self.full_name,
                            column_current=column_current,
                            column_desired=column_desired
                            )
                    statements.append("; ".join(alter_column_tags_statements)+";")

            updated_instance.table_columns = self.desired_instance.table_columns

        # alter target_lag
        if self.current_instance.target_lag != self.desired_instance.target_lag:
            statements.append(
                self._generate_target_lag_statement(
                    dynamic_table_name=self.full_name,
                    target_lag=self.desired_instance.target_lag,
                )
            )
            updated_instance.target_lag = self.desired_instance.target_lag

        # alter warehouse
        if self.current_instance.warehouse != self.desired_instance.warehouse:
            statements.append(
                self._generate_warehouse_statement(
                    dynamic_table_name=self.full_name,
                    warehouse=self.desired_instance.warehouse,
                )
            )
            updated_instance.warehouse = self.desired_instance.warehouse

        # alter retention_time
        if (
            self.current_instance.retention_time != self.desired_instance.retention_time
        ) or (
            self.current_instance.schema_retention_time
            != self.desired_instance.schema_retention_time
        ):
            statements.append(
                self._generate_retention_time_statement(
                    dynamic_table_name=self.full_name,
                    retention_time=self.desired_instance.retention_time,
                    schema_retention_time=self.desired_instance.schema_retention_time,
                )
            )
            updated_instance.retention_time = self.desired_instance.retention_time

        # alter comment
        if self.current_instance.comment != self.desired_instance.comment:
            statements.append(
                self._generate_comment_statement(
                    dynamic_table_name=self.full_name,
                    comment=self.desired_instance.comment
                )
            )
            updated_instance.comment = self.desired_instance.comment

        # alter cluster by
        if self.current_instance.clustering_key != self.desired_instance.clustering_key:
            statements.append(
                self._generate_clustering_statement(
                    dynamic_table_name=self.full_name,
                    clustering_key_desired=self.desired_instance.clustering_key,
                )
            )
            updated_instance.clustering_key = self.desired_instance.clustering_key

        # alter tags
        if self.current_instance.tags!= self.desired_instance.tags:
            settag_statement=self._generate_settag_statement()
            if settag_statement:
                statements.append(settag_statement+";")
            unsettag_statement=self._generate_unsettag_statement()
            if unsettag_statement:
                statements.append(unsettag_statement+";")
            updated_instance.tags = self.desired_instance.tags

        if updated_instance == self.desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, self.desired_instance
            )
            error_message = f"Required ALTER DYNAMIC TABLE is not supported for {self.current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-dynamic-table"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here

    @staticmethod
    def _generate_target_lag_statement(
        dynamic_table_name: str, target_lag: str
    ) -> str:
        """
        Generate a statement to alter the target lag.
        """
        return f"ALTER DYNAMIC TABLE {dynamic_table_name} SET TARGET_LAG = '{target_lag}';"

    @staticmethod
    def _generate_warehouse_statement(
        dynamic_table_name: str, warehouse: str
    ) -> str:
        """
        Generate a statement to alter the target lag.
        """
        return f"ALTER DYNAMIC TABLE {dynamic_table_name} SET WAREHOUSE = {warehouse};"

    @staticmethod
    def _generate_retention_time_statement(
        dynamic_table_name: str, retention_time: int, schema_retention_time: int
    ) -> str:
        """
        Generate a statement to alter the retention time.
        """
        if retention_time == schema_retention_time:
            return f"ALTER DYNAMIC TABLE {dynamic_table_name} UNSET DATA_RETENTION_TIME_IN_DAYS;"
        else:
            return f"ALTER DYNAMIC TABLE {dynamic_table_name} SET DATA_RETENTION_TIME_IN_DAYS = {retention_time};"

    @staticmethod
    def _generate_comment_statement(dynamic_table_name: str, comment: Union[str, None]) -> str:
        """
        Generate a statement to alter the comment.
        """
        if comment is None:
            return f"ALTER DYNAMIC TABLE {dynamic_table_name} UNSET COMMENT;"
        else:
            return f"ALTER DYNAMIC TABLE {dynamic_table_name} SET COMMENT = '{comment}';"

    @staticmethod
    def _generate_clustering_statement(dynamic_table_name, clustering_key_desired: str):
        """
            Generate a statement for altering the clustering key.
        Args:
            clustering_key_desired: str - desired clustering key, e.g. "LINEAR(MANDANT_ID,KJMO)" or "(MANDANT_ID,KJMO)"
        Note:
            snowflake output for clustering key depends on when table was created, see
            https://community.snowflake.com/s/article/LINEAR-keyword-missing-in-clustering-key-column-in-information-schema-table-table
        """
        if clustering_key_desired is None:
            cluster_statement = "DROP CLUSTERING KEY"
        else:
            m = re.match(
                r"(LINEAR)?\s*\((?P<key>.*)\)",
                clustering_key_desired,
                re.IGNORECASE + re.DOTALL,
            )
            cluster_statement = f"CLUSTER BY ({m.group('key')})"
        return f"ALTER DYNAMIC TABLE {dynamic_table_name} {cluster_statement};"
    
    @staticmethod
    def _generate_dynamcic_table_alter_comment_on_column_statement(
        dynamic_table_name: str, column_current: ColumnInstance, column_desired: ColumnInstance
    ) -> str:
        """
        Generate a statement to alter a Dynamic Table comment on a column.
        """
        comment = (
            column_desired.comment.replace("'", "''")
            if column_desired.comment is not None
            else ""
        )
        statement = f"ALTER DYNAMIC TABLE {dynamic_table_name} ALTER {column_current.column_name} COMMENT '{comment}';"

        return statement
    
    @staticmethod
    def _generate_dynamcic_table_alter_tags_on_column_statement(
        dynamic_table_name: str, column_current: ColumnInstance, column_desired: ColumnInstance
    ) -> List[str]:
        """
        Generate statements to alter Dynamic Table tags on a column.
        """
        statements = []

        # alter tags on column
        column_settag_statement=DbObjectAction._generate_column_settag_statement(column_current, column_desired)
        if column_settag_statement:
            statements.append(column_settag_statement)
        column_unsettag_statement=DbObjectAction._generate_column_unsettag_statement(column_current, column_desired)
        if column_unsettag_statement:
            statements.append(column_unsettag_statement)

        return [f"ALTER DYNAMIC TABLE {dynamic_table_name} {s}" for s in statements]
        

    # TODO: Re-use method from TableAction
    def _get_column_diff(self) -> Tuple[List[str], List[str], List[str]]:
        """
            Get differences between desired and current columns.
            Returns 3 lists with names of columns to add, drop or alter.
            List will contain column names in lowercase.
        Returns:
            columns_to_add, columns_to_drop, columns_to_alter: (List[str], List[str], List[str]) - Lists of column names
        """
        column_names_desired = [
            c.column_name for c in self.desired_instance.table_columns
        ]
        column_names_current = [
            c.column_name for c in self.current_instance.table_columns
        ]
        columns_to_add = [
            c.casefold() for c in column_names_desired if c not in column_names_current
        ]
        columns_to_drop = [
            c.casefold() for c in column_names_current if c not in column_names_desired
        ]
        columns_in_both = [
            c.casefold() for c in column_names_current if c in column_names_desired
        ]
        columns_to_alter = []
        for column_name in columns_in_both:
            column_desired = [
                c
                for c in self.desired_instance.table_columns
                if c.column_name.casefold() == column_name
            ][0]
            column_current = [
                c
                for c in self.current_instance.table_columns
                if c.column_name.casefold() == column_name
            ][0]
            if not column_desired == column_current:
                columns_to_alter.append(column_name)
        return columns_to_add, columns_to_drop, columns_to_alter


class NetworkRuleAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceNetworkRule = None,
        desired_instance: InstanceNetworkRule = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.NETWORKRULE,
            action=action,
            file_content=file_content,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement()
        elif self.action == DbActionType.DROP:
            return f"DROP NETWORK RULE IF EXISTS {self.full_name}"

    def __str__(self):
        return f"NetworkRuleAction: {self.id}"

    def __repr__(self):
        return f"NetworkRuleAction: {self.id}"


    def _generate_alter_statement(self) -> str:
        """
            Generate SQL statements for this object action.
            If more than one statement is required, they will be returned as a single
            string, separated by semicolons.
        Returns:
            statement: str - SQL statements which will perform the action (separated by ;)
        """
        statements = []

        updated_instance = copy.deepcopy(
            self.current_instance
        )  # variable used to track changes for which statements are added

        
        if self.current_instance.type != self.desired_instance.type or self.current_instance.mode != self.desired_instance.mode:
            statements.append(string_util.add_create_or_replace(self.file_content))
            return " ".join(statements)


        # alter value_list
        if self.current_instance.value_list != self.desired_instance.value_list:
            statements.append(
                self._generate_value_list_statement(
                    network_rule_name=self.full_name,
                    value_list=self.desired_instance.value_list,
                )
            )
            updated_instance.value_list = self.desired_instance.value_list

        # alter comment
        if self.current_instance.comment != self.desired_instance.comment:
            statements.append(
                self._generate_comment_statement(
                    network_rule_name=self.full_name,
                    comment=self.desired_instance.comment,
                )
            )
            updated_instance.comment = self.desired_instance.comment
        

        if updated_instance == self.desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, self.desired_instance
            )
            error_message = f"Required ALTER NETWORK RULE is not supported for {self.current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/create-network-rule"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here

    @staticmethod
    def _generate_comment_statement(network_rule_name: str, comment: Union[str, None]) -> str:
        """
        Generate a statement to alter the comment of a Network Rule.
        """
        if comment is None:
            return f"ALTER NETWORK RULE {network_rule_name} UNSET COMMENT;"
        else:
            return f"ALTER NETWORK RULE {network_rule_name} SET COMMENT = '{comment}';"

    @staticmethod
    def _generate_value_list_statement(network_rule_name: str, value_list: Union[str, None]) -> str:
        """
        Generate a statement to alter the value_list of a Network Rule.
        """

        value_list_string = dict_and_list_util.list_to_string_representation(value_list.split(','))

        if not value_list:
            return f"ALTER NETWORK RULE {network_rule_name} UNSET VALUE_LIST;"
        else:
            return f"ALTER NETWORK RULE {network_rule_name} SET VALUE_LIST = ({value_list_string});"

class TagAction(DbObjectAction):
    def __init__(
        self,
        schema: str,
        name: str,
        action: DbActionType,
        file_content: str = None,
        current_instance: InstanceTag = None,
        desired_instance: InstanceTag = None,
        **_,
    ):
        super().__init__(
            schema=schema,
            name=name,
            object_type=DbObjectType.TAG,
            action=action,
            current_instance=current_instance,
            desired_instance=desired_instance,
            file_content=file_content,
        )

    def _generate_statement(self, **_):
        if self.action == DbActionType.ADD:
            return string_util.remove_create_or_replace(self.file_content)
        elif self.action == DbActionType.ALTER:
            return self._generate_alter_statement(
                self.current_instance, self.desired_instance
            )
        elif self.action == DbActionType.DROP:
            return f"DROP TAG IF EXISTS {self.full_name}"

    def __str__(self):
        return f"TagAction: {self.id}"

    def __repr__(self):
        return f"TagAction: {self.id}"

    @staticmethod
    def _generate_alter_statement( # TODO: write tests for this function
        current_instance: InstanceTag, desired_instance: InstanceTag
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a tag to the desired state.
        """
        statements = []
        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # storage_allowed_locations
        if updated_instance.allowed_values  != desired_instance.allowed_values:
            if not desired_instance.allowed_values:
                statements.append(
                    f"ALTER TAG {current_instance.full_name} UNSET ALLOWED_VALUES;"
                )
            else:
                additional_allowed_values=[allowed_value for allowed_value in desired_instance.allowed_values if allowed_value not in updated_instance.allowed_values]

                if additional_allowed_values:
                    additional_allowed_values_str=dict_and_list_util.list_to_string_representation(additional_allowed_values)

                    statements.append(
                        f"ALTER TAG {current_instance.full_name} ADD ALLOWED_VALUES {additional_allowed_values_str};"
                    )

                removed_allowed_values=[allowed_value for allowed_value in updated_instance.allowed_values if allowed_value not in desired_instance.allowed_values]

                if removed_allowed_values:
                    removed_allowed_values_str=dict_and_list_util.list_to_string_representation(removed_allowed_values)

                    statements.append(
                        f"ALTER TAG {current_instance.full_name} DROP ALLOWED_VALUES {removed_allowed_values_str};"
                    )

            updated_instance.allowed_values = desired_instance.allowed_values

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER TAG {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                statements.append(
                    f"ALTER TAG {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # sucessful if all changes could be performed
        if updated_instance == desired_instance:
            return " ".join(statements)
        else:
            property_error_message = DbObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance
            )
            error_message = f"Required ALTER TAG is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-tag.html"
            raise ValueError(error_message)
            # TODO: might want to use a custom error type here


