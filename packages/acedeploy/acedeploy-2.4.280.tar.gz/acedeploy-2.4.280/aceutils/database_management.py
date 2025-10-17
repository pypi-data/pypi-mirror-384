import copy
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple

from acedeploy.core.model_configuration import SolutionConfig
from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
from acedeploy.services.metadata_service import MetadataService
from aceservices.snowflake_service import SnowClient, SnowClientConfig
import aceutils.dict_and_list_util as dict_and_list_util
import aceutils.file_util as file_util
from aceutils.logger import LoggingAdapter, LogStatus
from acedeploy.services.policy_service import PolicyService, get_policy_assignments_info_from_object
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType


logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def get_client_from_config() -> SnowClient:
    """
        Read config from path given in environment variable ACEDEPLOY_CONFIG_PATH.
        Return snowflake client (database scoped).
    Returns:
        SnowClient
    """
    config = SolutionConfig()
    snow_client = SnowClient(SnowClientConfig.get_from_solution_config(config))
    return snow_client


def get_schema_list_from_config() -> List[str]:
    """
        Read config from path given in environment variable ACEDEPLOY_CONFIG_PATH.
        Return schema name list.
    Returns:
        List[str] - list of schema names
    """
    config = SolutionConfig()
    return config.schema_list


def get_role_from_config() -> str:
    """
        Read config from path given in environment variable ACEDEPLOY_CONFIG_PATH.
        Return snowflake role.
    Returns:
        str - name of the role
    """
    config = SolutionConfig()
    return config.snow_role


def create_database(
    database_name: str,
    snow_client: SnowClient,
    replace_if_exists: bool = False,
    drop_schema_public: bool = False,
    db_retention_time_in_days: int = None,
) -> None:
    """
        Create a database.
    Args:
        database_name: str - name of the database to create
        snow_client: SnowClient - client to connect to snowflake account
        replace_if_exists: bool - replace database if it already exists
        drop_schema_public: bool - drop the schema PUBLIC after creation
        db_retention_time_in_days: int - if this value is given, set the parameter DATA_RETENTION_TIME_IN_DAYS for the target database to this value
    """
    log.info(
        f"CREATE database [ '{database_name}' ]",
        db=database_name,
        status=LogStatus.PENDING,
    )
    if db_retention_time_in_days is None:
        retention_statement = ""
    else:
        retention_statement = (
            f" DATA_RETENTION_TIME_IN_DAYS = {db_retention_time_in_days}"
        )
    if replace_if_exists:
        statement = f"CREATE OR REPLACE DATABASE {database_name}{retention_statement};"
    else:
        statement = f"CREATE DATABASE {database_name}{retention_statement};"
    snow_client.execute_statement(statement)
    if drop_schema_public:
        snow_client.execute_statement(f"DROP SCHEMA {database_name}.PUBLIC;")


def drop_database(database_name: str, snow_client: SnowClient) -> None:
    """
        Drop a database.
    Args:
        database_name: str - name of the database to create
        snow_client: SnowClient - client to connect to snowflake account
    """
    log.info(
        f"DROP database [ '{database_name}' ]",
        db=database_name,
        status=LogStatus.PENDING,
    )
    statement = f"DROP DATABASE {database_name}"
    snow_client.execute_statement(statement)


def drop_database_and_set_retention_time(
    database_name: str, snow_client: SnowClient, retention_time_in_days: int = None
) -> None:
    """
        Drop a database after setting it's retention time.
        First, set the retention time on the database and unset it on schemas.
        Second, drop the database.
        Skip the first step if retention_time_in_days is not set.
    Args:
        database_name: str - name of the database to create
        retention_time_in_days: int - value to set DATA_RETENTION_TIME_IN_DAYS on the database and schemas
        snow_client: SnowClient - client to connect to snowflake account
    """
    if retention_time_in_days is not None:
        set_database_and_schema_retention_time(
            database_name, retention_time_in_days, snow_client
        )
    drop_database(database_name, snow_client)


def set_database_and_schema_retention_time(
    database_name: str, retention_time_in_days: int, snow_client: SnowClient
) -> None:
    """
        Set the retention time of a database and all schemas in that database.
        Any value set on a schema will be unset, so that it will use the database default value.
        Will not affect retention times set directly on tables.
    Args:
        database_name: str - name of the database to create
        retention_time_in_days: int - value to set DATA_RETENTION_TIME_IN_DAYS on the database and schemas. if None it the retention time on the database will be unset.
        snow_client: SnowClient - client to connect to snowflake account
    """
    set_database_retention_time(database_name, retention_time_in_days, snow_client)
    unset_schemata_retention_time(database_name, snow_client)


def set_database_retention_time(
    database_name: str, retention_time_in_days: int, snow_client: SnowClient
) -> None:
    """
        Set or unset the retention time of a database.
    Args:
        database_name: str - name of the database
        retention_time_in_days: int - value to set DATA_RETENTION_TIME_IN_DAYS on the schemas, if set to "None", the function will UNSET the value
        snow_client: SnowClient - client to connect to snowflake account
    """
    if retention_time_in_days is None:
        unset_database_retention_time(database_name, snow_client)
    else:
        log.debug(
            f"SET DATA_RETENTION_TIME_IN_DAYS on database [ '{database_name}' ] to [ '{retention_time_in_days}' ]",
            db=database_name,
            status=LogStatus.PENDING,
        )
        statement = f"ALTER DATABASE {database_name} SET DATA_RETENTION_TIME_IN_DAYS = {retention_time_in_days};"
        snow_client.execute_statement(statement)


def unset_database_retention_time(database_name: str, snow_client: SnowClient) -> None:
    """
        Unset the retention time of a database.
    Args:
        database_name: str - name of the database
        snow_client: SnowClient - client to connect to snowflake account
    """
    log.debug(
        f"UNSET DATA_RETENTION_TIME_IN_DAYS on database [ '{database_name}' ]",
        db=database_name,
        status=LogStatus.PENDING,
    )
    statement = f"ALTER DATABASE {database_name} UNSET DATA_RETENTION_TIME_IN_DAYS;"
    snow_client.execute_statement(statement)


def set_schemata_retention_time(
    database_name: str, retention_time_in_days: int, snow_client: SnowClient
) -> None:
    """
        Set or unset the retention time of all schemas in a database.
    Args:
        database_name: str - name of the database
        retention_time_in_days: int - value to set DATA_RETENTION_TIME_IN_DAYS on the database, if set to "None", the function will UNSET the value
        snow_client: SnowClient - client to connect to snowflake account
    """
    if retention_time_in_days is None:
        unset_schemata_retention_time(database_name, snow_client)
    else:
        schemas, __ = get_schema_names(database_name, {"blacklist": []}, snow_client)
        log.debug(
            f"SET DATA_RETENTION_TIME_IN_DAYS on all schemas in database [ '{database_name}' ] to [ '{retention_time_in_days}' ]",
            db=database_name,
            status=LogStatus.PENDING,
        )
        for schema in schemas:
            statement = f"ALTER SCHEMA {database_name}.{schema} SET DATA_RETENTION_TIME_IN_DAYS = {retention_time_in_days};"
            snow_client.execute_statement(statement)


def unset_schemata_retention_time(database_name: str, snow_client: SnowClient) -> None:
    """
        Unset the retention time of all schemas in a database, so they will use the database default.
    Args:
        database_name: str - name of the database
        snow_client: SnowClient - client to connect to snowflake account
    """
    log.debug(
        f"UNSET DATA_RETENTION_TIME_IN_DAYS on all schemas in database [ '{database_name}' ]",
        db=database_name,
        status=LogStatus.PENDING,
    )

    schemas, __ = get_schema_names(database_name, {"blacklist": []}, snow_client)
    for schema in schemas:
        statement = (
            f"ALTER SCHEMA {database_name}.{schema} UNSET DATA_RETENTION_TIME_IN_DAYS;"
        )
        snow_client.execute_statement(statement)


def clone_database(
    source_database_name: str,
    target_database_name: str,
    snow_client: SnowClient,
    replace_if_exists: bool = False,
    db_retention_time_in_days: int = None,
    include_internal_stages: bool = False,
) -> None:
    """
        Clone a database.
    Args:
        source_database_name: str - name of the database to be cloned
        target_database_name: str - name of the database to be created
        snow_client: SnowClient - client to connect to snowflake account
        replace_if_exists: bool - replace target database if it already exists
        db_retention_time_in_days: int - if this value is given, set the parameter DATA_RETENTION_TIME_IN_DAYS for the target database to this value. If not given, use the setting on the source database
        include_internal_stages: bool - if True, clone internal stages of the source database to the target database (default: False)
    """
    log.info(
        f"CREATE database [ '{target_database_name}' ] as CLONE of [ '{source_database_name}' ]"
    )

    _check_snowclient_database(snow_client)

    if source_database_name.lower() == target_database_name.lower():
        raise ValueError(
            "source_database_name and target_database_name can not be identical."
        )

    log.info(
        f"CREATE database [ '{target_database_name}' ] AS clone [ '{source_database_name}' ]",
        db=target_database_name,
        status=LogStatus.PENDING,
    )
    if include_internal_stages:
        iis_statement = " INCLUDE INTERNAL STAGES "
    else:
        iis_statement = ""
    if replace_if_exists:
        statement = f"CREATE OR REPLACE DATABASE {target_database_name} CLONE {source_database_name}{iis_statement};"
    else:
        statement = (
            f"CREATE DATABASE {target_database_name} CLONE {source_database_name}{iis_statement};"
        )
    snow_client.execute_statement(statement)
    if db_retention_time_in_days is not None:
        set_database_retention_time(
            target_database_name, db_retention_time_in_days, snow_client
        )


