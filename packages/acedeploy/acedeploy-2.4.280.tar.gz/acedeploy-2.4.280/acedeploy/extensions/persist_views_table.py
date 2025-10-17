import logging
from typing import Dict, List

from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
from aceservices.snowflake_service import SnowClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def set_persist_tags(
    persist_table_name: str,
    action_list: List[DbObjectAction],
    database_name: str,
    snow_client: SnowClient,
):
    """
        Set the tag CREATE_FG for each altered and added view in action_list
    Params:
        persist_table_name: Fully qualified name of the persist table (database.schema.tablename)
        action_list: List of object actions that were performed during the deployment
        database_name: Name of the database to which the objects were deployed
        snow_client: account-scoped snowflake client
    """
    views = get_views(action_list)

    if len(views) == 0:
        log.info(
            f"SET tag CREATE_FG in table [ '{persist_table_name}' ] NOT required, no views deployed"
        )
        return

    statement_template = """
        UPDATE {persist_table_name}
        SET CREATE_FG = 1
        WHERE TARGET_DATABASE ILIKE '{database}'
        AND (UPPER(ORIGIN_TABLE_SCHEMA), UPPER(TABLE_NAME)) IN
        (
            {table_selects}
        );
    """
    table_select_template = "SELECT '{schema}', '{view}'"
    table_selects = []
    for view in views:
        table_selects.append(
            table_select_template.format(
                schema=view["schema_name"].upper(), view=view["view_name"].upper()
            )
        )

    statement = statement_template.format(
        persist_table_name=persist_table_name,
        database=database_name,
        table_selects="\nUNION ".join(table_selects),
    )

    log.info(
        f"SET tag CREATE_FG in table [ '{persist_table_name}' ] for [ '{len(table_selects)}' ] views"
    )
    snow_client.execute_statement(statement)


def get_views(action_list: List[DbActionType]) -> List[Dict[str, str]]:
    """
    Return a list of views that were added or altered
    """
    return [
        {"schema_name": a.schema, "view_name": a.name}
        for a in action_list
        if (
            (a.object_type == DbObjectType.VIEW)
            and (a.action in (DbActionType.ADD, DbActionType.ALTER))
        )
    ]
