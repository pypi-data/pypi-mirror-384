import logging
from typing import List
import copy
from collections import defaultdict

import aceutils.dict_and_list_util as dict_and_list_util
from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_solution_entities import SolutionObject
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
from acedeploy.services.dependency_parser import DependencyParser
from acedeploy.services.solution_service import SolutionClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def order_action_list(
    object_action_list: List[DbObjectAction],
    dependency_client: DependencyParser,
    is_meta_deployment: bool,
) -> List[List[List[DbObjectAction]]]:
    """
        Order a list of db object actions:
            - CREATE and ALTER schemas
            - CREATE and ALTER object (except tasks)
            - CREATE and ALTER tasks
            - DROP objects, except schemas
            (- currently disabled: DROP schemas)
    Args:
        object_action_list: List[DbObjectAction] - unordered list of db object actions
        solution_client: SolutionClient - contains all files loaded from disk
        is_meta_deployment: bool - if action list is used to deploy to a meta database
    Returns:
        ordered_object_action_list: List[List[List[DbObjectAction]]] - ordered list of db object actions
            - first list level: each list below needs to processed in order
            - second list level: this list contains collections steps that can be run in parallel
            - third level: this step collection must be executed in order
        Example (for clarity, using statements instead of DbObjectAction):
            [
                [
                    ["CREATE SCHEMA A"], ["CREATE SCHEMA B"]
                ], [
                    ["CREATE TABLE A.T1 ...", "CREATE VIEW A.V1 AS SELECT * FROM A.T1" ],
                    ["CREATE TABLE B.T2 ...", "CREATE VIEW A.V1 AS SELECT * FROM B.T2" ],
                    ["CREATE TABLE B.T3"]
                ], [
                    ["CREATE TASK A.T1 ..."], ["CREATE TASK B.T2 ..."]
                ], [
                    ["DROP VIEW C.V5"]
                ]
            ]
    """
    log.info(f"ORDER actions WITH count [ '{len(object_action_list)}' ]")
    ordered_object_action_list = []

    # always create new schemas first
    ordered_object_action_list.append(
        _generate_action_sublist_unordered(
            object_action_list,
            (DbObjectType.SCHEMA,),
            (DbActionType.ADD, DbActionType.ALTER),
        )
    )

    # always create new tags befor creating objects
    ordered_object_action_list.append(
        _generate_action_sublist_unordered(
            object_action_list,
            (DbObjectType.TAG,),
            (DbActionType.ADD, DbActionType.ALTER),
        )
    )

     # always drop overloaded procedures and functions before creating new ones (when Object-Option dropOverloadedObjects is set for procedures or functions)
    ordered_object_action_list.append(
        _generate_action_sublist_unordered(
            object_action_list,
            (DbObjectType.PROCEDURE, DbObjectType.FUNCTION ),
            (DbActionType.DROPOVERLOADED,),
        )
    )

    # add and alter objects
    ordered_object_action_list.append(
        _generate_action_sublist_ordered(
            object_action_list,
            (
                DbObjectType.VIEW,
                DbObjectType.MATERIALIZEDVIEW,
                DbObjectType.TABLE,
                DbObjectType.EXTERNALTABLE,
                DbObjectType.FUNCTION,
                DbObjectType.PROCEDURE,
                DbObjectType.FILEFORMAT,
                DbObjectType.SEQUENCE,
                DbObjectType.STAGE,
                DbObjectType.PIPE,
                DbObjectType.STREAM,
                DbObjectType.MASKINGPOLICY,
                DbObjectType.ROWACCESSPOLICY,
                DbObjectType.DYNAMICTABLE,
                DbObjectType.NETWORKRULE,
            ),
            (DbActionType.ADD, DbActionType.ALTER),
            dependency_client,
            is_meta_deployment,
        )
    )

    # add and alter tasks (task content is not validated on CREATE TASK, therefore they can by created independently of other objects)
    ordered_object_action_list.append(
        _generate_action_sublist_ordered(
            object_action_list,
            (DbObjectType.TASK,),
            (DbActionType.ADD, DbActionType.ALTER),
            dependency_client,
            is_meta_deployment,
        )
    )

    # objects to be dropped, except schemas
    ordered_object_action_list.append(
        _generate_action_sublist_unordered(
            object_action_list,
            [t for t in DbObjectType if t != DbObjectType.SCHEMA],
            (DbActionType.DROP,),
        )
    )

    # schemas to be dropped (currently disabled)
    # ordered_object_action_list.append(
    #     self._generate_action_sublist_unordered(
    #         object_action_list,
    #         (DbObjectType.SCHEMA,),
    #         (DbActionType.DROP,)
    #     )
    # )

    return ordered_object_action_list


def _generate_action_sublist_unordered(
    all_actions: List[DbObjectAction],
    object_types: List[DbObjectType],
    action_type: List[DbActionType],
) -> List[List[DbObjectAction]]:
    """
    Given a list of action, return all actions that match a specific DbObjectAction and DbActionType.

    It is assumed that the returned actions can be deployed without any interdependencies.
    Therefore, the each action will be returned in its own list. (Which can later be used for parallel deployment.)
    """
    return [
        [a]
        for a in all_actions
        if (a.object_type in object_types) and (a.action in action_type)
    ]