def copy_database_grants(
    source_database_name: str, target_database_name: str, snow_client: SnowClient
) -> None:
    """
        Copy grants on database level from source db to target db.
    Args:
        source_database_name: str - name of the database from which grants are copied
        target_database_name: str - name of the database to which grants are copied
        snow_client: SnowClient - client to connect to snowflake account
    """
    _check_snowclient_database(snow_client)

    log.info(
        f"COPY grants FROM database [ '{target_database_name}' ] TO database [ '{source_database_name}' ]",
        db=target_database_name,
        status=LogStatus.PENDING,
    )
    query = f"SHOW GRANTS ON DATABASE {source_database_name};"
    source_grants = snow_client.execute_query(query)
    for grant in source_grants:
        grant_option = (
            "WITH GRANT OPTION" if grant["grant_option"].casefold() == "true" else ""
        )
        statement = f"GRANT {grant['privilege']} ON DATABASE {target_database_name} TO {grant['granted_to']} {grant['grantee_name']} {grant_option};"
        snow_client.execute_statement(statement)


def swap_databases(
    database1_name: str, database2_name: str, snow_client: SnowClient
) -> None:
    """
        Swap two databases (rename both to the other name in a single transaction).
    Args:
        database1_name: str - name of the first database to be swapped
        database2_name: str - name of the second database to be swapped
        snow_client: SnowClient - client to connect to snowflake account
    """
    _check_snowclient_database(snow_client)

    log.info(
        f"SWAP database [ '{database1_name}' ] WITH database [ '{database2_name}' ]",
        db=database1_name,
        status=LogStatus.PENDING,
    )
    statement = f"ALTER DATABASE {database1_name} SWAP WITH {database2_name};"
    snow_client.execute_statement(statement)


def drop_tables_in_schema(
    database_name: str,
    schema_name: str,
    snow_client: SnowClient,
    whitelist: List[str] = None,
) -> None:
    """
        Drop all tables in a schema.
    Args:
        database_name: str - name of the database
        schema_name: str - name of the schema
        snow_client: SnowClient - client to connect to snowflake account
        whitelist: List[str] - list of table names which will not be dropped
    """
    if whitelist is None:
        whitelist = []
    query = f"SHOW TABLES IN SCHEMA {database_name}.{schema_name};"
    tables = snow_client.execute_query(query)
    tables_filtered = [
        t["name"]
        for t in tables
        if t["name"].casefold() not in [w.casefold() for w in whitelist]
    ]
    log.info(
        f"DROP [ '{len(tables_filtered)}' ] table(s) IN schema [ '{database_name}.{schema_name}' ]",
        db=database_name,
        status=LogStatus.PENDING,
    )
    for table in tables_filtered:
        statement = f"DROP TABLE {database_name}.{schema_name}.{table};"
        snow_client.execute_statement(statement)


def get_schema_names(
    database_name: str,
    schema_list: Dict[str, List[str]],
    snow_client: SnowClient,
    snow_edition: str = "Enterprise",
) -> Tuple[List[str], List[str]]:
    """
        Get a list of schemas on the database. Filter by schema_list (as whitelist or blacklist).
    Args:
        database_name: str - name of the database
        schema_list: Dict[str, List[str]]) - names of the schemas as given in config file (whitelist or blacklist)
        snow_client: SnowClient - client to connect to snowflake account
        snow_edition: str - The edition of your Snowflake account. Defaults to "Enterprise".
    Returns:
        (List[str], List[str]) - list of schema names:
            first entry: list that matched the filter in schema_list
            second entry: list that did not match the filter in schema_list
    """
    _check_snowclient_database(snow_client)

    metadata_service = MetadataService(snow_client, snow_edition)
    source_schema_list = metadata_service.get_object_count_per_schema(database_name)

    if "whitelist" in schema_list:
        schemas_whitelist = [s.casefold() for s in schema_list["whitelist"]]
        matches = [
            s
            for s in [ss["SCHEMA_NAME"].casefold() for ss in source_schema_list]
            if s in schemas_whitelist
        ]
        removed = [
            s
            for s in [ss["SCHEMA_NAME"].casefold() for ss in source_schema_list]
            if s not in schemas_whitelist
        ]
        return matches, removed
    elif "blacklist" in schema_list:
        schemas_blacklist = [s.casefold() for s in schema_list["blacklist"]]
        matches = [
            s
            for s in [ss["SCHEMA_NAME"].casefold() for ss in source_schema_list]
            if s not in schemas_blacklist
        ]
        removed = [
            s
            for s in [ss["SCHEMA_NAME"].casefold() for ss in source_schema_list]
            if s in schemas_blacklist
        ]
        return matches, removed
    else:
        raise EnvironmentError(
            "MALFORMED config value [ 'schema_list' ] (contains neither blacklist nor whitelist)"
        )


def clone_database_by_schemas(
    source_database_name: str,
    target_database_name: str,
    schema_list: Dict[str, List[str]],
    snow_client: SnowClient,
    replace_if_exists: bool = False,
    parallel_threads=1,
    create_filtered_schemas=False,
    with_managed_access=False,
    db_retention_time_in_days: int = None,
) -> None:
    """
        Clone a database schema by schema, using a list of schemas.
    Args:
        source_database_name: str - name of the database
        target_database_name: str - name of the database
        schema_list: Dict[str, List[str]]) - names of the schemas to clone (whitelist or blacklist)
        snow_client: SnowClient - client to connect to snowflake account
        replace_if_exists: bool - replace target database if it already exists
        parallel_threads: int - number of parallel threads while cloning
        create_filtered_schemas: bool - create schemas (empty) which are on source database but are filtered through schema_list
        with_managed_access: bool - set WITH MANAGED ACCESS for each (cloned or created empty) schema
        db_retention_time_in_days: int - if this value is given, set the parameter DATA_RETENTION_TIME_IN_DAYS for the target database to this value. If not given, use the setting on the source database
    """
    log.info(
        f"CREATE database [ '{target_database_name}' ] as CLONE of [ '{source_database_name}' ] (cloning each schema individually)"
    )

    _check_snowclient_database(snow_client)

    if source_database_name.lower() == target_database_name.lower():
        raise ValueError(
            "source_database_name and target_database_name can not be identical."
        )

    schemas_to_clone, schemas_to_create_empty = get_schema_names(
        source_database_name, schema_list, snow_client
    )

    create_database(
        database_name=target_database_name,
        snow_client=snow_client,
        replace_if_exists=replace_if_exists,
        drop_schema_public=True,
        db_retention_time_in_days=db_retention_time_in_days,
    )

    statements = []
    if with_managed_access:
        managed_access = " WITH MANAGED ACCESS"
    else:
        managed_access = ""

    log.info(
        f"CLONE [ '{len(schemas_to_clone)}' ] schema(s) FROM database [ '{source_database_name}' ] TO database [ '{target_database_name}' ]",
        db=target_database_name,
        status=LogStatus.PENDING,
    )
    for schema in schemas_to_clone:
        s = f"CREATE SCHEMA {target_database_name}.{schema} CLONE {source_database_name}.{schema}{managed_access};"
        statements.append(s)

    if create_filtered_schemas:
        for schema in schemas_to_create_empty:
            statements.append(
                f"CREATE SCHEMA {target_database_name}.{schema}{managed_access};"
            )

    with ThreadPoolExecutor(max_workers=parallel_threads) as pool:
        for __ in pool.map(snow_client.execute_statement, statements):
            pass  # need to iterate over results from execute_and_log(), otherwise exceptions in execute_and_log() will not be raised in main thread

    unset_schemata_retention_time(target_database_name, snow_client)


