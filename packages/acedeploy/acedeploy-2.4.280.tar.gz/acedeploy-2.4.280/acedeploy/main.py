import logging
from typing import List, Tuple

from acedeploy.core.model_configuration import SolutionConfig
from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_prepostdeploymentsteps import (
    PreOrPostDeploymentScriptTarget,
    PreOrPostDeploymentScriptsExecutionOptions,
)
from acedeploy.extensions import persist_views_table
from acedeploy.services.db_compare_service import DbCompareClient
from acedeploy.services.deploy_service import DeployService
from acedeploy.services.git_service import GitClient
from acedeploy.services.metadata_service import MetadataService
from acedeploy.services.policy_service import PolicyService
from aceservices.snowflake_service import SnowClient, SnowClientConfig
from acedeploy.services.solution_service import SolutionClient
from acedeploy.services.dependency_parser import DependencyParser
from acedeploy.core.model_sql_entities import DbObjectType
from aceutils import database_management
from aceutils.action_generator import (
    generate_actions_from_git_diff,
    generate_actions_from_solution,
)
from aceutils.general_util import save_action_json, save_action_list
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def configure() -> SolutionConfig:
    """
    Load the current configuration from the path set in ACEDEPLOY_CONFIG_PATH.

    Returns:
        Configuration object
    """
    return SolutionConfig()


def execute_deployment(config: SolutionConfig) -> None:
    """
    Execute the deployment defined in the given `config`.

    Use `configure()` generate the config object.
    """
    target_clone_created = False

    try:
        # prepare clients
        snow_client_account = SnowClient(
            SnowClientConfig.get_from_solution_config(config)
        )
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
            config_project_folder_filter=config.project_folder_filter,
            disabled_object_types=config.disabled_object_types,
        )

        log.info(f"SET deployment mode [ '{config.deployment_mode}' ]")

        # deploy to meta database
        if config.ignore_git_information is True:
            solution_client.load_solution(
                string_replace_dict=config.string_replace,
                pre_and_postdeployment_execution=PreOrPostDeploymentScriptsExecutionOptions.ALL,
            )
            dependency_client = DependencyParser(solution_client)
            dependency_client.build_full_dependency_graph()
            log.info(f"DEPLOY full solution TO meta db [ '{config.database_meta}' ]")
            action_list_meta = deploy_to_meta_database(
                solution_client,
                dependency_client,
                snow_client_meta,
                config,
                "solution",
                config.parallel_threads,
            )
        else:
            git_client = GitClient(
                config.solution_root_path, config.git_tag_regex, config.deployment_mode
            )
            git_changed_file_list = git_client.get_diff_filelist()
            solution_client.load_solution(
                git_changed_file_list=git_changed_file_list,
                string_replace_dict=config.string_replace,
                pre_and_postdeployment_execution=PreOrPostDeploymentScriptsExecutionOptions.GIT,
            )
            dependency_client = DependencyParser(solution_client)
            dependency_client.build_full_dependency_graph()
            log.info(f"DEPLOY git diff TO meta db [ '{config.database_meta}' ]")
            action_list_meta = deploy_to_meta_database(
                solution_client,
                dependency_client,
                snow_client_meta,
                config,
                "git",
                config.parallel_threads,
            )

        # create a clone
        if config.deploy_to_clone:
            log.info(
                f"CREATE TARGET database [ '{config.database_target}' ] as CLONE of [ '{config.clone_source_database}' ] with mode [ '{config.deploy_to_clone_mode}' ]"
            )
            pre_or_postdeployment_steps_will_be_executed = (
                len(
                    [
                        s
                        for s in solution_client.postdeployment_steps
                        + solution_client.predeployment_steps
                        if s.execute_step
                    ]
                )
                > 0
            )
            create_target_clone(
                snow_client_account,
                action_list_meta,
                config,
                pre_or_postdeployment_steps_will_be_executed,
            )
            target_clone_created = True

        # deploy to target database
        if config.deployment_mode.casefold() != "validate":
            log.info(
                f"START solution deployment TO target db [ '{config.database_target}' ]."
            )
            (
                action_list,
                predeployment_steps,
                postdeployment_steps,
            ) = deploy_to_target_database(
                snow_client_target,
                snow_client_meta,
                snow_client_account,
                solution_client,
                dependency_client,
                config,
                not config.abort_on_data_loss,
                config.deployment_mode.casefold() == "release",
            )

            if config.action_summary_path != "":
                log.info(f"SAVE ACTION SUMMARY TO [ '{config.action_summary_path}' ]")
                save_action_list(
                    config.action_summary_path,
                    action_list,
                    predeployment_steps,
                    postdeployment_steps,
                )

            if config.action_json_path != "":
                log.info(f"SAVE ACTION JSON TO [ '{config.action_json_path}' ]")
                save_action_json(
                    config.action_json_path,
                    action_list,
                    config.database_target,
                    config.snow_role,
                )

            # set flags in persist table
            if config.persist_views_table:
                persist_views_table.set_persist_tags(
                    config.persist_views_table,
                    action_list,
                    config.database_target,
                    snow_client_account,
                )

    except Exception as err:
        log.error(str(err))
        raise err

    finally:
        database_management.drop_database_and_set_retention_time(
            database_name=config.database_meta,
            snow_client=snow_client_account,
            retention_time_in_days=config.temp_db_retention_time,
        )
        if (
            target_clone_created
            and config.deploy_to_clone
            and config.deploy_to_clone_mode
            and config.drop_clone_after_run
            and (config.clone_source_database.lower() != config.database_target.lower())
        ):
            database_management.drop_database_and_set_retention_time(
                database_name=config.database_target,
                snow_client=snow_client_account,
                retention_time_in_days=config.temp_db_retention_time,
            )