def _generate_action_sublist_ordered(
    all_actions: List[DbObjectAction],
    object_types: List[DbObjectType],
    action_type: List[DbActionType],
    dependency_client: DependencyParser,
    is_meta_deployment: bool,
) -> List[List[DbObjectAction]]:
    """
    Given a list of action, return all actions that match a specific DbObjectAction and DbActionType and order them.
    """
    object_action_list_to_be_ordered = [
        a
        for a in all_actions
        if (a.object_type in object_types) and (a.action in action_type)
    ]
    return _order_actions_with_internal_dependencies(
        object_action_list_to_be_ordered,
        dependency_client,
        is_meta_deployment,
    )


def order_actions_with_internal_dependencies_from_solution(
    object_types: List[DbObjectType],
    object_action_list_to_be_ordered: List[DbObjectAction],
    solution_client: SolutionClient,
    is_meta_deployment: bool,
) -> List[List[DbObjectAction]]:
    """
    Order a list of object actions with internal dependencies.
    """
    dep_client = DependencyParser(solution_client)
    dep_client.build_full_dependency_graph(object_types)
    return _order_actions_with_internal_dependencies(
        object_action_list_to_be_ordered, dep_client, is_meta_deployment
    )


def _order_actions_with_internal_dependencies(
    object_action_list_to_be_ordered: List[DbObjectAction],
    dependency_client: DependencyParser,
    is_meta_deployment: bool,
) -> List[List[DbObjectAction]]:
    """
    Order a list of object actions with internal dependencies.
    """
    if len(object_action_list_to_be_ordered) == 0:
        return []
    dep_client = copy.deepcopy(
        dependency_client
    )  # this function will make changes to dep_client, but the original dependency_client should not be affected
    filter_mode = "meta_deployment" if is_meta_deployment else "target_deployment"
    dep_client.filter_graph_by_object_ids(
        [a.id for a in object_action_list_to_be_ordered], filter_mode
    )
    dep_client.build_subgraphs()
    ordered_solution_objects = dep_client.get_ordered_objects()
    ordered_solution_objects.sort(key=len)
    ordered_solution_objects.reverse()

    action_type = DbActionType.ADD if is_meta_deployment else DbActionType.ALTER
    object_actions_from_dependency_parser = (
        _generate_actions_from_ordered_solution_objects(
            object_action_list_to_be_ordered, ordered_solution_objects, action_type
        )
    )

    if not _check_all_actions_are_present(
        object_action_list_to_be_ordered, object_actions_from_dependency_parser
    ):
        raise ValueError(
            "Deployment parser sanity check failed: Not all actions appear in ordered action list"
        )

    return object_actions_from_dependency_parser


def _generate_actions_from_ordered_solution_objects(
    unordered_action_list: List[DbObjectAction],
    ordered_solution_object_list: List[List[SolutionObject]],
    action_type: DbActionType,
):
    """
    Given a list of (unordered) actions, order the given list using a nested list of solution objects.
    If an action in the list exists that corresponds to the solution object, use that action.
    If a matching action does not exists, create one.
    """
    log.info("MATCH actions to ordered solution objects")
    ordered_action_list = []

    unordered_action_dict_by_id = defaultdict(list)
    for action in unordered_action_list:
        unordered_action_dict_by_id[action.id].append(action)

    for ordered_solution_sublist in ordered_solution_object_list:
        tmp = []
        for solution_object in ordered_solution_sublist:
            action = _match_action_to_solution_object(
                unordered_action_dict_by_id, solution_object.id
            )
            if action:
                tmp.append(action)
            else:
                tmp.append(
                    DbObjectAction.factory_from_solution_object(
                        solution_object, action_type
                    )
                )
        ordered_action_list.append(tmp)
    return ordered_action_list


def _match_action_to_solution_object(action_dict_by_id, solution_object_id):
    """
    Find a matching action in action_dict_by_id for the given solution_object id.
    If such an action does not exist in action_dict_by_id, return None.

    action_dict_by_id must be a dictionary where each key is an id and each value is a
    list of actions with zero or one elements.
    """
    result = action_dict_by_id[solution_object_id]
    if len(result) == 0:
        log.debug(
            f"OBJECT with id [ '{solution_object_id}' ] NOT in FOUND in action list"
        )
        return None
    elif len(result) > 1:
        raise ValueError(
            f"OBJECT with id [ '{solution_object_id}' ] NOT UNIQUE in action list. Found [ '{len(result)}' ]"
        )
    else:
        return result[0]


def _check_all_actions_are_present(action_list1, action_list2):
    """
    Sanity check after ordering of dependency graph.
    Return True if all actions in action_list1 appear in action_list2.
    Else return False.
    """
    action_list2_ids = [a.id for a in dict_and_list_util.flatten(action_list2)]
    for action1 in dict_and_list_util.flatten(action_list1):
        if not action1.id in action_list2_ids:
            return False
    return True
