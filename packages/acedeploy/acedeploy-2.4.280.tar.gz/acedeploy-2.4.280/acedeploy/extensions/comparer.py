import difflib
import logging
import re
from acedeploy.services.dependency_parser import DependencyParser

import aceutils.database_management as database_management
import aceutils.string_util as string_util
from acedeploy.core.model_configuration import SolutionConfig
from acedeploy.core.model_instance_objects import InstanceTable
from acedeploy.core.model_sql_entities import DbObjectType
from acedeploy.main import deploy_to_meta_database
from acedeploy.services.metadata_service import MetadataService
from aceservices.snowflake_service import SnowClient, SnowClientConfig
from acedeploy.services.solution_service import SolutionClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def configure() -> SolutionConfig:
    """
        Loads the current configuration from the deployment.json file.
    Returns:
        SolutionConfigVCollection
    """
    return SolutionConfig()


def compare_files_and_database(
    config: SolutionConfig,
    detailed_output: bool = False,
    ignore_column_order: bool = True,
) -> None:
    """
        Compare solution to database
    Args:
        config: SolutionConfig - deployment configuration
        detailed_output: bool - print diff between both DDLs if no match (default: false)
        ignore_column_order: bool - ignore order of columns when comparing tables
    Returns:
        None
    """
    snow_client_account = SnowClient(SnowClientConfig.get_from_solution_config(config))
    database_management.create_database(
        config.database_meta,
        snow_client_account,
        replace_if_exists=True,
        drop_schema_public=True,
        db_retention_time_in_days=config.target_db_retention_time,
    )
    snow_client_meta = SnowClient(
        SnowClientConfig.get_from_solution_config(config, config.database_meta)
    )
    snow_client_target = SnowClient(
        SnowClientConfig.get_from_solution_config(config, config.database_target)
    )
    solution_client = SolutionClient(
        project_folder=config.project_folder,
        predeployment_folders=config.pre_deployment_folders,
        postdeployment_folders=config.post_deployment_folders,
        predeployment_settings=config.pre_deployment_settings,
        postdeployment_settings=config.post_deployment_settings,
        prepostdeployment_filter_list=config.prepostdeployment_filter_list,
        config_schema_list=config.schema_list,
        disabled_object_types=config.disabled_object_types,
    )
    solution_client.load_solution(string_replace_dict=config.string_replace)

    try:

        try:
            dependency_client = DependencyParser(solution_client)
            dependency_client.build_full_dependency_graph()
            log.info(f"DEPLOY full solution TO meta db [ '{config.database_meta}' ]")
            deploy_to_meta_database(
                solution_client=solution_client,
                dependency_client=dependency_client,
                snow_client=snow_client_meta,
                config=config,
                mode="solution",
                parallel_threads=config.parallel_threads,
            )
        except Exception as err:
            log.error("DEPLOYMENT to meta db FAILED. Solution might not be valid.")
            raise err

        missing_objects = []
        changed_objects = []

        # compare tables
        log.info(
            f"COMPARE METADATA (tables and views) ON target db [ '{config.database_target}' ] AND meta db [ '{config.database_meta}' ]"
        )
        (
            missing_tables,
            changed_tables,
            _,
            changed_views,
        ) = _compare_tables_and_views_metadata(
            snow_client_meta, snow_client_target, config, ignore_column_order
        )
        missing_objects.extend(missing_tables)
        changed_objects.extend([f"{o} (metadata mismatch)" for o in changed_tables])
        # missing_objects.extend(missing_views) # views will be added through ddl comparison
        changed_objects.extend([f"{o} (metadata mismatch)" for o in changed_views])

        # compare ddls
        log.info(
            f"COMPARE DDLS (objects other than tables) ON target db [ '{config.database_target}' ] AND meta db [ '{config.database_meta}' ]"
        )
        for object_local in solution_client.all_objects:
            if (
                object_local.object_type == DbObjectType.SCHEMA
            ):  # schemas do not need to be compared
                continue
            if (
                object_local.object_type == DbObjectType.STAGE
            ):  # get_ddl not supported in get_ddl, i.e. DDLs cannot be compared
                continue
            elif (
                object_local.object_type == DbObjectType.TABLE
            ):  # tables cannot be compared using DDLs (order of columns might not be the same)
                continue
            else:
                missing_object, changed_object = _compare_object_ddl(
                    object_local, config, snow_client_account, detailed_output
                )
                missing_objects.extend(missing_object)
                changed_objects.extend([f"{o} (DDL mismatch)" for o in changed_object])

        _print_summary(
            missing_objects,
            changed_objects,
            config.project_folder,
            config.database_target,
        )

    except Exception as err:
        log.error(str(err))
        raise err

    finally:
        database_management.drop_database_and_set_retention_time(
            config.database_meta, snow_client_account, config.temp_db_retention_time
        )


