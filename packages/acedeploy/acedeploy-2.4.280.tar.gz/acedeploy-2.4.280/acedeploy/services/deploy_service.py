import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from threading import current_thread
from datetime import datetime
from typing import Dict, List
import time

import aceutils.action_order_util as action_order_util
import aceutils.database_management as database_management
import aceutils.dict_and_list_util as dict_and_list_util
import aceutils.general_util as gen_util
import aceutils.parallelization_util as parallelization_util
from acedeploy.services.dependency_parser import DependencyParser
from acedeploy.core.model_db_statement import DbStatement
from acedeploy.core.model_object_action_entities import DbObjectAction, TableAction
from acedeploy.core.model_prepostdeploymentsteps import PreOrPostDeploymentScriptTarget, PreOrPostDeploymentScriptType
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
from aceservices.snowflake_service import SnowClient, SnowClientConfig
from acedeploy.core.model_configuration import SolutionConfig
from acedeploy.services.solution_service import SolutionClient
from acedeploy.services.policy_service import PolicyService
from aceutils.logger import LoggingAdapter, LogOperation, LogStatus

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class DeployService:
    """
    Service to handle deployment to a database.

    Main functionalities:
        Generate a list of actions to be performed on a database
        Order a list of actions so that dependent objects are deployed in the correct order
        Deploy a list of ordered actions to a database
        Rollback a deployment in case an error occurs
    """

    def __init__(
        self,
        solution_client: SolutionClient,
        dependency_client: DependencyParser,
        snow_client: SnowClient,
        config: SolutionConfig,
        snow_client_meta: SnowClient = None,
        snow_client_account: SnowClient = None,
        release_name: str = "",
        temp_db_retention_time: int = None,
    ) -> None:
        """
        Initialize a new deployment agent.

        Args:
            solution_client: Solution client which contains all files on disk
            snow_client: Snowflake client for database operations (the deployment will be performed onto this database)
            dependency_client: DependencyParser which contains the (unsorted) graph for all solution objects
            snow_client_meta: Snowflake client to obtain meta data information on desired state from meta db
            snow_client_account: Snowflake client to perform database operations (e.g. cloning of database). Required for use of rollback.
            release_name: Name of the release (current timestamp will be appended to this name)
            temp_db_retention_time: retention time to which the rollback db will be set shortly before it is dropped
        """
        self._snow_client = snow_client
        self._snow_client_meta = snow_client_meta
        self._snow_client_account = snow_client_account
        self._config = config
        self._solution_client = solution_client
        self._dependency_client = dependency_client
        self._target_db_name = self._snow_client.database
        self._release_name = (
            ""
            if release_name == ""
            else f"{release_name}_{datetime.now().strftime('%Y%m%d%H%m')}"
        )
        self._release_name_clean = re.sub("[^0-9a-zA-Z]+", "_", self._release_name)
        self._rollback_db_name = (
            f"{self._snow_client.database}_ROLLBACK_CLONE_{self._release_name_clean}"
        )
        self._temp_db_retention_time = temp_db_retention_time
        self._policy_service = None
        self._stream_objects = None

    def start_deployment(
        self,
        action_list: List[DbObjectAction],
        is_meta_deployment: bool,
        allow_dataloss: bool = False,
        rollback_enabled: bool = False,
        schema_list: Dict[str, List[str]] = None,
        parallel_threads: int = 1,
        autoresume_tasks: bool = False,
        policy_service: PolicyService = None,
        execute_in_parallel_sessions: bool = False,
    ) -> List[List[List[DbObjectAction]]]:
        """
        Execute a deployment against target database.

        Main steps:
            Order Db Actions and determines additional dependencies
            Generate SQL statements based on Db actions
            Execute SQL statements
            Execute post deployment scripts

        Args:
            `action_list`: List of (unordered) actions to be performed
            `is_meta_deployment`: Flag to indicate the deployment to a meta db
            `allow_dataloss`: Allow dataloss during deployment
            `rollback_enabled`: Roll back deployment on error
            `schema_list`: Names of the schemas to clone for rollback clone
            `parallel_threads`: Number of parallel threads used during some snowflake operations
            `autoresume_tasks`: Resume all tasks that were modified and that were started before the deployment
            `policy_service`: PolicyService to handle policy assignments during the deployment
            `execute_in_parallel_sessions`: Flag to execute the deployment in different session when using parallel threads (only applies when the parameter parallel_threads>1)

        Returns:
            Nested list of actions that were performed during the deployment.
            The list is nested and ordered to allow parallel deployment of objects which do not share dependencies.
            Refer to `action_order_util.order_action_list()` for details.
        """
        action_summary = "\n".join(gen_util.generate_action_log_summaries(action_list))
        log.info(
            f"SUMMARY desired actions (excluding actions on dependent objects):\n{action_summary}"
        )

        dataloss_occurs = self.check_dataloss(action_list)
        if dataloss_occurs and (not allow_dataloss):
            raise ValueError(
                "DATA LOSS detected. ABORT deployment. See full log for more details."
            )

        if rollback_enabled:
            schema_list_filtered = self._filter_schema_list_by_action_list(action_list, schema_list)
            self.create_rollback_clone(schema_list_filtered, parallel_threads, action_list)
            self._get_stream_objects_for_rollback(self._target_db_name)

        ordered_action_list = action_order_util.order_action_list(
            action_list, self._dependency_client, is_meta_deployment
        )

        self._policy_service=policy_service
        
        start_time_generate_statements_from_object_actions = time.time()
        statement_list = self.generate_statements_from_object_actions(
            ordered_action_list
        )
        end_time_generate_statements_from_object_actions = time.time()
        log.info(f"============= Execution Time generate_statements_from_object_actions: {round(end_time_generate_statements_from_object_actions - start_time_generate_statements_from_object_actions, 2)} seconds")


        self._pause_pipes(action_list)

        self.deploy_database_objects(statement_list, rollback_enabled, parallel_threads, execute_in_parallel_sessions)

        if rollback_enabled:
            database_management.drop_database_and_set_retention_time(
                self._rollback_db_name,
                self._snow_client_account,
                self._temp_db_retention_time,
            )

        if autoresume_tasks and not is_meta_deployment:
            self._resume_tasks(action_list)

        return ordered_action_list
    
    @staticmethod
    def _filter_schema_list_by_action_list(action_list: List[DbObjectAction], schema_list: Dict[str, List[str]] = None) -> Dict[str, List[str]]:
        """
        Filter list of schemas by schemas included in the `action_list`.
        In case there is a blacklist defined, a whitelist will be created and filtered additonally by the blacklist - the blacklist will consequently be dropped.
        """
        if not schema_list:
            schema_list={}
    
        action_schema_list = []
        for action in action_list:
            action_schema = action.schema.casefold()
            if action_schema not in action_schema_list:
                action_schema_list.append(action_schema)
    
        if not 'whitelist' in schema_list:
            schema_list["whitelist"] = action_schema_list
        else:
            schema_whitelist = [s.casefold() for s in schema_list["whitelist"]]
            schema_list["whitelist"] = [ s for s in schema_whitelist if s in action_schema_list ]
    
        if 'blacklist' in schema_list:
            schemas_blacklist = [s.casefold() for s in schema_list["blacklist"]]
            schema_list["whitelist"] = [ s for s in schema_list["whitelist"] if s not in schemas_blacklist]
            schema_list.pop('blacklist')
    
        return schema_list
    
    def _get_stream_objects_for_rollback(self, target_db_name: str) -> Dict:
        """
        Get stream objects (tables, views, directory tables, or external tables) to produce warnings in case affected stream during rollback (which cannot rolled back). 
        Only streams in the target database will be checked.
        Returns casefold stream object identifiers.
        Note: By renaming the objects during rollback these stream break even if the stream was not altered/recreated during deployment (yet).
        """
        show_streams_query= f"SHOW STREAMS IN DATABASE {target_db_name}"

        result = self._snow_client.execute_query(show_streams_query, use_dict_cursor=True)

        self._stream_objects = {stream["table_name"].casefold():f"{stream['database_name']}.{stream['schema_name']}.{stream['name']}"  for stream in result}


    def create_rollback_clone(self, schema_list, parallel_threads, action_list):
        """
        Create a clone of the target database to use for rollback.
        """
        log.info(f"CREATE rollback clone database [ '{self._rollback_db_name}' ]")
        if self._release_name == "":
            raise ValueError("Release name must be set if rollback is enabled.")
        if schema_list:
            database_management.clone_database_by_schemas(
                self._target_db_name,
                self._rollback_db_name,
                schema_list,
                self._snow_client_account,
                replace_if_exists=False,
                parallel_threads=parallel_threads,
            )
        else:
            database_management.clone_database(
                self._target_db_name,
                self._rollback_db_name,
                self._snow_client_account,
                replace_if_exists=False,
            )
        # if a schema is created during deployment, it does not yet exist on the target database.
        # therefore, these schemas will not be created on the rollback db through the above functions.
        # the rollback function requires these schemas (even if they are empty), so they are created here.
        for schema_action in [
            a for a in action_list if a.object_type == DbObjectType.SCHEMA
        ]:
            self._snow_client_account.execute_statement(
                f"CREATE SCHEMA IF NOT EXISTS {self._rollback_db_name}.{schema_action.schema};"
            )

    def check_dataloss(self, action_list: List[DbObjectAction]) -> bool:
        """
        Check if dataloss occurs for the given `action_list`.

        Returns:
            True if dataloss occurs, else False
        """
        dataloss_occurs = False
        for action in action_list:
            if action.object_type == DbObjectType.TABLE:
                if action.action == DbActionType.ALTER:
                    dataloss_occurs = (
                        self._check_dataloss_alter(action) or dataloss_occurs
                    )
                elif action.action == DbActionType.DROP:
                    dataloss_occurs = (
                        self._check_dataloss_drop(action) or dataloss_occurs
                    )

        return dataloss_occurs

    def _check_dataloss_drop(self, action: TableAction) -> bool:
        """
        Check if dataloss will occur for DROP TABLE in a given `action`.

        Returns:
            True if dataloss occurs, else False
        """
        query = f"SELECT COUNT(1) FROM {action.full_name}"
        column_count = self._snow_client.execute_query(query, use_dict_cursor=False)[0][
            0
        ]
        if column_count != 0:
            log.warning(
                f"DATA LOSS detected if deployment continues. Required action will DROP table  [ '{action.full_name}' ] (affects {column_count} row(s))"
            )
            return True
        else:
            return False

    def _check_dataloss_alter(self, action: TableAction) -> bool:
        """
        Check if dataloss will occur for ALTER TABLE in a given `action`.

        Returns:
            True if dataloss occurs, else False
        """
        if len(action.columns_to_drop) == 0:
            return False
        dataloss_occurs = False
        query_counts = [f"COUNT({c}) AS {c}" for c in action.columns_to_drop]
        query = f"SELECT {', '.join(query_counts)} FROM {action.full_name}"
        counts = self._snow_client.execute_query(query)[0]
        for column in counts:
            if counts[column] > 0:
                dataloss_occurs = True
                log.warning(
                    f"DATA LOSS detected if deployment continues. Required action will DROP column [ '{action.full_name}.{column}' ] (affects {counts[column]} row(s))."
                )
        return dataloss_occurs

    def _execute_pre_or_postdeployment(self, selector: str, target: PreOrPostDeploymentScriptTarget) -> List[str]:
        """
        Execute pre- or postdeployment steps from  `self._solution_client`.

        Will only execute steps where `execute_step == True`.

        Args:
            `selector`: `pre` or `post`

        Returns:
            List of steps (content of file) that were executed.
        """
        if selector.lower() == "pre":
            step_list = self._solution_client.predeployment_steps
        elif selector.lower() == "post":
            step_list = self._solution_client.postdeployment_steps
        else:
            raise ValueError(f"Selector must be 'pre' or 'post', was '{selector}'")
        log.info(
            f"EXECUTE {selector}deployment",
            status=LogStatus.PENDING,
            db=self._snow_client.database,
        )
        for step in step_list:
            if step.execute_step and step.target == target:
                if step.type == PreOrPostDeploymentScriptType.SQL:
                    log.info(
                        f"EXECUTE sql file [ '{step.path}' ]",
                        status=LogStatus.PENDING,
                        db=self._snow_client.database,
                        operation=LogOperation.SQLCOMMAND,
                    )
                    self._snow_client.execute_statement(step.content)
                # if step.type == PreOrPostDeploymentScriptType.PYTHON:
                #     self._execute_python_file(step.path) # for security reasons, python postdeployment steps are currently not supported (also removed in solution service)
        log.info(
            f"SUCCESS {selector}deployment",
            status=LogStatus.SUCCESS,
            db=self._snow_client.database,
        )
        return step_list

    def execute_predeployment(self, target: PreOrPostDeploymentScriptTarget) -> List[str]:
        """
        Execute predeployment steps as given in `self._solution client`.

        Returns:
            List of steps (content of file) that were executed.
        """
        return self._execute_pre_or_postdeployment("pre", target)

    def execute_postdeployment(self, target: PreOrPostDeploymentScriptTarget) -> List[str]:
        """
        Execute postdeployment steps as given in `self._solution client`.

        Returns:
            List of steps (content of file) that were executed.
        """
        return self._execute_pre_or_postdeployment("post", target)

    # def _execute_python_file(self, script_path: str) -> None:
    #     """
    #     Execute a given python file.
    #     """
    #     log.info(
    #         f"EXECUTE python file [' {script_path} ']",
    #         status=LogStatus.PENDING,
    #     )
    #     connection_info = self._snow_client._config.get_connect_info()
    #     process = subprocess.run(
    #         ["python", script_path, json.dumps(connection_info)],
    #         capture_output=True,
    #     )
    #     stdout = process.stdout.decode("utf-8")
    #     for line in stdout.splitlines():
    #         log.info(line)
    #     if process.returncode != 0:
    #         raise RuntimeError(
    #             f"Error while executing python script {script_path}:\n{process.stderr.decode('utf-8')}"
    #         )

    def deploy_database_objects(
        self,
        db_statements: List[List[List[DbStatement]]],
        rollback_enabled: bool = False,
        parallel_threads: int = 1,
        execute_in_parallel_sessions: bool = False,
    ) -> None:
        """
        Deploy database objects, as given by a list of SQL statements.

        If an error occurs during deployment, the rollback database (if set) will be
        used to roll back the deployment.

        Args:
            `db_statements`: Ordered list of statement objects (see `generate_statements_from_object_actions()` for details on structure of list)
            `rollback_enabled`: If error occurs during deployment, roll back deployment
            `parallel_threads`: number of threads used during deployment
        """
        query_tag = (
            f"Release {self._release_name} to {self._target_db_name} (rollback db: {self._rollback_db_name})"
            if rollback_enabled
            else ""
        )
        log_summary = self._generate_deployment_log_summary(db_statements)
        log.info(
            f"START deployment TO database [ '{self._target_db_name}' ] WITH query tag [ '{query_tag}' ] SUMMARY (including dependent objects): {log_summary}",
            status=LogStatus.PENDING,
            db=self._snow_client.database,
        )
        self._snow_client.execute_statement(
            f'ALTER SESSION SET QUERY_TAG = "{query_tag}"'
        )

        if rollback_enabled:
            db_statements_flat = dict_and_list_util.flatten(db_statements)
            for (
                db_statement
            ) in (
                db_statements_flat
            ):  # for rollback to work, parallel execution cannot be used
                try:
                    self._snow_client.execute_statement(db_statement.statement)
                except Exception as err:
                    self._rollback_deployment(db_statements_flat, db_statement)
                    raise err
        else:

            if execute_in_parallel_sessions:
                def execute_and_log_new_session(config: SolutionConfig, statements: List[List]):
                    logger.info(f"START execution of statement set with thread name: {current_thread().name}.")
                    snow_client_target = SnowClient(SnowClientConfig.get_from_solution_config(config, config.database_target))
                    with snow_client_target as snow_client:
                        for statement in statements:
                            snow_client.execute_statement(statement)
                        logger.info(f"FINISH execution of statement set in Snowflake session ID {snow_client.connection.session_id} with thread name: {current_thread().name}.")

            else:
                def execute_and_log(statements, i, n):
                    log.info(
                        f"START execution of statement set [ '{i+1} of {n}' ] with LENGTH [ '{len(statements)}' ]"
                    )
                    self._snow_client.execute_statement(statements)
                    log.debug(
                        f"FINISH execution of statement set [ '{i+1} of {n}' ] with LENGTH [ '{len(statements)}' ]"
                    )

            for db_statement_list in db_statements:
                statements = []
                statements_dict = {}
                for db_statement_sublist in db_statement_list:
                    if db_statement_sublist:
                        statements.append([s.statement for s in db_statement_sublist])
                        statements_dict = {i: s for i, s in enumerate(statements)}

                if execute_in_parallel_sessions:
                    if statements:
                        log.info(f"INITIALIZE execution of [ '{len(statements)}' ] statement sets in [ '{parallel_threads}' ] parallel Snowflake Sessions")
                        _ =parallelization_util.execute_func_in_parallel(execute_and_log_new_session, statements, parallel_threads, self._config)
                else:
                    with ThreadPoolExecutor(max_workers=parallel_threads) as pool:
                        for __ in pool.map(
                            lambda k: execute_and_log(
                                statements_dict[k], k, len(statements_dict)
                            ),
                            statements_dict,
                        ):
                            pass  # need to iterate over results from execute_and_log(), otherwise exceptions in execute_and_log() will not be raised in main thread

        log.info(
            f"SUCCESS deployment TO database [ '{self._target_db_name}' ]",
            status=LogStatus.SUCCESS,
            db=self._snow_client.database,
        )
        self._snow_client.execute_statement('ALTER SESSION SET QUERY_TAG = ""')

    def _pause_pipes(self, action_list: List[DbObjectAction]) -> None:
        """
        Pause all running pipes that have ALTER PIPE actions in `action_list`.
        Make sure none of the pipes have pending files.

        Only pipes in state RUNNING can be paused. Skip all other pipes.
        See link for all possible pipe states:
        https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status.html
        """
        log.info("PAUSE running PIPES that need to be altered.")
        pipe_full_names = [
            a.full_name
            for a in action_list
            if (a.object_type == DbObjectType.PIPE and a.action == DbActionType.ALTER)
        ]
        for pipe_full_name in pipe_full_names:
            pipe_status_before = self._get_pipe_status(pipe_full_name)
            if pipe_status_before["executionState"] == "RUNNING":
                statement = (
                    f"ALTER PIPE {pipe_full_name} SET PIPE_EXECUTION_PAUSED = TRUE;"
                )
                self._snow_client.execute_statement(statement)
                pipe_status_after = self._get_pipe_status(pipe_full_name)
                if pipe_status_after["executionState"] != "PAUSED":
                    raise EnvironmentError(
                        f"Something went wrong trying to pause pipe [ '{pipe_full_name}' ]. Current status is [ '{pipe_status_after['executionState']}' ]. Please fix before restarting deployment. The following pipes might now be in paused state instead of running state: {pipe_full_names}. You might want to manually set their state to running."
                    )
                if pipe_status_after["pendingFileCount"] > 0:
                    raise EnvironmentError(
                        f"Pipe [ '{pipe_full_name}' ] has [ '{pipe_status_after['pendingFileCount']}' ] pending files. Wait for processing to finish before restarting deployment. The following pipes might now be in paused state instead of running state: {pipe_full_names}. You might want to manually set their state to running."
                    )
            elif pipe_status_before["pendingFileCount"] > 0:
                raise EnvironmentError(
                    f"Pipe [ '{pipe_full_name}' ] is in state [ '{pipe_status_before['executionState']}' ] and has [ '{pipe_status_before['pendingFileCount']}' ] pending files. Wait for processing to finish before restarting deployment. The following pipes might now be in paused state instead of running state: {pipe_full_names}. You might want to manually set their state to running."
                )
            else:
                log.debug(
                    f"Pipe [ '{pipe_full_name}' ] does not need to be paused (is not running and has no pending files)."
                )
        log.info(f"PAUSED [ '{len(pipe_full_names)}' ] PIPES.")

    def _get_pipe_status(self, pipe_full_name: str) -> Dict:
        """
        Get the status of a pipe.
        """
        query = f"SELECT SYSTEM$PIPE_STATUS('{pipe_full_name}') AS STATUS"
        result = self._snow_client.execute_query(query, use_dict_cursor=True)
        return json.loads(result[0]["STATUS"])

    def _resume_tasks(self, action_list: List[DbObjectAction]) -> None:
        """
        Resume all tasks that appear in given `action_list`.
        """
        log.info("RESUMING TASKS that were in state [ 'started' ] before deployment")
        task_actions = [
            a
            for a in action_list
            if (
                a.object_type == DbObjectType.TASK
                and a.action in (DbActionType.ADD, DbActionType.ALTER)
            )
        ]
        ordered_task_actions = (
            action_order_util.order_actions_with_internal_dependencies_from_solution(
                [DbObjectType.TASK],
                task_actions,
                self._solution_client,
                is_meta_deployment=False,
            )
        )
        statements = []
        for tasklist in ordered_task_actions:
            for task in reversed(
                tasklist
            ):  # root task must be resumed last https://docs.snowflake.com/en/sql-reference/sql/alter-task.html#usage-notes
                statement = task.generate_resume_statement()
                if statement:
                    statements.append(statement)
        self._snow_client.execute_statement(statements)
        log.info(f"RESUMED [ '{len(statements)}' ] of [ '{len(task_actions)}' ] TASKS")

    def _rollback_deployment(
        self, db_statements: List[DbStatement], failed_statement: DbStatement
    ) -> None:
        """
        Roll back deployment, using rollback db.

        All elements affected by db_statements up to and including the failed statement will be rolled back.
        Rollback is performed by renaming the objects from the target database to a new name. Afterwards,
        the backed up object from the rollback database is renamed to take the place of the original object
        in the target database.

        Args:
            `db_statements`: ordered list of original deployment statements
            `failed_statement`: Statement during which the deployment failed. Must be element in db_statements.
        """
        log.info(
            f"ROLLBACK deployment TO database [ '{self._target_db_name}' ] USING database [ '{self._rollback_db_name}' ]",
            status=LogStatus.PENDING,
            db=self._snow_client.database,
        )
        query_tag = f"Roll back deployment {self._release_name} to {self._target_db_name} using {self._rollback_db_name}"
        self._snow_client.execute_statement(
            f'ALTER SESSION SET QUERY_TAG = "{query_tag}"'
        )

        db_statements.reverse()  # need to go in reverse: if view a references view b it can only be renamed, if view b exists
        failed_index = db_statements.index(failed_statement)
        db_object_list = []
        for i, statement in enumerate(db_statements):
            if i <= failed_index:
                continue  # this change has not been deployed as therefore does not need to be rolled back
            if statement.object_type not in (
                DbObjectType.TABLE,
                DbObjectType.VIEW,
                DbObjectType.MATERIALIZEDVIEW,
                DbObjectType.FUNCTION,
                DbObjectType.PROCEDURE,
                DbObjectType.FILEFORMAT,
                DbObjectType.DYNAMICTABLE,
                DbObjectType.TAG
            ):
                log.info(
                    f"SKIP rollback of [ '{statement.full_name}' ] (type [ '{statement.object_type}' ] cannot be rolled back)"
                )
                continue  # do not roll back these types of objects
            statement.statement = (
                ""  # statement is no longer needed, removing it makes comparison easier
            )
            if (
                statement not in db_object_list
            ):  # objects can have multiple statements, we only need each object once
                db_object_list.append(statement)

        for db_object in db_object_list:
            log.info(
                f"ROLLBACK object [ '{db_object.full_name}' ]",
                status=LogStatus.PENDING,
                db=self._snow_client.database,
            )
            rollback_statement = self._generate_rollback_statement(
                db_object,
                self._target_db_name,
                self._rollback_db_name,
                self._release_name_clean,
            )
            self._snow_client.execute_statement(rollback_statement)

        # check if streams are affected by rollback
        self._check_streams_on_rollback_objects(self._target_db_name, db_object_list)

        log.info(
            f"SUCCESS ROLLBACK deployment TO database [ '{self._target_db_name}' ] USING database [ '{self._rollback_db_name}' ]",
            status=LogStatus.SUCCESS,
            db=self._snow_client.database,
        )
        self._snow_client.execute_statement('ALTER SESSION SET QUERY_TAG = ""')


    def _check_streams_on_rollback_objects(
        self,
        target_db_name: str,
        rollback_objects: list
    ):
        """
        Produces a warning in case of affected streams by rollback. 
        Compares case-insensitive object identifiers.
        Note: By renaming the objects during rollback these streams break even if the stream was not altered/recreated during deployment (yet).
        """
        for rollback_object in rollback_objects:
            rollback_object_identifier = f"{target_db_name}.{rollback_object.schema}.{rollback_object.name}"

            if rollback_object_identifier.casefold() in self._stream_objects:
                affected_stream = self._stream_objects[rollback_object_identifier.casefold()]
                log.warning(
                            f"AFFECTED stream by rollback [ '{affected_stream}' ] will be referencing backup object - cannot be rolled back"
                        )

    @staticmethod
    def _generate_rollback_statement(
        original_statement: DbStatement,
        target_db_name: str,
        rollback_db_name: str,
        release_name_clean: str,
    ) -> str:
        """
        Generate rollback statement for object, using object information from DbStatement (statement of that object is not used).

        First, the object of the original statement is renamed. Then the object from the rollback db is used to replace the original object.
        Not applicable to schemas.

        Args:
            `original_statement`: statement object containing the object schema and name to be rolled back
            `target_db_name`: name of the database to be rolled back
            `rollback_db_name`: name of the database which contains the backed up objects
            `release_name_clean`: name of the release. may only contain characters valid for snowflake objects

        Returns:
            String with two statements, separated by semicolon: Rename object in target db & rename object in rollback db
        """

        def remove_parameters(object_name):
            """
            Remove anything in parantheses and whitespace before that.

            Examples:
                'DB1.SCHEMA1.PROC1 (INT, FLOAT)' -> 'DB1.SCHEMA1.PROC1'
                'DB1.SCHEMA2.VIEW1' -> 'DB1.SCHEMA2.VIEW1'
            """
            return re.sub(r"\s*(\(.*\))\s*$", "", object_name)

        if original_statement.object_type not in (
            DbObjectType.TABLE,
            DbObjectType.VIEW,
            DbObjectType.MATERIALIZEDVIEW,
            DbObjectType.FUNCTION,
            DbObjectType.PROCEDURE,
            DbObjectType.FILEFORMAT,
            DbObjectType.DYNAMICTABLE,
            DbObjectType.TAG
        ):
            raise ValueError(
                f"Objects of type [ '{original_statement.object_type}' ] cannot be rolled back"
            )

        object_type_text = DbObjectType.get_sql_object_type(
            original_statement.object_type
        )

        failed_object_backup = f"{target_db_name}.{remove_parameters(original_statement.full_name)}_ROLLBACK_{release_name_clean}"
        target_object = f"{target_db_name}.{original_statement.full_name}"
        rename_failed_statement = f"ALTER {object_type_text} IF EXISTS {target_object} RENAME TO {failed_object_backup};"

        source_object = f"{rollback_db_name}.{original_statement.full_name}"
        rename_clone_statement = f"ALTER {object_type_text} IF EXISTS {source_object} RENAME TO {remove_parameters(target_object)};"

        return rename_failed_statement + rename_clone_statement

    @staticmethod
    def _generate_deployment_log_summary(
        db_statements: List[List[List[DbStatement]]],
    ) -> str:
        """
        Generate a short summary of objects to deploy.

        Args:
            db_statements: Ordered list of statement objects (see docstring for `generate_statements_from_object_actions()` for details)

        Returns:
            Summar string, e.g. "3 schema(s), 1 table(s), 2 view(s), ..."
        """
        counts = {object_type: 0 for object_type in [o.value for o in DbObjectType]}
        for obj in dict_and_list_util.flatten(db_statements):
            counts[obj.object_type.value] += 1
        return ", ".join([f"{counts[key]} {key.lower()}(s)" for key in counts])

    def generate_statements_from_object_actions(
        self, object_action_list: List[List[List[DbObjectAction]]]
    ) -> List[List[List[DbStatement]]]:
        """
        Generate list of db statements from a given list of object actions.

        Given list should be ordered, so that gerenated statements can be
        executed without additional ordering.

        Args:
            `object_action_list`: list of object actions (see docstring for `order_action_list()` for details)

        Returns:
            List of statement objects (see docstring for order_action_list for details)
            Example (for clarity, using statements only instead of full DbStatement objects):
                [
                    [
                        ["CREATE SCHEMA A"], ["CREATE SCHEMA B"]
                    ], [
                        ["CREATE FUNCTION A.F1 ..."], ["CREATE FUNCTION B.F2 ..."]
                    ], [
                        ["CREATE TABLE A.T1 ...", "CREATE VIEW A.V1 AS SELECT * FROM A.T1" ],
                        ["CREATE TABLE B.T2 ...", "CREATE VIEW A.V1 AS SELECT * FROM B.T2" ],
                        ["CREATE TABLE B.T3"]
                    ], [
                        ["DROP VIEW C.V5"]
                    ]
                ]
        """
        log.info(
            f"GENERATE sql statements WITH count [ '{len(dict_and_list_util.flatten(object_action_list))}' ]"
        )



        return [
            [
                [
                    action.generate_statement_object(snow_client_meta=self._snow_client_meta, snow_client_target=self._snow_client, policy_service=self._policy_service)
                    for action in l3 if action.generate_statement_object(snow_client_meta=self._snow_client_meta, snow_client_target=self._snow_client, policy_service=self._policy_service).statement
                ]
                for l3 in l2
            ]
            for l2 in object_action_list
        ]