def deploy_to_meta_database(
    solution_client: SolutionClient,
    dependency_client: DependencyParser,
    snow_client: SnowClient,
    config: SolutionConfig,
    mode: str,
    parallel_threads: int,
) -> List[List[List[DbObjectAction]]]:
    """
    Deploy entire solution or git diff to meta database.

    Used to validate the sql code and to initialize the meta db for comparison with the target db in a later step.

    Args:
        `solution_client`: Collection of solution items
        `dependency_client`: (Unordered) graph of solution items
        `snow_client`: Connection to Snowflake (must be scoped to meta database)
        `mode`: 'git' or 'solution'. Flag wether we are deploying changes based off git or all solution items
        `parallel_threads`: Number of parallel threads during deployment

    Returns:
        Nested list of actions that were performed during the deployment.
        The list is nested and ordered to allow parallel deployment of objects which do not share dependencies.
        Refer to `deploy_client.start_deployment()` for details.
    """
    action_list = []
    deploy_client = DeployService(solution_client, dependency_client, snow_client, config)
    log.info(f"START validation TO meta db [ '{snow_client.database}' ]")
    if mode == "git":
        action_list = generate_actions_from_git_diff(solution_client)
    elif mode == "solution":
        action_list = generate_actions_from_solution(solution_client)
    else:
        raise ValueError(f"ERROR invalid meta deployment mode [ '{mode}' ]")

    deploy_client.execute_predeployment(target=PreOrPostDeploymentScriptTarget.META)
    action_list = deploy_client.start_deployment(
        action_list, True, parallel_threads=parallel_threads
    )
    deploy_client.execute_postdeployment(target=PreOrPostDeploymentScriptTarget.META)
    log.info(f"SUCCESS validation TO meta db [ '{snow_client.database}' ]")

    return action_list