def _compare_tables_and_views_metadata(
    snow_client_meta: SnowClient,
    snow_client_target: SnowClient,
    config: SolutionConfig,
    ignore_column_order=True,
    snow_edition: str = "Enterprise",
):
    """
        Compares tables and views by their metadata
    Returns:
        (table_names_missing, table_names_alter), where
            table_names_missing is a list containing n strings (object name)
            table_names_alter is a list containing n strings (object name)
    """
    metadata_service_metadb = MetadataService(snow_client_meta, snow_edition, config.disabled_object_types)
    metadata_service_metadb.get_all_metadata(
        config.schema_list, config.parallel_threads
    )
    metadata_service_targetdb = MetadataService(snow_client_target, snow_edition, config.disabled_object_types)
    metadata_service_targetdb.get_all_metadata(
        config.schema_list, config.parallel_threads
    )

    def compare(meta_objects_list, target_objects_list):
        object_names_alter = []
        object_names_missing = []
        for meta_object in meta_objects_list:
            missing = True
            if meta_object.schema.upper() == "INFORMATION_SCHEMA":
                continue
            for target_object in target_objects_list:
                target_object.ignore_column_order = ignore_column_order
                if (target_object.schema == meta_object.schema) and (
                    target_object.name == meta_object.name
                ):
                    if target_object != meta_object:
                        log.info(
                            f"METADATA MISMATCH [ '{meta_object.schema}.{meta_object.name}' ] ON databases [ '{config.database_target}' ] and [ '{config.database_meta}' ]"
                        )
                        log.info(
                            InstanceTable.generate_diff_description(
                                target_object, meta_object
                            )
                        )
                        object_names_alter.append(
                            f"{meta_object.schema}.{meta_object.name}"
                        )
                    missing = False
                    break
            if missing:
                log.info(
                    f"OBJECT NOT FOUND [ '{meta_object.schema}.{meta_object.name}' ] ON database [ '{config.database_target}' ]"
                )
                object_names_missing.append(f"{meta_object.schema}.{meta_object.name}")
        return object_names_missing, object_names_alter

    table_names_missing, table_names_alter = compare(
        metadata_service_metadb.tables, metadata_service_targetdb.tables
    )
    view_names_missing, view_names_alter = compare(
        metadata_service_metadb.views, metadata_service_targetdb.views
    )

    return table_names_missing, table_names_alter, view_names_missing, view_names_alter


def _compare_object_ddl(
    object_local, config, snow_client_account, detailed_output=False
):
    """
        Compares object by their DDLs
    Returns:
        (missing_object, changed_object), where
            missing_object is a list containing 1 or 0 strings (object name)
            changed_object is a list containing 1 or 0 strings (object name)
    """
    ddl_target = _get_object_ddl(
        config.database_target,
        object_local.full_name,
        object_local.object_type,
        snow_client_account,
    )
    if not ddl_target:
        log.debug(
            f"DDL NOT FOUND [ '{object_local.full_name}' ] ON database [ '{config.database_target}' ]"
        )
        return [object_local.full_name], []

    ddl_target = _remove_whitespace(string_util.remove_comment(ddl_target))
    ddl_meta = _get_object_ddl(
        config.database_meta,
        object_local.full_name,
        object_local.object_type,
        snow_client_account,
    )
    ddl_meta = _remove_whitespace(string_util.remove_comment(ddl_meta))

    if object_local.object_type in (DbObjectType.PROCEDURE, DbObjectType.FUNCTION):
        ddl_target = _remove_whitespace(
            _remove_comment_from_procedure_function_body(ddl_target)
        )
        ddl_meta = _remove_whitespace(
            _remove_comment_from_procedure_function_body(ddl_meta)
        )
    if object_local.object_type in (DbObjectType.TASK,):
        ddl_target = ddl_target.replace(f"{config.database_target}.", "")
        ddl_meta = ddl_meta.replace(f"{config.database_meta}.", "")

    if ddl_meta.casefold().strip() != ddl_target.casefold().strip():
        if detailed_output:
            log.info(
                f"DDL MISMATCH [ '{object_local.full_name}' ] ON databases [ '{config.database_target}' ] and [ '{config.database_meta}' ]"
            )
            log.info(
                "".join(
                    difflib.unified_diff(
                        ddl_meta.splitlines(keepends=True),
                        ddl_target.splitlines(keepends=True),
                        fromfile="solution",
                        tofile="database",
                    )
                )
            )
        else:
            log.debug(
                f"DDL MISMATCH [ '{object_local.full_name}' ] ON databases [ '{config.database_target}' ] and [ '{config.database_meta}' ]"
            )
        return [], [object_local.full_name]

    return [], []


