
from typing import Dict
import aceutils.misc_utils as misc_utils
from aceaccount.core.model_account_object import AccountObject
from aceaccount.core.model_account_object_sql_entities import AccountObjectType

class AccountObjectInstance(AccountObject):
    """
    Base object for storing basic information about an account object
    Only for inherit usage
    """

    def __init__(self, result, object_type: AccountObjectType):
        """
            inits a new instance
        Args:
            result: any - resultset entry for this entity
        """
        super().__init__(result["OBJECT_NAME"], object_type)

    def __eq__(self, other: "AccountObjectInstance") -> bool:
        return self.object_type == other.object_type and self.name == other.name

    @staticmethod
    def factory(object_type, metadata_query_result: Dict, grants_included: bool=True, tags_included: bool=True):
        mapping = {
            AccountObjectType.STORAGEINTEGRATION: StorageIntegrationInstance,
            AccountObjectType.WAREHOUSE: WarehouseInstance,
            AccountObjectType.SHARE: ShareInstance,
            AccountObjectType.DATABASE: DatabaseInstance,
            AccountObjectType.EXTERNALVOLUME: ExternalVolumeInstance,
        }
        return mapping[object_type](metadata_query_result=metadata_query_result, grants_included=grants_included, tags_included=tags_included)
    
    @staticmethod
    def _case_sensitivity_handling(name):
        return name.upper()
    
class StorageIntegrationInstance(AccountObjectInstance):
    """
    Account object instance of a single storage integration
    """

    def __init__(self, metadata_query_result: Dict, grants_included: bool=True, tags_included: bool=True):
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, AccountObjectType.STORAGEINTEGRATION)
        
        self.type = metadata_query_result["type"].upper()  # TODO: check if we need to compare this property
        self.enabled = misc_utils.string_or_bool_to_bool( metadata_query_result["enabled"])
        self.storage_provider = metadata_query_result["storage_provider"].upper()
        self.azure_tenant_id = metadata_query_result.get("azure_tenant_id", '')
        self.storage_allowed_locations = metadata_query_result["storage_allowed_locations"]
        self.storage_blocked_locations = metadata_query_result.get("storage_blocked_locations", [])
        self.comment = metadata_query_result.get("comment", '')
        if grants_included and "grants" in metadata_query_result:
            self.grants = metadata_query_result.get("grants", {})
        if tags_included and "tags" in metadata_query_result:
            self.tags = metadata_query_result.get("tags", {})
        
            # TODO: in order to support other cloud providers (AWS, GCP), we'll need to include some kind of switch here
            # self.azure_consent_url = metadata_query_result["azure_consent_url"] # this property can not be set, so we don't need to manage it
            # self.azure_multi_tenant_app_name = metadata_query_result["azure_multi_tenant_app_name"] # this property can not be set, so we don't need to manage it

    def __str__(self):
        return f"StorageIntegrationInstance: {self.id}"

    def __repr__(self):
        return f"StorageIntegrationInstance: {self.id}"

    def __eq__(self, other: "StorageIntegrationInstance") -> bool:
        return (
            super().__eq__(other)
            and self.type == other.type
            and self.enabled == other.enabled
            and self.comment == other.comment
            and self.storage_provider == other.storage_provider
            and self.storage_allowed_locations == other.storage_allowed_locations
            and self.storage_blocked_locations == other.storage_blocked_locations
            and self.azure_tenant_id == other.azure_tenant_id
        )

