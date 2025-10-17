import logging
import os
import json
from pathlib import PurePath
from jsonschema import validate, RefResolver
import datetime
import time

from dataclasses import dataclass
import aceutils.file_util as file_util
from aceaccount.configuration import AccountObjectConfig
from aceservices.snowflake_service import SnowClient, SnowClientConfig
from aceaccount.services.account_objects_metadata_service import AccountMetadataService
from aceaccount.services.account_objects_solution_service import AccountSolutionClient
from aceaccount.services.account_objects_validation_service import AccountValidationService
from aceutils.logger import LoggingAdapter
from aceaccount.services.account_objects_compare_service import (
    AccountObjectCompareClient,
)

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)

@dataclass
class AccountObjectParams:
    technical_jsonschema_folder_path:str        = 'resources/json-schemas/account_object_json_schemas/technical_validation/'
    technical_jsonschema_file_name:str          = 'account_objects_technical_validation.schema.json'

def execute(
        config: AccountObjectConfig,
        dryrun: bool = False, 
        output_sql_statements: bool = False, output_path: str = '', 
        optional_technical_jsonschema_absolute_folder_path: str = None,
        optional_technical_jsonschema_file_name: str = None
        ):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M_%S")

        start_time_validate_technical = time.time()
        validate_technical(config, optional_technical_jsonschema_absolute_folder_path, optional_technical_jsonschema_file_name)
        end_time_validate_technical = time.time()
        log.info(f"============= Execution Time validate_technical: {round(end_time_validate_technical - start_time_validate_technical, 2)} seconds")

        start_time_solution_client = time.time()
        solution_client = AccountSolutionClient(config.enabled_object_types, config.source_files)
        end_time_solution_client = time.time()
        log.info(f"============= Execution Time solution_client: {round(end_time_solution_client - start_time_solution_client, 2)} seconds")


        start_time_snow_client = time.time()
        snow_client_config = SnowClientConfig(
            account=config.snow_account,
            user=config.snow_login,
            password=config.snow_password,
            warehouse=config.snow_warehouse,
            role=config.snow_role,
        )

        snow_client = SnowClient(snow_client_config)
        end_time_snow_client = time.time()
        log.info(f"============= Execution Time snow_client: {round(end_time_snow_client - start_time_snow_client, 2)} seconds")

        start_time_metadata_client = time.time()
        metadata_client = AccountMetadataService(config.enabled_object_types, snow_client, dryrun)
        end_time_metadata_client = time.time()
        log.info(f"============= Execution Time metadata_client: {round(end_time_metadata_client - start_time_metadata_client, 2)} seconds")

        start_time_get_all_account_objects_metadata = time.time()
        metadata_client.get_all_account_objects_metadata(max_number_of_threads=config.max_number_of_threads)
        end_time_get_all_account_objects_metadata = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata: {round(end_time_get_all_account_objects_metadata - start_time_get_all_account_objects_metadata, 2)} seconds")

        start_time_generate_actions = time.time()
        compare_client = AccountObjectCompareClient(solution_client, metadata_client, snow_client_config)
        compare_client.generate_add_actions()
        if config.drop_enabled:
            compare_client.generate_drop_actions(config.drop_enabled)
        compare_client.generate_alter_actions()
        end_time_generate_actions = time.time()
        log.info(f"============= Execution Time generate_actions: {round(end_time_generate_actions - start_time_generate_actions, 2)} seconds")

        start_time_generate_statements = time.time()
        statements = []
        for action in compare_client.action_list:
            statement_object = action.generate_statement_object()
            statements.append(statement_object.statement)
        statements_text = '\n\n'.join(statements)
        if not statements_text:
            statements_text = ' '
        end_time_generate_statements = time.time()
        log.info(f"============= Execution Time generate_statements: {round(end_time_generate_statements - start_time_generate_statements, 2)} seconds")

        if not dryrun:
            start_time_execute_statements = time.time()
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info("Executing the following statements - includes grant statements and set-tag statements for newly created objects:")
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info(statements_text)
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            snow_client.execute_statement(statements)
            end_time_execute_statements = time.time()
            log.info(f"============= Execution Time execute_statements: {round(end_time_execute_statements - start_time_execute_statements, 2)} seconds")
        else:
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info("The dry-run produced the following statements - includes grant statements and set-tag statements for newly created objects:")
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info(statements_text)
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        start_time_generate_grant_actions = time.time()
        compare_client.generate_grant_actions()
        if config.revoke_enabled:
            compare_client.generate_revoke_actions()
        end_time_generate_grant_actions = time.time()
        log.info(f"============= Execution Time generate_grant_actions and generate_revoke_actions: {round(end_time_generate_grant_actions - start_time_generate_grant_actions, 2)} seconds")

        start_time_generate_grant_statements = time.time()
        account_objects_grant_statements = []
        for grant_action in compare_client.grant_action_list:
            grant_action_object = grant_action.generate_statement_object()
            account_objects_grant_statements.append(grant_action_object.statement)
        account_objects_grant_statements_text = '\n'.join(filter(None,account_objects_grant_statements))
        if not account_objects_grant_statements_text:
            account_objects_grant_statements_text = ' '
        end_time_generate_grant_statements = time.time()
        log.info(f"============= Execution Time generate_grant_statements: {round(end_time_generate_grant_statements - start_time_generate_grant_statements, 2)} seconds")

        if not dryrun:
            start_time_execute_grant_statements = time.time()
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info("Executing the following grant statements for previously existing objects - does not include grants for newly created objects:")
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info(account_objects_grant_statements_text)
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            snow_client.execute_statement(account_objects_grant_statements)
            end_time_execute_grant_statements = time.time()
            log.info(f"============= Execution Time execute_grant_statements: {round(end_time_execute_grant_statements - start_time_execute_grant_statements, 2)} seconds")
        else:
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info("The dry-run produced the following grant statements for previously existing objects - does not include grants for newly created objects:")
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info(account_objects_grant_statements_text)
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        start_time_generate_tag_actions = time.time()
        compare_client.generate_settag_actions()
        if config.unsettag_enabled:
            compare_client.generate_unsettag_actions()
        end_time_generate_tag_actions = time.time()
        log.info(f"============= Execution Time generate_settag_actions and generate_unsettag_actions: {round(end_time_generate_tag_actions - start_time_generate_tag_actions, 2)} seconds")

        start_time_generate_tag_statements = time.time()
        account_objects_tag_statements = []
        for tag_action in compare_client.tag_action_list:
            tag_action_object = tag_action.generate_statement_object()
            account_objects_tag_statements.append(tag_action_object.statement)
        account_objects_tag_statements_text = '\n'.join(filter(None,account_objects_tag_statements))
        if not account_objects_tag_statements_text:
            account_objects_tag_statements_text = ' '
        end_time_generate_tag_statements = time.time()
        log.info(f"============= Execution Time generate_tag_statements: {round(end_time_generate_tag_statements - start_time_generate_tag_statements, 2)} seconds")

        if not dryrun:
            start_time_execute_tag_statements = time.time()
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info("Executing the following tag statements for previously existing objects - does not include tags for newly created objects:")
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info(account_objects_tag_statements_text)
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            snow_client.execute_statement(account_objects_tag_statements)
            end_time_execute_tag_statements = time.time()
            log.info(f"============= Execution Time execute_grant_statements: {round(end_time_execute_tag_statements - start_time_execute_tag_statements, 2)} seconds")
        else:
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info("The dry-run produced the following tag statements for previously existing objects - does not include tags for newly created objects:")
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            log.info(account_objects_tag_statements_text)
            log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        start_time_generate_output_sql_statements = time.time()
        if output_sql_statements:
            if output_path:
                filename_sql_statements = os.path.join(output_path, f"account_objects_sql_statements.{timestamp}.sql")
                filename_grant_statements = os.path.join(output_path, f"account_objects_grant_statements.{timestamp}.sql")
                filename_tag_statements = os.path.join(output_path, f"account_objects_tag_statements.{timestamp}.sql")
                log.info(f"Saving resulting sql statements of the account objects in file '{filename_sql_statements}' - includes grant statements for newly created objects.")
                log.info(f"Saving resulting grant statements of the account objects in file '{filename_grant_statements}' - does not include grants for newly created objects.")
                log.info(f"Saving resulting tag statements of the account objects in file '{filename_tag_statements}' - does not include tags for newly created objects.")
                os.makedirs(output_path, exist_ok=True)
                with open(filename_sql_statements, 'w') as f:
                    f.write(statements_text)
                with open(filename_grant_statements, 'w') as f:
                    f.write(account_objects_grant_statements_text)
                with open(filename_tag_statements, 'w') as f:
                    f.write(account_objects_tag_statements_text)
            else:
                log.info("No output_path defined. Statements are not saved in a file.")
        end_time_generate_output_sql_statements = time.time()
        log.info(f"============= Execution Time generate_output_sql_statements: {round(end_time_generate_output_sql_statements - start_time_generate_output_sql_statements, 2)} seconds")
        log.info("done")

    except Exception as err:
        log.error(str(err))
        raise err