def deploy_to_target_database(
    snow_client_target: SnowClient,
    snow_client_meta: SnowClient,
    snow_client_account: SnowClient,
    solution_client: SolutionClient,
    dependency_client: DependencyParser,
    config: SolutionConfig,
    allow_dataloss: bool,
    rollback_enabled: bool,
) -> Tuple[List[DbObjectAction], List[str], List[str]]:
    """
    Deploy changes to the target database.

    Steps:
        1) Execute predeployment scripts on target database
        2) Compare meta database and target database and determine required actions
        3) Execute required actions on target database
        4) Execute postdeployment scripts on target database

    Args:
        `snow_client_target`: Connection to Snowflake (must be scoped to target database)
        `snow_client_meta`: Connection to Snowflake (must be scoped to meta database)
        `snow_client_account`: Connection to Snowflake (must not be scoped to a database)
        `solution_client`: Collection of solution items
        `dependency_client`: (unordered) graph of solution items
        `config`: Deployment configuration
        `allow_dataloss`: Flag wether deployment will be performed if dataloss in a table is detected
        `rollback_enabled`: Flag wether roll back will be performed on failed deployment

    Returns:
        Nested list of actions that were performed during the deployment.
        The list is nested and ordered to allow parallel deployment of objects which do not share dependencies.
        Refer to `deploy_client.start_deployment()` for details.
    """
    deploy_client = DeployService(
        solution_client,
        dependency_client,
        snow_client_target,
        config,
        snow_client_meta=snow_client_meta,
        snow_client_account=snow_client_account,
        release_name=config.release_name,
        temp_db_retention_time=config.temp_db_retention_time,
    )
    predeployment_steps = deploy_client.execute_predeployment(
        target=PreOrPostDeploymentScriptTarget.TARGET
    )
    action_list, policy_assignments_handler = generate_actions_from_db_diff(
        snow_client_meta, snow_client_target, solution_client, config
    )

    policy_service = None
    if config.handle_policy_assignments:
        log.info(f'START handling policy assignments.')
        policy_service = PolicyService(
            policy_assignments_handler, 
            config.policy_assignments_deployment_database, 
            config.policy_assignments_config_file_path, 
            config.policy_assignments_project, 
            config.policy_assignments_info_output_folder_path,
            config.policy_assignments_repo_path
        )
        policy_service.get_policy_assignments_info()

    deploy_client.start_deployment(
        action_list=action_list,
        is_meta_deployment=False,
        allow_dataloss=allow_dataloss,
        rollback_enabled=rollback_enabled,
        schema_list=config.schema_list,
        parallel_threads=config.parallel_threads,
        autoresume_tasks=config.autoresume_tasks,
        policy_service=policy_service,
        execute_in_parallel_sessions=config.execute_in_parallel_sessions,
    )

    if config.handle_policy_assignments:
        if config.policy_assignments_save_info:
            policy_service.save_policy_assignments_info()
        if config.policy_assignments_create_azure_pull_request_comments:
            policy_service.create_azure_devops_pr_comment_from_policy_assignments_info()


    postdeployment_steps = deploy_client.execute_postdeployment(
        target=PreOrPostDeploymentScriptTarget.TARGET
    )
    return action_list, predeployment_steps, postdeployment_steps


def generate_actions_from_db_diff(
    snow_client_meta: SnowClient,
    snow_client_target: SnowClient,
    solution_client: SolutionClient,
    config: SolutionConfig,
) -> List[DbObjectAction]:
    """
    Compare meta and target database and generate list of actions.

    The meta database corresponds to the desired state of the target.
    By comparing both databases a list of required actions is generated.

    Args:
        `snow_client_meta`: Connection to Snowflake (must be scoped to meta database)
        `snow_client_target`: Connection to Snowflake (must be scoped to target database)
        `solution_client`: Collection of solution items
        `config`: Deployment configuration

    Returns:
        Unordered list of actions
    """
    metadata_service_metadb = MetadataService(
        snow_client=snow_client_meta,
        snow_edition=config.snow_edition,
        disabled_object_types=config.disabled_object_types,
        object_options=config.object_options,
        workarounds_options=config.workarounds
    )
    metadata_service_metadb.get_all_metadata(
        schema_list=config.schema_list, 
        parallel_threads=config.parallel_threads,
        check_for_language_restrictions=True,
    )
    schemas_on_meta = [s.name for s in metadata_service_metadb.schemas]
    schema_filter_target = {"whitelist": schemas_on_meta}

    metadata_service_targetdb = MetadataService(
        snow_client=snow_client_target,
        snow_edition=config.snow_edition,
        disabled_object_types=config.disabled_object_types,
        object_options=config.object_options,
        workarounds_options=config.workarounds
    )
    metadata_service_targetdb.get_all_metadata(
        schema_filter_target,
        config.parallel_threads,
        get_policies_on_objects_legacy=config.reapply_existing_policies,
    )

    log.info("GET information schema DIFF")

    compare_client = DbCompareClient(
        metadata_service_metadb, metadata_service_targetdb, solution_client
    )
    compare_client.get_add_actions()
    compare_client.get_alter_actions()
    if config.object_options.get(DbObjectType.PROCEDURE, {}).dropOverloadedObjects or config.object_options.get(DbObjectType.FUNCTION, {}).dropOverloadedObjects:
        compare_client.get_drop_overloaded_actions(config.object_options.get(DbObjectType.PROCEDURE, {}).dropOverloadedObjects, config.object_options.get(DbObjectType.FUNCTION, {}).dropOverloadedObjects)

    if config.drop_target_objects:
        if config.ignore_git_information:
            compare_client.get_drop_actions_from_solution()
        else:
            compare_client.get_drop_actions_from_git()

    return compare_client.action_list, compare_client.policy_assignments_handler