class WarehouseInstance(AccountObjectInstance):
    """
    Account object instance of a single warehouse
    """

    def __init__(self, metadata_query_result: Dict, grants_included: bool=True, tags_included: bool=True):
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, AccountObjectType.WAREHOUSE)
        
        self.type = metadata_query_result.get("type","STANDARD").upper()
        
        warehouse_size_mapping = self.get_warehouse_size_mapping()
        
        metadata_warehouse_size=metadata_query_result.get("size","XSMALL").upper()

        self.size=warehouse_size_mapping.get(metadata_warehouse_size,"")

        if not self.size:
            error_message = f"Error in definition of warehouse {metadata_query_result['OBJECT_NAME']}: Warehouse size '{metadata_warehouse_size}' not found in mapping! Please define one of the following values 'X-SMALL', 'SMALL', 'MEDIUM', 'LARGE', 'X-LARGE',  '2X-LARGE',  '3X-LARGE', '4X-LARGE', '5X-LARGE', '6X-LARGE'."
            raise ValueError(error_message)

        self.max_cluster_count = metadata_query_result.get("max_cluster_count",1)
        self.min_cluster_count = metadata_query_result.get("min_cluster_count",1)
        self.scaling_policy = metadata_query_result.get("scaling_policy","STANDARD").upper()
        self.auto_suspend = metadata_query_result.get("auto_suspend",600)
        self.auto_resume = misc_utils.string_or_bool_to_bool(metadata_query_result.get("auto_resume", True))
        self.resource_monitor = metadata_query_result.get("resource_monitor",'null')
        self.comment = metadata_query_result.get("comment", '')
        self.enable_query_acceleration = misc_utils.string_or_bool_to_bool(metadata_query_result.get("enable_query_acceleration", False))
        self.query_acceleration_max_scale_factor = metadata_query_result.get("query_acceleration_max_scale_factor",8)
        
        self.max_concurrency_level = metadata_query_result.get("max_concurrency_level",8)
        self.statement_queued_timeout_in_seconds = metadata_query_result.get("statement_queued_timeout_in_seconds",0)
        self.statement_timeout_in_seconds = metadata_query_result.get("statement_timeout_in_seconds",172800)

        if grants_included and "grants" in metadata_query_result:
            self.grants = metadata_query_result.get("grants", {})
        if tags_included and "tags" in metadata_query_result:
            self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"WarehouseInstance: {self.id}"

    def __repr__(self):
        return f"WarehouseInstance: {self.id}"

    def __eq__(self, other: "WarehouseInstance") -> bool:
        return (
            super().__eq__(other)
            and self.type == other.type
            and self.size == other.size
            and self.max_cluster_count == other.max_cluster_count
            and self.min_cluster_count == other.min_cluster_count
            and self.scaling_policy == other.scaling_policy
            and self.auto_suspend == other.auto_suspend
            and self.auto_resume == other.auto_resume
            and self.resource_monitor == other.resource_monitor
            and self.comment == other.comment
            and self.enable_query_acceleration == other.enable_query_acceleration
            and self.query_acceleration_max_scale_factor == other.query_acceleration_max_scale_factor
            and self.max_concurrency_level == other.max_concurrency_level
            and self.statement_queued_timeout_in_seconds == other.statement_queued_timeout_in_seconds
            and self.statement_timeout_in_seconds == other.statement_timeout_in_seconds
        )
    
    @staticmethod
    def get_warehouse_size_mapping():
        warehouse_size_mapping={
            "X-SMALL": "X-SMALL",
            "XSMALL": "X-SMALL",
            "XS": "X-SMALL",
            "SMALL": "SMALL",
            "S": "SMALL",
            "MEDIUM": "MEDIUM",
            "M": "MEDIUM",
            "LARGE": "LARGE",
            "L": "LARGE",
            "X-LARGE": "X-LARGE",
            "XLARGE": "X-LARGE",
            "XL": "X-LARGE",
            "2X-LARGE": "2X-LARGE",
            "X2LARGE": "2X-LARGE",
            "XXLARGE": "2X-LARGE",
            "2XL": "2X-LARGE",
            "3X-LARGE": "3X-LARGE",
            "X3LARGE": "3X-LARGE",
            "XXXLARGE": "3X-LARGE",
            "3XL": "3X-LARGE",
            "4X-LARGE": "4X-LARGE",
            "X4LARGE": "4X-LARGE",
            "4XL": "4X-LARGE",
            "5X-LARGE": "5X-LARGE",
            "X5LARGE": "5X-LARGE",
            "5XL": "5X-LARGE",
            "6X-LARGE": "6X-LARGE",
            "X6LARGE": "6X-LARGE",
            "6XL": "6X-LARGE"
        }
        return warehouse_size_mapping

    
class ShareInstance(AccountObjectInstance):
    """
    Account object instance of a single share
    """

    def __init__(self, metadata_query_result: Dict, grants_included: bool=True, tags_included: bool=True):
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, AccountObjectType.SHARE)

        
        self.database_name = self._case_sensitivity_handling(metadata_query_result.get("database_name",''))
        self.accounts = [account.upper() for account in metadata_query_result.get("accounts",[])]
        #self.share_restrictions = metadata_query_result.get("share_restrictions", {})
        #self.grants_to_share = metadata_query_result.get("grants_to_share", {})
        self.comment = metadata_query_result.get("comment", '')

        if tags_included and "tags" in metadata_query_result:
            self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"ShareInstance: {self.id}"

    def __repr__(self):
        return f"ShareInstance: {self.id}"

    def __eq__(self, other: "ShareInstance") -> bool:
        return (
            super().__eq__(other)
            and self.database_name == other.database_name
            and self.accounts == other.accounts
            #and self.share_restrictions == other.share_restrictions
            #and self.grants_to_share == other.grants_to_share
            and self.comment == other.comment
        )
    