def validate_technical(
        config, 
        optional_technical_jsonschema_absolute_folder_path: str = None,
        optional_technical_jsonschema_file_name: str = None
    ):
    """
        Technical validation of account objects.
        Raises an Error when the validation fails.
        Initializes the AccountSolutionClient as a test to check, e.g., for duplicates.

        Optional:
            Define optional JSON Schemas for the technical validation e.g. in the "setup-repository".
            This way, it is possible to circumvent the default restrictions by Snowflake in case there was a change by Snowflake just for a specific account.
            For example, if there is an exception on a Snowflake Account by which the max_cluster_count for a Warehouse can be set to 20 instead of the usual default maximum of 10.
            Use the following paramters to define the path to the optional JSON Schemas located outside of the acedeploy repo:
                optional_technical_jsonschema_absolute_folder_path
                optional_technical_jsonschema_file_name
            Note: Please define both of these parameters or none.
    """
    try:
        validation_service = AccountValidationService(config)

        module_root_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


        if optional_technical_jsonschema_absolute_folder_path and optional_technical_jsonschema_file_name:
            technical_jsonschema_absolute_folder_path = PurePath(module_root_folder).joinpath(PurePath(optional_technical_jsonschema_absolute_folder_path))
            technical_jsonschema_file_name = optional_technical_jsonschema_file_name
        else:
            technical_jsonschema_absolute_folder_path = PurePath(module_root_folder).joinpath(PurePath(AccountObjectParams.technical_jsonschema_folder_path))
            technical_jsonschema_absolute_folder_path = PurePath(module_root_folder).joinpath(PurePath(AccountObjectParams.technical_jsonschema_folder_path))
            technical_jsonschema_file_name = AccountObjectParams.technical_jsonschema_file_name
        
        validation_service.validate_against_json_schema(technical_jsonschema_absolute_folder_path, technical_jsonschema_file_name)
        
        # Test-Initialization of the AccountSolutionClient to check, e.g., for duplicates
        AccountSolutionClient(config.enabled_object_types, config.source_files)
    except Exception as err:
        log.error(str(err))
        raise err

