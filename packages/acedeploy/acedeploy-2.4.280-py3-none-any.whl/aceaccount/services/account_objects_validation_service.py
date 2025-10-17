import logging
import re
import inspect
from pathlib import PurePath
from collections import defaultdict

import aceutils.file_util as file_util
from aceaccount.configuration import AccountObjectConfig
from aceaccount.services.account_objects_solution_service import AccountSolutionClient
from aceservices.snowflake_service import SnowClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class AccountValidationService:
    """
    Class to validate account objects on a technical level and on a content level.
    """

    def __init__(self, config: AccountObjectConfig, snow_client: SnowClient = None):
        self._config = config
        self._snow_client = snow_client

    def validate_against_json_schema(
        self, jsonschema_absolute_folder_path: str, jsonschema_file_name: str
    ):
        """
        Validate account objects against a JSON schema.
        Raises an Error when the validation fails.
        """
        try:
            account_objects_jsonschema_path_content = PurePath(
                jsonschema_absolute_folder_path
            ).joinpath(PurePath(jsonschema_file_name))

            for source_file in self._config.source_files:
                if (
                    file_util.validate_json(
                        account_objects_jsonschema_path_content,
                        source_file,
                        jsonschema_absolute_folder_path,
                    )
                    is False
                ):
                    raise EnvironmentError(
                        f"FAILED validation of {source_file} \n against schema {account_objects_jsonschema_path_content}"
                    )
                else:
                    log.info(
                        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
                    )
                    log.info(
                        f"SUCCEEDED validation of {source_file} \n  against schema {account_objects_jsonschema_path_content}"
                    )

        except Exception as err:
            log.error(str(err))
            raise err

    def validate_tags(self, solution_client: AccountSolutionClient):
        tags = set()
        tag_values_per_tag = defaultdict(list)
        for account_object in solution_client.all_account_objects:
            if hasattr(account_object, "tags"):
                tags.update(account_object.tags.keys())
                for tag, tag_value in account_object.tags.items():
                    tag_values_per_tag[tag].append(tag_value)

        tags = list(tags)

        self._validate_tags_check_fully_qualified_identifiers(tags)
        self._validate_tag_values_against_allowed_values(tag_values_per_tag)

    def _validate_tags_check_fully_qualified_identifiers(self, tags: list):
        for tag in tags:
            if not len(tag.split(".")) == 3:
                raise ValueError(
                    f"The Snowflake tag {tag} is not fully identified with Snowflake database and Snowflake schema."
                )

    def _validate_tag_values_against_allowed_values(self, tag_values_per_tag: dict):
        for tag, tag_values in tag_values_per_tag.items():
            query = f"SELECT SYSTEM$GET_TAG_ALLOWED_VALUES('{tag}');"
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            allowed_tag_values_string = list(result[0].values())[0]
            if allowed_tag_values_string:
                allowed_tag_values = allowed_tag_values_string[2:-2].split('","')
                for tag_value in tag_values:
                    if tag_value not in allowed_tag_values:
                        raise ValueError(
                            f"The tag value {tag_value} is not in the allowed tag values for the tag {tag} as defined on the Snowflake Account."
                        )

def validate_additionally_storage_integration_allowed_locations(config: AccountObjectConfig, additional_validation_folder_path: str='', additional_validation_file_name: str=''):
    """
    Validate the storage_allowed_locations parameter of storage integrations.
    Check if the name of the integration exists in all paths of the storage_allowed_locations.
    Raises an Error when the validation fails.
    """
    storage_allowed_locations_not_in_line = {}
    additional_validation_config = {}
    storage_integration_exceptions = []
    validated_source_files = []

    if additional_validation_folder_path and additional_validation_file_name:
        additional_validation_file_path = PurePath(
                    additional_validation_folder_path
                ).joinpath(PurePath(additional_validation_file_name))

        additional_validation_config=file_util.load_json(additional_validation_file_path)
    
    for source_file in config.source_files:
        account_object_solution = file_util.load_json(source_file)
        if "storage_integrations" not in account_object_solution.keys():
            continue
        else:
            validated_source_files.append(source_file)
            for storage_integration_name, storage_integration_parameters  in account_object_solution["storage_integrations"].items():

                storage_integration_name_split=storage_integration_name.lower().split('sti_', 1)
                if len(storage_integration_name_split) == 1:
                    storage_integration_identifier=storage_integration_name_split[0]
                else:
                    storage_integration_identifier=storage_integration_name_split[1]   

                if additional_validation_config:
                    storage_integration_exceptions=additional_validation_config["exceptions_storage_integration_allowed_locations"].get(storage_integration_name)

                if storage_integration_exceptions:
                    pattern = rf'^azure:\/\/(.*{storage_integration_identifier}.*|{"|".join(storage_integration_exceptions)})(.blob.core.windows.net\/).+|^[*]{1}$'
                else:
                    pattern = rf'^azure:\/\/.*{storage_integration_identifier}.*(.blob.core.windows.net\/).+|^[*]{1}$'
                
                if not (storage_integration_exceptions and "*" in storage_integration_exceptions):
                    for storage_allowed_location in storage_integration_parameters["storage_allowed_locations"]:
                        m = re.match(pattern, storage_allowed_location, re.IGNORECASE)
                        if not m: 
                            if storage_integration_name not in storage_allowed_locations_not_in_line:
                                storage_allowed_locations_not_in_line[storage_integration_name]=[]
                            storage_allowed_locations_not_in_line[storage_integration_name].append(storage_allowed_location)

    if not storage_allowed_locations_not_in_line:
        log.info(
            f"SUCCEEDED additional validation of storage_allowed_locations for storage integrations in the following source files {validated_source_files}."
        )
    else:
        raise ValueError(inspect.cleandoc(f"FAILED additional validation of storage_allowed_locations for storage integrations.\n\
                                            The following path/paths in the storage_allowed_locations is/are not allowed - the path/paths does/do not contain the name of the storage integration:\n\
                                            {storage_allowed_locations_not_in_line}"
                                        )
                        )
