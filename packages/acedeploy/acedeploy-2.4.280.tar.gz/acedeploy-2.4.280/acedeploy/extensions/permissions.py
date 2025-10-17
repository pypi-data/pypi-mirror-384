import logging
from typing import Dict, List
import jinja2
from concurrent.futures import ThreadPoolExecutor

from aceservices.snowflake_service import SnowClient
from aceutils.logger import LoggingAdapter
import aceutils.file_util as file_util

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def set_permissions_on_database(
    snow_client: SnowClient,
    template_path: str,
    database_name: str,
    schema_list: Dict[str, List[str]],
    return_future_ownerships: bool = True,
    parallel_threads: int = 10,
) -> None:
    """
    Set permissions on a database using a given template.

    Args:
        snow_client: Snowflake connection
        template_path: Absolute path to the Jinja template. See below for details.
        database_name: Name of the database
        schema_list: Blacklist or whitelist of schemas to set grants for. To use all, input {"blacklist": []}
            Examples:
                {"blacklist": ["PUBLIC", "SECURITY"]}
                {"whitelist": ["CORE", "REPORTING"]}
        return_future_ownerships: Flag to determine whether information on future ownership grants is queried and provided to template.
        parallel_threads: int - number of parallel threads during execution


    Jinja template information:
        - Path must be given as absolute path.
        - Referencing any non-existing variables in the template will raise an exception.
        - database_name and schema_name will always be provided to template.
        - If return_future_ownerships=True, future_owners will be provided to template.
        - future_owners is a dict which shows all future grants in the schema, e.g.:
          { "TABLE": "R_TABLE_OWNER", "VIEW": "R_VIEW_OWNER" }
        - future_owners might be required if future grants need to be set, because existing future grants must be revoked before setting new grants
    """
    schema_names = _get_and_filter_schema_names(
        snow_client=snow_client,
        database_name=database_name,
        schema_list=schema_list,
    )

    def _run(schema):
        set_permissions_on_schema(
            snow_client=snow_client,
            template_path=template_path,
            database_name=database_name,
            schema_name=schema,
            return_future_ownerships=return_future_ownerships,
        )

    with ThreadPoolExecutor(max_workers=parallel_threads) as pool:
        for __ in pool.map(_run, schema_names):
            pass  # need to iterate over results from _run(), otherwise exceptions in _run() will not be raised in main thread


def set_permissions_on_schema(
    snow_client: SnowClient,
    template_path: str,
    database_name: str,
    schema_name: str,
    return_future_ownerships: bool = True,
) -> None:
    """
    Set permissions on a single schema using a given template.

    Args:
        snow_client: Snowflake connection
        template_path: Path to the Jinja template. See below for details.
        database_name: Name of the database
        schema_name: Name of the schema
        return_future_ownerships: Flag to determine whether information on future ownership grants is queried and provided to template.

    Jinja template information:
        - Referencing any non-existing variables in the template will raise an exception.
        - database_name and schema_name will always be provided to template.
        - If return_future_ownerships=True, future_owners will be provided to template.
        - future_owners is a dict which shows all future grants in the schema, e.g.:
          { "TABLE": "R_TABLE_OWNER", "VIEW": "R_VIEW_OWNER" }
        - future_owners might be required if future grants need to be set, because existing future grants must be revoked before setting new grants
    """
    log.info(
        f"SET permission template on SCHEMA [ '{database_name}.{schema_name}' ] using TEMPLATE [ '{template_path}' ]"
    )
    log.debug(f"LOAD permission template from FILE [ '{template_path}' ]")
    jinja_template_content = file_util.get_content(template_path)
    jinja_template = jinja2.Template(
        jinja_template_content, undefined=jinja2.StrictUndefined
    )
    if return_future_ownerships:
        future_owners = _get_future_ownerships(
            snow_client,
            database_name,
            schema_name,
        )
    else:
        future_owners = {}
    statements = jinja_template.render(
        database_name=database_name,
        schema_name=schema_name,
        future_owners=future_owners,
    )
    snow_client.execute_statement(statements)


def _get_future_ownerships(
    snow_client: SnowClient,
    database_name: str,
    schema_name: str,
) -> Dict[str, str]:
    """
    Get future ownerships in a schema and return as dictionary.

    Returns:
        Dictionary like {
            object_type1: role_with_ownership1,
            object_type2: role_with_ownership2,
            ...
        }
    """
    log.info(
        f'GET future ownership grants in SCHEMA [ \'"{database_name}"."{schema_name}"\' ]'
    )
    query = f'SHOW FUTURE GRANTS IN SCHEMA "{database_name}"."{schema_name}";'
    query_result = snow_client.execute_query(query)
    result = {
        q["grant_on"]: q["grantee_name"]
        for q in query_result
        if q["privilege"] == "OWNERSHIP"
    }
    return result


def _get_all_schema_names(
    snow_client: SnowClient,
    database_name: str,
) -> List[str]:
    """
    Get names of all schemas in a database and return them as a list.

    This function can be executed by SECURITYADMIN, since it only uses SHOW.
    """
    log.info(f"GET schemas in DATABASE [ '{database_name}' ]")
    query = f'SHOW SCHEMAS IN DATABASE "{database_name}";'
    query_result = snow_client.execute_query(query)
    result = [q["name"] for q in query_result]
    return result


def _get_and_filter_schema_names(
    snow_client: SnowClient,
    database_name: str,
    schema_list: Dict[str, List[str]],
) -> List[str]:
    """
    Get names of all schemas in a database and filter them by schema_list.

    This function can be executed by SECURITYADMIN, since it only uses SHOW.
    """
    schema_names = _get_all_schema_names(
        snow_client=snow_client, database_name=database_name
    )
    if "whitelist" in schema_list:
        schemas_whitelist = [s.casefold() for s in schema_list["whitelist"]]
        result = [s for s in schema_names if s.casefold() in schemas_whitelist]
    elif "blacklist" in schema_list:
        schemas_blacklist = [s.casefold() for s in schema_list["blacklist"]]
        result = [s for s in schema_names if s.casefold() not in schemas_blacklist]
    else:
        raise EnvironmentError(
            "MALFORMED config value [ 'schema_list' ] (contains neither blacklist nor whitelist)"
        )
    return [r for r in result if r != "INFORMATION_SCHEMA"]
