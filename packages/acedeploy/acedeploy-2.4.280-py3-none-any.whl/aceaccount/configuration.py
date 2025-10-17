import os
from typing import Dict, List, Union

import aceutils.file_util as file_util
from acedeploy.services.secret_service import EnvironmentSecretService


class AccountObjectConfig(object):
    """
    Holds solution config.
    """

    def __init__(self):
        """ """
        self.module_root_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        self.config_path = os.environ.get("ACEACCOUNT_CONFIG_PATH")

        self.config_dict = file_util.load_json(self.config_path)

        key_service = EnvironmentSecretService()
        self.key_service = key_service

        self.parse_config()

    def parse_config(self):
        """
        Parses config file.
        """
        self.source_files = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["sourceFiles"])
        )

        self.snow_edition = self._get_env_var(
            self._get_nested_dict_value(
                self.config_dict, ["connection", "snowflakeEdition"], "Enterprise"
            )
        )
        self.snow_account = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["connection", "account"])
        )
        self.snow_login = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["connection", "login"])
        )
        self.snow_password = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["connection", "password"])
        )
        self.snow_role = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["connection", "role"])
        )
        self.snow_warehouse = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["connection", "warehouse"])
        )
        self.object_options = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["objectOptions"])
        )

        self.drop_enabled = {object_type: object_option["dropEnabled"] for object_type, object_option in self.object_options.items()}

        self.enabled_object_types = [object_type for object_type, object_option in self.object_options.items() if object_option["enabled"]]

        self.revoke_enabled = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["revokeEnabled"])
        ) 
        self.unsettag_enabled = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["unsettagEnabled"])
        ) 
        self.max_number_of_threads = self._get_env_var(
            self._get_nested_dict_value(self.config_dict, ["maxNumberOfThreads"])
        )        
        self.max_number_of_threads = 1 if self.max_number_of_threads is None else self.max_number_of_threads

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
