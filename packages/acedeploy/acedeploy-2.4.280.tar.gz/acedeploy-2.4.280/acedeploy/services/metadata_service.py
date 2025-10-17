import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Union, DefaultDict
from collections import defaultdict  

import aceutils.file_util as file_util
import aceutils.string_util as string_util
import aceutils.parallelization_util as parallelization_util
from acedeploy.core.model_instance_objects import InstanceObject
from acedeploy.core.model_sql_entities import DbObjectType
from acedeploy.core.model_configuration import ObjectOption
from aceservices.snowflake_service import SnowClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class MetadataService:
    """
    Class to query metadata information from snowflake.
    An instance of this class is scoped to a single database (defined by the given snow_client)
    """

    def __init__(
        self,
        snow_client: SnowClient,
        snow_edition: str = "Enterprise",
        disabled_object_types: List[DbObjectType] = [], # TODO: consider removing this and referencing the information from object_options instead
        object_options: Dict[DbObjectType, ObjectOption] = None,
        workarounds_options: Dict = {}
    ):
        """
            Inits a metadata service.
        Args:
            snow_client: SnowClient - provides connection a snowflake database
            snow_edition: str - Edition of the Snowflake account, "Enterprise" or "Standard"
            disabled_object_types: List[DbObjectType] - List of sql object types for which no metadata should be queried
            object_options: Dict[DbObjectType, ObjectOption] - Dict of object options (e.g. whether tags should be queried for each type)
        """
        self._snow_client = snow_client
        self._snow_edition = snow_edition
        self._disabled_object_types = disabled_object_types
        self._object_options = object_options
        self._workarounds_options = workarounds_options
        module_root_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self._sql_files_path = os.path.abspath(
            os.path.join(module_root_folder, "resources", "sql")
        )
        self.all_objects = []        
        self.all_objects_dict_by_id = None
        self.database_name = None
        self.check_for_language_restrictions = None

    def get_all_objects_subset(self, object_type: DbObjectType):
        return [o for o in self.all_objects if o.object_type == object_type]

    @property
    def schemas(self):
        return self.get_all_objects_subset(DbObjectType.SCHEMA)

    @property
    def tables(self):
        return self.get_all_objects_subset(DbObjectType.TABLE)

    @property
    def externaltables(self):
        return self.get_all_objects_subset(DbObjectType.EXTERNALTABLE)

    @property
    def views(self):
        return self.get_all_objects_subset(DbObjectType.VIEW)

    @property
    def materializedviews(self):
        return self.get_all_objects_subset(DbObjectType.MATERIALIZEDVIEW)

    @property
    def functions(self):
        return self.get_all_objects_subset(DbObjectType.FUNCTION)

    @property
    def procedures(self):
        return self.get_all_objects_subset(DbObjectType.PROCEDURE)

    @property
    def fileformats(self):
        return self.get_all_objects_subset(DbObjectType.FILEFORMAT)

    @property
    def stages(self):
        return self.get_all_objects_subset(DbObjectType.STAGE)

    @property
    def streams(self):
        return self.get_all_objects_subset(DbObjectType.STREAM)

    @property
    def tasks(self):
        return self.get_all_objects_subset(DbObjectType.TASK)

    @property
    def pipes(self):
        return self.get_all_objects_subset(DbObjectType.PIPE)

    @property
    def sequences(self):
        return self.get_all_objects_subset(DbObjectType.SEQUENCE)

    @property
    def maskingpolicies(self):
        return self.get_all_objects_subset(DbObjectType.MASKINGPOLICY)

    @property
    def rowaccesspolicies(self):
        return self.get_all_objects_subset(DbObjectType.ROWACCESSPOLICY)
    
    @property
    def dynamictables(self):
        return self.get_all_objects_subset(DbObjectType.DYNAMICTABLE)
    
    @property
    def networkrules(self):
        return self.get_all_objects_subset(DbObjectType.NETWORKRULE)

    @property
    def tags(self):
        return self.get_all_objects_subset(DbObjectType.TAG)


    def get_object_by_object(self, obj: InstanceObject) -> InstanceObject:
        """
        Return the matching InstanceObject for the given obj.
        Compares the id of the object.
        """
        return self.get_object_by_id(obj.id)

    def get_object_by_id(self, object_id: str) -> InstanceObject:
        """
        Return the InstanceObject for the given object_id.
        """
        result = self.all_objects_dict_by_id[object_id.replace('"', "")]
        if len(result) == 0:
            log.debug(
                f"OBJECT with [ id='{object_id}' ] NOT in FOUND in MetadataService"
            )
            return None
        elif len(result) > 1:
            raise ValueError(
                f"OBJECT with [ id='{object_id}' ] NOT UNIQUE in MetadataService. Found [ '{len(result)}' ]"
            )
        else:
            return result[0]
        
    def _populate_all_objects_dict_by_id(self) -> None:
        self.all_objects_dict_by_id = defaultdict(list)
        for obj in self.all_objects:
            self.all_objects_dict_by_id[obj.id].append(obj)

    def get_all_metadata(
        self,
        schema_list: Dict[str, List[str]],
        parallel_threads: int = 1,
        get_policies_on_objects_legacy: bool = False,
        check_for_language_restrictions: bool = None, 
    ) -> None:
        """
        Get all metadata information (schemas, tables+views and other objects) from the database.
        """
        log.info(f"QUERY object information ON [ '{self._snow_client.database}' ].")

        mapping = {
            DbObjectType.SCHEMA: self._get_metadata_schemas,
            DbObjectType.FUNCTION: self._get_metadata_functions,
            DbObjectType.PROCEDURE: self._get_metadata_procedures,
            DbObjectType.FILEFORMAT: self._get_metadata_fileformats,
            DbObjectType.STREAM: self._get_metadata_streams,
            DbObjectType.TASK: self._get_metadata_tasks,
            DbObjectType.SEQUENCE: self._get_metadata_sequences,
            DbObjectType.MATERIALIZEDVIEW: self._get_metadata_materializedviews,
            DbObjectType.TABLE: self._get_metadata_tables,
            DbObjectType.EXTERNALTABLE: self._get_metadata_externaltables,
            DbObjectType.VIEW: self._get_metadata_views,
            DbObjectType.STAGE: self._get_metadata_stages,
            DbObjectType.PIPE: self._get_metadata_pipes,
            DbObjectType.MASKINGPOLICY: self._get_metadata_maskingpolicies,
            DbObjectType.ROWACCESSPOLICY: self._get_metadata_rowaccesspolicies,
            DbObjectType.DYNAMICTABLE: self._get_metadata_dynamictables,
            DbObjectType.NETWORKRULE: self._get_metadata_networkrules,
            DbObjectType.TAG: self._get_metadata_tags,
        }

        self.database_name = self._snow_client.database
        self.check_for_language_restrictions = check_for_language_restrictions
        self._get_policies_on_objects_legacy = get_policies_on_objects_legacy

        schemas_to_query = self._get_filtered_schema_name_list(schema_list)

        if self._object_options is not None and any([getattr(oo, "manageRowAccessPolicyReferences", False) for oo in self._object_options.values()]):
            row_access_policy_references = self._get_row_access_policy_references(schemas_to_query, parallel_threads)

        if self._object_options is not None and any([getattr(oo, "manageMaskingPolicyReferences", False) for oo in self._object_options.values()]):
            masking_policy_references = self._get_masking_policy_references(schemas_to_query, parallel_threads)

        for object_type, metadata_function in mapping.items():
            if object_type not in self._disabled_object_types:
                log.info(f"QUERY object information FOR type [ '{object_type}' ]")
                metadata_list = metadata_function(schemas_to_query, parallel_threads)
                if self._object_options is not None and getattr(self._object_options[object_type], "manageRowAccessPolicyReferences", False):
                    metadata_list = self._extend_metadata_policyreferences(metadata_list, row_access_policy_references[object_type])
                if self._object_options is not None and getattr(self._object_options[object_type], "manageMaskingPolicyReferences", False):
                    metadata_list = self._extend_metadata_policyreferences(metadata_list, masking_policy_references[object_type])
                if self._object_options is not None:
                    metadata_list = self._update_metadata_using_object_options(metadata_list, getattr(self._object_options[object_type], "metadataOptions", {}))
                self.all_objects.extend(
                    [InstanceObject.factory(
                        object_type=object_type,
                        metadata_query_result=m,
                        object_options=self._object_options[object_type] if self._object_options is not None else None,
                    ) for m in metadata_list]
                )            
        self._populate_all_objects_dict_by_id()


    def _extend_metadata_policyreferences(self, metadata_list: List[Dict], policy_references: List[Dict]):
        for obj in metadata_list:
            refs = [
                ref for ref in policy_references if (
                    ref["REF_DATABASE_NAME"] == obj["DATABASE_NAME"]
                    and ref["REF_SCHEMA_NAME"] == obj["SCHEMA_NAME"]
                    and ref["REF_ENTITY_NAME"] == obj["OBJECT_NAME"]
                )
            ]
            if "policy_references" in obj:
                obj["policy_references"].extend(refs)
            else:
                obj["policy_references"] = refs
        return metadata_list

    @staticmethod
    def _update_metadata_using_object_options(metadata_list: List[Dict], metadata_options: Dict[str, Union[Dict[str, str], Dict[str, Dict[str, str]]]]):
        """
            Given a list of metadata, update certain fields according to the metadata options.
        """
        def _update_single_property(this_options: Dict, this_obj: any, this_property: str):
            for option_key, option_value in this_options.items():
                if option_key == "ignore":
                    if option_value:
                        this_obj[this_property] = None # TODO: take care of data type
                else:
                    raise ValueError(f"Unknown metadataOption '{option_key}'")

        for obj in metadata_list:
            for property, options in metadata_options.items():
                if property == "COLUMN_DETAILS":
                    for subproperty, suboptions in metadata_options[property].items():
                        for col in obj[property]:
                            _update_single_property(suboptions, col, subproperty)
                else:
                    _update_single_property(options, obj, property)

        return metadata_list



    def _get_row_access_policy_references(self, schemas_to_query, parallel_threads) -> Dict[DbObjectType, List[Dict]]:
        log.debug(f"QUERY row access policy references")
        if self._snow_edition == "Standard":
            return []
        template_path = os.path.join(
            self._sql_files_path, "get_rowaccesspolicy_names.sql"
        )
        object_type = DbObjectType.ROWACCESSPOLICY
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._extend_metadata_policy_references(metadata_list)

        # at this point, we only care about entries in the policy_references field
        # the actual policy metadata is fetched in another function
        row_access_policy_references_list = []
        for metadata_entry in metadata_list:
            row_access_policy_references_list.extend(metadata_entry["references"])

        row_access_policy_references = {}
        for object_type, object_option in self._object_options.items():
            if getattr(object_option, "manageRowAccessPolicyReferences", False):
                row_access_policy_references[object_type] = [ref for ref in row_access_policy_references_list if object_type == DbObjectType.get_object_type_for_policy_references(ref["REF_ENTITY_DOMAIN"])]
            else:
                row_access_policy_references[object_type] = []

        return row_access_policy_references

    def _get_masking_policy_references(self, schemas_to_query, parallel_threads) -> Dict[DbObjectType, List[Dict]]:
        log.debug(f"QUERY masking policy references")
        if self._snow_edition == "Standard":
            return []
        template_path = os.path.join(
            self._sql_files_path, "get_maskingpolicy_names.sql"
        )
        object_type = DbObjectType.MASKINGPOLICY
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._extend_metadata_policy_references(metadata_list)

        # at this point, we only care about entries in the policy_references field
        # the actual policy metadata is fetched in another function
        masking_policy_references_list = []
        for metadata_entry in metadata_list:
            masking_policy_references_list.extend(metadata_entry["references"])

        masking_policy_references = {}
        for object_type, object_option in self._object_options.items():
            if getattr(object_option, "manageMaskingPolicyReferences", False):
                masking_policy_references[object_type] = [ref for ref in masking_policy_references_list if object_type == DbObjectType.get_object_type_for_policy_references(ref["REF_ENTITY_DOMAIN"])]
            else:
                masking_policy_references[object_type] = []

        return masking_policy_references

    def _get_metadata_schemas(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_schemas.sql")
        object_type = DbObjectType.SCHEMA
        return self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )

    def _get_metadata_functions(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_functions.sql")
        object_type = DbObjectType.FUNCTION
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )  # note: metadata details are currently not evaluated, see db_compare_service.py

        # check for disabled languages
        if self._object_options and self.check_for_language_restrictions:
            for udf in metadata_list:
                if udf["LANGUAGE"].upper() in self._object_options[object_type].disabledLanguages:
                    raise ValueError(f'The usage of language {udf["LANGUAGE"]} for User-Defined Functions is disabled! Detected in UDF: {udf["DATABASE_NAME"]}.{udf["SCHEMA_NAME"]}.{udf["OBJECT_NAME"]}')
        return metadata_list

    def _get_metadata_procedures(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_procedures.sql"
        )
        object_type = DbObjectType.PROCEDURE
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )  # note: metadata details are currently not evaluated, see db_compare_service.py

        # check for disabled languages
        if self._object_options and self.check_for_language_restrictions:
            for procedure in metadata_list:
                if procedure["LANGUAGE"].upper() in self._object_options[object_type].disabledLanguages:
                    raise ValueError(f'The usage of language {procedure["LANGUAGE"]} for Stored Procedures is disabled! Detected in Stored Procedure: {procedure["DATABASE_NAME"]}.{procedure["SCHEMA_NAME"]}.{procedure["OBJECT_NAME"]}')
        return metadata_list

    def _get_metadata_fileformats(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_fileformats.sql"
        )
        object_type = DbObjectType.FILEFORMAT
        return self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )

    def _get_metadata_streams(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_streams.sql")
        object_type = DbObjectType.STREAM
        return self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )

    def _get_metadata_tasks(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_tasks.sql")
        object_type = DbObjectType.TASK
        return self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )  # note: metadata details are currently not evaluated, see db_compare_service.py

    def _get_metadata_sequences(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_sequences.sql")
        object_type = DbObjectType.SEQUENCE
        return self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )

    def _get_metadata_materializedviews(self, schemas_to_query, parallel_threads):
        if self._snow_edition == "Standard":
            return []
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_materializedviews.sql"
        )
        object_type = DbObjectType.MATERIALIZEDVIEW
        metadata_list= self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )  # note: metadata details are currently not evaluated, see db_compare_service.py

        self._convert_column_details_to_dict(metadata_list)

        if self._object_options is not None and self._object_options[object_type].manageTagAssignments:
            metadata_list = self._extend_metadata_with_tags(metadata_list, parallel_threads, object_type)
        return metadata_list

    def _get_metadata_tables(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_tables.sql")
        object_type = DbObjectType.TABLE
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._get_constraint_metadata(
            schemas_to_query, parallel_threads, metadata_list
        )


        self._convert_column_details_to_dict(metadata_list)

        if self._object_options is not None and self._object_options[object_type].manageTagAssignments:
            metadata_list = self._extend_metadata_with_tags(metadata_list, parallel_threads, object_type)


        return metadata_list

    def _get_metadata_externaltables(self, schemas_to_query, parallel_threads):
        
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_externaltables.sql"
        )
        object_type = DbObjectType.EXTERNALTABLE
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        # TODO: evaluate if we want to include constraint metadata here (for now this is not required, because we the metadata of external tables is not evaluated, see db_compare_service.py)
        

        self._convert_column_details_to_dict(metadata_list)

        if self._object_options is not None and self._object_options[object_type].manageTagAssignments:
            metadata_list = self._extend_metadata_with_tags(metadata_list, parallel_threads, object_type)
        
        
        return metadata_list

    def _get_metadata_views(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_views.sql")
        object_type = DbObjectType.VIEW
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        if self._get_policies_on_objects_legacy:
            metadata_list = self._query_policies_on_objects_legacy(metadata_list)

        self._convert_column_details_to_dict(metadata_list)
        
        if self._workarounds_options.get("snowflakeBugs", {}).get("2025-02-clonedViewsQuotes", {}).get("enabled", False):
            metadata_list = self._fix_view_definitions(metadata_list) # This fixes a Snowflake bug when retrieving the VIEW_DEFINITION from the INFORMATION_SCHEMA.VIEWS after cloning the schema that contains the view.

        if self._object_options is not None and self._object_options[object_type].manageTagAssignments:
            metadata_list = self._extend_metadata_with_tags(metadata_list, parallel_threads, object_type)

        return metadata_list
    
    def _fix_view_definitions(self, metadata_list: List[dict]) -> List[dict]:
        """
        This fixes a Snowflake bug when retrieving the VIEW_DEFINITION from the INFORMATION_SCHEMA.VIEWS after cloning the schema that contains the view.
        """

        for n, metadata_view in enumerate(metadata_list):
                
            if 'VIEW_DEFINITION' in metadata_view:
                metadata_view['VIEW_DEFINITION'] = string_util.fix_view_definition(metadata_view['VIEW_DEFINITION'])

            metadata_list[n] = metadata_view

        return metadata_list

    def _get_metadata_stages(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_stages.sql")
        object_type = DbObjectType.STAGE
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._extend_metadata_stages(metadata_list)
        return metadata_list

    def _get_metadata_pipes(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_pipes.sql")
        object_type = DbObjectType.PIPE
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._extend_metadata_pipes(metadata_list)
        return metadata_list

    def _get_metadata_maskingpolicies(self, schemas_to_query, parallel_threads):
        if self._snow_edition == "Standard":
            return []
        template_path = os.path.join(
            self._sql_files_path, "get_maskingpolicy_names.sql"
        )
        object_type = DbObjectType.MASKINGPOLICY
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._extend_metadata_maskingpolicies(metadata_list)
        return metadata_list

    def _get_metadata_rowaccesspolicies(self, schemas_to_query, parallel_threads):
        if self._snow_edition == "Standard":
            return []
        template_path = os.path.join(
            self._sql_files_path, "get_rowaccesspolicy_names.sql"
        )
        object_type = DbObjectType.ROWACCESSPOLICY
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        metadata_list = self._extend_metadata_rowaccesspolicies(metadata_list)
        return metadata_list
    
    def _get_metadata_dynamictables(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_dynamictables.sql")
        
        object_type = DbObjectType.DYNAMICTABLE

        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )

        self._convert_column_details_to_dict(metadata_list)

        metadata_list = self._extend_metadata_dynamictables(metadata_list, object_type, schemas_to_query, parallel_threads)

        if self._object_options is not None and self._object_options[object_type].manageTagAssignments:
            metadata_list = self._extend_metadata_with_tags(metadata_list, parallel_threads, object_type)

        return metadata_list
    
    def _extend_metadata_dynamictables(self, metadata_list: List[Dict], object_type: DbObjectType, schemas_to_query: list, parallel_threads: int) -> List[Dict]:
        """
        Dynamic tables metadata needs to be extended with metadata from "show dynamic tables".
        """
        template_path_extended = os.path.join(self._sql_files_path, "get_metadata_dynamictables_extended.sql")

        metadata_list_extended = self._query_metadata(
            object_type, template_path_extended, schemas_to_query, parallel_threads
        )

        used_keys = ['target_lag', 'warehouse', 'refresh_mode']

        metadata_list_ = {f"{metadata['DATABASE_NAME']}.{metadata['SCHEMA_NAME']}.{metadata['OBJECT_NAME']}": metadata for metadata in metadata_list}

        for extended_metadata in metadata_list_extended:

            extended_metadata_ = {used_key.upper(): extended_metadata[used_key] for used_key in used_keys}

            metadata_list_[f"{extended_metadata['database_name']}.{extended_metadata['schema_name']}.{extended_metadata['name']}"].update(extended_metadata_)

        metadata_list = list(metadata_list_.values())

        return metadata_list
    
    def _get_metadata_networkrules(self, schemas_to_query, parallel_threads):
        template_path = os.path.join(self._sql_files_path, "get_metadata_networkrules.sql")
        
        object_type = DbObjectType.NETWORKRULE

        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )

        self._convert_column_details_to_dict(metadata_list)

        metadata_list = self._extend_metadata_networkrules(metadata_list, object_type, schemas_to_query, parallel_threads)

        return metadata_list
    
    def _extend_metadata_networkrules(self, metadata_list: List[Dict], object_type: DbObjectType, schemas_to_query: list, parallel_threads: int) -> List[Dict]:
        """
        Network rules metadata needs to be extended with metadata from "show network rules".
        """

        for metadata_entry in metadata_list:
            query_template = f'DESCRIBE NETWORK RULE {metadata_entry["schema_name"]}.{metadata_entry["name"]}'
            metadata_result = self._snow_client.execute_query(query_template, use_dict_cursor=True)
            metadata_entry.update(metadata_result[0])
            # Update keys to uppercase in place
            for key in list(metadata_entry.keys()):  # Use list() to avoid runtime changes during iteration
                metadata_entry[key.upper()] = metadata_entry.pop(key)
            metadata_entry["OBJECT_NAME"] = metadata_entry["NAME"]

        return metadata_list
    
    def _get_metadata_tags(self, schemas_to_query, parallel_threads):
        if self._snow_edition == "Standard":
            return []
        template_path = os.path.join(self._sql_files_path, "get_metadata_tags.sql")
        object_type = DbObjectType.TAG
        metadata_list = self._query_metadata(
            object_type, template_path, schemas_to_query, parallel_threads
        )
        return metadata_list


    def _query_metadata(
        self,
        object_type: DbObjectType,
        template_path: str,
        schemas_to_query: List[str],
        parallel_threads: int = 1,
        database_name="",
    ) -> List[Dict]:
        """
        Query metadata for a given object type. Return raw result
        """
        log.debug(f"QUERY object information for TYPE [ '{str(object_type)}' ].")
        query_template = file_util.load(template_path)
        queries = [
            query_template.format(schema_name=schema, database_name=database_name)
            for schema in schemas_to_query
        ]
        if (
            len(queries) == 0
        ):  # on a new database, no schemas are present and therefore, no objects exist (apart from public and information_schema)
            return []
        with ThreadPoolExecutor(max_workers=parallel_threads) as pool:
            results = pool.map(
                lambda q: self._snow_client.execute_query(q, use_dict_cursor=True),
                queries,
            )
        results_flat = [item for subresult in results for item in subresult]
        return results_flat

    def _get_constraint_metadata(
        self,
        schemas_to_query: List[str],
        parallel_threads,
        table_metadata_list: List[Dict],
    ) -> List[Dict]:
        """
        Get metadata for constraints and add them to given table metadata.
        This function exists because it is not possible to perform the required preprocessing of the data in Snowflake.
        (The information is only available in SHOW commands, which cannot be joined or filtered).
        """
        constraints_mapping = {
            "constraint_foreign_keys": {
                "template": os.path.join(
                    self._sql_files_path, "get_metadata_constraint_foreign_keys.sql"
                ),
                "schema_key": "fk_schema_name",
                "name_key": "fk_table_name",
            },
            "constraint_primary_keys": {
                "template": os.path.join(
                    self._sql_files_path, "get_metadata_constraint_primary_keys.sql"
                ),
                "schema_key": "schema_name",
                "name_key": "table_name",
            },
            "constraint_unique_keys": {
                "template": os.path.join(
                    self._sql_files_path, "get_metadata_constraint_unique_keys.sql"
                ),
                "schema_key": "schema_name",
                "name_key": "table_name",
            },
        }
        if len(table_metadata_list) == 0:
            return table_metadata_list
        database_name = table_metadata_list[0][
            "DATABASE_NAME"
        ]  # constraint SHOW commands require database name, should be the same for all entries in list
        for constraint, constraint_entry in constraints_mapping.items():
            metadata_constraints = [
                m
                for m in self._query_metadata(
                    constraint,
                    constraint_entry["template"],
                    schemas_to_query,
                    parallel_threads,
                    database_name,
                )
            ]
            for t in table_metadata_list:
                table_constraint_info = [
                    c
                    for c in metadata_constraints
                    if (
                        c[constraint_entry["schema_key"]] == t["SCHEMA_NAME"]
                        and c[constraint_entry["name_key"]] == t["OBJECT_NAME"]
                    )
                ]
                t.update({constraint: table_constraint_info})
        return table_metadata_list
    

    def _extend_metadata_policy_references(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Add information on which row access policy is referenced where.
        """
        query_template = file_util.load(
            os.path.join(self._sql_files_path, "get_policy_references.sql")
        )
        for metadata_entry in metadata_list:
            if metadata_entry["kind"] not in ("MASKING_POLICY", "ROW_ACCESS_POLICY"):
                raise ValueError("Policy references can only be returned for masking policy or row access policy")
            query = query_template.format(
                schema_name=metadata_entry["schema_name"],
                object_name=metadata_entry["name"],
            )
            result = self._snow_client.execute_query(query, use_dict_cursor=True) # TODO: consider parallelization
            metadata_entry["references"] = result
        return metadata_list
            

    def _query_policies_on_objects_legacy(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Query policies currently applied to objects in the given metadata list.
        """
        query_template = file_util.load(
            os.path.join(self._sql_files_path, "get_policies_on_single_object.sql")
        )
        for metadata_entry in metadata_list:
            if metadata_entry["TABLE_TYPE"] == "VIEW":
                query = query_template.format(
                    schema_name=metadata_entry["SCHEMA_NAME"],
                    object_name=metadata_entry["OBJECT_NAME"],
                    object_type=metadata_entry["TABLE_TYPE"],
                )
                result = self._snow_client.execute_query(query, use_dict_cursor=True)
                metadata_entry["APPLIED_POLICIES_LEGACY"] = result
            else:
                raise NotImplementedError(
                    "Getting policies for table type [ '{metadata_entry['TABLE_TYPE']}' ] not implemented."
                )
        return metadata_list

    def _extend_metadata_maskingpolicies(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Policy metadata needs to be collected for each object individually, since snowflake does not provide any other option.
        """
        query_template = file_util.load(
            os.path.join(self._sql_files_path, "get_maskingpolicy_metadata.sql")
        )
        return self._extend_metadata_policies(metadata_list, query_template)

    def _extend_metadata_rowaccesspolicies(
        self, metadata_list: List[Dict]
    ) -> List[Dict]:
        """
        Policy metadata needs to be collected for each object individually, since snowflake does not provide any other option.
        """
        query_template = file_util.load(
            os.path.join(self._sql_files_path, "get_rowaccesspolicy_metadata.sql")
        )
        return self._extend_metadata_policies(metadata_list, query_template)

    def _extend_metadata_policies(
        self, metadata_list: List[Dict], query_template: str
    ) -> List[Dict]:
        """
        Policy metadata needs to be collected for each object individually, since snowflake does not provide any other option.
        """
        for metadata_entry in metadata_list:
            query = query_template.format(
                schema_name=metadata_entry["schema_name"],
                policy_name=metadata_entry["name"],
            )
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            metadata_entry.update(result[0])
        return metadata_list

    def _extend_metadata_pipes(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        INFORMATION_SCHEMA.PIPES does not contain information on INTEGRATION. We get this information here.
        #TODO: Evaluate if we should use SHOW PIPES IN SCHEMA instead of querying each pipe with DESC individually. (Information is the same in both cases.)
        """
        query_template = 'DESC PIPE "{schema_name}"."{pipe_name}";'
        for metadata_entry in metadata_list:
            query = query_template.format(
                schema_name=metadata_entry["SCHEMA_NAME"],
                pipe_name=metadata_entry["OBJECT_NAME"],
            )
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            pipe_status = self._get_pipe_status(
                metadata_entry["SCHEMA_NAME"], metadata_entry["OBJECT_NAME"]
            )
            execution_state = {"execution_state": pipe_status["executionState"]}
            result[0].update(execution_state)
            metadata_entry.update(result[0])
        return metadata_list

    def _get_pipe_status(self, pipe_schema: str, pipe_name: str) -> Dict:
        """
        Get the status of a pipe.
        """
        query = (
            f'SELECT SYSTEM$PIPE_STATUS(\'"{pipe_schema}"."{pipe_name}"\') AS STATUS'
        )
        result = self._snow_client.execute_query(query, use_dict_cursor=True)
        return json.loads(result[0]["STATUS"])

    def _extend_metadata_stages(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        INFORMATION_SCHEMA.STAGES and SHOW STAGES do not contain all information. We get this information here.
        """
        parent_properties = [
            "STAGE_FILE_FORMAT",
            "STAGE_COPY_OPTIONS",
            "STAGE_LOCATION",
            "STAGE_INTEGRATION",
            "DIRECTORY",
        ]
        query_template = 'DESC STAGE "{schema_name}"."{stage_name}";'
        for metadata_entry in metadata_list:
            query = query_template.format(
                schema_name=metadata_entry["schema_name"],
                stage_name=metadata_entry["name"],
            )
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            # result has the form of an array with dicts: [{parent_property, property, property_value}, {...}, ...]
            # convert this into a nested dict: {parent_property1: {property1:property_value1, property2:property_value2, ...}, ...}
            for parent_property in parent_properties:
                properties = [
                    r["property"]
                    for r in result
                    if r["parent_property"] == parent_property
                ]
                parent_property_value = {
                    r["property"]: r["property_value"]
                    for r in result
                    if (
                        r["parent_property"] == parent_property
                        and r["property"] in properties
                    )
                }
                # set PARSE_HEADER parameter on the default value ('false') if the key "PARSE_HEADER" does not exist - handles outdated instances of stages for which the parameter is missing
                if parent_property == "STAGE_FILE_FORMAT" and not "PARSE_HEADER" in parent_property_value:
                    parent_property_value["PARSE_HEADER"]='false'
                
                # The MULTI_LINE property of STAGE_FILE_FORMAT was introduced by the Snowflake Change Bundle 2024_08 and will be ignored because it can not be set or altered (yet)
                if parent_property == "STAGE_FILE_FORMAT":
                    parent_property_value.pop("MULTI_LINE", None)

                metadata_entry[parent_property] = parent_property_value
            
        return metadata_list

    def _get_meta_data_schema_names(self) -> List[str]:
        """
            Gets the schema names on the current database.
        Returns:
            List[str] - List of schema names
        """
        log.debug("GET list of SCHEMAS")
        query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA');"
        result = self._snow_client.execute_query(query)
        return [s["SCHEMA_NAME"] for s in result]

    def _get_filtered_schema_name_list(
        self, schema_list: Dict[str, List[str]]
    ) -> List[str]:
        """
        Get a list of all schemas on the database. Filter by schema_list.

        schema_list is a dictionary of either 'whitelist' or 'blacklist'.
        """
        schemas_on_db = self._get_meta_data_schema_names()
        if "whitelist" in schema_list:
            log.debug(
                f"FILTER list of schemas with WHITELIST [ {schema_list['whitelist']} ]"
            )
            schemas_whitelist = [s.casefold() for s in schema_list["whitelist"]]
            schemas_filtered = [
                s for s in schemas_on_db if s.casefold() in schemas_whitelist
            ]
        elif "blacklist" in schema_list:
            log.debug(
                f"FILTER list of schemas with BLACKLIST [ {schema_list['blacklist']} ]"
            )
            schemas_blacklist = [s.casefold() for s in schema_list["blacklist"]]
            schemas_filtered = [
                s for s in schemas_on_db if s.casefold() not in schemas_blacklist
            ]
        else:
            raise EnvironmentError(
                "MALFORMED config value [ 'schema_list' ] (contains neither blacklist nor whitelist)"
            )
        return schemas_filtered

    def get_all_objects(self, database_name: str) -> List[List[Union[str, int]]]:
        """
            Gets a list of all tables, views, functions, procedures, file formats and stages on a Snowflake database.
        Args:
            database_name: str - Name of the database
        Returns:
             List[List[Union[str,int]]] - Raw query return set provided by Snowflake
        """
        query = file_util.load(
            os.path.join(self._sql_files_path, "get_all_objects.sql")
        ).format(database_name=database_name)
        return self._snow_client.execute_query(query, use_dict_cursor=True)

    def get_all_objects_filtered(
        self, database_name: str, schema_list: List[str]
    ) -> List[List[Union[str, int]]]:
        """
            Gets a list of all tables, views, functions, procedures, file formats and stages on a Snowflake database,
            filtered by a list of given schemas.
        Args:
            database_name: str - Name of the database
            schema_list: List[str] - List of schemas to include
        Returns:
             List[List[Union[str,int]]] - Raw query return set provided by Snowflake
        """
        result = self.get_all_objects(database_name)
        return [
            r
            for r in result
            if r["SCHEMA_NAME"].lower() in [s.lower() for s in schema_list]
        ]

    def get_object_count_per_schema(self, database_name) -> List[Dict]:
        """
        Get a list of schemas in the database with a count of objects in each, ordered by number of objects (descending).

        Example output:
        [{'COUNT': 5, 'SCHEMA_NAME': 'S1'}, {'COUNT': 3, 'SCHEMA_NAME': 'S2'}]
        """
        query = file_util.load(
            os.path.join(self._sql_files_path, "get_object_count_per_schema.sql")
        ).format(database_name=database_name)
        return self._snow_client.execute_query(query, use_dict_cursor=True)
    

    @staticmethod
    def _convert_column_details_to_dict(metadata_list: List[dict]) -> None:
        """
        Given a metadata list for a table like object, convert the COLUMN_DETAILS from a json string to a list of dicts.
        """
        for metadata_object in metadata_list:
            if "COLUMN_DETAILS" in metadata_object.keys():
                metadata_object["COLUMN_DETAILS"] = json.loads(metadata_object["COLUMN_DETAILS"])
    
    def _extend_metadata_with_tags(        
            self, metadata_list: List[Dict], max_number_of_threads: int, object_type: str
    ) -> List[Dict]:
        """
        Get all tags on an table-like object (e.g. tables, views, materialized views).
        Here, each object is queried individually.
        """
        start_time_extend_metadata_with_tags = time.time()
        object_domain_tags = DbObjectType.get_object_domain_from_object_type_for_tag_references(object_type)

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extended_with_tags=self._get_metadata_tags_on_objects(object_domain_tags, metadata_list)
        else:
            # with threading
            metadata_list_extended_with_tags=parallelization_util.execute_func_in_parallel(self._get_metadata_tags_on_objects, metadata_list, max_number_of_threads, object_domain_tags)

        end_time_extend_metadata_with_tags = time.time()
        log.debug(f"EXECUTED _extend_metadata_with_tags for object_type {object_type}: [ '{round(end_time_extend_metadata_with_tags - start_time_extend_metadata_with_tags, 2)} seconds' ]")

        return metadata_list_extended_with_tags
    
    def _get_metadata_tags_on_objects(self, object_domain_tags: str, metadata_list: list[Dict])-> list[Dict]:
        """
        Get all tags on a list of objects and add them to the metadata information.
        """

        for metadata_entry in metadata_list:
            metadata_entry_database_name=metadata_entry["DATABASE_NAME"]
            metadata_entry_schema_name=metadata_entry["SCHEMA_NAME"]
            metadata_entry_object_name=metadata_entry["OBJECT_NAME"]
            
            metadata_entry["tags"]={}
           
            if object_domain_tags == 'TABLE':
                metadata_entry_column_tags={}
                query = f"SELECT * FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('{metadata_entry_database_name}.{metadata_entry_schema_name}.{metadata_entry_object_name}', '{object_domain_tags}'));"
                result = self._snow_client.execute_query(query, use_dict_cursor=True)
                for row in result: 
                    if row["LEVEL"]=='TABLE':
                        metadata_entry["tags"][f'{row["TAG_SCHEMA"]}.{row["TAG_NAME"]}']=row["TAG_VALUE"]
                    elif row["LEVEL"]=='COLUMN':
                        if row["COLUMN_NAME"] not in metadata_entry_column_tags.keys():
                            metadata_entry_column_tags[row["COLUMN_NAME"]]={f'{row["TAG_SCHEMA"]}.{row["TAG_NAME"]}':row["TAG_VALUE"]}
                        else:
                            metadata_entry_column_tags[row["COLUMN_NAME"]].update({f'{row["TAG_SCHEMA"]}.{row["TAG_NAME"]}':row["TAG_VALUE"]})
                    
                for column_detail in metadata_entry["COLUMN_DETAILS"]:
                    if column_detail["COLUMN_NAME"] in metadata_entry_column_tags.keys():
                        column_detail["tags"]=metadata_entry_column_tags[column_detail["COLUMN_NAME"]]
                    else:
                        column_detail["tags"]={}

        return metadata_list

