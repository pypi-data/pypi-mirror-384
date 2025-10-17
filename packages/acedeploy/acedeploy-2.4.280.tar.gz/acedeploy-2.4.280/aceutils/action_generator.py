from typing import List

from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
from acedeploy.services.solution_service import SolutionClient


def generate_actions_from_git_diff(
    solution_client: SolutionClient,
) -> List[DbObjectAction]:
    """
        Generate list of db object actions for deployment of git diff to meta db
    Returns:
        List[DbObjectAction] - List of db object actions
    Notes:
        When view was added, dependend objects of the views need to be added
    """
    object_action_list = []

    # always add all schemas and sequences and functions
    for obj in solution_client.all_objects:
        if (obj.object_type in (DbObjectType.SCHEMA,)) or (
            obj.git_change_type in ("A", "M", "R")
        ):
            action = DbObjectAction.factory_from_solution_object(obj, DbActionType.ADD)
            object_action_list.append(action)

    return object_action_list


def generate_actions_from_solution(solution_client) -> List[DbObjectAction]:
    """
        Generates list of db actions for deployment based on solution items
    Returns:
        List[DbObjectAction] - List of db object actions
    """
    object_action_list = []

    for obj in solution_client.all_objects:
        action = DbObjectAction.factory_from_solution_object(obj, DbActionType.ADD)
        object_action_list.append(action)

    return object_action_list
