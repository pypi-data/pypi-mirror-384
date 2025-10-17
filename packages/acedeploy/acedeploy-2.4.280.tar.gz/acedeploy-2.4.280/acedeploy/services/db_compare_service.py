import logging

from acedeploy.core.model_object_action_entities import DbObjectAction
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
from acedeploy.core.model_instance_objects import InstanceObject
from acedeploy.services.metadata_service import MetadataService
from acedeploy.services.policy_service import PolicyAssignmentObjectTypes, PolicyAssignmentAlterObjectTypes, PolicyHandlingTypes, PolicyService
from acedeploy.services.solution_service import SolutionClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class DbCompareClient(object):
    """
    Compare two databases states (current state and desired state).
    Generate a list of actions to change current state into desired state.
    Requires current state to be generated based on solution.
    All objects of desired state need to be DDLs in solution.
    """

    def __init__(
        self,
        desired_state: MetadataService,
        current_state: MetadataService,
        solution_client: SolutionClient,
    ) -> None:
        """
            Inits a new DbCompareClient
        Args:
            desired_state: MetadataService - Database state that should be achieved
            current_state: MetadataService - Current database state
            solution_client: SolutionClient - SQL DDL solution on disk
        """
        self._desired_state = desired_state
        self._current_state = current_state
        self._solution_client = solution_client
        self.action_list = []
        self.policy_assignments_handler = {}
        self._check_desired_state_in_solution()

    def _check_desired_state_in_solution(self):
        """
        Sanity check: Is every item in _desired_state in solution_client?
        The normal workflow is to create the desired_state through a deployment
        of (a subset of) the SQL solution to a database.
        If there are items in _desired_state that are not in the solution,
        something went wrong somewhere.
        """
        log.debug("CHECK all desired state objects in sql solution")
        for obj in self._desired_state.all_objects:
            if not self._solution_client.get_object_by_object(obj):
                raise ValueError(
                    f"The database object [ '{obj}' ] appears in _desired_state, but not in _solution_client."
                )
    
    def _fill_policy_assignments_handler(self, current_instance: InstanceObject , desired_instance: InstanceObject, object_type: str, policy_handling_type: PolicyHandlingTypes):
        """
        Fill policy assignments handler with current instance and desired instance of an object for which the policy assignments needs to be checked/handled.
        """
        current_instance_name, current_instance_columns = PolicyService.parse_instance_for_policy_assignments_handler(current_instance)

        desired_instance_name, desired_instance_columns = PolicyService.parse_instance_for_policy_assignments_handler(desired_instance)

        if current_instance_name:
            instance_name=current_instance_name
        else:
            instance_name=desired_instance_name

        if not (policy_handling_type == PolicyHandlingTypes.ADD_TABLECOLUMN and set(desired_instance_columns) == set(current_instance_columns)):

            if object_type not in self.policy_assignments_handler:
                self.policy_assignments_handler[object_type]= {}

            if current_instance:
                self.policy_assignments_handler[object_type][instance_name]={"policy_handling_type": policy_handling_type.value, "current_instance":{"columns": current_instance_columns}, "desired_instance":{"columns": desired_instance_columns}}
            else:
                self.policy_assignments_handler[object_type][instance_name]={"policy_handling_type": policy_handling_type.value, "desired_instance":{"columns": desired_instance_columns}}

            
    def get_add_actions(self) -> None:
        """
        Get all ADD actions and add them to action list.
        Add all objects that are in _desired_state, but not in _current_state.
        """
        log.debug("ADD actions of type [ 'ADD' ] to action_list")
        for obj in self._desired_state.all_objects:
            current_obj = self._current_state.get_object_by_object(obj)
            if not current_obj:
                log.debug(f"ADD action of type [ 'ADD' ] for object [ '{str(obj)}' ]")
                solution_object = self._solution_client.get_object_by_object(obj)
                self.action_list.append(
                    DbObjectAction.factory_from_solution_object(
                        solution_object, DbActionType.ADD, desired_instance=obj
                    )
                )
                if obj.object_type.name in PolicyAssignmentObjectTypes._member_names_:
                    self._fill_policy_assignments_handler(
                        current_instance={},
                        desired_instance=obj,
                        object_type=obj.object_type.name,
                        policy_handling_type=PolicyHandlingTypes.NEW_OBJECT
                    )

    def get_drop_actions_from_solution(self) -> None:
        """
        Based on the solution, get all DROP actions and add them to the action_list.
        Add all objects which are in _current_state, but not in the SQL solution.
        """
        log.debug(
            "ADD actions of type [ 'DROP' ] to action_list using information from SOLUTION"
        )
        for obj in self._current_state.all_objects:
            solution_obj = self._solution_client.get_object_by_object(obj)
            if not solution_obj:
                log.debug(f"ADD action of type [ 'DROP' ] for object [ '{str(obj)}' ]")
                self.action_list.append(
                    DbObjectAction.factory_from_instance_object(obj, DbActionType.DROP)
                )

    def get_drop_overloaded_actions(self, drop_overloaded_procedures: bool, drop_overloaded_functions: bool) -> None:
        """
        Get DROPOVERLOADED actions for overloaded objects (e.g. procedures, functions) and add them to the action_list.
        This is required if the user has configured to drop overloaded objects.
        """
        log.debug("ADD actions of type [ 'DROP' ] for overloaded objects to action_list")
        for obj in self._desired_state.all_objects:
            if (
                obj.object_type == DbObjectType.PROCEDURE 
                and drop_overloaded_procedures 
                and obj.id in [action.id for action in self.action_list if action.object_type == DbObjectType.PROCEDURE] # check if the procedure is in the action list to only drop overloaded procedures for which we have an ADD or ALTER action
            ):
                overloaded_procedures = [proc for proc in self._current_state.procedures if proc.name == obj.name and proc.schema == obj.schema]
                for overloaded_proc in overloaded_procedures:
                    log.debug(f"ADD action of type [ 'DROPOVERLOADED' ] for object [ '{str(overloaded_proc)}' ]")
                    self.action_list.append(
                        DbObjectAction.factory_from_instance_object(overloaded_proc, DbActionType.DROPOVERLOADED)
                    )
            elif (
                obj.object_type == DbObjectType.FUNCTION 
                and drop_overloaded_functions
                and obj.id in [action.id for action in self.action_list if action.object_type == DbObjectType.FUNCTION] # check if the function is in the action list to only drop overloaded functions for which we have an ADD or ALTER action
            ):
                overloaded_functions = [func for func in self._current_state.procedures if func.name == obj.name and func.schema == obj.schema]
                for overloaded_func in overloaded_functions:
                    log.debug(f"ADD action of type [ 'DROPOVERLOADED' ] for object [ '{str(overloaded_func)}' ]")
                    self.action_list.append(
                        DbObjectAction.factory_from_instance_object(overloaded_func, DbActionType.DROPOVERLOADED)
                    )

    def get_drop_actions_from_git(self) -> None:
        """
        Based on the git diff, get all DROP actions and add them to the action_list.
        Add all objects which have git change type DELETED and appear in _current_state.
        This function will not add objects which have been RENAMED in git and therefore no longer appear in the solution.
        """
        raise NotImplementedError("Drop actions based on git diff is not implemented.")
        # CODE BELOW DOES NOT WORK: deleted objects do not appear in _solution_client
        # log.debug(f"ADD actions of type [ 'DROP' ] to action_list using information from GIT")
        # for solution_obj in self._solution_client.all_objects:
        #     if solution_obj.git_change_type == 'D': # this does not work: deleted objects do not appear in _solution_client
        #         current_obj = self._current_state.get_object_by_object(solution_obj)
        #         if current_obj:
        #             self._add_to_action_list(current_obj, DbActionType.DROP)

    def get_alter_actions(self) -> None:
        """
        Get ALTER actions and add them to the action_list.
        Go through all objects which appear both in _current_state and in _desired_state.
            - for objects that we will alter via ALTER statement: add to action_list, if difference between boths states detected
            - for all other object (which we will alter via CREATE OR REPLACE statement): add this object to action list.
        """
        log.debug("ADD actions of type [ 'ALTER' ] to action_list")
        for desired_obj in self._desired_state.all_objects:
            current_obj = self._current_state.get_object_by_object(desired_obj)
            if current_obj:
                if current_obj.object_type in (
                    DbObjectType.SCHEMA,
                    DbObjectType.TABLE,
                    DbObjectType.VIEW,
                    DbObjectType.SEQUENCE,
                    DbObjectType.STREAM,
                    DbObjectType.MASKINGPOLICY,
                    DbObjectType.ROWACCESSPOLICY,
                    DbObjectType.PIPE,
                    DbObjectType.STAGE,
                    DbObjectType.FILEFORMAT,
                    DbObjectType.DYNAMICTABLE,
                    DbObjectType.NETWORKRULE,
                    DbObjectType.TAG,
                    # DbObjectType.FUNCTION, # functions can currently not be added here: we do not query all required metadata (e.g. HANDLER, parameter default values)
                    # DbObjectType.PROCEDURE, # procedures can currently not be added here: we do not query all required metadata (e.g. EXECUTE AS, parameter default values)
                    # DbObjectType.MATERIALIZEDVIEW, # materialized views can currently not be added here: we do not query all required metadata (e.g. DEFINITION)
                    # DbObjectType.TASK, # with the current implementation, we can not add tasks here (i.e. conditionally if a change is detected). we currently rely on always adding the full tree if any task in that tree is changed. if we did not add the full tree, we would need to take care of properly suspending tasks in that tree that we do not want to alter.
                    # DbObjectType.MATERIALIZEDTABLE, # materialized tables can currently not be added here: we do not query all required metadata (e.g. AUTO REFRESH)
                ):
                    if current_obj != desired_obj:
                        log.debug(
                            f"ADD action of type [ 'ALTER' ] for object [ '{str(current_obj)}' ]"
                        )
                        solution_object = self._solution_client.get_object_by_object(
                            desired_obj
                        )

                        alter_action= DbObjectAction.factory_from_instance_objects(
                                current_obj,
                                desired_obj,
                                DbActionType.ALTER,
                                file_content=solution_object.content,
                            )

                        self.action_list.append(alter_action)

                        if current_obj.object_type.name in PolicyAssignmentAlterObjectTypes._member_names_:
                            policy_handling_type= PolicyAssignmentAlterObjectTypes.get_policy_handling_type(PolicyAssignmentAlterObjectTypes(current_obj.object_type.name))
                            self._fill_policy_assignments_handler(
                                current_instance=current_obj,
                                desired_instance=desired_obj,
                                object_type=current_obj.object_type.name,
                                policy_handling_type=policy_handling_type
                            )
                else:
                    log.debug(
                        f"ADD action of type [ 'ALTER' ] for object [ '{str(desired_obj)}' ]"
                    )
                    solution_object = self._solution_client.get_object_by_object(
                        desired_obj
                    )
                    if current_obj.object_type == DbObjectType.TASK:
                        self.action_list.append(
                            DbObjectAction.factory_from_solution_object(
                                solution_object,
                                DbActionType.ALTER,
                                state_before_deployment=current_obj.state,
                            )
                        )
                    else:
                        self.action_list.append(
                            DbObjectAction.factory_from_solution_object(
                                solution_object, DbActionType.ALTER
                            )
                        )
