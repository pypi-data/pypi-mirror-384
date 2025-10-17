
from abc import abstractmethod
import copy as copy
import logging
import inspect
from typing import List
import aceutils.dict_and_list_util as dict_and_list_util
from acedeploy.core.model_instance_objects import InstanceObject
from aceaccount.core.model_account_object import AccountObject
from aceaccount.core.model_account_object_statement import AccountObjectStatement
from aceaccount.core.model_account_object_instances import AccountObjectInstance, StorageIntegrationInstance, WarehouseInstance, ShareInstance, DatabaseInstance, ExternalVolumeInstance
from aceaccount.core.model_account_object_sql_entities import AccountObjectActionType, AccountObjectType
from aceservices.snowflake_service import SnowClientConfig

from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class AccountObjectAction(AccountObject):
    """
    Collects information about an account object and the action
    that will be applied to it (CREATE, ALTER, DROP).
    This object can create the statement object (AccountObjectStatement)
    that is used to perform the desired action.
    """

    def __init__(
        self,
        name: str,
        object_type: AccountObjectType,
        action_type: AccountObjectActionType,
        current_instance: AccountObjectInstance = None,
        desired_instance: AccountObjectInstance = None,
    ):
        super().__init__(name, object_type)
        self.action_type = action_type
        self.current_instance = current_instance
        self.desired_instance = desired_instance
        if (self.action_type == AccountObjectActionType.DROP) and not (
            (self.current_instance is not None) and (self.desired_instance is None)
        ):
            raise ValueError(
                "If the action type is DROP, a current instance must be given and a desired instance can not be given"
            )

    @staticmethod
    def factory(
        name: str,
        object_type: AccountObjectType,
        action_type: AccountObjectActionType,
        **kwargs,
    ) -> "AccountObjectAction":
        """
        Generate and return a AccountObjectAction for the given parameters.
        """
        mapping = {
            AccountObjectType.STORAGEINTEGRATION: StorageIntegrationAction,
            AccountObjectType.WAREHOUSE: WarehouseAction,
            AccountObjectType.SHARE: ShareAction,
            AccountObjectType.DATABASE: DatabaseAction,
            AccountObjectType.EXTERNALVOLUME: ExternalVolumeAction
        }
        return mapping[object_type](name=name, action_type=action_type, **kwargs)

    @staticmethod
    def factory_from_instance_object(
        instance_object: AccountObjectInstance,
        action_type: AccountObjectActionType,
        **kwargs,
    ) -> "AccountObjectAction":
        """
        Generate and return a AccountObjectAction for the given a AccountObjectInstance and AccountObjectActionType.
        """
        if action_type not in (
            AccountObjectActionType.DROP,
            AccountObjectActionType.ADD,
        ):
            raise ValueError(
                f"Action of type [ '{action_type}' ] can not be generated using this function. Use AccountObjectAction.factory() instead."
            )
        return AccountObjectAction.factory(
            name=instance_object.name,
            object_type=instance_object.object_type,
            action_type=action_type,
            **kwargs,
        )

    @staticmethod
    def factory_from_instance_objects(
        current_instance: AccountObjectInstance,
        desired_instance: AccountObjectInstance,
        action_type: AccountObjectActionType,
        **kwargs,
    ) -> "AccountObjectAction":
        """
        Generate and return a AccountObjectAction for the given a current InstanceObject, a desired InstanceObject and DbActionType.
        """
        if action_type != AccountObjectActionType.ALTER:
            raise ValueError(
                f"Action of type [ '{action_type}' ] can not be generated using this function. Use AccountObjectAction.factory() instead."
            )
        if str(current_instance) != str(desired_instance):
            raise ValueError(
                f"Name or type of current and desired instance do not match ( current: ['{str(current_instance)}'], desired: ['{str(desired_instance)}'] )"
            )
        return AccountObjectAction.factory(
            name=current_instance.name,
            object_type=current_instance.object_type,
            action_type=action_type,
            current_instance=current_instance,
            desired_instance=desired_instance,
            **kwargs,
        )
    
    def _generate_grant_statements_for_new_objects(desired_instance) -> str:
        """
            Function to generate grant statements from account objects definitions for newly created account objects (which are not in the current state).
        """
        object_domain=AccountObjectType.get_object_domain_from_object_type(desired_instance.object_type)

        grant_statements=[]

        for account_object_privilege in desired_instance.grants:

            for role in desired_instance.grants[account_object_privilege]:
    
                grant_statements.append(f'GRANT {account_object_privilege.upper()} ON {object_domain} {desired_instance.full_name} TO ROLE "{role}";')

        return "\n".join(grant_statements)
    
    def _generate_grant_statements(self) -> str:
        """
            Function to generate grant statements from account objects definitions to align the current state of an account objects to the desired state.
        """
        object_domain=AccountObjectType.get_object_domain_from_object_type(self.object_type)

        grant_statements=[]

        for account_object_privilege in self.desired_instance.grants:

            current_grants_of_privilege = self.current_instance.grants.get(account_object_privilege, [])

            for role in self.desired_instance.grants[account_object_privilege]:
    
                if not role in current_grants_of_privilege:

                    grant_statements.append(f'GRANT {account_object_privilege.upper()} ON {object_domain} {self.desired_instance.full_name} TO ROLE "{role}";')

        return "\n".join(grant_statements)

    def _generate_revoke_statements(self) -> str:
        """
            Function to generate revoke statements from account objects definitions to align the current state of an account objects to the desired state.
        """
        object_domain=AccountObjectType.get_object_domain_from_object_type(self.object_type)

        revoke_statements = []

        for account_object_privilege in self.current_instance.grants:

            if not self.desired_instance.grants:
                desired_grants_of_privilege=[]
            else:
                desired_grants_of_privilege = self.desired_instance.grants.get(account_object_privilege, [])

            for role in self.current_instance.grants[account_object_privilege]:
    
                if not role in desired_grants_of_privilege:

                    revoke_statements.append(f'REVOKE {account_object_privilege.upper()} ON {object_domain} {self.desired_instance.full_name} FROM ROLE "{role}";')

        return "\n".join(revoke_statements)
    
    def _generate_settag_statements_for_new_objects(desired_instance) -> str:
        """
            Function to generate set-tag statements from account objects definitions for newly account objects (which are not in the current state).
        """
        object_domain=AccountObjectType.get_object_domain_from_object_type(desired_instance.object_type)

        settag_statement=""

        set_tags=[]
        for tag, tag_value in desired_instance.tags.items():
            if tag_value:
                set_tags.append(f"{tag} = '{tag_value}'")
        set_tags = ", ".join(set_tags)
        if set_tags:
            settag_statement=f"ALTER {object_domain} {desired_instance.full_name} SET TAG {set_tags};"

        return settag_statement
    
    def _generate_settag_statements(self) -> str:
        """
            Function to generate set-tag statements from account objects definitions to align the current state of a an account objects to the desired state.
        """
        object_domain=AccountObjectType.get_object_domain_from_object_type(self.object_type)

        settag_statement=""

        set_tags=[]
        for tag, tag_value in self.desired_instance.tags.items():
            if not hasattr(self.current_instance, "tags") or tag.lower() not in {tag.lower() for tag in self.current_instance.tags} or tag_value != self.current_instance.tags[tag.lower()]:
                set_tags.append(f"{tag} = '{tag_value}'")
        set_tags = ", ".join(set_tags)
        if set_tags:
            settag_statement = f"ALTER {object_domain} {self.desired_instance.full_name} SET TAG {set_tags};"

        return settag_statement

    def _generate_unsettag_statements(self) -> str:
        """
            Function to generate unset-tag statements from account objects definitions to align the current state of a an account objects to the desired state.
        """
        object_domain=AccountObjectType.get_object_domain_from_object_type(self.object_type)

        unsettag_statement=''
        unset_tags=[]
        for tag, tag_value in self.current_instance.tags.items():
            if tag.lower() not in {tag.lower() for tag in self.desired_instance.tags} or not tag_value:
                unset_tags.append(tag)
        unset_tags = ", ".join(unset_tags)
        if unset_tags:
            unsettag_statement = f"ALTER {object_domain} {self.desired_instance.full_name} UNSET TAG {unset_tags};"

        return unsettag_statement

    @abstractmethod
    def _generate_statement(self, **kwargs):
        pass

    def generate_statement_object(self) -> AccountObjectStatement:
        """
            Generate a AccountObjectStatement object, which contains the SQL code required
            to perform the desired action on the db object.
        Returns:
            AccountObjectStatement - containing the SQL statement(s) to achieve the desired result.
        """
        return AccountObjectStatement(
            name=self.name,
            statement=self._generate_statement(),
            object_type=self.object_type,
        )

    @abstractmethod
    def _generate_statement(self, **kwargs):
        pass

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


