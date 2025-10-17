import logging
import os
from typing import Dict, List, Union, DefaultDict
from collections import defaultdict

import aceutils.file_util as file_util
import aceutils.general_util as gen_util
from acedeploy.core.model_git_entities import GitFile
from acedeploy.core.model_prepostdeploymentsteps import (
    PreOrPostDeploymenStep,
    PreOrPostDeploymentScriptsExecutionOptions,
)
from acedeploy.core.model_solution_entities import (
    SolutionObject,
    SolutionParametersObject,
    SolutionSchema,
)
from acedeploy.core.model_sql_entities import DbObjectType
from aceutils.logger import LoggingAdapter
from acedeploy.core.model_configuration import PreOrPostdeploymentConfigList

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class SolutionClient(object):
    """
    Object that collects all functionality based around the acedeploy physical solution folder.
    All operations and information based upon these files is stored here.
    """

    def __init__(
        self,
        project_folder: str,
        predeployment_folders: List[str] = [],
        postdeployment_folders: List[str] = [],
        predeployment_settings: PreOrPostdeploymentConfigList = PreOrPostdeploymentConfigList(),
        postdeployment_settings: PreOrPostdeploymentConfigList = PreOrPostdeploymentConfigList(),
        prepostdeployment_filter_list: List[str] = None,
        config_schema_list: Dict[str, List[str]] = None,
        config_project_folder_filter: List[str] = None,
        disabled_object_types: List[DbObjectType] = None,
    ) -> None:
        """
            Init a new SolutionClient
        Args:
            project_folder: str - path of the root folder of the SQL project. This folder contains all the schemas.
            DEPRECATED OPTION - predeployment_folders: List[str] = [] - list of folders that contain predeployment scripts
            DEPRECATED OPTION - postdeployment_folders: List[str] = [] - list of folders that contain postdeployment scripts
            predeployment_settings: PreOrPostdeploymentConfigList - Settings for the predeployments
            postdeployment_settings: PreOrPostdeploymentConfigList - Settings for the postdeployments
            prepostdeployment_filter_list: List[str]=[] - optional, list of regular expressions (case insensitive). If any regex matches against the content, an exception will be raised
            schema_list: Dict[str, List[str]] - optional, dict of schemas, either blacklist or whitelist
            config_project_folder_filter: List[str] - optional, list of expressions to match against filenames. matches are removed.
            disabled_object_types: List[DbObjectType] - optional, list of sql object types which are not allowed in the solution
        """
        if (bool(predeployment_folders) or bool(postdeployment_folders)) and (
            bool(predeployment_settings.items) or bool(postdeployment_settings.items)
        ):
            raise ValueError(
                "You can either supply predeployment_folders and postdeployment_folders or predeployment_settings and postdeployment_settings, but not parameters from both pairs at the same time."
            )

        # legacy support for deprecated arguments
        if bool(predeployment_folders) or bool(postdeployment_folders):
            log.warning(
                "The settings 'preDeployment' and 'postDeployment' are deprecated. Consider using 'preDeploymentSettings' and 'postDeploymentSettings' instead"
            )
            predeployment_folders = (
                [] if predeployment_folders is None else predeployment_folders
            )
            postdeployment_folders = (
                [] if postdeployment_folders is None else postdeployment_folders
            )
            self.predeployment_settings = PreOrPostdeploymentConfigList.from_dict(
                [
                    {"path": f, "type": "folder", "condition": "onChange"}
                    for f in predeployment_folders
                ],
                "",
            )
            self.postdeployment_settings = PreOrPostdeploymentConfigList.from_dict(
                [
                    {"path": f, "type": "folder", "condition": "onChange"}
                    for f in postdeployment_folders
                ],
                "",
            )

        else:
            self.predeployment_settings = predeployment_settings
            self.postdeployment_settings = postdeployment_settings
            predeployment_folders = [
                item.full_path
                for item in self.predeployment_settings.items
                if item.type == "folder"
            ]
            postdeployment_folders = [
                item.full_path
                for item in self.postdeployment_settings.items
                if item.type == "folder"
            ]

        self.pre_and_postdeployment_folders = (
            predeployment_folders + postdeployment_folders
        )

        self.project_folder = project_folder
        self.config_schema_list = config_schema_list
        self.all_objects: List[Union[SolutionObject, SolutionSchema]] = []
        self.all_objects_dict_by_full_name: DefaultDict[
            str, List[Union[SolutionObject, SolutionSchema]]
        ] = None
        self.all_objects_dict_by_id: DefaultDict[
            str, List[Union[SolutionObject, SolutionSchema]]
        ] = None
        self.parameterobjects_dict_by_name_without_parameters: DefaultDict[
            str, List[Union[SolutionObject, SolutionSchema]]
        ] = None
        self.postdeployment_steps: List[PreOrPostDeploymenStep] = []
        self.predeployment_steps: List[PreOrPostDeploymenStep] = []

        self.prepostdeployment_filter_list = (
            []
            if prepostdeployment_filter_list is None
            else prepostdeployment_filter_list
        )
        self.config_project_folder_filter = (
            []
            if config_project_folder_filter is None
            else config_project_folder_filter
        )
        self.disabled_object_types = (
            []
            if disabled_object_types is None
            else disabled_object_types
        )

    def load_solution(
        self,
        git_changed_file_list: List[GitFile] = None,
        string_replace_dict: Dict[str, str] = None,
        pre_and_postdeployment_execution=PreOrPostDeploymentScriptsExecutionOptions.NONE,
    ) -> None:
        """
            Wrapper function for loading all file information about a acedeploy solution.
            Will load schemas, tables, views, functions, procedures, fileformats, predeployment steps, postdeployment steps
        Args:
            git_changed_file_list: List[GitFile] - optional, contains information on git changes to files
            string_replace_dict: Dict[str, str] - optional, contains information about strings which need to be replaced in SQL DDLs
            pre_and_postdeployment_execution: PreOrPostDeploymentScriptsExecutionOptions - optional, determines which pre/postdeployment scripts will be executed
        """
        if git_changed_file_list is None:
            git_changed_file_list = []
        if string_replace_dict is None:
            string_replace_dict = {}
        log.info(f"LOAD files from [ '{self.project_folder}' ]")
        if not os.path.exists(self.project_folder):
            raise EnvironmentError(
                f"Solution path [ '{self.project_folder}' ] is not valid"
            )

        folder_list = [f.path for f in os.scandir(self.project_folder) if f.is_dir()]
        ddl_folder_list = [
            f for f in folder_list if f not in self.pre_and_postdeployment_folders
        ]

        git_changed_file_dict = {
            f.file_name: f.change_type for f in git_changed_file_list
        }

        self._load_objects(ddl_folder_list, git_changed_file_dict, string_replace_dict)
        self._validate_object_ids_unique()
        self._validate_solution_objects_included_in_schema_list()
        self._populate_all_objects_dict_by_full_name()
        self._populate_all_objects_dict_by_id()
        self._populate_parameterobjects_dict_by_name_without_parameters()

        self._load_pre_and_postdeployment(
            self.predeployment_settings,
            self.postdeployment_settings,
            git_changed_file_dict,
            string_replace_dict,
            self.prepostdeployment_filter_list,
            pre_and_postdeployment_execution,
        )

        log_message = (
            f"FOUND files in [ '{self.project_folder}' ]: {gen_util.generate_object_log_summaries(self.all_objects)}, "
            + f"{len(self.predeployment_steps)} predeployment step(s), "
            + f"{len(self.postdeployment_steps)} postdeployment step(s)"
        )
        log.info(log_message)

    def _load_objects(
        self,
        ddl_folder_list: List[str],
        git_changed_file_dict: Dict[str, str] = None,
        string_replace_dict: Dict[str, str] = None,
    ) -> None:
        """
            Load all database objects in given folders. (This does not include schemas and pre/postdeployment scripts.)
        Args:
            ddl_folder_list: List[str] - list of folder names (absolute paths) from which objects should be loaded
            git_changed_file_dict - Dict[str, str]: optional, contains information on git changes to files
            string_replace_dict: Dict[str, str] - optional, contains information about strings which need to be replaced in SQL DDLs
        """
        if git_changed_file_dict is None:
            git_changed_file_dict = {}
        if string_replace_dict is None:
            string_replace_dict = {}
        for ddl_folder in ddl_folder_list:
            filelist = file_util.get_filelist(ddl_folder, [".sql"])
            filelist = file_util.filter_filelist_negative(filelist, self.config_project_folder_filter)
            for filepath in filelist:
                obj = SolutionObject.factory(
                    filepath,
                    git_changed_file_dict.get(filepath, None),
                    string_replace_dict,
                )
                if obj:
                    if obj.object_type in self.disabled_object_types:
                        raise ValueError(f"DISABLED type [ '{obj.object_type}' ] for FILE [ '{filepath}' ]")
                    self.all_objects.append(obj)
                else:
                    log.info(f"EXCLUDE file [ '{filepath}' ] from solution")

    def _load_pre_and_postdeployment(
        self,
        predeployment_settings: PreOrPostdeploymentConfigList,
        postdeployment_settings: PreOrPostdeploymentConfigList,
        git_changed_file_dict: Dict[str, str] = None,
        string_replace_dict: Dict[str, str] = None,
        regex_filter_list: List[str] = None,
        pre_and_postdeployment_execution=PreOrPostDeploymentScriptsExecutionOptions.NONE,
    ) -> None:
        """
            Load pre- and postdeployment steps
        Args:
            predeployment_settings: PreOrPostdeploymentConfigList - list of predeployment settings
            postdeployment_settings: PreOrPostdeploymentConfigList - list of predeployment settings
            git_changed_file_dict - Dict[str, str]: optional, contains information on git changes to files
            string_replace_dict: Dict[str, str] - optional, contains information about strings which need to be replaced in SQL DDLs
            regex_filter_list: List[str]=[] - optional, contains a list of regular expressions (case insensitive). If any regex matches against the content, an exception will be raised
            pre_and_postdeployment_execution: PreOrPostDeploymentScriptsExecutionOptions - optional, determines which pre/postdeployment scripts will be executed
        """
        if git_changed_file_dict is None:
            git_changed_file_dict = {}
        if string_replace_dict is None:
            string_replace_dict = {}
        if regex_filter_list is None:
            regex_filter_list = []
        self.predeployment_steps = SolutionClient._get_pre_or_postdeployment_steps(
            predeployment_settings,
            git_changed_file_dict,
            string_replace_dict,
            regex_filter_list,
            pre_and_postdeployment_execution,
        )
        self.postdeployment_steps = SolutionClient._get_pre_or_postdeployment_steps(
            postdeployment_settings,
            git_changed_file_dict,
            string_replace_dict,
            regex_filter_list,
            pre_and_postdeployment_execution,
        )

    @staticmethod
    def _get_pre_or_postdeployment_steps(
        prepostdeployment_settings: PreOrPostdeploymentConfigList,
        git_changed_file_dict: Dict[str, str] = None,
        string_replace_dict: Dict[str, str] = None,
        regex_filter_list: List[str] = None,
        pre_and_postdeployment_execution=PreOrPostDeploymentScriptsExecutionOptions.NONE,
    ) -> List[PreOrPostDeploymenStep]:
        """
            Return pre- or postdeployment steps for given config.
        Args:
            prepostdeployment_settings: PreOrPostdeploymentConfigList - list of predeployment settings
            git_changed_file_dict - Dict[str, str]: optional, contains information on git changes to files
            string_replace_dict: Dict[str, str] - optional, contains information about strings which need to be replaced in SQL DDLs
            regex_filter_list: List[str]=[] - optional, contains a list of regular expressions (case insensitive). If any regex matches against the content, an exception will be raised
            pre_and_postdeployment_execution: PreOrPostDeploymentScriptsExecutionOptions - optional, determines which pre/postdeployment scripts will be executed
        """
        if git_changed_file_dict is None:
            git_changed_file_dict = {}
        if string_replace_dict is None:
            string_replace_dict = {}
        if regex_filter_list is None:
            regex_filter_list = []

        steps = []
        for pp_setting in prepostdeployment_settings.items:
            if pp_setting.type == "folder":
                all_files = []
                for root, __, files in os.walk(pp_setting.full_path):
                    for name in files:
                        all_files.append(os.path.join(root, name))

                sorted_files = sorted(all_files)
                for step_path in sorted_files:
                    step = PreOrPostDeploymenStep(
                        path=step_path,
                        git_change_type=git_changed_file_dict.get(step_path, None),
                        string_replace_dict=string_replace_dict,
                        regex_filter_list=regex_filter_list,
                    )
                    step.set_target(pp_setting.target)
                    step.set_execute_step(
                        pre_and_postdeployment_execution, pp_setting.condition
                    )
                    log.debug(
                        f"ADD pre/postdeployment step [ '{step.path}' ] with execute_step set to [ '{step.execute_step}' ]"
                    )
                    steps.append(step)
            else:
                raise ValueError("Pre/postdeployment setting type can only be 'folder'")
        return steps

    def _populate_all_objects_dict_by_full_name(self) -> None:
        self.all_objects_dict_by_full_name: DefaultDict[
            str, List[Union[SolutionObject, SolutionSchema]]
        ] = defaultdict(list)
        for obj in self.all_objects:
            self.all_objects_dict_by_full_name[obj.full_name].append(obj)

    def _populate_all_objects_dict_by_id(self) -> None:
        self.all_objects_dict_by_id: DefaultDict[
            str, List[Union[SolutionObject, SolutionSchema]]
        ] = defaultdict(list)
        for obj in self.all_objects:
            self.all_objects_dict_by_id[obj.id].append(obj)

    def _populate_parameterobjects_dict_by_name_without_parameters(self) -> None:
        self.parameterobjects_dict_by_name_without_parameters: DefaultDict[
            str, List[Union[SolutionObject, SolutionSchema]]
        ] = defaultdict(list)
        for obj in self.all_objects:
            if obj.object_type in (DbObjectType.FUNCTION, DbObjectType.PROCEDURE):
                self.parameterobjects_dict_by_name_without_parameters[
                    obj.name_without_params
                ].append(obj)

    def get_object_by_id(self, object_id: str) -> SolutionObject:
        """
            Return the InstanceObject for the given object_id.
        Args:
            id: str
        """
        result = self.all_objects_dict_by_id[object_id.replace('"', "")]
        if len(result) == 0:
            log.debug(f"OBJECT with [ id='{object_id}' ] NOT in FOUND in solution")
            return None
        elif len(result) > 1:
            raise ValueError(
                f"OBJECT with [ id='{object_id}' ] NOT UNIQUE in solution. Found [ '{len(result)}' ]"
            )
        else:
            return result[0]

    def get_object_by_full_name(self, full_name: str, include_schemas: bool = True) -> SolutionObject:
        """
            Return the SolutionObject for the given object full_name
        Args:
            full_name: str
            include_schemas: bool - Optional (default True), include schemas in the result
        """
        result = self.all_objects_dict_by_full_name[full_name.upper().replace('"', "")]
        if not include_schemas:
            result = [r for r in result if r.object_type != DbObjectType.SCHEMA]
        if len(result) == 0:
            log.debug(f"OBJECT with name [ '{full_name}' ] NOT in FOUND in solution")
            return None
        elif len(result) > 1:
            raise ValueError(
                f"OBJECT with name [ '{full_name}' ] NOT UNIQUE in solution. Found [ '{len(result)}' ]"
            )
        else:
            return result[0]

    def get_parameterobject_by_name_without_params(
        self, name_without_params: str
    ) -> SolutionParametersObject:
        """
            Return the SolutionParametersObject function for the given object name_without_params without the function parameters
        Args:
            name_without_params: str - Name of the function or procedure without parameters, i.e. schema.parameters
        """
        result = self.parameterobjects_dict_by_name_without_parameters[
            name_without_params.upper().replace('"', "")
        ]
        if len(result) == 0:
            log.debug(
                f"OBJECT with name [ '{name_without_params}' ] NOT in FOUND in solution"
            )
            return None
        elif len(result) > 1:
            raise ValueError(
                f"OBJECT with name [ '{name_without_params}' ] NOT UNIQUE in solution. Found [ '{len(result)}' ]"
            )
        else:
            return result[0]

    # todo: richtigen type angeben
    def get_object_by_object(self, obj: SolutionObject) -> SolutionObject:
        """
        Return the matching SolutionObject for the given obj.
        Compares the id of the object.
        """
        return self.get_object_by_id(obj.id)

    def _validate_object_ids_unique(self) -> None:
        """
        Validate that each object id in the solution client is unique.
        Raise exception if not.
        """
        seen = set()
        seen_objects = set()
        duplicates = []
        for obj in self.all_objects:
            if obj.id not in seen:
                seen.add(obj.id)
                seen_objects.add(obj)
            else:
                duplicates.append([o for o in seen_objects if o.id == obj.id][0])
                duplicates.append(obj)
        for obj in duplicates:
            log.info(f"DUPLICATE object [ '{obj.id}' ] in FILE [ '{obj.path}' ]")
        if len(duplicates) > 0:
            raise ValueError(
                "DUPLICATE OBJECTS DETECTED. Object ids (type + schema + name) must be unique."
            )

    def _validate_solution_objects_included_in_schema_list(self):
        """
        Validate if the all loaded solution objects are located in schemas allowed by config_schema_list
        """
        if self.config_schema_list:
            objects_in_filtered_schemas = self._get_solution_objects_not_in_schema_list(
                self.all_objects, self.config_schema_list
            )
            if len(objects_in_filtered_schemas) > 0:
                object_names = [o.full_name for o in objects_in_filtered_schemas]
                raise ValueError(
                    f"OBJECTS [ '{object_names}' ] are NOT ALLOWED by setting projectSchemas [ '{self.config_schema_list}' ]"
                )

    @staticmethod
    def _get_solution_objects_not_in_schema_list(
        solution_objects: List[Union[SolutionObject, SolutionSchema]],
        schema_list: Dict[str, List[str]],
    ) -> List[SolutionObject]:
        """
        Return a list of all solution objects, which are not in schemas allowed by schema_list.

        solution_objects: List of solution objects
        schema_list: Dict[str, List[str]]: dict of schemas, either blacklist or whitelist
        """
        if "whitelist" in schema_list:
            schemas_whitelist = [s.upper() for s in schema_list["whitelist"]]
            objects_in_wrong_schema = [
                o for o in solution_objects if o.schema.upper() not in schemas_whitelist
            ]

        elif "blacklist" in schema_list:
            schemas_blacklist = [s.upper() for s in schema_list["blacklist"]]
            objects_in_wrong_schema = [
                o for o in solution_objects if o.schema.upper() in schemas_blacklist
            ]

        else:
            raise EnvironmentError(
                "MALFORMED config value [ 'schema_list' ] (contains neither blacklist nor whitelist)"
            )
        return objects_in_wrong_schema