def clone_database_by_objects(
    source_database_name: str,
    target_database_name: str,
    schema_list: Dict[str, List[str]],
    snow_client: SnowClient,
    replace_if_exists: bool = False,
    parallel_threads=1,
    create_filtered_schemas=False,
    snow_edition: str = "Enterprise",
    db_retention_time_in_days: int = None,
) -> None:
    """
        Clone a database object by object (if possible), using a list of schemas.
        For each schema: If schema contains only tables, clone each table; if schema contains any other object type, clone full schema.
    Args:
        source_database_name: str - name of the database
        target_database_name: str - name of the database
        schema_list: Dict[str, List[str]]) - names of the schemas to clone (whitelist or blacklist)
        snow_client: SnowClient - client to connect to snowflake account
        replace_if_exists: bool - replace target database if it already exists
        parallel_threads: int - number of parallel threads while cloning
        create_filtered_schemas: bool - create schemas (empty) which are on source database but are filtered through schema_list
        snow_edition: str - The edition of your Snowflake account. Defaults to "Enterprise".
        db_retention_time_in_days: int - if this value is given, set the parameter DATA_RETENTION_TIME_IN_DAYS for the target database to this value. If not given, use the setting on the source database
    """
    log.info(
        f"CREATE database [ '{target_database_name}' ] as CLONE of [ '{source_database_name}' ] (cloning each table individually)"
    )

    _check_snowclient_database(snow_client)

    if source_database_name.lower() == target_database_name.lower():
        raise ValueError(
            "source_database_name and target_database_name can not be identical."
        )

    schemas_to_clone, schemas_to_create_empty = get_schema_names(
        source_database_name, schema_list, snow_client
    )

    metadata_service = MetadataService(snow_client, snow_edition)
    object_details = metadata_service.get_all_objects_filtered(
        source_database_name, schemas_to_clone
    )
    object_details_by_schema = {
        s: [o for o in object_details if o["SCHEMA_NAME"].lower() == s.lower()]
        for s in schemas_to_clone
    }

    statements_sequential = (
        []
    )  # list of statements to be executed sequentially before any other statements
    statements_parallel_schemas = (
        []
    )  # cloning full schemas takes a long time --> start with schemas
    statements_parallel_tables = (
        []
    )  # cloning a single tables is fast --> end with tables --> there should never be unused threads

    create_database(
        database_name=target_database_name,
        snow_client=snow_client,
        replace_if_exists=replace_if_exists,
        drop_schema_public=True,
        db_retention_time_in_days=db_retention_time_in_days,
    )

    if create_filtered_schemas:
        for schema in schemas_to_create_empty:
            statements_sequential.append(
                f"CREATE SCHEMA {target_database_name}.{schema};"
            )

    schemas_to_clone_objectwise = []
    schemas_to_clone_schemawise = []
    for schema, objects in sorted(
        object_details_by_schema.items(), key=lambda x: len(x[1]), reverse=True
    ):  # order by number of objects in schema (desc)
        tables = [
            b
            for b in objects
            if (
                b["SCHEMA_NAME"].lower() == schema.lower()
                and b["OBJECT_TYPE"] == "BASE TABLE"
            )
        ]
        if len(objects) == len(tables):
            schemas_to_clone_objectwise.append(schema)
            log.debug(f"SCHEMA [ '{schema}' ] contains TABLES only")
            statements_sequential.append(
                f"CREATE SCHEMA {target_database_name}.{schema};"
            )
            for table in tables:
                statements_parallel_tables.append(
                    f"CREATE TABLE {target_database_name}.{table['SCHEMA_NAME']}.{table['OBJECT_NAME']} CLONE {source_database_name}.{table['SCHEMA_NAME']}.{table['OBJECT_NAME']};"
                )
        else:
            schemas_to_clone_schemawise.append(schema)
            log.debug(f"SCHEMA [ '{schema}' ] contains OTHER OBJECTS than tables")
            statements_parallel_schemas.append(
                f"CREATE SCHEMA {target_database_name}.{schema} CLONE {source_database_name}.{schema};"
            )

    log.info(
        f"CLONE FROM database [ '{source_database_name}' ] TO database [ '{target_database_name}' ]. Summary:\n"
        + f"    Clone on schema level: {', '.join(schemas_to_clone_schemawise) if len(schemas_to_clone_schemawise)>0 else '(none)'}\n"
        + f"    Clone on object level: {', '.join(schemas_to_clone_objectwise) if len(schemas_to_clone_objectwise)>0 else '(none)'}\n"
        + f"    Create empty: {', '.join(schemas_to_create_empty) if (len(schemas_to_create_empty)>0 and create_filtered_schemas) else '(none)'}",
        db=target_database_name,
        status=LogStatus.PENDING,
    )

    snow_client.execute_statement(statements_sequential)

    with ThreadPoolExecutor(max_workers=parallel_threads) as pool:
        for __ in pool.map(
            snow_client.execute_statement,
            statements_parallel_schemas + statements_parallel_tables,
        ):
            pass  # need to iterate over results in order to get exception from pool

    if db_retention_time_in_days is not None:
        unset_schemata_retention_time(target_database_name, snow_client)

    log.debug(
        f"FINISH CLONE FROM database [ '{source_database_name}' ] TO database [ '{target_database_name}' ]",
        db=target_database_name,
        status=LogStatus.SUCCESS,
    )


def create_clone_by_ordered_action_list(
    source_database_name: str,
    target_database_name: str,
    ordered_action_list: List[List[List[DbObjectAction]]],
    snow_client: SnowClient,
    replace_if_exists: bool = False,
    db_retention_time_in_days: int = None,
    policy_assignments_role: str = '',
) -> None:
    """
        Given a list of ordered object actions, clone/create only these objects from one database to a new database.
        - TABLES are cloned
        - other objects: GET_DDL from source, CREATE on target
    Args:
        source_database_name: str - name of the database
        target_database_name: str - name of the database
        ordered_action_list: List[List[List[DbObjectAction]]] - ordered list of object actions. will be used to determine which objects to deploy in which order
        snow_client: SnowClient - client to connect to snowflake account
        replace_if_exists: bool - replace target database if it already exists
        db_retention_time_in_days: int - if this value is given, set the parameter DATA_RETENTION_TIME_IN_DAYS for the target database to this value. If not given, use the setting on the source database
    """
    _check_snowclient_database(snow_client)

    if not source_database_name:
        raise ValueError("source_database_name can not be empty or None.")

    if source_database_name.lower() == target_database_name.lower():
        raise ValueError(
            "source_database_name and target_database_name can not be identical."
        )

    log.info(
        f"CREATE database [ '{target_database_name}' ] as CLONE of [ '{source_database_name}' ] (using action list)"
    )

    create_database(
        database_name=target_database_name,
        snow_client=snow_client,
        replace_if_exists=replace_if_exists,
        drop_schema_public=True,
        db_retention_time_in_days=db_retention_time_in_days,
    )

    statements = []

    for action_block in ordered_action_list:
        statement_block = []
        actions = [
            a
            for a in dict_and_list_util.flatten(action_block)
            if a.action in (DbActionType.ADD, DbActionType.ALTER)
        ]
        for action in actions:
            if action.object_type == DbObjectType.SCHEMA:
                statement_block.append(
                    f"CREATE SCHEMA {target_database_name}.{action.name};"
                )
            else:
                object_exists, object_is_transient = _test_object_exists(
                    action.object_type,
                    source_database_name,
                    action.schema,
                    action.name,
                    snow_client,
                )
                if object_exists:
                    transient = ''
                    if object_is_transient:
                        transient = 'TRANSIENT'

                    if action.object_type == DbObjectType.TABLE:
                        statement_block.append(
                            f"CREATE {transient} TABLE {target_database_name}.{action.full_name} CLONE {source_database_name}.{action.full_name};"
                        )

                    elif action.object_type == DbObjectType.DYNAMICTABLE:
                        #TODO fetching "transient" from _test_object_exists does not work for Dynamic Tables yet
                        statement_block.append(
                            f"CREATE {transient} DYNAMIC TABLE {target_database_name}.{action.full_name} CLONE {source_database_name}.{action.full_name};"
                        )
                    else:
                        ddl = _get_object_ddl(
                            action.object_type,
                            source_database_name,
                            action.full_name,
                            snow_client,
                            policy_assignments_role,
                        )
                        if policy_assignments_role and action.object_type not in (DbObjectType.ROWACCESSPOLICY, DbObjectType.MASKINGPOLICY):
                            statement_block.append(f'USE SECONDARY ROLES {policy_assignments_role};')
                            statement_block.append(
                                re.sub(
                                    rf'(?<!ROW ACCESS POLICY )(?<!MASKING POLICY ){source_database_name}',
                                    target_database_name,
                                    ddl,
                                    flags=re.IGNORECASE,
                                )
                            )
                            statement_block.append(f"USE SECONDARY ROLES NONE;")
                        else:
                            statement_block.append(
                                re.sub(
                                    source_database_name,
                                    target_database_name,
                                    ddl,
                                    flags=re.IGNORECASE,
                                )
                            )
        statements.append(statement_block)
    snow_client.execute_statement(dict_and_list_util.flatten(statements))
    log.debug(
        f"FINISH CLONE FROM database [ '{source_database_name}' ] TO database [ '{target_database_name}' ]",
        db=target_database_name,
        status=LogStatus.SUCCESS,
    )