class DatabaseInstance(AccountObjectInstance):
    """
    Account object instance of a single database
    """

    def __init__(self, metadata_query_result: Dict, grants_included: bool=True, tags_included: bool=True):
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, AccountObjectType.DATABASE)
        
        self.transient =  metadata_query_result.get("transient").upper()
        self.data_retention_time_in_days = metadata_query_result.get("data_retention_time_in_days")
        self.max_data_extension_time_in_days = metadata_query_result.get("max_data_extension_time_in_days")
        self.default_ddl_collation = metadata_query_result.get("default_ddl_collation")
        self.log_level = metadata_query_result.get("log_level").upper()
        self.suspend_task_after_num_failures = metadata_query_result.get("suspend_task_after_num_failures")
        self.trace_level = metadata_query_result.get("trace_level").upper()
        
        warehouse_size_mapping = WarehouseInstance.get_warehouse_size_mapping()
        
        metadata_user_task_managed_initial_warehouse_size = metadata_query_result.get("user_task_managed_initial_warehouse_size","").upper()

        self.user_task_managed_initial_warehouse_size=warehouse_size_mapping.get(metadata_user_task_managed_initial_warehouse_size,"")

        if not self.user_task_managed_initial_warehouse_size:
            error_message = f"Error in definition of database {metadata_query_result['OBJECT_NAME']}: user_task_managed_initial_warehouse_size '{metadata_user_task_managed_initial_warehouse_size}' not found in mapping! Please define one of the following values 'X-SMALL', 'SMALL', 'MEDIUM', 'LARGE', 'X-LARGE',  '2X-LARGE',  '3X-LARGE', '4X-LARGE', '5X-LARGE', '6X-LARGE'."
            raise ValueError(error_message)

        self.user_task_timeout_ms = metadata_query_result.get("user_task_timeout_ms")
        self.comment = metadata_query_result.get("comment", '')

        if grants_included and "grants" in metadata_query_result:
            self.grants = metadata_query_result.get("grants", {})
        if tags_included and "tags" in metadata_query_result:
            self.tags = metadata_query_result.get("tags", {})

    def __str__(self):
        return f"DatabaseInstance: {self.id}"

    def __repr__(self):
        return f"DatabaseInstance: {self.id}"

    def __eq__(self, other: "DatabaseInstance") -> bool:
        return (
            super().__eq__(other)
            and self.transient == other.transient
            and self.data_retention_time_in_days == other.data_retention_time_in_days
            and self.max_data_extension_time_in_days == other.max_data_extension_time_in_days
            and self.default_ddl_collation == other.default_ddl_collation
            and self.log_level == other.log_level
            and self.suspend_task_after_num_failures == other.suspend_task_after_num_failures
            and self.trace_level == other.trace_level
            and self.user_task_managed_initial_warehouse_size == other.user_task_managed_initial_warehouse_size
            and self.user_task_timeout_ms == other.user_task_timeout_ms
            and self.comment == other.comment
        )
    
class ExternalVolumeInstance(AccountObjectInstance):
    """
    Account object instance of a single external volume
    """

    def __init__(self, metadata_query_result: Dict, grants_included: bool=True, tags_included: bool=False):
        metadata_query_result["OBJECT_NAME"] = metadata_query_result["name"]
        super().__init__(metadata_query_result, AccountObjectType.EXTERNALVOLUME)
        self.storage_locations = metadata_query_result.get("storage_locations", {})

        for storage_location in self.storage_locations.values():
            if "encryption" not in storage_location:
                storage_location["encryption"] = {"type": "NONE"}
        self.allow_writes = misc_utils.string_or_bool_to_bool(metadata_query_result.get("allow_writes",True))

        if "used_by_iceberg_tables" in metadata_query_result and metadata_query_result["used_by_iceberg_tables"]:
            self.used_by_iceberg_tables = True
        elif "used_by_iceberg_tables" in metadata_query_result and not metadata_query_result["used_by_iceberg_tables"]:
            self.used_by_iceberg_tables = False
        else:
            self.used_by_iceberg_tables = None

        if "active" in metadata_query_result:
            self.active_storage_location = metadata_query_result["active"]
        else:
            self.active_storage_location = None

        self.comment = metadata_query_result.get("comment", '')

        if grants_included and "grants" in metadata_query_result:
            self.grants = metadata_query_result.get("grants", {})

        if tags_included and "tags" in metadata_query_result:
            raise ValueError(f'Tags are currently not supported for object type {AccountObjectType.EXTERNALVOLUME.value}. Object name: {metadata_query_result["name"]}')

    def __str__(self):
        return f"ExternalVolumeInstance: {self.id}"

    def __repr__(self):
        return f"ExternalVolumeInstance: {self.id}"

    def __eq__(self, other: "ExternalVolumeInstance") -> bool:
        return (
            super().__eq__(other)
            and self.storage_locations == other.storage_locations
            and self.allow_writes == other.allow_writes
            and self.comment == other.comment
        )
