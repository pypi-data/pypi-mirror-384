from enum import Enum


class AccountObjectActionType(Enum):
    """
    Enum for valid account operations
    """

    ALTER = "ALTER"
    DROP = "DROP"
    ADD = "ADD"
    REVOKE = "REVOKE"
    GRANT = "GRANT"
    SETTAG = "SETTAG"
    UNSETTAG = "UNSETTAG"


class AccountObjectType(Enum):
    """
    Enum for valid account objects
    """

    STORAGEINTEGRATION = "STORAGEINTEGRATION"
    WAREHOUSE = "WAREHOUSE"
    SHARE = "SHARE"
    DATABASE = "DATABASE"
    EXTERNALVOLUME = "EXTERNALVOLUME"

    @staticmethod
    def get_object_domain_from_object_type(object_type) -> str:
        """
        Get Snowflake object domain by object type.
        """
        mapping_object_type_object_domain = {
            AccountObjectType.STORAGEINTEGRATION: "INTEGRATION",
            AccountObjectType.WAREHOUSE: "WAREHOUSE",
            AccountObjectType.SHARE: "SHARE",
            AccountObjectType.DATABASE: "DATABASE",
            AccountObjectType.EXTERNALVOLUME: "EXTERNAL VOLUME"
        }

        object_domain = mapping_object_type_object_domain[object_type]

        return object_domain
    
    @staticmethod
    def get_supported_externalvolume_storage_location_params() -> list:
        """
        Supported parameters for the storage locations of external volumes.
        Note: encryption_kms_key_id is covered by the encryption_type.
        """
        return  [
        'name',
        'storage_provider',
        'storage_base_url',
        'storage_aws_role_arn',
        'storage_aws_external_id',
        'azure_tenant_id',
        'encryption_type'
        ]