def _test_object_exists(
    object_type: DbObjectType,
    database: str,
    object_schema: str,
    object_name: str,
    snow_client: SnowClient,
) -> Tuple[bool, bool]:
    """
    Test if a given object exists on the database.
    Additionally, check wether the object is transient.
    """
    object_is_transient = False
    query = f"SHOW {DbObjectType.get_object_type_for_show(object_type)} LIKE '{object_name}' IN SCHEMA {database}.{object_schema};"
    query_result = snow_client.execute_query(query)

    object_exists = len(query_result) >= 1

    if len(query_result) == 1 and "kind" in query_result[0]:
        if query_result[0]["kind"] == 'TRANSIENT':
            object_is_transient = True

    return object_exists, object_is_transient


def _get_object_ddl(
    object_type: DbObjectType,
    database: str,
    full_object_name: str,
    snow_client: SnowClient,
    policy_assignments_role: str = '',
) -> str:
    """
    Get a the DDL for a given object
    """
    
    query = f"SELECT GET_DDL('{DbObjectType.get_object_type_for_get_ddl(object_type)}', '{database}.{full_object_name}', TRUE) AS DDL"

    if policy_assignments_role:
        snow_client.execute_statement(f'USE SECONDARY ROLES {policy_assignments_role};')

    ddl = snow_client.execute_query(query)[0]["DDL"]

    if policy_assignments_role:
        snow_client.execute_statement(f"USE SECONDARY ROLES NONE;")

    return ddl


def refresh_database(
    source_database_name: str,
    target_database_name: str,
    object_list: List[str],
    snow_client: SnowClient,
    old_object_suffix: str,
    continue_on_sql_error: bool = False,
    unset_db_retention_time: bool = False,
) -> None:
    """
        Refresh a database by cloning new schemas and tables into the database from some other database. Existing schemas and tables in the target database will be renamed.
    Args:
        source_database_name: str - name of the database
        target_database_name: str - name of the database
        object: List[str] - names of the objects to clone, can contain both schemas (without database identifier, e.g. "DBP_DATA") or tables (must include schema name, e.g. "DBP_DATA.MY_TABLE")
        snow_client: SnowClient - client to connect to snowflake account
        old_object_suffix: str - string to append to old objects, e.g. "_BACKUP_20201020_135854"
        continue_on_sql_error: bool = False - continue execution if errors occur during statement execution
        unset_db_retention_time: bool = False - unset the parameter DATA_RETENTION_TIME_IN_DAYS on cloned schemas
    """
    schema_list = []
    table_list = []
    for obj in object_list:
        if "." in obj:
            table_list.append(obj)
        else:
            schema_list.append(obj)
    refresh_tables(
        source_database_name,
        target_database_name,
        table_list,
        snow_client,
        old_object_suffix,
        continue_on_sql_error,
    )
    refresh_schemas(
        source_database_name,
        target_database_name,
        schema_list,
        snow_client,
        old_object_suffix,
        continue_on_sql_error,
        unset_db_retention_time=unset_db_retention_time,
    )


def refresh_schemas(
    source_database_name: str,
    target_database_name: str,
    schema_list: List[str],
    snow_client: SnowClient,
    old_schema_suffix: str,
    continue_on_sql_error: bool = False,
    unset_db_retention_time: bool = False,
) -> None:
    """
        Refresh schemas in a database from another database, using a list of schemas.
    Args:
        source_database_name: str - name of the database
        target_database_name: str - name of the database
        schema_list: List[str] - names of the schemas to clone
        snow_client: SnowClient - client to connect to snowflake account
        old_schema_suffix: str - string to append to old schemas, e.g. "_BACKUP_20201020_135854"
        continue_on_sql_error: bool = False - continue execution if errors occur during statement execution
        unset_db_retention_time: bool = False - unset the parameter DATA_RETENTION_TIME_IN_DAYS on cloned schemas
    """
    if source_database_name.lower() == target_database_name.lower():
        raise ValueError(
            "source_database_name and target_database_name can not be identical."
        )

    if len(old_schema_suffix) < 3:
        raise ValueError("Length of old_schema_suffix is too small")

    old_schema_suffix_clean = "".join(
        [c if c.isalnum() else "_" for c in old_schema_suffix]
    )

    if not check_input_list_valid(schema_list):
        raise ValueError("Schema list contains invalid object names")

    _check_snowclient_database(snow_client)

    snow_client.execute_statement(
        "ALTER SESSION SET QUOTED_IDENTIFIERS_IGNORE_CASE=True"
    )

    log.info(
        f"CLONE [ '{len(schema_list)}' ] schema(s) FROM database [ '{source_database_name}' ] TO database [ '{target_database_name}' ] rename OLD [ '{old_schema_suffix_clean}' ]",
        db=target_database_name,
        status=LogStatus.PENDING,
    )
    for schema in schema_list:
        schema = schema.replace('"', "")
        try:
            snow_client.execute_statement(
                f'ALTER SCHEMA IF EXISTS "{target_database_name}"."{schema}" RENAME TO "{target_database_name}"."{schema}{old_schema_suffix_clean}";'
            )
            snow_client.execute_statement(
                f'CREATE SCHEMA "{target_database_name}"."{schema}" CLONE "{source_database_name}"."{schema}";'
            )
            if unset_db_retention_time:
                snow_client.execute_statement(
                    f'ALTER SCHEMA "{target_database_name}"."{schema}" UNSET DATA_RETENTION_TIME_IN_DAYS;'
                )
        except Exception as err:
            if continue_on_sql_error and ("SQL compilation error" in err.msg):
                log.warning(
                    f'SQL compilation error. Skip statements for "{schema}" and continue'
                )
            else:
                raise err


def refresh_tables(
    source_database_name: str,
    target_database_name: str,
    table_list: List[str],
    snow_client: SnowClient,
    old_table_suffix: str = "",
    continue_on_sql_error: bool = False,
    is_transient_tables: bool = False,
    overwrite_existing: bool = False,
) -> None:
    """
        Refresh schemas in a database from another database, using a list of schemas.
    Args:
        source_database_name: str - name of the database
        target_database_name: str - name of the database
        table_list: List[str] - names of the tables to clone
        snow_client: SnowClient - client to connect to snowflake account
        old_table_suffix: str - string to append to old tables, e.g. "_BACKUP_20201020_135854"
        continue_on_sql_error: bool = False - continue execution if errors occur during statement execution
        is_transient_tables: bool = False - use to clone transient tables
        overwrite_existing: bool = False - overwrite existing tables instead of renameing them
    """
    if source_database_name.lower() == target_database_name.lower():
        raise ValueError(
            "source_database_name and target_database_name can not be identical."
        )

    if len(old_table_suffix) < 3:
        raise ValueError("Length of old_table_suffix is too small")

    old_table_suffix_clean = "".join(
        [c if c.isalnum() else "_" for c in old_table_suffix]
    )

    if not check_input_list_valid(table_list):
        raise ValueError("Table list contains invalid object names")

    _check_snowclient_database(snow_client)

    snow_client.execute_statement(
        "ALTER SESSION SET QUOTED_IDENTIFIERS_IGNORE_CASE=True"
    )

    if overwrite_existing:
        log_string_old = "replace OLD"
    else:
        log_string_old = f"rename OLD [ '{old_table_suffix_clean}' ]"
    log.info(
        f"CLONE [ '{len(table_list)}' ] {'transient ' if is_transient_tables else ''}tables(s) FROM database [ '{source_database_name}' ] TO database [ '{target_database_name}' ] {log_string_old}. List of tables: [ '{str(table_list)}' ]",
        db=target_database_name,
        status=LogStatus.PENDING,
    )
    for table in table_list:
        table = table.replace('"', "").replace(".", '"."')
        try:
            if not overwrite_existing:
                snow_client.execute_statement(
                    f'ALTER TABLE IF EXISTS "{target_database_name}"."{table}" RENAME TO "{target_database_name}"."{table}{old_table_suffix_clean}";'
                )
            snow_client.execute_statement(
                f'CREATE {"OR REPLACE" if overwrite_existing else ""} {"TRANSIENT" if is_transient_tables else ""} TABLE "{target_database_name}"."{table}" CLONE "{source_database_name}"."{table}";'
            )
        except Exception as err:
            if continue_on_sql_error and ("SQL compilation error" in err.msg):
                log.warning(
                    f'SQL compilation error. Skip statements for "{table}" and continue'
                )
            else:
                raise err


