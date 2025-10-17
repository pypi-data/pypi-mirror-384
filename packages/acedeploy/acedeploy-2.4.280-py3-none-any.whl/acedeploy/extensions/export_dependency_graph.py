import datetime
import logging
from typing import List, Set

import aceservices.snowflake_service as snowflake_service
import aceutils.dict_and_list_util as dict_and_list_util
import aceutils.file_util as file_util
import networkx as nx
from acedeploy.core.model_sql_entities import DbObjectType
from acedeploy.services.dependency_parser import DependencyParser
from acedeploy.services.solution_service import SolutionClient
from aceutils.logger import LoggingAdapter


logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def get_dependency_parser(
    solution_folder: str,
    pre_deployment_folders: List[str] = [],
    post_deployment_folders: List[str] = [],
    object_types: Set[DbObjectType] = (
        DbObjectType.TABLE,
        DbObjectType.VIEW,
        DbObjectType.MATERIALIZEDVIEW,
        DbObjectType.FUNCTION,
    ),
) -> DependencyParser:
    """
        Convienience function to gerenate a dependency parser client for a given folder
    Args:
        project_folder: str - path of solution to be loaded
        pre_deployment_folders: List[str] - predeployment folders must be given so they can be skipped
        post_deployment_folders: List[str] - postdeployment folders must be given so they can be skipped
        object_types: object_types: set[DbObjectType] - types of objects to be considered
    Returns:
        dependency_graph: DependencyParser - dependency parser
    """
    solution_client = SolutionClient(
        solution_folder, pre_deployment_folders, post_deployment_folders
    )
    solution_client.load_solution()
    dependency_client = DependencyParser(solution_client)
    dependency_client.build_full_dependency_graph(object_types)
    return dependency_client


def get_dependency_graph(
    solution_folder: str,
    pre_deployment_folders: List[str] = [],
    post_deployment_folders: List[str] = [],
    object_types: Set[DbObjectType] = (
        DbObjectType.TABLE,
        DbObjectType.VIEW,
        DbObjectType.MATERIALIZEDVIEW,
        DbObjectType.FUNCTION,
    ),
) -> nx.DiGraph:
    """
        Convienience function to gerenate a dependency graph for a given folder
    Args:
        project_folder: str - path of solution to be loaded
        pre_deployment_folders: List[str] - predeployment folders must be given so they can be skipped
        post_deployment_folders: List[str] - postdeployment folders must be given so they can be skipped
        object_types: object_types: set[DbObjectType] - types of objects to be considered
    Returns:
        dependency_graph: nx.DiGraph - dependency graph
    """
    dependency_client = get_dependency_parser(
        solution_folder, pre_deployment_folders, post_deployment_folders, object_types
    )
    return dependency_client._dependency_graph


def convert_dependency_graph_to_nested_dict(
    dependency_graph: nx.DiGraph, schema_filter: List[str] = []
) -> dict:
    """
        Convert a given dependency graph to a nested dictionary
    Args:
        dependency_graph: nx.DiGraph - dependency graph of solution objects
        schema_filter: List[str] - only get information on objects in these schemas (empty=all schemas)
    Returns:
        dict - dictionary containing information on dependency graph
    """
    log.info(f"CONVERT graph to nested DICT")
    if schema_filter:
        schema_filter_upper = [s.upper() for s in schema_filter]
        nodes = [n for n in dependency_graph.nodes() if n.schema in schema_filter_upper]
    else:
        nodes = list(dependency_graph.nodes())
    result = []

    for node in nodes:
        result.append(
            {
                "type": DbObjectType.get_sql_object_type(node.object_type),
                "schema": node.schema,
                "name": node.name,
                "dependsOn": [
                    {
                        "type": DbObjectType.get_sql_object_type(n.object_type),
                        "schema": n.schema,
                        "name": n.name,
                    }
                    for n in nx.descendants(dependency_graph.reverse(), node)
                ],
                "requiredFor": [
                    {
                        "type": DbObjectType.get_sql_object_type(n.object_type),
                        "schema": n.schema,
                        "name": n.name,
                    }
                    for n in nx.descendants(dependency_graph, node)
                ],
            }
        )

    return result


def convert_dependency_graph_to_nested_json(
    file_path: str, dependency_graph: nx.DiGraph, schema_filter: List[str] = []
) -> None:
    """
        Convert a given dependency graph to a nested json
    Args:
        file_path: str - path where the output will be stored (overwritten without asking)
        dependency_graph: nx.DiGraph - dependency graph of solution objects
        schema_filter: List[str] - only get information on objects in these schemas (empty=all schemas)
    Returns:
        str - json containing information on dependency graph
    """
    dictionary = convert_dependency_graph_to_nested_dict(
        dependency_graph, schema_filter
    )
    log.info(f"SAVE graph as [ '{file_path}' ]")
    file_util.save_json(file_path, dictionary)


def convert_dependency_graph_to_list_of_dict(
    dependency_graph: nx.DiGraph, schema_filter: List[str] = []
) -> List[dict]:
    """
        Convert a given dependency graph to a list of dictionaries
    Args:
        dependency_graph: nx.DiGraph - dependency graph of solution objects
        schema_filter: List[str] - only get information on objects in these schemas (empty=all schemas)
    Returns:
        List[dict] - list containing information on dependency graph
    """
    log.info(f"CONVERT graph to LIST of DICTS")
    if schema_filter:
        schema_filter_upper = [s.upper() for s in schema_filter]
        nodes = [n for n in dependency_graph.nodes() if n.schema in schema_filter_upper]
    else:
        nodes = list(dependency_graph.nodes())
    result = []

    for node in nodes:
        result.extend(
            [
                {
                    "type": DbObjectType.get_sql_object_type(node.object_type),
                    "schema": node.schema,
                    "name": node.name,
                    "dependsOnType": DbObjectType.get_sql_object_type(n.object_type),
                    "dependsOnSchema": n.schema,
                    "dependsOnName": n.name,
                }
                for n in nx.descendants(dependency_graph.reverse(), node)
            ]
        )

    return result