class StorageIntegrationAction(AccountObjectAction):
    def __init__(
        self,
        name: str,
        action_type: AccountObjectActionType,
        current_instance: StorageIntegrationInstance = None,
        desired_instance: StorageIntegrationInstance = None,

        **_,
    ):
        super().__init__(
            name=name,
            object_type=AccountObjectType.STORAGEINTEGRATION,
            action_type=action_type,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )

    def _generate_statement(self, **_):
        if self.action_type == AccountObjectActionType.ADD:
            return self._generate_create_statement(self.desired_instance)
        elif self.action_type == AccountObjectActionType.ALTER:
            return self._generate_alter_statement(self.current_instance, self.desired_instance)
        elif self.action_type == AccountObjectActionType.DROP:
            return f"DROP STORAGE INTEGRATION {self.full_name};"
        elif self.action_type == AccountObjectActionType.GRANT:
            return self._generate_grant_statements()
        elif self.action_type == AccountObjectActionType.REVOKE:
            return self._generate_revoke_statements()
        elif self.action_type == AccountObjectActionType.SETTAG:
            return self._generate_settag_statements()
        elif self.action_type == AccountObjectActionType.UNSETTAG:
            return self._generate_unsettag_statements()

    def __str__(self):
        return f"StorageIntegrationAction: {self.id}"

    def __repr__(self):
        return f"StorageIntegrationAction: {self.id}"

    @staticmethod
    def _generate_create_statement(desired_instance: StorageIntegrationInstance) -> str:
        """
        Generate create storage integration statements for storage integrations in the desired state but not in the current state.
        Generate grant statements for those storage integrations. Set tags on those storage integrations.
        """
        statements = []

        allowed_locs_str = dict_and_list_util.list_to_string_representation(desired_instance.storage_allowed_locations)
        blocked_locs_str = dict_and_list_util.list_to_string_representation(desired_instance.storage_blocked_locations)

        comment = desired_instance.comment.replace("'", "''")
        comment = comment.replace("\\", "\\\\")

        if desired_instance.storage_provider == "AZURE":
            create_statement = inspect.cleandoc(f"""
                                                CREATE STORAGE INTEGRATION "{desired_instance.name}"
                                                TYPE = EXTERNAL_STAGE
                                                STORAGE_PROVIDER = {desired_instance.storage_provider}
                                                AZURE_TENANT_ID = '{desired_instance.azure_tenant_id}'
                                                ENABLED = {desired_instance.enabled}
                                                STORAGE_ALLOWED_LOCATIONS = ({allowed_locs_str})
                                                COMMENT = '{comment}'
                                                """)
            
            if desired_instance.storage_blocked_locations:
                create_statement += f"""\nSTORAGE_BLOCKED_LOCATIONS = ({blocked_locs_str})"""
        else:
            error_message = f"The storage provider {desired_instance.storage_provider} is not supported for storage integrations."
            raise ValueError(error_message)

        create_statement = f"""{create_statement};"""

        statements.append(create_statement)

        if hasattr(desired_instance, "tags") and desired_instance.tags:
            tag_statements=AccountObjectAction._generate_settag_statements_for_new_objects(desired_instance)
            statements.append(tag_statements)

        if hasattr(desired_instance, "grants") and desired_instance.grants:
            grant_statements=AccountObjectAction._generate_grant_statements_for_new_objects(desired_instance)
            statements.append(grant_statements)

        return "\n".join(statements)

    @staticmethod
    def _generate_alter_statement(
        current_instance: StorageIntegrationInstance,
        desired_instance: StorageIntegrationInstance,
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a storage integration to the desired state.
        """
        statements = []

        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        # enabled
        if updated_instance.enabled != desired_instance.enabled:
            statements.append(
                f"ALTER STORAGE INTEGRATION {current_instance.full_name} SET ENABLED = {desired_instance.enabled};"
            )
            updated_instance.enabled = desired_instance.enabled

        # comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER STORAGE INTEGRATION {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                comment = comment.replace("\\", "\\\\")

                statements.append(
                    f"ALTER STORAGE INTEGRATION {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        # storage_allowed_locations
        if updated_instance.storage_allowed_locations != desired_instance.storage_allowed_locations:
            if desired_instance.storage_allowed_locations is not None:
                allowed_locs_str = dict_and_list_util.list_to_string_representation(desired_instance.storage_allowed_locations)
                if allowed_locs_str:
                    statements.append(
                            f"ALTER STORAGE INTEGRATION {current_instance.full_name} SET STORAGE_ALLOWED_LOCATIONS = ({allowed_locs_str});"
                        )
                    updated_instance.storage_allowed_locations = desired_instance.storage_allowed_locations
                else:                
                    error_message = f"Requiered parameter STORAGE_ALLOWED_LOCATIONS for storage integration {current_instance.full_name} not defined."
                    raise ValueError(error_message)
            else:
                error_message = f"Requiered parameter STORAGE_ALLOWED_LOCATIONS for storage integration {current_instance.full_name} not defined."
                raise ValueError(error_message)

        # storage_blocked_locations
        if updated_instance.storage_blocked_locations != desired_instance.storage_blocked_locations:
            if desired_instance.storage_blocked_locations is not None:
                blocked_locs_str = dict_and_list_util.list_to_string_representation(desired_instance.storage_blocked_locations)
                if blocked_locs_str:
                    statements.append(
                            f"ALTER STORAGE INTEGRATION {current_instance.full_name} SET STORAGE_BLOCKED_LOCATIONS = ({blocked_locs_str});"
                        )
                    updated_instance.storage_blocked_locations = desired_instance.storage_blocked_locations
                else:
                    statements.append(
                            f"ALTER STORAGE INTEGRATION {current_instance.full_name} UNSET STORAGE_BLOCKED_LOCATIONS;"
                        )
                    updated_instance.storage_blocked_locations = []
            else:
                statements.append(
                            f"ALTER STORAGE INTEGRATION {current_instance.full_name} UNSET STORAGE_BLOCKED_LOCATIONS;"
                        )
                updated_instance.storage_blocked_locations = None

        # azure tenant id -> only if storage_provider = AZURE
        if desired_instance.storage_provider == "AZURE" and updated_instance.azure_tenant_id != desired_instance.azure_tenant_id:
            statements.append(
                f"ALTER STORAGE INTEGRATION {current_instance.full_name} SET AZURE_TENANT_ID = '{desired_instance.azure_tenant_id}';"
            )
            updated_instance.azure_tenant_id = desired_instance.azure_tenant_id

        if updated_instance == desired_instance:
            return "\n".join(statements)
        else:
            property_error_message = AccountObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance, ["tags", "grants"]
            )
            error_message = f"Required ALTER STORAGE INTEGRATION is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-storage-integration.html"
            raise ValueError(error_message)


class WarehouseAction(AccountObjectAction):
    def __init__(
        self,
        name: str,
        action_type: AccountObjectActionType,
        snow_client_config: SnowClientConfig,
        current_instance: WarehouseInstance = None,
        desired_instance: WarehouseInstance = None,
        
        **_,
    ):
        super().__init__(
            name=name,
            object_type=AccountObjectType.WAREHOUSE,
            action_type=action_type,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )
        self.snow_client_config=snow_client_config

    def _generate_statement(self, **_):
        if self.action_type == AccountObjectActionType.ADD:
            return self._generate_create_statement(self.desired_instance, self.snow_client_config)
        elif self.action_type == AccountObjectActionType.ALTER:
            return self._generate_alter_statement(self.current_instance, self.desired_instance)
        elif self.action_type == AccountObjectActionType.DROP:
            return f"DROP WAREHOUSE {self.full_name};"
        elif self.action_type == AccountObjectActionType.GRANT:
            return self._generate_grant_statements()
        elif self.action_type == AccountObjectActionType.REVOKE:
            return self._generate_revoke_statements()
        elif self.action_type == AccountObjectActionType.SETTAG:
            return self._generate_settag_statements()
        elif self.action_type == AccountObjectActionType.UNSETTAG:
            return self._generate_unsettag_statements()

    def __str__(self):
        return f"WarehouseAction: {self.id}"

    def __repr__(self):
        return f"WarehouseAction: {self.id}"

    @staticmethod
    def _generate_create_statement(desired_instance: WarehouseInstance, snow_client_config: SnowClientConfig) -> str:
        """
        Generate create warehouse statements for warehouses in the desired state but not in the current state and generate grant statements for those warehouses.
        Change the current warehouse back to the configured warehouse, since creating a virtual warehouse automatically sets it as the active/current warehouse for the current session.
        Generate grant statements for those warehouses. Set tags on those warehouses.
        """
        statements=[]

        if snow_client_config.warehouse:

            comment = desired_instance.comment.replace("'", "''")
            comment = comment.replace("\\", "\\\\")

            create_statement = inspect.cleandoc(f"""
                                                CREATE WAREHOUSE "{desired_instance.name}"
                                                INITIALLY_SUSPENDED = TRUE
                                                WAREHOUSE_TYPE = '{desired_instance.type}'
                                                WAREHOUSE_SIZE = '{desired_instance.size}'
                                                MAX_CLUSTER_COUNT = {desired_instance.max_cluster_count}
                                                MIN_CLUSTER_COUNT = {desired_instance.min_cluster_count}
                                                SCALING_POLICY = '{desired_instance.scaling_policy}'
                                                AUTO_SUSPEND = {desired_instance.auto_suspend}
                                                AUTO_RESUME = {desired_instance.auto_resume}
                                                COMMENT = '{comment}'
                                                """)
            
            if desired_instance.resource_monitor and not desired_instance.resource_monitor=='null':
                create_statement += f"\nRESOURCE_MONITOR = '{desired_instance.resource_monitor}'"
            if desired_instance.enable_query_acceleration:
                create_statement += f"\nENABLE_QUERY_ACCELERATION = {desired_instance.enable_query_acceleration}"
            if desired_instance.query_acceleration_max_scale_factor:
                create_statement += f"\nQUERY_ACCELERATION_MAX_SCALE_FACTOR = {desired_instance.query_acceleration_max_scale_factor}"
            if desired_instance.max_concurrency_level:
                create_statement += f"\nMAX_CONCURRENCY_LEVEL = {desired_instance.max_concurrency_level}"
            if desired_instance.statement_queued_timeout_in_seconds:
                create_statement += f"\nSTATEMENT_QUEUED_TIMEOUT_IN_SECONDS = {desired_instance.statement_queued_timeout_in_seconds}"
            if desired_instance.statement_timeout_in_seconds:
                create_statement += f"\nSTATEMENT_TIMEOUT_IN_SECONDS = {desired_instance.statement_timeout_in_seconds}"
            if desired_instance.tags:
                statement_tags_ = []
                for tag, tag_value in desired_instance.tags.items():
                    statement_tags_.append(f"{tag} = '{tag_value}'")
                statement_tags_ = ", ".join(statement_tags_)
                statement_tags = f"\nWITH TAG ({statement_tags_})"
                create_statement += statement_tags

            create_statement = f"""{create_statement};\nUSE WAREHOUSE {snow_client_config.warehouse};"""

        else:
            error_message = f"No default warehouse retrieved. Please check Snowflake client configuration."
            raise ValueError(error_message) 
        
        statements.append(create_statement)

        if hasattr(desired_instance, "grants") and desired_instance.grants:
            grant_statements=AccountObjectAction._generate_grant_statements_for_new_objects(desired_instance)
            statements.append(grant_statements)
            
        return "\n".join(statements)

    @staticmethod
    def _generate_alter_statement(
        current_instance: WarehouseInstance,
        desired_instance: WarehouseInstance,
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a warehouse to the desired state.
        """
        statements = []

        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        #warehouse_type
        if updated_instance.type != desired_instance.type:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET WAREHOUSE_TYPE = '{desired_instance.type}';"
            )
            updated_instance.type = desired_instance.type

        #warehouse_size
        if updated_instance.size != desired_instance.size:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET WAREHOUSE_SIZE = '{desired_instance.size}';"
            )
            updated_instance.size = desired_instance.size

        #max_cluster_count
        if updated_instance.max_cluster_count != desired_instance.max_cluster_count:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET MAX_CLUSTER_COUNT = {desired_instance.max_cluster_count};"
            )
            updated_instance.max_cluster_count = desired_instance.max_cluster_count

        #min_cluster_count
        if updated_instance.min_cluster_count != desired_instance.min_cluster_count:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET MIN_CLUSTER_COUNT = {desired_instance.min_cluster_count};"
            )
            updated_instance.min_cluster_count = desired_instance.min_cluster_count

        #scaling_policy
        if updated_instance.scaling_policy != desired_instance.scaling_policy:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET SCALING_POLICY = '{desired_instance.scaling_policy}';"
            )
            updated_instance.scaling_policy = desired_instance.scaling_policy

        #auto_suspend
        if updated_instance.auto_suspend != desired_instance.auto_suspend:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET AUTO_SUSPEND = {desired_instance.auto_suspend};"
            )
            updated_instance.auto_suspend = desired_instance.auto_suspend

        #auto_resume
        if updated_instance.auto_resume != desired_instance.auto_resume:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET AUTO_RESUME = {desired_instance.auto_resume};"
            )
            updated_instance.auto_resume = desired_instance.auto_resume

        #resource_monitor
        if updated_instance.resource_monitor != desired_instance.resource_monitor:
            if desired_instance.resource_monitor and not desired_instance.resource_monitor=='null':
                statements.append(
                    f"ALTER WAREHOUSE {current_instance.full_name} SET RESOURCE_MONITOR = '{desired_instance.resource_monitor}';"
                )
            else:
                statements.append(
                    f"ALTER WAREHOUSE {current_instance.full_name} UNSET RESOURCE_MONITOR;"
                )
            updated_instance.resource_monitor = desired_instance.resource_monitor

        #comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER WAREHOUSE {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                comment = comment.replace("\\", "\\\\")

                statements.append(
                    f"ALTER WAREHOUSE {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment

        #enable_query_acceleration
        if updated_instance.enable_query_acceleration != desired_instance.enable_query_acceleration:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET ENABLE_QUERY_ACCELERATION = {desired_instance.enable_query_acceleration};"
            )
            updated_instance.enable_query_acceleration = desired_instance.enable_query_acceleration

        #query_acceleration_max_scale_factor
        if updated_instance.query_acceleration_max_scale_factor != desired_instance.query_acceleration_max_scale_factor:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET QUERY_ACCELERATION_MAX_SCALE_FACTOR = {desired_instance.query_acceleration_max_scale_factor};"
            )
            updated_instance.query_acceleration_max_scale_factor = desired_instance.query_acceleration_max_scale_factor

        #max_concurrency_level
        if updated_instance.max_concurrency_level != desired_instance.max_concurrency_level:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET MAX_CONCURRENCY_LEVEL = {desired_instance.max_concurrency_level};"
            )
            updated_instance.max_concurrency_level = desired_instance.max_concurrency_level

        #statement_queued_timeout_in_seconds
        if updated_instance.statement_queued_timeout_in_seconds != desired_instance.statement_queued_timeout_in_seconds:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = {desired_instance.statement_queued_timeout_in_seconds};"
            )
            updated_instance.statement_queued_timeout_in_seconds = desired_instance.statement_queued_timeout_in_seconds

        #statement_timeout_in_seconds
        if updated_instance.statement_timeout_in_seconds != desired_instance.statement_timeout_in_seconds:
            statements.append(
                f"ALTER WAREHOUSE {current_instance.full_name} SET STATEMENT_TIMEOUT_IN_SECONDS = {desired_instance.statement_timeout_in_seconds};"
            )
            updated_instance.statement_timeout_in_seconds = desired_instance.statement_timeout_in_seconds

        if updated_instance == desired_instance:
            return "\n".join(statements)
        else:
            property_error_message = AccountObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance, ["tags", "grants"]
            )
            error_message = f"Required ALTER WAREHOUSE is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-warehouse.html"
            raise ValueError(error_message)
        