def refresh_by_json(
    source_database_name: str,
    target_database_name: str,
    json_file: str,
    snow_client: SnowClient,
    old_table_suffix: str = "",
    overwrite_existing: bool = False,
    ignore_metadata_differences: bool = True,
    continue_on_sql_error: bool = False,
    transient_tables: bool = False,
    ignore_retention_time: bool = True,
    ignore_comment: bool = True,
):
    """
        Refresh tables in target database by cloning them from the source database. Load list of schemas and tables from json file.
        Skip tables as given in the json.
        Json must validate against resources/json-schemas/refresh-clone.schema.json
        Json example: { "schemasToClone": { "DATA1": { "tablesToSkip": ["TABLE1", "TABLE2" ] }, "DATA2": { "tablesToSkip": [ "TABLE1", "TABLE2" ] } } }
        Json example: { "schemasToClone": { "DATA1": { "tablesToInclude": ["TABLE1", "TABLE2" ] }, "DATA2": { "tablesToInclude": [ "TABLE1", "TABLE2" ] } } }

    Args:
        source_database_name: str - Name of the source database,
        target_database_name: str - Name of the target database,
        json_file: str - Path of the json file which contains the configuration,
        snow_client: SnowClient - Snowflake connection,
        old_table_suffix: str = '' - String to be appended to renamed tables,
        overwrite_existing: bool = False - Flag wether to overwrite existing tables or to rename them,
        ignore_metadata_differences: bool = True - If tables exist on both target and source, copy them, even if their metadata is not the same (excepeptions for retention time and comments can be set in other parameters)
        continue_on_sql_error: bool = False - Flag to continue execution on sql error
        transient_tables: bool = False - Flag to clone transient tables instead of base tables
        ignore_retention_time: bool = True - If ignore_metadata_differences is true, do not compare retention time metadata
        ignore_comment: bool = True - If ignore_metadata_differences is true, do not compare table comment metadata
    """
    json_schema_file = file_util.get_path(
        ["resources", "json-schemas", "refresh-clone.schema.json"]
    )
    if not file_util.validate_json(json_schema_file, json_file):
        raise EnvironmentError(
            f"Configuration JSON {json_file} failed validation against schema {json_schema_file}"
        )
    all_settings = file_util.load_json(json_file)

    if not ignore_metadata_differences:
        metadata_source = _get_db_metadata(
            source_database_name, all_settings["schemasToClone"].keys(), snow_client
        )
        metadata_target = _get_db_metadata(
            target_database_name, all_settings["schemasToClone"].keys(), snow_client
        )

    word = "TRANSIENT TABLES" if transient_tables else "TABLES"
    log.info(
        f"GET list of {word} to clone FROM [ '{source_database_name}' ] and FILTER by [ '{json_file}' ]"
    )
    all_tables = []
    for schema_name, schema_settings in all_settings["schemasToClone"].items():
        tables = _get_table_names_in_schema(
            source_database_name,
            schema_name,
            snow_client,
            is_transient="YES" if transient_tables else "NO",
        )
        if "tablesToSkip" in schema_settings:
            all_tables.extend(
                [
                    f"{schema_name}.{t}"
                    for t in tables
                    if t.lower()
                    not in [tt.lower() for tt in schema_settings["tablesToSkip"]]
                ]
            )
        elif "tablesToInclude" in schema_settings:
            all_tables.extend(
                [
                    f"{schema_name}.{t}"
                    for t in tables
                    if t.lower()
                    in [tt.lower() for tt in schema_settings["tablesToInclude"]]
                ]
            )
        else:
            raise ValueError(f"Invalid configuration for schema [ '{schema_name}' ]")

    if not ignore_metadata_differences:
        all_tables = _filter_table_list_by_metadata_differences(
            metadata_source,
            metadata_target,
            all_tables,
            ignore_retention_time,
            ignore_comment,
        )

    refresh_tables(
        source_database_name=source_database_name,
        target_database_name=target_database_name,
        table_list=all_tables,
        snow_client=snow_client,
        old_table_suffix=old_table_suffix,
        continue_on_sql_error=continue_on_sql_error,
        is_transient_tables=transient_tables,
        overwrite_existing=overwrite_existing,
    )

    return all_tables


def resume_reclustering_in_schemas(
    database_name: str, schema_list: List[str], snow_client: SnowClient
) -> None:
    """
        Given a list of schemas, resume reclustering for all tables with a clustering key where reclustering is currently suspended.
    Args:
        database_name: str - name of the database
        schema_list: List[str] - names of the schemas in which to resume reclustering on tables
        snow_client: SnowClient - client to connect to snowflake account
    """
    if not check_input_list_valid(schema_list):
        raise ValueError("Schema list contains invalid object names")

    _check_snowclient_database(snow_client)

    snow_client.execute_statement(
        "ALTER SESSION SET QUOTED_IDENTIFIERS_IGNORE_CASE=True"
    )

    schema_string = ", ".join([f"'{s.upper()}'" for s in schema_list])

    log.info(
        f"GET TABLES with SUSPENDED CLUSTERING in schemas [ '{schema_string}' ] in database [ '{database_name}' ]"
    )
    query = f"""
        SELECT
            T.TABLE_SCHEMA,
            T.TABLE_NAME
        FROM {database_name}.INFORMATION_SCHEMA.TABLES T
        WHERE 1=1
            AND T.TABLE_TYPE IN ('BASE TABLE')
            AND T.TABLE_SCHEMA  IN ({schema_string})
            AND T.CLUSTERING_KEY IS NOT NULL
            AND AUTO_CLUSTERING_ON = 'NO'
        ORDER BY
            T.TABLE_SCHEMA,
            T.TABLE_NAME
        ;
    """
    table_list = snow_client.execute_query(query)
    table_name_list = [f"{t['TABLE_SCHEMA']}.{t['TABLE_NAME']}" for t in table_list]

    log.info(
        f"RESUMING RECLUSTER for [ '{len(table_name_list)}' ] tables in database [ '{database_name}' ]. Table list: [ '{', '.join(table_name_list)}' ]"
    )

    for table_name in table_name_list:
        snow_client.execute_statement(
            f"ALTER TABLE {database_name}.{table_name} RESUME RECLUSTER;"
        )


def _filter_table_list_by_metadata_differences(
    metadata1: MetadataService,
    metadata2: MetadataService,
    table_list: List[str],
    ignore_retention_time: bool = False,
    ignore_comment: bool = False,
) -> List[str]:
    """
        Given a list of tables, filter out all tables which exist on both databases and do not have the same metadata on both databases.

    Args:
        metadata1: MetadataService - Metadata information on database 1
        metadata2: MetadataService - Metadata information on database 2
        table_list: List[str] - List of tables to be filtered
        ignore_retention_time: bool = False - When comapring metadata, ignore retention time (both on schema and on table)
        ignore_comment: bool = False - When comapring metadata, ignore comments on the table

    Returns
        List[str] - filtered table list
    """
    table1_metadata_filtered = [
        t
        for t in metadata1.tables
        if t.full_name.upper() in [a.upper() for a in table_list]
    ]
    table2_metadata_filtered = [
        t
        for t in metadata2.tables
        if t.full_name.upper() in [a.upper() for a in table_list]
    ]

    if ignore_retention_time:
        for t in table1_metadata_filtered:
            t.retention_time = 1
            t.schema_retention_time = 1
        for t in table2_metadata_filtered:
            t.retention_time = 1
            t.schema_retention_time = 1

    if ignore_comment:
        for t in table1_metadata_filtered:
            t.comment = ""
        for t in table2_metadata_filtered:
            t.comment = ""

    tables_to_remove = []
    for t1 in table1_metadata_filtered:
        for t2 in table2_metadata_filtered:
            if t1.full_name.upper() == t2.full_name.upper():
                if not (t1 == t2):
                    tables_to_remove.append(t1.full_name.upper())

    log.info(
        f"SKIP [ '{len(tables_to_remove)}' ] TABLES with mismatched metadata: [ '{tables_to_remove}' ]"
    )

    return [
        t for t in table_list if t.lower() not in [a.lower() for a in tables_to_remove]
    ]


def _get_db_metadata(
    database_name: str,
    schema_list: List[str],
    snow_client: SnowClient,
    snow_edition: str = "Enterprise",
) -> MetadataService:
    """
        Get metadata from a database for a given database.
        Snow Client does not need to be scoped to database, a copy will be created pointing to correct database.

    Args:
        database_name: str - Name of the database
        schema_list: List[str] - List of schemas for which to get metadata
        snow_client: SnowClient - Snowflake connection (can be scoped to database or unscoped)
        snow_edition: str - The edition of your Snowflake account. Defaults to "Enterprise".

    Returns:
        metadata: MetadataService
    """
    snow_client_db_config = copy.deepcopy(snow_client._config)
    snow_client_db_config.database = database_name
    snow_client_db = SnowClient(snow_client_db_config)
    metadata_service = MetadataService(snow_client_db, snow_edition)
    metadata_service.get_all_metadata({"whitelist": schema_list})
    return metadata_service


def _get_table_names_in_schema(
    database_name, schema_name, snow_client, is_transient="NO"
):
    """
    Return a list of all tables (base tables only, no views) in a given schema.
    """
    query = f"SELECT TABLE_NAME FROM {database_name}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{schema_name}' AND TABLE_TYPE='BASE TABLE' AND IS_TRANSIENT='{is_transient}';"
    result = snow_client.execute_query(query)
    return [s["TABLE_NAME"] for s in result]


