import os
from typing import Dict, List, Union
from dataclasses import dataclass, field, fields, is_dataclass
from typing import get_origin, get_args

from acedeploy.core.model_prepostdeploymentsteps import PreOrPostDeploymentScriptTarget
import aceutils.file_util as file_util
from acedeploy.core.model_sql_entities import DbObjectType
from acedeploy.services.secret_service import EnvironmentSecretService


@dataclass
class MetadataOption:
    ignore: bool = field(default=False)


@dataclass
class ObjectOption:
    enabled: bool = field(default=True)
    metadataOptions: Dict[str, Union[MetadataOption, Dict[str, MetadataOption]]] = field(default_factory=dict)

@dataclass
class TableCreateAndInsertOptionWarehouse:
    byteThreshold: int
    name: str

@dataclass
class TableCreateAndInsertOptions:
    enabled: bool = field(default=False)
    dropOldTable: bool = field(default=False)
    useAsFallback: bool = field(default=False)
    updateAutoincrement: bool = field(default=False)
    warehouses: List[TableCreateAndInsertOptionWarehouse] = field(default_factory=list)

@dataclass
class TableAlterOptions:
    createAndInsert: TableCreateAndInsertOptions = field(default_factory=TableCreateAndInsertOptions)
    keepColumnOrder: bool = field(default=False)

@dataclass
class TableLikeObjectOption(ObjectOption):
    manageTagAssignments: bool = field(default=False)

@dataclass
class TableObjectOption(TableLikeObjectOption):
    manageRowAccessPolicyReferences: bool = field(default=False)
    manageMaskingPolicyReferences: bool = field(default=False)
    alterOptions: TableAlterOptions = field(default_factory=TableAlterOptions)

@dataclass
class FunctionLikeObjectOption(ObjectOption):
    disabledLanguages: list = field(default_factory=list)
    dropOverloadedObjects: bool = field(default=False)

class ObjectOptionFactory:
    @staticmethod
    def get(object_type: DbObjectType) -> ObjectOption:
        mapping = {
            DbObjectType.TABLE: TableObjectOption,
            DbObjectType.EXTERNALTABLE: TableLikeObjectOption,
            DbObjectType.VIEW: TableLikeObjectOption,
            DbObjectType.MATERIALIZEDVIEW: TableLikeObjectOption,
            DbObjectType.FUNCTION: FunctionLikeObjectOption,
            DbObjectType.PROCEDURE: FunctionLikeObjectOption,
            DbObjectType.DYNAMICTABLE: TableLikeObjectOption,
        }
        return mapping.get(object_type, ObjectOption)

    @staticmethod
    def init_from_dict(cls, data: dict):
        """
        Given a dictionary that matches the given dataclass, populate the dataclass.

        This function will work with nested classes and list of objects.
        """
        init_values = {}
        for field_info in fields(cls):
            field_name = field_info.name
            field_type = field_info.type
            if field_name in data:
                if hasattr(field_type, '__dataclass_fields__'):
                    init_values[field_name] = ObjectOptionFactory.init_from_dict(field_type, data[field_name])
                elif get_origin(field_type) is list:
                    list_args = get_args(field_type)
                    element_type = list_args[0] if len(list_args) else None
                    init_values[field_name] = [
                        ObjectOptionFactory.init_from_dict(element_type, item) if is_dataclass(element_type) else item
                        for item in data[field_name]
                    ]
                else:
                    init_values[field_name] = data[field_name]
        return cls(**init_values)

@dataclass
class PreOrPostdeploymentConfig:
    root_path: str
    path: str
    type: str # TODO: we should use a Enum class here and everywhere it is used (similar to "target")
    condition: str # TODO: we should use a Enum class here and everywhere it is used (similar to "target")
    target: str = field(default="targetDatabase")

    def __post_init__(self):
        if isinstance(self.target, str):
            self.target = PreOrPostDeploymentScriptTarget(self.target)

    @property
    def full_path(self):
        return os.path.join(self.root_path, self.path)


@dataclass
class PreOrPostdeploymentConfigList:
    items: list[PreOrPostdeploymentConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: List[dict], root_path: str):
        items = [PreOrPostdeploymentConfig(root_path, **item) for item in data]
        return cls(items)