class ShareAction(AccountObjectAction):
    def __init__(
        self,
        name: str,
        action_type: AccountObjectActionType,
        snow_client_config: SnowClientConfig,
        current_instance: ShareInstance = None,
        desired_instance: ShareInstance = None,
        
        **_,
    ):
        super().__init__(
            name=name,
            object_type=AccountObjectType.SHARE,
            action_type=action_type,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )
        self.snow_client_config=snow_client_config

    def _generate_statement(self, **_):
        if self.action_type == AccountObjectActionType.ADD:
            return self._generate_create_statement(self.desired_instance, self.snow_client_config)
        elif self.action_type == AccountObjectActionType.ALTER:
            return self._generate_alter_statement(self.current_instance, self.desired_instance)
        elif self.action_type == AccountObjectActionType.DROP:
            return f"DROP SHARE {self.full_name};"
        elif self.action_type == AccountObjectActionType.GRANT:
            return self._generate_grant_statements()
        elif self.action_type == AccountObjectActionType.REVOKE:
            return self._generate_revoke_statements()
        elif self.action_type == AccountObjectActionType.SETTAG:
            return self._generate_settag_statements()
        elif self.action_type == AccountObjectActionType.UNSETTAG:
            return self._generate_unsettag_statements()

    def __str__(self):
        return f"ShareAction: {self.id}"

    def __repr__(self):
        return f"ShareAction: {self.id}"

    @staticmethod
    def _generate_create_statement(desired_instance: ShareInstance, snow_client_config: SnowClientConfig) -> str:
        """
        Generate "create share" statements for shares in the desired state but not in the current state.
        Grant usage privlege on database to share. Add accounts to share. Set tags on share.
        """
        statements=[]

        comment = desired_instance.comment.replace("'", "''")
        comment = comment.replace("\\", "\\\\")

        create_statement = inspect.cleandoc(f"""
                                            CREATE SHARE "{desired_instance.name}"
                                            COMMENT = '{comment}';
                                            """)
        
        if desired_instance.database_name:
            create_statement += f"\nGRANT USAGE ON DATABASE {desired_instance.database_name} TO SHARE {desired_instance.name};"
        
        if desired_instance.accounts:
            accounts_str = dict_and_list_util.list_to_string_representation(desired_instance.accounts)
            create_statement += f"\nALTER SHARE {desired_instance.name} SET ACCOUNTS= {accounts_str};"
        
        statements.append(create_statement)

        if hasattr(desired_instance, "tags") and desired_instance.tags:
            tag_statements=AccountObjectAction._generate_settag_statements_for_new_objects(desired_instance)
            statements.append(tag_statements)

        return "\n".join(statements)

    @staticmethod
    def _generate_alter_statement(
        current_instance: ShareInstance,
        desired_instance: ShareInstance,
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a share to the desired state.
        """
        statements = []

        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added


        # database_name
        if updated_instance.database_name.upper() != desired_instance.database_name.upper():
            if updated_instance.database_name:
                statements.append(
                        f"REVOKE USAGE ON DATABASE {updated_instance.database_name} FROM SHARE {current_instance.full_name};"
                    )
            if desired_instance.database_name:
                statements.append(
                        f"GRANT USAGE ON DATABASE {desired_instance.database_name} TO SHARE {current_instance.full_name};"
                    )
            updated_instance.database_name = desired_instance.database_name

        # accounts
        if updated_instance.accounts != desired_instance.accounts:
            if desired_instance.accounts:
                accounts_str = dict_and_list_util.list_to_string_representation(desired_instance.accounts)
                statements.append(
                        f"ALTER SHARE {current_instance.full_name} SET ACCOUNTS= {accounts_str};"
                    )
            else:
                statements.append(
                        f"ALTER SHARE {current_instance.full_name} UNSET ACCOUNTS;"
                    )
            updated_instance.accounts = desired_instance.accounts

        #comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER SHARE {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                comment = comment.replace("\\", "\\\\")

                statements.append(
                    f"ALTER SHARE {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment


        if updated_instance == desired_instance:
            return "\n".join(statements)
        else:
            property_error_message = AccountObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance, ["tags"]
            )
            error_message = f"Required ALTER SHARE is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-share.html"
            raise ValueError(error_message)
        
class DatabaseAction(AccountObjectAction):
    def __init__(
        self,
        name: str,
        action_type: AccountObjectActionType,
        snow_client_config: SnowClientConfig,
        current_instance: DatabaseInstance = None,
        desired_instance: DatabaseInstance = None,
        
        **_,
    ):
        super().__init__(
            name=name,
            object_type=AccountObjectType.DATABASE,
            action_type=action_type,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )
        self.snow_client_config=snow_client_config

    def _generate_statement(self, **_):
        if self.action_type == AccountObjectActionType.ADD:
            return self._generate_create_statement(self.desired_instance, self.snow_client_config)
        elif self.action_type == AccountObjectActionType.ALTER:
            return self._generate_alter_statement(self.current_instance, self.desired_instance)
        elif self.action_type == AccountObjectActionType.DROP:
            return f"DROP DATABASE {self.full_name};"
        elif self.action_type == AccountObjectActionType.GRANT:
            return self._generate_grant_statements()
        elif self.action_type == AccountObjectActionType.REVOKE:
            return self._generate_revoke_statements()
        elif self.action_type == AccountObjectActionType.SETTAG:
            return self._generate_settag_statements()
        elif self.action_type == AccountObjectActionType.UNSETTAG:
            return self._generate_unsettag_statements()

    def __str__(self):
        return f"DatabaseAction: {self.id}"

    def __repr__(self):
        return f"DatabaseAction: {self.id}"

    @staticmethod
    def _generate_create_statement(desired_instance: DatabaseInstance, snow_client_config: SnowClientConfig) -> str:
        """
        Generate "create database" statements for databases in the desired state but not in the current state.
        Set tags on database.
        """
        statements=[]

        comment = desired_instance.comment.replace("'", "''")
        comment = comment.replace("\\", "\\\\")

        create_statement = inspect.cleandoc(f"""
                                            CREATE {desired_instance.transient} DATABASE "{desired_instance.name}"
                                            DATA_RETENTION_TIME_IN_DAYS = {desired_instance.data_retention_time_in_days}
                                            MAX_DATA_EXTENSION_TIME_IN_DAYS  = {desired_instance.max_data_extension_time_in_days}
                                            DEFAULT_DDL_COLLATION  = '{desired_instance.default_ddl_collation}'
                                            COMMENT = '{comment}'
                                            """)
        
        if desired_instance.log_level and not desired_instance.log_level.upper()=='OFF':
            create_statement += f"\nLOG_LEVEL = '{desired_instance.log_level}'"

        if desired_instance.suspend_task_after_num_failures and not desired_instance.suspend_task_after_num_failures==0:
            create_statement += f"\nSUSPEND_TASK_AFTER_NUM_FAILURES = {desired_instance.suspend_task_after_num_failures}"

        if desired_instance.trace_level and not desired_instance.trace_level.upper()=='OFF':
            create_statement += f"\nTRACE_LEVEL = '{desired_instance.trace_level}'"

        if desired_instance.user_task_managed_initial_warehouse_size and not desired_instance.user_task_managed_initial_warehouse_size.upper()=='MEDIUM':
            create_statement += f"\nUSER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = '{desired_instance.user_task_managed_initial_warehouse_size}'"

        if desired_instance.user_task_timeout_ms and not desired_instance.user_task_timeout_ms==3600000:
            create_statement += f"\nUSER_TASK_TIMEOUT_MS = {desired_instance.user_task_timeout_ms}"

        if desired_instance.tags:
                statement_tags_ =[]
                for tag, tag_value in desired_instance.tags.items():
                    statement_tags_.append(f"{tag} = '{tag_value}'")
                statement_tags_ = ", ".join(statement_tags_)
                statement_tags = f"\nWITH TAG ({statement_tags_})"
                create_statement += statement_tags

        create_statement = f"""{create_statement};"""

        statements.append(create_statement)

        if hasattr(desired_instance, "grants") and desired_instance.grants:
            grant_statements=AccountObjectAction._generate_grant_statements_for_new_objects(desired_instance)
            statements.append(grant_statements)

        return "\n".join(statements)

    @staticmethod
    def _generate_alter_statement(
        current_instance: DatabaseInstance,
        desired_instance: DatabaseInstance,
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a database to the desired state.
        """
        statements = []

        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added

        #data_retention_time_in_days
        if updated_instance.data_retention_time_in_days != desired_instance.data_retention_time_in_days:
            if desired_instance.data_retention_time_in_days is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET DATA_RETENTION_TIME_IN_DAYS;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET DATA_RETENTION_TIME_IN_DAYS = {desired_instance.data_retention_time_in_days};"
                )
            updated_instance.data_retention_time_in_days = desired_instance.data_retention_time_in_days

        #max_data_extension_time_in_days 
        if updated_instance.max_data_extension_time_in_days  != desired_instance.max_data_extension_time_in_days:
            if desired_instance.max_data_extension_time_in_days is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET MAX_DATA_EXTENSION_TIME_IN_DAYS;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET MAX_DATA_EXTENSION_TIME_IN_DAYS = {desired_instance.max_data_extension_time_in_days};"
                )
            updated_instance.max_data_extension_time_in_days = desired_instance.max_data_extension_time_in_days

        #default_ddl_collation  
        if updated_instance.default_ddl_collation  != desired_instance.default_ddl_collation:
            if desired_instance.default_ddl_collation is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET DEFAULT_DDL_COLLATION;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET DEFAULT_DDL_COLLATION = '{desired_instance.default_ddl_collation}';"
                )
            updated_instance.default_ddl_collation = desired_instance.default_ddl_collation

        #log_level
        if updated_instance.log_level != desired_instance.log_level:
            if desired_instance.log_level is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET LOG_LEVEL;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET LOG_LEVEL = '{desired_instance.log_level}';"
                )
            updated_instance.log_level = desired_instance.log_level

        #suspend_task_after_num_failures
        if updated_instance.suspend_task_after_num_failures != desired_instance.suspend_task_after_num_failures:
            if desired_instance.suspend_task_after_num_failures is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET SUSPEND_TASK_AFTER_NUM_FAILURES;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET SUSPEND_TASK_AFTER_NUM_FAILURES = {desired_instance.suspend_task_after_num_failures};"
                )
            updated_instance.suspend_task_after_num_failures = desired_instance.suspend_task_after_num_failures

        #trace_level
        if updated_instance.trace_level != desired_instance.trace_level:
            if desired_instance.trace_level is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET TRACE_LEVEL;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET TRACE_LEVEL = '{desired_instance.trace_level}';"
                )
            updated_instance.trace_level = desired_instance.trace_level

        #user_task_managed_initial_warehouse_size
        if updated_instance.user_task_managed_initial_warehouse_size != desired_instance.user_task_managed_initial_warehouse_size:
            if desired_instance.user_task_managed_initial_warehouse_size is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = '{desired_instance.user_task_managed_initial_warehouse_size}';"
                )
            updated_instance.user_task_managed_initial_warehouse_size = desired_instance.user_task_managed_initial_warehouse_size

        #user_task_timeout_ms
        if updated_instance.user_task_timeout_ms != desired_instance.user_task_timeout_ms:
            if desired_instance.user_task_timeout_ms is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET USER_TASK_TIMEOUT_MS;"
                )
            else:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET USER_TASK_TIMEOUT_MS = {desired_instance.user_task_timeout_ms};"
                )
            updated_instance.user_task_timeout_ms = desired_instance.user_task_timeout_ms

        #comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} UNSET COMMENT;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                comment = comment.replace("\\", "\\\\")

                statements.append(
                    f"ALTER DATABASE {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment


        if updated_instance == desired_instance:
            return "\n".join(statements)
        else:
            property_error_message = AccountObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance, ["tags", "grants"]
            )
            error_message = f"Required ALTER DATABASE is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-database.html"
            raise ValueError(error_message)
        