def get_external_stages(database_name: str, snow_client: SnowClient):
    """
        Lists all external stages in database.
    Args:
        database_name: str - name of the database
        snow_client: SnowClient - client to connect to snowflake account
    """
    stages = snow_client.execute_query(f"SHOW STAGES IN DATABASE {database_name};")
    stages_filtered = [s for s in stages if s["type"] == "EXTERNAL"]
    return stages_filtered


def get_tasks(database_name: str, snow_client: SnowClient):
    """
        Lists all tasks in database.
    Args:
        database_name: str - name of the database
        snow_client: SnowClient - client to connect to snowflake account
    """
    tasks = snow_client.execute_query(f"SHOW TASKS IN DATABASE {database_name};")
    return tasks


def get_pipes(database_name: str, snow_client: SnowClient):
    """
        Lists all pipes in database.
    Args:
        database_name: str - name of the database
        snow_client: SnowClient - client to connect to snowflake account
    """
    pipes = snow_client.execute_query(f"SHOW PIPES IN DATABASE {database_name};")
    return pipes


def get_dynamic_tables(database_name: str, snow_client: SnowClient):
    """
        Lists all dynamic tables in a database.
    Args:
        database_name: str - name of the database
        snow_client: SnowClient - client to connect to snowflake account
    """
    dynamic_tables = snow_client.execute_query(f"SHOW DYNAMIC TABLES IN DATABASE {database_name};")
    return dynamic_tables

def get_warehouses(snow_client: SnowClient):
    """
        Lists all Snowflake warehouses.
    Args:
        snow_client: SnowClient - client to connect to snowflake account
    """
    warehouses = snow_client.execute_query(f"SHOW WAREHOUSES;")
    return warehouses


def alter_external_stages(
    database_name: str,
    target_env: str,
    regex_pattern: Dict,
    snow_client: SnowClient,
    schema_list: List[str] = None,
):
    r"""
        Alter storage integration and url of stages.
    Args:
        database_name: str - name of the database
        target_env: str - abbreviation for target environment, second group regex pattern should be mentioned, e.g. 'dev\g<x>'
        regex_pattern: Dict - dict with regex patterns for different stage properties, e.g. {
                'STORAGE_INTEGRATION': '(?P<env>DEV|QS|PROD)(?P<x>$)',
                'URL': '(?P<env>dev|qs|prod)(?P<x>\.blob\.core)'
            }
        snow_client: SnowClient - client to connect to snowflake account
        schema_list: List[str] (default None) - only alter stages in schemas given in this list, use all schemas if schema_list==None
    """
    #TODO Evaluation error-handling and cleanup of clone database on error. Note: See also other alter-functions with this comment.

    _check_snowclient_database(snow_client)

    stages = get_external_stages(database_name, snow_client)

    for stage in stages:
        if not (
            (schema_list is None)
            or (stage["schema_name"].lower() in [s.lower() for s in schema_list])
        ):
            log.debug(
                f'Skip alter stage {stage["schema_name"]}.{stage["name"]} (is not in schema list {schema_list})'
            )
            continue

        properties = snow_client.execute_query(
            f'DESCRIBE STAGE {database_name}.{stage["schema_name"]}."{stage["name"]}";'
        )

        for prop in properties:
            if prop["property"] == "STORAGE_INTEGRATION":
                storage_integration = re.sub(
                    regex_pattern["STORAGE_INTEGRATION"],
                    target_env,
                    prop["property_value"],
                    flags=re.IGNORECASE,
                )
            elif prop["property"] == "URL":
                storage_url = re.sub(
                    regex_pattern["URL"],
                    target_env.lower(),
                    prop["property_value"].replace('["', "").replace('"]', ""),
                    flags=re.IGNORECASE,
                )

        statement = f"""ALTER STAGE "{database_name}"."{stage["schema_name"]}"."{stage["name"]}" SET STORAGE_INTEGRATION = "{storage_integration}" URL = '{storage_url}';"""

        try:
            log.info(statement)
            snow_client.execute_statement(statement)
        except:
            log.error(f'Could not alter stage {stage["schema_name"]}.{stage["name"]}')


def alter_stages(
    snow_client: SnowClient,
    database_name: str,
    replace_instructions: Dict[str, Dict[str, str]],
    schema_list: List[str] = None,
    continue_on_error: bool = False,
) -> None:
    """
    Alter storage integration and url of stages.

    Args:
        snow_client: client to connect to snowflake account
        database_name:  name of the database
        replace_instructions: dict with regex patterns for different stage properties, e.g.
            {
                'storage_integration': {'pattern': '(dev|test|prod)$', 'repl': 'dev'},
                'url': {'pattern': '(dev|test|prod)$', 'repl': 'dev'},
            }
        schema_list: (default None) - only alter stages in schemas given in this list, use all schemas if schema_list==None
        continue_on_error: Continue if a stage can not be altered, else raise exception
    """
    #TODO Evaluation error-handling and cleanup of clone database on error. Note: See also other alter-functions with this comment.

    if schema_list is None:
        schema_list_string = ""
    else:
        schema_list_string = f"in schemas [ '{', '.join(schema_list)}' ] "
    log.info(
        f"ALTER STAGES in database [ '{database_name}' ] {schema_list_string}using INSTRUCTIONS {str(replace_instructions)}"
    )

    _check_snowclient_database(snow_client)
    _validate_replace_instructions(replace_instructions)

    stages = get_external_stages(database_name, snow_client)

    for stage in stages:
        if not (
            (schema_list is None)
            or (stage["schema_name"].lower() in [s.lower() for s in schema_list])
        ):
            log.debug(
                f"SKIP alter stage [ '{stage['schema_name']}.{stage['name']}' ] (is not in schema list  [ '{schema_list})' ]"
            )
            continue

        properties = snow_client.execute_query(
            f'DESCRIBE STAGE {database_name}.{stage["schema_name"]}."{stage["name"]}";'
        )

        alter_integration = ""
        alter_url = ""

        for prop in properties:
            if prop["property"] == "STORAGE_INTEGRATION":
                if "storage_integration" in replace_instructions:
                    storage_integration = re.sub(
                        replace_instructions["storage_integration"]["pattern"],
                        replace_instructions["storage_integration"]["repl"],
                        prop["property_value"],
                        flags=re.IGNORECASE,
                    )
                    alter_integration = (
                        f' STORAGE_INTEGRATION = "{storage_integration}"'
                    )
            elif prop["property"] == "URL":
                if "url" in replace_instructions:
                    storage_integration = re.sub(
                        replace_instructions["url"]["pattern"],
                        replace_instructions["url"]["repl"],
                        prop["property_value"].replace('["', "").replace('"]', ""),
                        flags=re.IGNORECASE,
                    )
                    alter_url = f" URL = '{storage_integration}'"

        all_alters = alter_integration + alter_url
        if all_alters != "":
            statement = f"""ALTER STAGE "{database_name}"."{stage["schema_name"]}"."{stage["name"]}" SET{all_alters};"""
            try:
                log.info(f"ALTER STAGE [ '{stage['schema_name']}.{stage['name']}' ]")
                snow_client.execute_statement(statement)
            except Exception as err:
                log.error(
                    f"Could not alter stage [ '{stage['schema_name']}.{stage['name']}' ]. Error message: {str(err)}"
                )
                if not continue_on_error:
                    raise err


def alter_tasks(
    snow_client: SnowClient,
    database_name: str,
    replace_instructions: Dict[str, Dict[str, str]],
    schema_list: List[str] = None,
    continue_on_error: bool = False,
):
    """
    Alter warehouse and definition of tasks.

    Args:
        snow_client: client to connect to snowflake account
        database_name:  name of the database
        replace_instructions: dict with regex patterns for different task properties, e.g.
            {
                'warehouse': {'pattern': '(dev|test|prod)$', 'repl': 'dev'},
                'definition': {'pattern': "(?P<before>'WH_[a-z0-9_]*)(DEV|TEST|PROD)(?P<after>')", 'repl': r'\g<before>DEV\g<after>'},
            }
        schema_list: (default None) - only alter tasks in schemas given in this list, use all schemas if schema_list==None
        continue_on_error: Continue if a task can not be altered, else raise exception
    """
    #TODO Evaluation error-handling and cleanup of clone database on error. Note: See also other alter-functions with this comment.

    if schema_list is None:
        schema_list_string = ""
    else:
        schema_list_string = f"in schemas [ '{', '.join(schema_list)}' ] "
    log.info(
        f"ALTER TASKS in database [ '{database_name}' ] {schema_list_string}using INSTRUCTIONS {str(replace_instructions)}"
    )

    _check_snowclient_database(snow_client)
    _validate_replace_instructions(replace_instructions)

    tasks = get_tasks(database_name, snow_client)

    for task in tasks:
        if not (
            (schema_list is None)
            or (task["schema_name"].lower() in [s.lower() for s in schema_list])
        ):
            log.debug(
                f"SKIP alter task [ '{task['schema_name']}.{task['name']}' ] (is not in schema list  [ '{schema_list})' ]"
            )
            continue

        if "warehouse" in replace_instructions:
            warehouse = re.sub(
                replace_instructions["warehouse"]["pattern"],
                replace_instructions["warehouse"]["repl"],
                task["warehouse"],
                flags=re.IGNORECASE,
            )
        if "definition" in replace_instructions:
            definition = re.sub(
                replace_instructions["definition"]["pattern"],
                replace_instructions["definition"]["repl"],
                task["definition"],
                flags=re.IGNORECASE,
            )

        statement = f"""ALTER TASK "{database_name}"."{task["schema_name"]}"."{task["name"]}" SET WAREHOUSE = "{warehouse}"; """
        statement = (
            statement
            + f"""ALTER TASK "{database_name}"."{task["schema_name"]}"."{task["name"]}" MODIFY AS {definition};"""
        )

        try:
            log.info(f"ALTER TASK [ '{task['schema_name']}.{task['name']}' ]")
            snow_client.execute_statement(statement)
        except Exception as err:
            log.error(
                f"Could not alter task [ '{task['schema_name']}.{task['name']}' ]. Error message: {str(err)}"
            )
            if not continue_on_error:
                raise err