def convert_dependency_graph_to_flat_json(
    file_path: str, dependency_graph: nx.DiGraph, schema_filter: List[str] = []
) -> None:
    """
        Convert a given dependency graph to a flat json
    Args:
        file_path: str - path where the output will be stored (overwritten without asking)
        dependency_graph: nx.DiGraph - dependency graph of solution objects
        schema_filter: List[str] - only get information on objects in these schemas (empty=all schemas)
    Returns:
        str - json containing information on dependency graph
    """
    list_of_dicts = convert_dependency_graph_to_list_of_dict(
        dependency_graph, schema_filter
    )
    log.info(f"SAVE graph as [ '{file_path}' ]")
    file_util.save_json(file_path, list_of_dicts)


def convert_dependency_graph_to_csv(
    file_path: str,
    dependency_graph: nx.DiGraph,
    schema_filter: List[str] = [],
    csv_delimiter: str = ";",
) -> None:
    """
        Convert a given dependency graph to a csv
    Args:
        file_path: str - path where the output will be stored (overwritten without asking)
        dependency_graph: nx.DiGraph - dependency graph of solution objects
        schema_filter: List[str] - only get information on objects in these schemas (empty=all schemas)
    Returns:
        str - json containing information on dependency graph
    """
    list_of_dicts = convert_dependency_graph_to_list_of_dict(
        dependency_graph, schema_filter
    )
    log.info(f"SAVE graph as [ '{file_path}' ]")
    file_util.save_list_of_dicts_as_csv(
        file_path, list_of_dicts, delimiter=csv_delimiter
    )


def write_dependencies_to_table(
    snowclient_config: snowflake_service.SnowClientConfig,
    snowflake_database: str,
    snowflake_schema: str,
    snowflake_table: str,
    dependency_graph: nx.DiGraph,
    schema_filter: List[str] = [],
) -> None:
    """
    Write information in given dependency graph to a Snowflake table.
    The table must exist. Table will be truncated.

    DDL of the target table:
        CREATE OR REPLACE TABLE <database>.PUBLIC.OBJECT_DEPENDENCIES (
            TYPE VARCHAR COMMENT 'Type of the object',
            SCHEMA VARCHAR COMMENT 'Schema of the object',
            NAME VARCHAR COMMENT 'Name of the object',
            DEPENDS_ON_TYPE VARCHAR COMMENT 'Type of the object that this object depends on',
            DEPENDS_ON_SCHEMA VARCHAR COMMENT 'Type of the object that this object depends on',
            DEPENDS_ON_NAME VARCHAR COMMENT 'Type of the object that this object depends on',
            UPDATE_TIMESTAMP TIMESTAMP_TZ COMMENT 'Time at which this entry has been generated'
        );
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    dependency_dicts_list = convert_dependency_graph_to_list_of_dict(
        dependency_graph, schema_filter
    )
    statements = _generate_statements_snowflake_table(
        dependency_dicts_list,
        timestamp,
        snowflake_database,
        snowflake_schema,
        snowflake_table,
    )
    _execute_on_snowflake(statements, snowclient_config)


def _generate_statements_snowflake_table(
    dependency_dicts_list,
    timestamp,
    snowflake_database,
    snowflake_schema,
    snowflake_table,
) -> str:
    """
    Generate statements to insert the dependency info into a table.
    """
    log.info(f"GENERATE sql statements")

    statements = ["BEGIN;"]
    statements.append(
        f"TRUNCATE {snowflake_database}.{snowflake_schema}.{snowflake_table};"
    )

    values = []
    for d in dependency_dicts_list:
        values.append(
            f"""(
                '{d['type']}',
                '{d['schema']}',
                '{d['name']}',
                '{d['dependsOnType']}',
                '{d['dependsOnSchema']}',
                '{d['dependsOnName']}',
                TO_TIMESTAMP_TZ('{timestamp}')
            )"""
        )
    for value_sublist in dict_and_list_util.chunks(
        values, 10000
    ):  # insert statements cannot contain more than 16384 rows
        insert_statement = f"""
            INSERT INTO {snowflake_database}.{snowflake_schema}.{snowflake_table} (
                TYPE,
                SCHEMA,
                NAME,
                DEPENDS_ON_TYPE,
                DEPENDS_ON_SCHEMA,
                DEPENDS_ON_NAME,
                UPDATE_TIMESTAMP
            ) VALUES
            {','.join(value_sublist)}
            ;"""
        statements.append(insert_statement)

    log.debug(".   \n".join(statements))

    statements.append("COMMIT;")

    return statements


def _execute_on_snowflake(
    statements: str, snowclient_config: snowflake_service.SnowClientConfig
):
    """
    Connect to snowflake and execute a set of statements.
    """
    log.info(f"CONNECT to Snowflake")
    snowflake_client = snowflake_service.SnowClient(snowclient_config)
    snowflake_client.execute_statement(f"USE WAREHOUSE {snowclient_config.warehouse};")
    log.info(f"EXECUTE sql statements")
    snowflake_client.execute_statement(statements)