def create_target_clone(
    snow_client_account: SnowClient,
    action_list_meta: List[List[List[DbObjectAction]]],
    config: SolutionConfig,
    pre_or_postdeployment_steps_will_be_executed: bool,
) -> None:
    """
    Create a clone of a database to be used as the target database.

    There are different options on how exactly the clone is created, as set in
    `config.deploy_to_clone_mode`: `minimal`, `schemalist`, `full`.

    In mode `minimal`, if `pre_or_postdeployment_steps_will_be_executed` is true, mode
    `schemalist` is used instead. If cloning fails in mode `minimal`, cloning
    automatically falls back to mode `schemalist`.

    Args:
        `snow_client_meta`: Connection to Snowflake (must be scoped to meta db)
        `action_list_meta`: Ordered list of actions, as returned by `deploy_client.start_deployment()` after the meta deployment
        `config`: Deployment configuration
        `pre_or_postdeployment_steps_will_be_executed`: Flag wether the deployment will contain pre- or postdeployment steps.
    """
    mode = config.deploy_to_clone_mode.lower()
    if mode == "minimal" and pre_or_postdeployment_steps_will_be_executed:
        log.warning(
            "Minimal cloning not possible if pre- or postdeployment steps will be executed. Will create full database clone instead. This will take longer."
        )
        mode = "schemalist"
    if mode == "minimal":
        try:
            database_management.create_clone_by_ordered_action_list(
                config.clone_source_database,
                config.database_target,
                action_list_meta,
                snow_client_account,
                replace_if_exists=False,
                db_retention_time_in_days=config.target_db_retention_time,
                policy_assignments_role=config.policy_assignments_role
            )
        except Exception as err:
            log.warning(
                "Minimal cloning was not successful. Will create full database clone instead. This will take longer."
            )
            log.info(f"Reason for failed minimal clone step: {str(err)}")
            database_management.clone_database_by_schemas(
                config.clone_source_database,
                config.database_target,
                config.schema_list,
                snow_client_account,
                replace_if_exists=True,
                parallel_threads=config.parallel_threads,
                db_retention_time_in_days=config.target_db_retention_time,
            )
    elif mode == "schemalist":
        database_management.clone_database_by_schemas(
            config.clone_source_database,
            config.database_target,
            config.schema_list,
            snow_client_account,
            replace_if_exists=False,
            parallel_threads=config.parallel_threads,
            db_retention_time_in_days=config.target_db_retention_time,
        )
    elif mode == "full":
        database_management.clone_database(
            config.clone_source_database,
            config.database_target,
            snow_client_account,
            replace_if_exists=False,
        )
    else:
        raise ValueError(
            f"Invalid value for config.deploy_to_clone_mode. Must be one of (minimal, schemalist, full). Got '{config.deploy_to_clone_mode}'."
        )