def alter_dynamic_tables(
    database_name: str,
    target_env_abbreviation: str,
    regex_pattern_warehouse_source_env: Dict,
    snow_client: SnowClient,
    execute_statements: bool,
    schema_list: List[str] = None,
    continue_on_error: bool = False,
    regex_pattern_warehouse_target_env: str = '',
    secondary_role: str = ''
    
):
    r"""
        Alter dynamic tables refresh-warehouses.
    Args:
        database_name: str - name of the database
        target_env_abbreviation: str - abbreviation for target environment (with prefix group name and suffix group name), the e.g. r'\g<prefix>_D_\g<suffix>'
        regex_pattern_warehouse_source_env: str - regex pattern for the refresh warehouses, e.g. 
                r'(?P<prefix>WH_.*?)(?P<env>_P_)(?P<suffix>.*)$'
        snow_client: SnowClient - client to connect to snowflake account
        execute_statements: bool - Create and Execute "ALTER DYNAMIC TABLE"-Statements, else only validation of "check source warehouse follows regex pattern" and "check target warehouse exists" is done
        schema_list: List[str] (default None) - only alter dynamic tables in schemas given in this list, use all schemas if schema_list==None
        continue_on_error: bool - Continue if a Dynamic Table can not be altered, else raise exception
        regex_pattern_warehouse_target_env: str - optional - regex pattern for the refresh warehouses on the target environment (needs to be used when the warehouses on target could already be correctly defined e.g. when using refresh pipelines) , e.g. 
                r'(?P<prefix>WH_.*?)(?P<env>_D_)(?P<suffix>.*)$'
    """
    #TODO Evaluation error-handling and cleanup of clone database on error. Note: See also other alter-functions with this comment.

    _check_snowclient_database(snow_client)

    if secondary_role:
        snow_client.execute_statement(f"USE SECONDARY ROLES {secondary_role};")
    dynamic_tables = get_dynamic_tables(database_name, snow_client)
    if secondary_role:
        snow_client.execute_statement(f"USE SECONDARY ROLES NONE;")

    if not dynamic_tables:
        log.info(
            f"No Dynamic Tables found in database [ '{database_name}' ]."
        )
    else:

        if execute_statements:
            log.info(
                f"START alteration of Dynamic Tables refresh warehouses in database [ '{database_name}' ]."
            )
        else:
            log.info(
                f"START validation of Dynamic Tables refresh warehouses in database [ '{database_name}' ]."
            )

        warehouses = get_warehouses(snow_client)
        warehouses = [warehouse["name"].upper() for warehouse in warehouses]

        error_flag = False
        for dynamic_table in dynamic_tables:
            if not (
                (schema_list is None)
                or (dynamic_table["schema_name"].lower() in [s.lower() for s in schema_list])
            ):
                log.debug(
                    f'Skip alter dynamic table {dynamic_table["schema_name"]}.{dynamic_table["name"]} (is not in schema list {schema_list})'
                )
                continue

            dynamic_table_target_warehouse= re.sub(
                    regex_pattern_warehouse_source_env,
                    target_env_abbreviation,
                    dynamic_table["warehouse"],
                    flags=re.IGNORECASE,
                )

            # Check if target warehouse already matches with the desired target
            if regex_pattern_warehouse_target_env:
                target_match = re.match(
                    regex_pattern_warehouse_target_env,
                    dynamic_table["warehouse"],
                    flags=re.IGNORECASE,
                )
            else:
                target_match = None

            if target_match:
                log.info(f'The refresh warehouse {dynamic_table["warehouse"]} of the dynamic table {dynamic_table["database_name"]}.{dynamic_table["schema_name"]}.{dynamic_table["name"]} already matches with the desired target.')
            else:
                if not execute_statements:
                    # validation - check source warehouse follows regex pattern
                    if dynamic_table_target_warehouse == dynamic_table["warehouse"]:
                        error_message = f'The refresh warehouse {dynamic_table["warehouse"]} of the dynamic table {dynamic_table["database_name"]}.{dynamic_table["schema_name"]}.{dynamic_table["name"]} can not be altered -> no match was found for the regex pattern: {regex_pattern_warehouse_source_env}'
                        log.error(error_message)
                        error_flag= True
                        if not continue_on_error:        
                            raise Exception(error_message)

                    # validation - check target warehouse exists                   
                    if not dynamic_table_target_warehouse.upper() in warehouses:
                        error_message = f'The refresh warehouse {dynamic_table["warehouse"]} of the dynamic table {dynamic_table["database_name"]}.{dynamic_table["schema_name"]}.{dynamic_table["name"]} can not be altered -> target warehouse {dynamic_table_target_warehouse} does not exist or is not authorized!'
                        log.error(error_message)
                        error_flag= True
                        if not continue_on_error:  
                            raise Exception(error_message)
                if execute_statements:
                    statement = f"""ALTER DYNAMIC TABLE "{database_name}"."{dynamic_table["schema_name"]}"."{dynamic_table["name"]}" SET WAREHOUSE = {dynamic_table_target_warehouse};"""
                    try:
                        log.info(statement)
                        snow_client.execute_statement(statement)
                    except Exception as err:
                        log.error(f'Could not alter dynamic table {dynamic_table["database_name"]}.{dynamic_table["schema_name"]}.{dynamic_table["name"]}')
                        error_flag= True
                        if not continue_on_error:
                            raise err
                    
        if execute_statements and not error_flag:
            log.info(
                f"SUCCESS alteration of Dynamic Tables refresh warehouses in database [ '{database_name}' ]."
            )
        elif execute_statements and error_flag:
            log.info(
                f"FINISHED WITH ERRORS alteration of Dynamic Tables refresh warehouses in database [ '{database_name}' ]."
            )
        elif not execute_statements:
            log.info(
                f"SUCCESS validation of Dynamic Tables refresh warehouses in database [ '{database_name}' ]."
            )


