from typing import List, Tuple

from acedeploy.core.model_database_object import DatabaseObject
from aceaccount.core.model_account_object import (
    AccountObject,
    AccountObjectType,
)
from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
import aceutils.file_util as file_util


def generate_action_log_summaries(
    action_list: List[DbObjectAction],
) -> Tuple[str, str, str]:
    """
        Generate a short summary of actions to perform.
    Args:
        action_list: List[DbObjectAction] - list of db object actions
    Returns:
        string_add, string_alter, string_drop: (str, str, str) - each e.g. "create: 3 schema(s), 1 table(s), 2 view(s), ..."
    """
    dropoverloaded = False
    counts_add = {object_type: 0 for object_type in [o.value for o in DbObjectType]}
    counts_alter = {object_type: 0 for object_type in [o.value for o in DbObjectType]}
    counts_drop = {object_type: 0 for object_type in [o.value for o in DbObjectType]}
    counts_dropoverloaded = {object_type: 0 for object_type in [DbObjectType.PROCEDURE.value, DbObjectType.FUNCTION.value]}
    for action in action_list:
        if action.action == DbActionType.ADD:
            counts_add[action.object_type.value] += 1
        elif action.action == DbActionType.ALTER:
            counts_alter[action.object_type.value] += 1
        elif action.action == DbActionType.DROP:
            counts_drop[action.object_type.value] += 1
        elif action.action == DbActionType.DROPOVERLOADED:
            counts_dropoverloaded[action.object_type.value] += 1
            dropoverloaded = True
    
    if dropoverloaded:
        string_dropoverloaded = "drop_overloaded: " + ", ".join(
            [f"{counts_dropoverloaded[key]} {key.lower()}(s)" for key in counts_dropoverloaded]
        )
    else:
        string_dropoverloaded = ""

    string_add = "create: " + ", ".join(
        [f"{counts_add[key]} {key.lower()}(s)" for key in counts_add]
    )
    string_alter = "alter: " + ", ".join(
        [f"{counts_alter[key]} {key.lower()}(s)" for key in counts_alter]
    )
    string_drop = "drop: " + ", ".join(
        [f"{counts_drop[key]} {key.lower()}(s)" for key in counts_drop]
    )
    return string_dropoverloaded, string_add, string_alter, string_drop


def generate_object_log_summaries(object_list: List[DatabaseObject]) -> str:
    """
        Generate a short summary of given objects.
    Args:
        object_list: List[DatabaseObject] - list of db objects
    Returns:
        string - e.g. "create: 3 schema(s), 1 table(s), 2 view(s), ..."
    """
    counts = {object_type: 0 for object_type in [o.value for o in DbObjectType]}
    for obj in object_list:
        counts[obj.object_type.value] += 1
    return ", ".join([f"{counts[key]} {key.lower()}(s)" for key in counts])


def generate_account_object_log_summaries(object_list: List[AccountObject]) -> str:
    """
        Generate a short summary of given account objects.
    Args:
        object_list: List[AccountObject] - list of account objects
    Returns:
        string - e.g. "create: 3 schema(s), 1 table(s), 2 view(s), ..."
    """
    counts = {object_type: 0 for object_type in [o.value for o in AccountObjectType]}
    for obj in object_list:
        counts[obj.object_type.value] += 1
    return ", ".join([f"{counts[key]} {key.lower()}(s)" for key in counts])


def save_action_list(
    path: str,
    action_list: List[DbObjectAction],
    predeployment_steps: List[str],
    postdeployment_steps: List[str],
):
    """Save action list in file"""
    with open(path, "w") as f:
        action_summary = "\n".join(generate_action_log_summaries(action_list))
        f.write(f"{action_summary}\n")
        f.write("\nList of actions: \n")
        if len(action_list) == 0:
            f.write("(none)")
        for action in action_list:
            text = (
                f"{action.action.name} {action.object_type.name} {action.full_name}\n"
            )
            f.write(text)

        pre_steps = [s for s in predeployment_steps if s.execute_step]
        f.write("\nList of predeployment steps: \n")
        if len(pre_steps) == 0:
            f.write("(none)")
        for step in pre_steps:
            f.write(f"\n{step.path}\n{step.content}\n")

        post_steps = [s for s in postdeployment_steps if s.execute_step]
        f.write("\nList of postdeployment steps: \n")
        if len(post_steps) == 0:
            f.write("(none)")
        for step in post_steps:
            f.write(f"\n{step.path}\n{step.content}\n")


def save_action_json(path, action_list, database, role):
    """
    Save action json to file
    """
    json_object = {}
    json_object["database"] = database
    json_object["role"] = role
    json_object["objects"] = {}
    json_object["objects"]["views"] = [
        a.full_name for a in action_list if a.object_type == DbObjectType.VIEW
    ]
    json_object["objects"]["tables"] = [
        a.full_name for a in action_list if a.object_type == DbObjectType.TABLE
    ]

    file_util.save_json(path, json_object)