def _remove_comment_from_procedure_function_body(ddl):
    """
    Remove comments from the body of a function or procedure.

    Comments in the body of a function or procedure might not be automatically removed if they are given in single quotes.
    This function removes the comments and returns the result.
    Input should have comments (outside of body) already removed.
    """
    try:
        body = re.search(
            r"CREATE\s+(?:OR\s+REPLACE\s+)(?:PROCEDURE|FUNCTION).*AS\s*'(?P<body>.*)'\s*;",
            ddl,
            re.IGNORECASE + re.DOTALL,
        ).group("body")
        body_clean = string_util.remove_comment(body.replace("''", "'"))
        return ddl.replace(body, body_clean.replace("'", "''"))
    except:
        log.debug(
            f"Could not parse body. Return DDL with comments in body. DDL:\n{ddl}"
        )
        return ddl


def _print_summary(missing_objects, changed_objects, project_folder, target_database):
    message = f"SUMMARY comparison solution [ '{project_folder}' ] and database [ '{target_database}' ]"
    if len(missing_objects) == 0:
        message = message + "\n" + "All objects in solution are on database."
    else:
        message = (
            message
            + "\n"
            + f"List of objects in solution, but not on database (total {len(missing_objects)}):"
        )
        for mo in missing_objects:
            message = message + "\n" + f"    {mo}"
    if len(changed_objects) == 0:
        message = (
            message
            + "\n"
            + "All existing objects on database are identical to objects in solution."
        )
    else:
        message = (
            message
            + "\n"
            + f"List of differences between database and solution (total {len(changed_objects)}):"
        )
        for co in changed_objects:
            message = message + "\n" + f"    {co}"
    message = (
        message
        + "\n"
        + "This function does not check if there are objects on the database which do not appear in the solution."
    )
    message = (
        message
        + "\n"
        + "Objects might not be found on database due to insufficient rights to access the object."
    )
    log.info(message)
    if len(missing_objects) > 0 or len(changed_objects) > 0:
        log.error(
            f"DETECTED [ '{len(missing_objects) + len(changed_objects)}' ] DIFFERENCES between solution [ '{project_folder}' ] and database [ '{target_database}' ]"
        )
        log.info("Scroll up for details on differences.")


def _get_object_ddl(
    database: str,
    full_object_name: str,
    object_type: str,
    snow_client_account: SnowClient,
):
    try:
        object_type_string = DbObjectType.get_object_type_for_get_ddl(object_type)
        query = f"SELECT GET_DDL('{object_type_string}', '{database}.{full_object_name}') AS DDL"
        ddl_result = snow_client_account.execute_query(query)
    except Exception as err:
        if re.search(
            r"SQL compilation error:(.|\n)*does not exist or not authorized",
            repr(err),
            re.IGNORECASE | re.MULTILINE,
        ):
            return None
        else:
            raise err
    return ddl_result[0]["DDL"]


def _remove_whitespace(t):
    """
    Remove whitespace in each line and completely remove empty lines
    """
    return "\n".join([l.strip() for l in t.splitlines() if l.strip() != ""])