class SolutionConfig(object):
    """
    Holds solution config.
    """

    def __init__(self):
        """
        Init solution config by loading deployment.json.
        Requires environment variables ACEDEPLOY_SOLUTION_ROOT and ACEDEPLOY_CONFIG_PATH to be set.
        """
        self.module_root_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.solution_root_path = os.environ["ACEDEPLOY_SOLUTION_ROOT"]
        self.config_path = os.environ.get("ACEDEPLOY_CONFIG_PATH")

        schema_path = os.path.join(
            self.module_root_folder,
            "resources",
            "json-schemas",
            "deployment.schema.json",
        )
        if file_util.validate_json(schema_path, self.config_path) is False:
            raise EnvironmentError(
                f"Configuration JSON {self.config_path} failed validation against schema {schema_path}"
            )
        self.config_dict = file_util.load_json(self.config_path)

        if "keyService" in self.config_dict:
            if self.config_dict["keyService"] == "ENVIRONMENT":
                key_service = EnvironmentSecretService()
            else:
                raise ValueError(
                    f"Key service type '{self.config_dict['keyService']}' unknown. Allowed values are 'ENVIRONMENT'."
                )
        else:
            raise ValueError("Key service type (keyService) not set")
        self.key_service = key_service

        self.parse_config()

    def parse_config(self):
        """
        Parses config file.
        """
        self.key_service_type = self._get_nested_dict_value(
            self.config_dict, ["keyService"]
        )

        self.deployment_mode = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["deploymentMode"])
        )
        self.release_name = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["releaseName"])
        )
        self.git_tag_regex = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["solutionRepoTagRegex"])
        )

        self.ignore_git_information = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["solutionOptions", "ignoreGitInformation"]
            )
        )
        self.drop_target_objects = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["solutionOptions", "dropTargetObjectsIfNotInProject"]
            )
        )
        self.abort_on_data_loss = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["solutionOptions", "stopAtDataLoss"]
            )
        )

        self.deploy_to_clone = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["cloneOptions", "deployToClone"], False
            )
        )
        self.deploy_to_clone_mode = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["cloneOptions", "cloneMode"], ""
            )
        )
        self.drop_clone_after_run = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["cloneOptions", "dropCloneAfterDeployment"], False
            )
        )

        self.handle_policy_assignments = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension", "handlePolicyAssignments"], False
            )
        )

        self.policy_assignments_project = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsProject"], ""
            )
        )

        self.policy_assignments_deployment_database = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsDeploymentDB"], ""
            )
        )

        self.policy_assignments_role = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsRole"], ""
            )
        )

        self.policy_assignments_repo_path = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsRepoPath"], ""
            )
        )

        self.policy_assignments_config_file_path = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsConfigFilePath"], ""
            )
        )

        self.policy_assignments_save_info = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsSaveInfo"], False
            )
        )

        self.policy_assignments_info_output_folder_path = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsInfoOutputFolderPath"], ""
            )
        )

        self.policy_assignments_create_azure_pull_request_comments = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "policyHandlingCloeExtension","policyAssignmentsCreateAzurePullRequestComments"], False
            )
        )

        self.autoresume_tasks = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "resumeTasks"], False
            )
        )
        self.reapply_existing_policies = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict,
                ["deploymentOptions", "reapplyExistingPolicies"],
                False,
            )
        )
        
        if (
            self.reapply_existing_policies and self.handle_policy_assignments
        ):
            raise ValueError(
                "You can either set reapplyExistingPolicies or handlePolicyAssignments but not both parameters at the same time."
            )

        self.parallel_threads = int(
            self._get_env_var(
                self._get_nested_dict_value(self.config_dict, ["parallelThreads"])
            )
        )

        self.execute_in_parallel_sessions = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["deploymentOptions", "executeInParallelSessions"], False
            )
        )

        if (
            self.handle_policy_assignments and not self.execute_in_parallel_sessions
        ):
            raise ValueError(
                "The parameter handlePolicyAssignments can only be used in combination with the parameter execute_in_parallel_sessions."
            )

        self.action_summary_path = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["actionSummaryPath"], "")
        )
        self.action_json_path = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["actionJsonPath"], "")
        )

        self.prepostdeployment_filter_list = self._get_nested_dict_value(
            self.config_dict, ["preAndPostDeploymentFilter"], []
        )

        object_options_raw = self._get_nested_dict_value(
            self.config_dict, ["objectOptions"], {}
        )
        self.object_options = self._parse_object_options(object_options_raw)
        self.enabled_object_types = self._get_enabled_object_types(self.object_options)
        self.disabled_object_types = self._get_disabled_object_types(
            self.object_options
        )

        self.snow_edition = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "snowflakeEdition"], "Enterprise"
            )
        )
        self.snow_account = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["targetOptions", "account"])
        )
        self.snow_login = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["targetOptions", "login"])
        )
      
        self.snow_password = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["targetOptions", "password"])
        )
        self.snow_private_key = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["targetOptions", "privateKey"])
        )
        self.snow_private_key_pass = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["targetOptions", "privateKeyPass"])
        )
        
        if self.snow_password is not None and self.snow_private_key is not None:
            raise ValueError(
                "You can either use password or key-pair authentification, but not both at the same time."
            )
        if self.snow_password is None and self.snow_private_key is None:
            raise ValueError(
                "You must provide password or key-pair."
            )
    
        self.snow_role = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["targetOptions", "role"])
        )
        self.database_meta = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "metaDatabase"]
            )
        )

        self.database_target = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "targetDatabase"]
            )
        )
        self.clone_source_database = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "cloneSourceDatabase"], ""
            )
        )

        target_db_retention_time = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "targetDbRetentionTime"], "default"
            )
        )
        if target_db_retention_time == "default":
            self.target_db_retention_time = None
        else:
            self.target_db_retention_time = int(target_db_retention_time)

        temp_db_retention_time = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "tempDbRetentionTime"], 1
            )
        )
        if temp_db_retention_time == "default":
            self.temp_db_retention_time = None
        else:
            self.temp_db_retention_time = int(temp_db_retention_time)

        self.snow_warehouse = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "warehouse"]
            )
        )
        self.schema_list = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "projectSchemas"]
            )
        )

        self.project_folder = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "projectFolder"]
            )
        )
        if self.project_folder:
            self.project_folder = os.path.join(
                self.solution_root_path, self.project_folder
            )
        self.project_folder_filter = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "projectFolderFilter"]
            )
        )
        if self.project_folder_filter:
            self.project_folder_filter = [
                os.path.join(self.project_folder, f)
                for f in self.project_folder_filter
            ]
        self.pre_deployment_folders = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "preDeployment"], []
            )
        )
        if self.pre_deployment_folders:
            self.pre_deployment_folders = [
                os.path.join(self.solution_root_path, f)
                for f in self.pre_deployment_folders
            ]
        self.post_deployment_folders = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["targetOptions", "postDeployment"], []
            )
        )
        if self.post_deployment_folders:
            self.post_deployment_folders = [
                os.path.join(self.solution_root_path, f)
                for f in self.post_deployment_folders
            ]

        pre_deployment_settings = self._get_nested_dict_value(
            self.config_dict, ["targetOptions", "preDeploymentSettings"], []
        )
        pre_deployment_settings = [
            {k: self._get_env_var(v) for k, v in d.items()}
            for d in pre_deployment_settings
        ]
        self.pre_deployment_settings = PreOrPostdeploymentConfigList.from_dict(
            pre_deployment_settings, self.solution_root_path
        )

        post_deployment_settings = self._get_nested_dict_value(
            self.config_dict, ["targetOptions", "postDeploymentSettings"], []
        )
        post_deployment_settings = [
            {k: self._get_env_var(v) for k, v in d.items()}
            for d in post_deployment_settings
        ]
        self.post_deployment_settings = PreOrPostdeploymentConfigList.from_dict(
            post_deployment_settings, self.solution_root_path
        )

        if (
            bool(self.pre_deployment_folders) or bool(self.post_deployment_folders)
        ) and (
            bool(self.pre_deployment_settings.items)
            or bool(self.post_deployment_settings.items)
        ):
            raise ValueError(
                "You can either supply preDeployment and postDeployment or preDeploymentSettings and postDeploymentSettings, but not parameters from both pairs at the same time."
            )

        # sql variables
        sql_variables = self._get_nested_dict_value(
            self.config_dict, ["targetOptions", "sqlVariables"], {}
        )
        self.sql_variables = {}
        for key, value in sql_variables.items():
            self.sql_variables.update(
                {self._get_env_var(key): self._get_env_var(value)}
            )

        # string replace
        string_replace = self._get_nested_dict_value(
            self.config_dict, ["targetOptions", "stringReplace"], {}
        )
        self.string_replace = {}
        for key, value in string_replace.items():
            self.string_replace.update(
                {self._get_env_var(key): str(self._get_env_var(value))}
            )

        # extensions
        self.persist_views_table = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["extensions", "persistViewsTable"], ""
            )
        )

        # workarounds
        self.workarounds = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["workarounds"], {}
            )
        )

        # validate settings
        if self.reapply_existing_policies and self.snow_edition == "Standard":
            raise ValueError(
                "Setting 'reapplyExistingPolicies' must be false if snowflakeEdition is 'Standard'."
            )
        for ot, oo in self.object_options.items():
            manageRowAccessPolicyReferences = getattr(oo, "manageRowAccessPolicyReferences", False)
            if manageRowAccessPolicyReferences and self.snow_edition == "Standard":
                raise ValueError(
                    "Setting 'manageRowAccessPolicyReferences' must be false if snowflakeEdition is 'Standard'."
                )
            if manageRowAccessPolicyReferences and self.reapply_existing_policies:
                raise ValueError(
                    "It is not possible to use both 'manageRowAccessPolicyReferences' and 'reapplyExistingPolicies'."
                )
            if manageRowAccessPolicyReferences and self.handle_policy_assignments:
                raise ValueError(
                    "It is not possible to use both 'manageRowAccessPolicyReferences' and 'policyHandlingCloeExtension'."
                )
            manageMaskingPolicyReferences = getattr(oo, "manageMaskingPolicyReferences", False)
            if manageMaskingPolicyReferences and self.snow_edition == "Standard":
                raise ValueError(
                    "Setting 'manageMaskingPolicyReferences' must be false if snowflakeEdition is 'Standard'."
                )
            if manageMaskingPolicyReferences and self.reapply_existing_policies:
                raise ValueError(
                    "It is not possible to use both 'manageMaskingPolicyReferences' and 'reapplyExistingPolicies'."
                )
            if manageMaskingPolicyReferences and self.handle_policy_assignments:
                raise ValueError(
                    "It is not possible to use both 'manageMaskingPolicyReferences' and 'policyHandlingCloeExtension'."
                )
            manageTagAssignments = getattr(oo, "manageTagAssignments", False)
            if manageTagAssignments and self.snow_edition == "Standard":
                raise ValueError(
                    "Setting 'manageTagAssignments' must be false if snowflakeEdition is 'Standard'."
                )
        if (
            self.snow_edition == "Standard"
            and self.target_db_retention_time is not None
            and self.target_db_retention_time > 1
        ):
            raise ValueError(
                "Setting 'targetDbRetentionTime' must be 'default', 0 or 1 if snowflakeEdition is 'Standard'."
            )
        if (
            self.snow_edition == "Standard"
            and self.temp_db_retention_time is not None
            and self.temp_db_retention_time > 1
        ):
            raise ValueError(
                "Setting 'tempDbRetentionTime' must be 'default', 0 or 1 if snowflakeEdition is 'Standard'."
            )

    @staticmethod
    def _get_nested_dict_value(
        nested_dict: Dict, keys: List[str], default: str = None
    ) -> str:
        data = nested_dict
        for k in keys:
            if k in data:
                data = data[k]
            else:
                return default
        return data

    def _get_env_var(self, val: str) -> Union[str, bool]:
        """
            If the given value is enclosed with '@@', load value from environment variable of that name.
            Else, return the value.
            If the environment variable value is the string representation of a boolean, return that boolean.
        Args:
            val: str - environment variable name enclosed in '@@', or value
        Raises:
            ValueError - if secret was not found in configured Key Vault
        Returns:
            if value is not marked as name of environment variable: value
            if value is marked as name of environment variable:
                if environment variable is found - will return the environment variable value
                if environment variable is not found - ValueError
        """
        char_delimiter = "@@"

        if (
            isinstance(val, str)
            and val.startswith(char_delimiter)
            and val.endswith(char_delimiter)
        ):
            env_var_name = val[len(char_delimiter) : -len(char_delimiter)]
            env_var_value = self.key_service.get_secret(env_var_name)
            if env_var_value in ["True", "TRUE", "true"]:
                return True
            elif env_var_value in ["False", "FALSE", "false"]:
                return False
            else:
                return env_var_value
        else:
            return val

    @staticmethod
    def _parse_object_options(
        object_options_raw: Dict[str, Dict]
    ) -> Dict[DbObjectType, ObjectOption]:
        """
        Parse the raw object options and add default values.
        """
        object_option_factory = ObjectOptionFactory()
        result = dict()
        for object_type in DbObjectType:
            object_sql_name = DbObjectType.get_sql_object_type(object_type)
            object_dict = object_options_raw.get(object_sql_name, {})
            object_option = object_option_factory.get(object_type)
            result[object_type] = object_option_factory.init_from_dict(object_option, object_dict)
        return result

    @staticmethod
    def _get_enabled_object_types(
        object_options: Dict[DbObjectType, ObjectOption]
    ) -> List[DbObjectType]:
        """
        Return a list of all object types which are enabled.
        Assumes that object_options contains all object types.
        """
        return [t for t, o in object_options.items() if o.enabled]

    @staticmethod
    def _get_disabled_object_types(
        object_options: Dict[DbObjectType, ObjectOption]
    ) -> List[DbObjectType]:
        """
        Return a list of all object types which are disabled.
        Assumes that object_options contains all object types.
        """
        return [t for t, o in object_options.items() if not o.enabled]
