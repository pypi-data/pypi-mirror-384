import logging
from typing import List

from aceaccount.core.model_account_object_action_entities import AccountObjectAction
from aceaccount.core.model_account_object_sql_entities import AccountObjectActionType
from aceaccount.services.account_objects_metadata_service import AccountMetadataService
from aceaccount.services.account_objects_solution_service import AccountSolutionClient
from aceservices.snowflake_service import SnowClientConfig
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class AccountObjectCompareClient(object):
    """
    Compare the state of the account objects (current state) to the input file (desired state).
    Generate a list of actions to change current state into desired state.
    """

    def __init__(
        self,
        desired_state: AccountSolutionClient,
        current_state: AccountMetadataService,
        snow_client_config: SnowClientConfig
    ) -> None:
        """
            Inits a new DbCompareClient
        Args:
            desired_state: AccountMetadataService - State that should be achieved as defined by the input file
            current_state: MetadataService - Current account state
        """
        self._desired_state = desired_state
        self._current_state = current_state
        self._snow_client_config = snow_client_config
        self._action_list = []
        self._grant_action_list = []
        self._tag_action_list = []

    @property
    def action_list(self) -> List[AccountObjectAction]:
        return self._action_list
    
    @property
    def grant_action_list(self) -> List[AccountObjectAction]:
        return self._grant_action_list
    
    @property
    def tag_action_list(self) -> List[AccountObjectAction]:
        return self._tag_action_list

    def generate_add_actions(self) -> None:
        """
        Get all ADD actions and add them to action list.
        Add all objects that are in _desired_state, but not in _current_state.
        """
        log.debug("ADD actions of type [ 'ADD' ] to action_list")
        for desired_obj in self._desired_state.all_account_objects:
            current_obj = self._current_state.get_object_by_object(desired_obj)
            if not current_obj:
                log.debug(
                    f"ADD action of type [ 'ADD' ] for object [ '{str(desired_obj)}' ]"
                )
                self.action_list.append(
                    AccountObjectAction.factory(
                        name=desired_obj.name,
                        object_type=desired_obj.object_type,
                        action_type=AccountObjectActionType.ADD,
                        snow_client_config=self._snow_client_config,
                        desired_instance=desired_obj,
                    )
                )

    def generate_drop_actions(self, drop_enabled: dict) -> None:
        """
        Get all ADD actions and add them to action list.
        Add all objects that are in _current_state, but not in _desired_state.
        """
        log.debug("ADD actions of type [ 'DROP' ] to action_list")
        for current_obj in self._current_state.all_account_objects:
            desired_obj = self._desired_state.get_object_by_object(current_obj)

            if current_obj.object_type.value not in drop_enabled:
                raise ValueError(f"No dropEnabled parameter-configuration for the AccountObjectType {current_obj.object_type.value} found. Please adjust the config.json !")
            
            elif not desired_obj and drop_enabled[current_obj.object_type.value]:
                log.debug(
                    f"ADD action of type [ 'DROP' ] for object [ '{str(current_obj)}' ]"
                )
                self.action_list.append(
                    AccountObjectAction.factory(
                        name=current_obj.name,
                        object_type=current_obj.object_type,
                        action_type=AccountObjectActionType.DROP,
                        snow_client_config=self._snow_client_config,
                        current_instance=current_obj,
                    )
                )

    def generate_alter_actions(self) -> None:
        """
        Get all ADD actions and add them to action list.
        Add all objects that have different states in _current_state and in _desired_state.
        """
        log.debug("ADD actions of type [ 'ALTER' ] to action_list")
        for current_obj in self._current_state.all_account_objects:
            desired_obj = self._desired_state.get_object_by_object(current_obj)
            if (desired_obj is not None) and (desired_obj != current_obj):
                log.debug(
                    f"ADD action of type [ 'ALTER' ] for object [ '{str(current_obj)}' ]"
                )
                self.action_list.append(
                    AccountObjectAction.factory(
                        name=current_obj.name,
                        object_type=current_obj.object_type,
                        action_type=AccountObjectActionType.ALTER,
                        snow_client_config=self._snow_client_config,
                        current_instance=current_obj,
                        desired_instance=desired_obj,
                    )
                )

    def generate_grant_actions(self) -> None:
        """
        Get all GRANT actions and add them to action list.
        Add all grants that are in _desired_state, but not in _current_state.
        """
        log.debug("ADD actions of type [ 'GRANT' ] to action_list")
        for current_obj in self._current_state.all_account_objects:
            desired_obj = self._desired_state.get_object_by_object(current_obj)
            if (desired_obj is not None) and  hasattr(desired_obj, "grants") and desired_obj.grants:
                if  (not hasattr(current_obj, "grants") or ({key:set(value) for key,value in desired_obj.grants.items()} != {key:set(value) for key,value in current_obj.grants.items()})):
                    log.debug(
                        f"ADD action of type [ 'GRANT' ] for object [ '{str(current_obj)}' ]"
                    )
                    self.grant_action_list.append(
                        AccountObjectAction.factory(
                            name=current_obj.name,
                            object_type=current_obj.object_type,
                            action_type=AccountObjectActionType.GRANT,
                            snow_client_config=self._snow_client_config,
                            current_instance=current_obj,
                            desired_instance=desired_obj,
                        )
                    )

    def generate_revoke_actions(self) -> None:
        """
        Get all REVOKE actions and add them to action list.
        Add all grants that are in _current_state, but not in _desired_state.
        """
        log.debug("ADD actions of type [ 'REVOKE' ] to action_list")
        for current_obj in self._current_state.all_account_objects:
            desired_obj = self._desired_state.get_object_by_object(current_obj)
            if (desired_obj is not None) and hasattr(current_obj, "grants") and current_obj.grants:
                if hasattr(desired_obj, "grants") and ({key:set(value) for key,value in desired_obj.grants.items()} != {key:set(value) for key,value in current_obj.grants.items()}):
                    log.debug(
                        f"ADD action of type [ 'REVOKE' ] for object [ '{str(current_obj)}' ]"
                    )
                    self.grant_action_list.append(
                        AccountObjectAction.factory(
                            name=current_obj.name,
                            object_type=current_obj.object_type,
                            action_type=AccountObjectActionType.REVOKE,
                            snow_client_config=self._snow_client_config,
                            current_instance=current_obj,
                            desired_instance=desired_obj,
                        )
                    )

    def generate_settag_actions(self) -> None:
        """
        Get all SETTAG actions and add them to action list.
        Add all tags that are in _desired_state, but not in _current_state.
        """
        log.debug("ADD actions of type [ 'SETTAG' ] to action_list")
        for current_obj in self._current_state.all_account_objects:
            desired_obj = self._desired_state.get_object_by_object(current_obj)
            if (desired_obj is not None) and hasattr(desired_obj, "tags") and desired_obj.tags:
                if (not hasattr(current_obj, "tags") or ({key.upper():value for key,value in desired_obj.tags.items()} != {key.upper():value for key,value in current_obj.tags.items()})):
                    log.debug(
                        f"ADD action of type [ 'SETTAG' ] for object [ '{str(current_obj)}' ]"
                    )
                    self.tag_action_list.append(
                        AccountObjectAction.factory(
                            name=current_obj.name,
                            object_type=current_obj.object_type,
                            action_type=AccountObjectActionType.SETTAG,
                            snow_client_config=self._snow_client_config,
                            current_instance=current_obj,
                            desired_instance=desired_obj,
                        )
                    )

    def generate_unsettag_actions(self) -> None:
        """
        Get all UNSETTAG actions and add them to action list.
        Add all tags that are in _current_state, but not in _desired_state.
        """
        log.debug("ADD actions of type [ 'UNSETTAG' ] to action_list")
        for current_obj in self._current_state.all_account_objects:
            desired_obj = self._desired_state.get_object_by_object(current_obj)
            if (desired_obj is not None) and hasattr(current_obj, "tags") and current_obj.tags:
                if hasattr(desired_obj, "tags") and ({key.upper():value for key,value in desired_obj.tags.items()} != {key.upper():value for key,value in current_obj.tags.items()}):
                    log.debug(
                        f"ADD action of type [ 'UNSETTAG' ] for object [ '{str(current_obj)}' ]"
                    )
                    self.tag_action_list.append(
                        AccountObjectAction.factory(
                            name=current_obj.name,
                            object_type=current_obj.object_type,
                            action_type=AccountObjectActionType.UNSETTAG,
                            snow_client_config=self._snow_client_config,
                            current_instance=current_obj,
                            desired_instance=desired_obj,
                        )
                    )