class ExternalVolumeAction(AccountObjectAction):
    def __init__(
        self,
        name: str,
        action_type: AccountObjectActionType,
        snow_client_config: SnowClientConfig,
        current_instance: ExternalVolumeInstance = None,
        desired_instance: ExternalVolumeInstance = None,
        
        **_,
    ):
        super().__init__(
            name=name,
            object_type=AccountObjectType.EXTERNALVOLUME,
            action_type=action_type,
            current_instance=current_instance,
            desired_instance=desired_instance,
        )
        self.snow_client_config=snow_client_config

    def _generate_statement(self, **_):
        if self.action_type == AccountObjectActionType.ADD:
            return self._generate_create_statement(self.desired_instance)
        elif self.action_type == AccountObjectActionType.ALTER:
            return self._generate_alter_statement(self.current_instance, self.desired_instance)
        elif self.action_type == AccountObjectActionType.DROP:
            if self.current_instance.used_by_iceberg_tables:
                raise ValueError(f'External volume {self.current_instance.full_name} cannot be dropped because it has active iceberg table(s) using it.')
            else:
                return f"DROP EXTERNAL VOLUME {self.full_name};"
        elif self.action_type == AccountObjectActionType.GRANT:
            return self._generate_grant_statements()
        elif self.action_type == AccountObjectActionType.REVOKE:
            return self._generate_revoke_statements()
        elif self.action_type == AccountObjectActionType.SETTAG:
            return self._generate_settag_statements()
        elif self.action_type == AccountObjectActionType.UNSETTAG:
            return self._generate_unsettag_statements()

    def __str__(self):
        return f"ExternalVolumeAction: {self.id}"

    def __repr__(self):
        return f"ExternalVolumeAction: {self.id}"

    @staticmethod
    def _generate_storage_location_string(storage_location_name: str, storage_location: dict) -> str:
        """
        Generate a string defining a storage location which can be used in CREATE EXTERNAL VOLUME and ALTER EXTERNAL VOLUME statements.
        """

        storage_location_params_str = '( '
        storage_location_params_str += f"  \n name = '{storage_location_name}'"
        for param, value in storage_location.items():
            if param == "encryption":
                encryption_str = ''
                for encryption_param, encryption_value in value.items():
                    encryption_str += f" \n {encryption_param} = '{encryption_value}'"
                storage_location_params_str += f' \n {param} = ( {encryption_str} )'
            else:
                storage_location_params_str += f" \n {param} = '{value}'"
        
        storage_location_params_str += ' )'
        return storage_location_params_str

    def _generate_create_statement(self, desired_instance: ExternalVolumeInstance, or_replace: bool = False) -> str:
        """
        Generate "create external volume" statements for external volumes in the desired state but not in the current state.
        Grant usage privlege on database to external volume. Add accounts to external volume. Set tags on external volume.
        """
        statements=[]

        comment = desired_instance.comment.replace("'", "''")
        comment = comment.replace("\\", "\\\\")

        storage_locations_str = "\n ,".join([self._generate_storage_location_string(storage_location_name, storage_location_params) for storage_location_name, storage_location_params in desired_instance.storage_locations.items()])

        if or_replace:
            or_replace_str = 'OR REPLACE'
        else:
            or_replace_str = ''

        create_statement = inspect.cleandoc(f"""
                                            CREATE {or_replace_str} EXTERNAL VOLUME "{desired_instance.name}"
                                            STORAGE_LOCATIONS = ( {storage_locations_str} )
                                            ALLOW_WRITES = {desired_instance.allow_writes}
                                            COMMENT = '{comment}'
                                            """)
        
        create_statement = f"""{create_statement};"""

        statements.append(create_statement)

        if hasattr(desired_instance, "grants") and desired_instance.grants:
            grant_statements=AccountObjectAction._generate_grant_statements_for_new_objects(desired_instance)
            statements.append(grant_statements)

        if hasattr(desired_instance, "tags") and desired_instance.tags:
            raise ValueError(f'Tags are currently not supported for object type {AccountObjectType.EXTERNALVOLUME.value}. Object name: {desired_instance.name}')

        return "\n".join(statements)

    def _generate_alter_statement(
        self,
        current_instance: ExternalVolumeInstance,
        desired_instance: ExternalVolumeInstance,
    ) -> str:
        """
        Generate sql statement(s) to change the current state of a external volume to the desired state.
        """
        statements = []

        updated_instance = copy.deepcopy(
            current_instance
        )  # variable used to track changes for which statements are added


        # storage_locations

        if updated_instance.storage_locations != desired_instance.storage_locations:
            for desired_storage_location_name, desired_storage_location in desired_instance.storage_locations.items():
                
                desired_storage_location_string = self._generate_storage_location_string(desired_storage_location_name, desired_storage_location)

                if desired_storage_location_name not in updated_instance.storage_locations:
                    statements.append(
                            f"ALTER EXTERNAL VOLUME {updated_instance.full_name} ADD STORAGE_LOCATION = {desired_storage_location_string};"
                        )
            
                if desired_storage_location_name in updated_instance.storage_locations and desired_storage_location != updated_instance.storage_locations[desired_storage_location_name]:

                    if len(updated_instance.storage_locations) == 1:
                        # when altering the only existing storage location there is no option for ALTER EXTERNAL VOLUME
                        # -> altering only works with "remove" + "add" 
                        # -> first "remove" means there is no storage location defined which is not allowed 
                        # -> first "add" means adding a storage location with the same name which is also not allowed 
                        # TODO evaluate if it would be better to use a dummy storage location inbetween instead of "CREATE OR REPLACE"
                        if current_instance.used_by_iceberg_tables:
                            raise ValueError(f"The External volume {current_instance.full_name} cannot be replaced because it has active iceberg table(s) using it. Note: When altering the only existing storage location the external volume is re-created.")
                        else:
                            statements.append(self._generate_create_statement(desired_instance, or_replace= True))

                    else:
                        if updated_instance.active_storage_location.lower() == desired_storage_location_name.lower():
                            raise ValueError(f'The active storage location {desired_storage_location_name} cannot be removed on external volume {current_instance.full_name}. Note: When altering an existing storage location the storage location is updated by "remove and add".')
                        else:
                            statements.append(
                                    f"ALTER EXTERNAL VOLUME {updated_instance.full_name} REMOVE STORAGE_LOCATION '{desired_storage_location_name}';"
                                )
                            statements.append(
                                    f"ALTER EXTERNAL VOLUME {updated_instance.full_name} ADD STORAGE_LOCATION = {desired_storage_location_string};"
                                )


            for updated_storage_location_name in updated_instance.storage_locations:

                if updated_storage_location_name not in desired_instance.storage_locations:
                    if updated_instance.active_storage_location.lower() == updated_storage_location_name.lower():
                        raise ValueError(f'The active storage location {updated_storage_location_name} cannot be removed on external volume {current_instance.full_name}.')
                    else:
                        statements.append(
                                f"ALTER EXTERNAL VOLUME {updated_instance.full_name} REMOVE STORAGE_LOCATION '{updated_storage_location_name}';"
                            )

            updated_instance.storage_locations = desired_instance.storage_locations

        # allow_writes
        if updated_instance.allow_writes != desired_instance.allow_writes:

            statements.append(
                    f"ALTER EXTERNAL VOLUME {current_instance.full_name} SET ALLOW_WRITES =  {desired_instance.allow_writes};"
                )

            updated_instance.allow_writes = desired_instance.allow_writes

        #comment
        if updated_instance.comment != desired_instance.comment:
            if desired_instance.comment is None:
                statements.append(
                    f"ALTER EXTERNAL VOLUME {current_instance.full_name} = NULL;"
                )
            else:
                comment = desired_instance.comment.replace("'", "''")
                comment = comment.replace("\\", "\\\\")

                statements.append(
                    f"ALTER EXTERNAL VOLUME {current_instance.full_name} SET COMMENT = '{comment}';"
                )
            updated_instance.comment = desired_instance.comment


        if updated_instance == desired_instance:
            return "\n".join(statements)
        else:
            property_error_message = AccountObjectAction._alter_statement_error_summary(
                updated_instance, desired_instance, ["tags", "grants"]
            )
            error_message = f"Required ALTER EXTERNAL VOLUME is not supported for {current_instance.full_name} (for {property_error_message}), refer to https://docs.snowflake.com/en/sql-reference/sql/alter-external-volume.html"
            raise ValueError(error_message)