def validate_content(config, content_jsonschema_absolute_folder_path: str, content_jsonschema_file_name: str):
    """
        Function to validate account objects in regards to the content.
        Raises an Error when the validation fails.
        Validates also the Snowflake tags in regards to fully-qulified identifiers, existence, and allowed values.
    """
    try:
        snow_client_config = SnowClientConfig(
            account=config.snow_account,
            user=config.snow_login,
            password=config.snow_password,
            warehouse=config.snow_warehouse,
            role=config.snow_role,
        )

        snow_client = SnowClient(snow_client_config)

        validation_service = AccountValidationService(config, snow_client)

        validation_service.validate_against_json_schema(content_jsonschema_absolute_folder_path, content_jsonschema_file_name)

        solution_client = AccountSolutionClient(config.enabled_object_types, config.source_files)
        
        start_time_validate_tags = time.time()
        validation_service.validate_tags(solution_client)
        end_time_validate_tags = time.time()
        log.info(f"============= Execution Time validate_tags: {round(end_time_validate_tags - start_time_validate_tags, 2)} seconds")
    except Exception as err:
        log.error(str(err))
        raise err
    
def fetch_account_objects(config: AccountObjectConfig, output_path: str, dialect_json_schema_relative_file_path: str, fetch_grants: bool=True, fetch_tags: bool=True):
    """
        Function to fetch existing account objects from Snowflake. 
        Generates a parameter representation and saves it as a JSON file which can be used as an input for an account objects pipeline.
        Raises an Error when the fetching fails.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M_%S")
        snow_client_config = SnowClientConfig(
                account=config.snow_account,
                user=config.snow_login,
                password=config.snow_password,
                warehouse=config.snow_warehouse,
                role=config.snow_role,
            )
        
        snow_client = SnowClient(snow_client_config)
        
        metadata_client = AccountMetadataService(config.enabled_object_types, snow_client)
        metadata_client.get_all_account_objects_metadata(max_number_of_threads=config.max_number_of_threads, get_grants=fetch_grants, get_tags=fetch_tags)
        fetched_account_objects=metadata_client.get_account_objects_dict(dialect_json_schema_relative_file_path)

        if output_path:
            os.makedirs(output_path, exist_ok=True)

            for object_type, account_objects_parameter_representation in fetched_account_objects.items():
                filename_account_objects = os.path.join(output_path, f"fetched_account_objects_of_type_{object_type}.{timestamp}.json")
                logging.info(f"SAVING fetched account objects as JSON file in '{filename_account_objects}'")
                with open(filename_account_objects, 'w') as f:
                    json.dump(account_objects_parameter_representation, f, indent=4)
        else:
            log.info("No output_path defined. Fetched account objects are not saved in a file.")
      
    except Exception as err:
        log.error(str(err))
        raise err