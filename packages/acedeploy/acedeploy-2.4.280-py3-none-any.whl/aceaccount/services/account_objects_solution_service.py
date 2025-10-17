import logging
import os
import json
from typing import Dict, List, Union

import aceutils.file_util as file_util
import aceutils.general_util as gen_util
from aceaccount.core.model_account_object_sql_entities import AccountObjectType
from aceutils.logger import LoggingAdapter
from aceaccount.core.model_account_object_instances import AccountObjectInstance

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class AccountSolutionClient(object):
    """
    Object that collects all functionality based around the physical account object solution folder.
    All operations and information based upon these files is stored here.
    """

    def __init__(
        self,
        enabled_object_types: list,
        source_files: list,
    ) -> None:
        """
            Init a new SolutionClient
        Args:
            source_files: list - list of paths of the solution definitions
        """
        self._enabled_object_types = enabled_object_types
        self.source_files = source_files
        self.all_account_objects: List[AccountObjectInstance] = []
        self._load_solutions()

    def _dict_raise_on_duplicates(schema, ordered_pairs):
        """Reject duplicate keys."""
        d = {}
        for k, v in ordered_pairs:
            if k in d:
                raise ValueError("duplicate key: %r" % (k,))
            else:
                d[k] = v
        return d

    def _load_solutions(
        self,
    ) -> None:
        """
        Load the solutions form the source files
        """
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # validate source file paths
        for source_file in self.source_files:
            if not os.path.isfile(source_file):
                raise EnvironmentError(
                    f"Solution path [ '{source_file}' ] is not valid"
                )

        mapping = {  # maps the name/key of the dict entry in the source file to the AccountObjectType
            "storage_integrations": AccountObjectType.STORAGEINTEGRATION,
            "warehouses": AccountObjectType.WAREHOUSE,
            "shares": AccountObjectType.SHARE,
            "databases": AccountObjectType.DATABASE,
            "external_volumes": AccountObjectType.EXTERNALVOLUME,
        }
        
        # load source files
        loaded_source_files = []
        
        for source_file in self.source_files:
            log.info(f"LOAD solution from [ '{source_file}' ]")

            source_dict = json.loads(
                file_util.load(source_file),
                object_pairs_hook=self._dict_raise_on_duplicates,
            )

            source_file_account_objects=[]

            for object_type_name in source_dict:
                if not object_type_name == "$schema":
                    if object_type_name not in mapping:
                        raise ValueError(
                            f"Error loading the solution: '{object_type_name}' is not in the list of the following supported object types: {[k for k in mapping]}"
                        )
                    
                    if mapping[object_type_name].value not in self._enabled_object_types:
                        log.debug(
                            f"SKIPPING disabled object type: {mapping[object_type_name].value}"
                        )
                        continue

                    for name, definition in source_dict[object_type_name].items():
                        account_object_instance = self._generate_account_object_instance(mapping[object_type_name], name, definition)
                        if not account_object_instance.id in [account_object.id for account_object in self.all_account_objects]:
                            source_file_account_objects.append(account_object_instance)
                            self.all_account_objects.append(account_object_instance)
                        else:
                            raise ValueError(
                                f"Error loading the solution {source_file} -> duplicate found: \n Account object of type '{object_type_name}' and name '{name}' already loaded. \n Please also check the previously loaded files to find the duplicate -> {loaded_source_files}"
                            )

            log.info(
                f"FOUND objects in [ '{source_file}' ]: {gen_util.generate_account_object_log_summaries(source_file_account_objects)}"
            )
            loaded_source_files.append(source_file)

        log.info(
            f"FOUND objects in all input files: {gen_util.generate_account_object_log_summaries(self.all_account_objects)}"
        )
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        

    def _generate_account_object_instance(self, object_type, name, definition):
        definition["name"] = name
        return AccountObjectInstance.factory(
            object_type=object_type,
            metadata_query_result=definition,
        )

    def get_object_by_object(self, obj: AccountObjectInstance) -> AccountObjectInstance:
        """
        Return the matching AccountObjectInstance for the given obj.
        Compares the id of the object.
        """
        return self.get_object_by_id(obj.id)

    def get_object_by_id(self, object_id: str) -> AccountObjectInstance:
        """
            Return the AccountObjectInstance for the given object_id.
        Args:
            id: str
        """
        result = [o for o in self.all_account_objects if (o.compare_id(object_id))]
        if len(result) == 0:
            log.debug(f"OBJECT with [ id='{object_id}' ] NOT in FOUND in solution")
            return None
        elif len(result) > 1:
            raise ValueError(
                f"OBJECT with [ id='{object_id}' ] NOT UNIQUE in solution. Found [ '{len(result)}' ]"
            )
        else:
            return result[0]