def alter_policy_assignments(
    snow_client: SnowClient,
    objects: list,
    object_type: str,
    policy_assignments_target_database: str,
    policy_assignments_project: str,
    policy_assignments_config_file_path: str,
    policy_assignments_repo_path: str
):
    """
    Alter policy assignments based on policy assignments information.
    """

    if object_type == 'TABLE':
        dbobject_type = DbObjectType.TABLE
    elif object_type == 'VIEW':
        dbobject_type = DbObjectType.VIEW
    elif object_type == 'TAG':
        dbobject_type = DbObjectType.TAG
    elif object_type == 'DYNAMIC TABLE':
        dbobject_type = DbObjectType.DYNAMICTABLE
    else:
        raise ValueError(f"Object Type {object_type} not supported for policy handling!")

    policy_assignments_handler= {dbobject_type.name:{}}

    policy_service = PolicyService(
            policy_assignments_handler = policy_assignments_handler, 
            policy_assignments_target_database = policy_assignments_target_database, 
            policy_assignments_config_file_path = policy_assignments_config_file_path, 
            policy_assignments_project = policy_assignments_project, 
            policy_assignments_info_output_folder_path = '',
            policy_assignments_repo_path = policy_assignments_repo_path
        )
    policy_service.get_policy_assignments_info(get_all_assignments= True)
    
    for object in objects:
        object_schema = object.split('.')[0]
        object_name = object.split('.')[1]

        policy_assignments_info_from_object = get_policy_assignments_info_from_object( 
            object_schema=object_schema, 
            object_name=object_name, 
            object_type=dbobject_type,
            action_type=DbActionType.ADD, 
            policy_assignments_info=policy_service.policy_assignments_info)
        
        if policy_assignments_info_from_object:
            columns=[]
            statements=[]
            # Secondary Role is already used when querying the POLICY_REFERENCES
            snow_client.execute_statement(f'USE SECONDARY ROLES {policy_assignments_info_from_object["assignments"][0]["policy_pipeline_role"]};')
            for assignment_info in policy_assignments_info_from_object["assignments"]:
                
                if assignment_info["policy_type"]=='column_masking_policies':
                    if not columns:
                        columns_info= snow_client.execute_query(f'DESCRIBE {object_type} {policy_assignments_target_database}.{policy_assignments_info_from_object["object_identifier"]} ;')
                        columns= [column["name"].casefold() for column in columns_info]
                    column_name = assignment_info["assignment"].split(".")[2]
                    if column_name.casefold() in columns:
                        using_string = ""
                        if assignment_info["argument_columns"]:
                            using_string = f"{column_name}"
                            for arg_column in assignment_info["argument_columns"]:
                                using_string = f"{using_string}, {arg_column}"
                            using_string = f"USING ({using_string})"
                        statements.append(f'ALTER {object_type} {policy_assignments_target_database}.{policy_assignments_info_from_object["object_identifier"]} ALTER COLUMN {column_name} SET MASKING POLICY {assignment_info["policy_database"]}.{assignment_info["policy_schema"]}.{assignment_info["policy"]} {using_string} FORCE;')
                
                if assignment_info["policy_type"]=='row_access_policies':
                    if object_type == 'DYNAMIC TABLE':
                        ref_entity_domain='table'
                    else:
                        ref_entity_domain = object_type.lower()

                    columns_string = ""
                    for arg_column in assignment_info["argument_columns"]:
                        columns_string = f"{columns_string}, {arg_column}"
                    columns_string = f"ON ({columns_string[2:]})"

                    current_rap_assignment = snow_client.execute_query(f"SELECT POLICY_DB, POLICY_SCHEMA, POLICY_NAME FROM TABLE(INFORMATION_SCHEMA.POLICY_REFERENCES(REF_ENTITY_NAME => 'PNN_DEVELOPMENT.TEST_DATA.REGIONS', REF_ENTITY_DOMAIN => '{ref_entity_domain}')) WHERE POLICY_KIND = 'ROW_ACCESS_POLICY';")

                    if current_rap_assignment:
                        current_rap_identifier = f"{current_rap_assignment[0]['POLICY_DB']}.{current_rap_assignment[0]['POLICY_SCHEMA']}.{current_rap_assignment[0]['POLICY_NAME']}"
                        statements.append(f'ALTER {object_type} {policy_assignments_target_database}.{policy_assignments_info_from_object["object_identifier"]} DROP ROW ACCESS POLICY {current_rap_identifier}, ADD ROW ACCESS POLICY {assignment_info["policy_database"]}.{assignment_info["policy_schema"]}.{assignment_info["policy"]} {columns_string};')
                    else:
                        statements.append(f'ALTER {object_type} {policy_assignments_target_database}.{policy_assignments_info_from_object["object_identifier"]} ADD ROW ACCESS POLICY {assignment_info["policy_database"]}.{assignment_info["policy_schema"]}.{assignment_info["policy"]} {columns_string};')
            
            statements.append(f"USE SECONDARY ROLES NONE;")
            snow_client.execute_statement(statements)


def recreate_pipes(
    snow_client: SnowClient,
    source_database_name: str,
    target_database_name: str,
    replace_instructions: Dict[str, Dict[str, str]],
    schema_list: List[str] = None,
    continue_on_error: bool = False,
):
    """
    Recreate pipes to an a different database.

    Some pipes cannot be cloned, so use this function to get_ddl() on the source database
    and execute on it on the target database.

    Can update the DDL with the replace instructions: Pass empty dict for no changes.

    Can update existing pipes on a database: Pass same value for source and target database.

    Args:
        snow_client: client to connect to snowflake account
        source_database_name:  name of the source database
        target_database_name:  name of the target database
        replace_instructions: dict with regex patterns for different pipe definitions properties, e.g.
            {
                'integration': {'pattern': "(?P<before>integration='[a-z0-9_]*)(DEV|TEST|PROD)(?P<after>')", 'repl': '\g<before>DEV\g<after>' },
            }
        schema_list: (default None) - only alter pipes in schemas given in this list, use all schemas if schema_list==None
        continue_on_error: Continue if a pipe can not be altered, else raise exception
    """
    if schema_list is None:
        schema_list_string = ""
    else:
        schema_list_string = f"in schemas [ '{', '.join(schema_list)}' ] "
    log.info(
        f"RECREATE PIPES from database [ '{source_database_name}' ] {schema_list_string} to database [ '{target_database_name}' ] using INSTRUCTIONS {str(replace_instructions)}"
    )

    _check_snowclient_database(snow_client)
    _validate_replace_instructions(replace_instructions)

    pipes = get_pipes(source_database_name, snow_client)

    for pipe in pipes:
        if not (
            (schema_list is None)
            or (pipe["schema_name"].lower() in [s.lower() for s in schema_list])
        ):
            log.debug(
                f"SKIP recreate pipe [ '{pipe['schema_name']}.{pipe['name']}' ] (is not in schema list  [ '{schema_list})' ]"
            )
            continue

        log.info(f"RECREATE PIPE [ '{pipe['schema_name']}.{pipe['name']}' ]")
        ddl = snow_client.execute_query(
            f"SELECT GET_DDL('PIPE', '{source_database_name}.{pipe['schema_name']}.{pipe['name']}', TRUE) AS DDL;"
        )

        new_ddl = ddl[0]["DDL"]

        # we do not need to make sure new_ddl has "create OR REPLACE", because "select get_ddl()" always includes "OR REPLACE"
        new_ddl = re.sub(
            source_database_name,
            target_database_name,
            new_ddl,
            flags=re.IGNORECASE,
        )
        for instruction in replace_instructions:
            new_ddl = re.sub(
                replace_instructions[instruction]["pattern"],
                replace_instructions[instruction]["repl"],
                new_ddl,
                flags=re.IGNORECASE,
            )

        try:
            snow_client.execute_statement(
                f'USE DATABASE "{target_database_name}"; {new_ddl}'
            )
            snow_client._config.database = target_database_name
        except Exception as err:
            log.error(
                f"Could not recreate pipe [ '{pipe['schema_name']}.{pipe['name']}' ]. Error message: {str(err)}"
            )
            if not continue_on_error:
                raise err


def check_input_list_valid(l: List[str]):
    """
    Check if a given list of strings contains only valid SQL object names.
    Return True if only valid names in list, False otherwise
    """
    for i in l:
        r = re.compile(
            r"^([a-z0-9_]+|\"[a-z0-9_\-$]+\")(\.[a-z0-9_]+|\.\"[a-z0-9_\-$]+\")*$",
            re.IGNORECASE,
        )
        if not r.match(i):
            return False
    return True


def grant_all_ownerships(
    database_name: str, role_name: str, snow_client: SnowClient
) -> None:
    """
        Grant ownership on database and all schemas in a database to given role.
    Args:
        database_name: str - name of the database
        role_name: str - name of the role to grant the permission to
        snow_client: SnowClient - client to connect to snowflake account
        parallel_threads: int - number of parallel threads while granting ownership
    """
    snow_client.execute_statement(f"USE DATABASE {database_name};")
    statements = []
    statements.append(
        f'GRANT OWNERSHIP ON ALL TABLES IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL EXTERNAL TABLES IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL VIEWS IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL FUNCTIONS IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL PROCEDURES IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL FILE FORMATS IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL STAGES IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )
    statements.append(
        f'GRANT OWNERSHIP ON DATABASE {database_name} TO ROLE "{role_name}" REVOKE CURRENT GRANTS;'
    )

    log.info(
        f"GRANT ownership all objects IN database [ '{database_name}' ] TO role [ '{role_name}' ]",
        db=database_name,
        status=LogStatus.PENDING,
    )
    snow_client.execute_statement(statements)


def _check_snowclient_database(snow_client) -> None:
    """
    Some functions in this class might alter the default database target of a snowclient.
    This function prints a warning if a snow_client with a set database is supplied.
    """
    if snow_client.database is not None:
        log.warning(
            "Given snowclient has a database set. After this function has been executed, the database target might be changed. The database parameter of the snowclient will not reflect that change"
        )


def _validate_replace_instructions(d):
    """
    Validate if a given dictionary is a valid replace instruction for alter_stages, alter_tasks and replace_pipes.

    Given dictionary must contain dictionaries.
    Each of the inner dictionaries must have two properties: 'pattern' and 'repl'
    """
    if not isinstance(d, dict):
        raise ValueError("Given parameter is not a dictionary.")
    if len(d) == 0:
        raise ValueError("Given dictionary is empty.")
    for k, v in d.items():
        if not isinstance(v, dict):
            raise ValueError(f"Entry '{k}' is not a dictionary.")
        if not "pattern" in v:
            raise ValueError(f"Entry '{k}' does not have property 'pattern'.")
        if not "repl" in v:
            raise ValueError(f"Entry '{k}' does not have property 'repl'.")
