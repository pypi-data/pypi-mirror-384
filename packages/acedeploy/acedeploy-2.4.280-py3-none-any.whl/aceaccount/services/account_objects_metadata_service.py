import logging
import os
import time
import json
from typing import Dict, List, Union
from aceaccount.core.model_account_object_instances import AccountObjectInstance
from aceaccount.core.model_account_object_sql_entities import AccountObjectType

import aceutils.file_util as file_util
import aceutils.general_util as gen_util
import aceutils.parallelization_util as parallelization_util
from aceservices.snowflake_service import SnowClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class AccountMetadataService:
    """
    Class to query metadata information from snowflake account objects.
    An instance of this class is not scoped to a database.
    """

    def __init__(
        self,
        enabled_object_types: list,
        snow_client: SnowClient,
        dryrun: bool = False
    ):
        """
            Inits a account metadata service.
        Args:
            snow_client: SnowClient - provides connection a snowflake database
        """
        self._enabled_object_types = enabled_object_types
        self._snow_client = snow_client
        self._dryrun = dryrun

        module_root_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        
        self._sql_files_path = os.path.abspath(
            os.path.join(module_root_folder, "resources", "sql")
        )
        self.all_account_objects = []

        self.account_objects_parameter_representation = {}

    def get_account_objects_subset(self, object_type: AccountObjectType):
        return [account_object for account_object in self.all_account_objects if account_object.object_type == object_type]

    def get_all_account_objects_metadata(self, max_number_of_threads: int=1, get_grants: bool=True, get_tags:  bool=True) -> None:
        """
        Get all metadata information (e.g. on storage integrations) from the account.
        """
        log.info(f"QUERY account object information for object types: {str(self._enabled_object_types)}")

        mapping = {
            AccountObjectType.STORAGEINTEGRATION: self._get_metadata_storageintegrations,
            AccountObjectType.WAREHOUSE: self._get_metadata_warehouses,
            AccountObjectType.SHARE: self._get_metadata_shares,
            AccountObjectType.DATABASE: self._get_metadata_databases,
            AccountObjectType.EXTERNALVOLUME: self._get_metadata_externalvolumes
        }

        for object_type, metadata_function in mapping.items():
            if object_type.value not in self._enabled_object_types:
                log.debug(
                    f"SKIPPING disabled object type: {object_type.value}"
                )
                continue
            metadata_list = metadata_function(max_number_of_threads, get_grants, get_tags)
            self.all_account_objects.extend(
                [AccountObjectInstance.factory(object_type, m, get_grants, get_tags) for m in metadata_list]
            )

        log.info(
            f"FOUND objects in account: {gen_util.generate_account_object_log_summaries(self.all_account_objects)}"
        )

    def _query_metadata(
        self,
        object_type: AccountObjectType,
        template_path: str,
    ) -> List[Dict]:
        """
        Query metadata for a given object type. Return raw result
        """
        log.debug(f"QUERY object information for TYPE [ '{str(object_type)}' ].")
        query = file_util.load(template_path)
        return self._snow_client.execute_query(query)

    def _get_metadata_storageintegrations(self, max_number_of_threads: int=1, get_grants: bool=True, get_tags: bool=True):
        """
        Get all metadata information for storage integrations from the Snowflake account.
        """
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_storageintegrations.sql"
        )
        object_type = AccountObjectType.STORAGEINTEGRATION
        metadata_list_ = self._query_metadata(
            object_type, template_path
        )
        metadata_list_ = self._extend_metadata_storageintegrations(metadata_list_, max_number_of_threads)

        # filter on storage integrations for which the executing Snowflake role has ownership on
        metadata_list = self._filter_storageintegrations_by_ownership(metadata_list_, max_number_of_threads)

        if get_grants:
            metadata_list = self._extend_metadata_with_grants(metadata_list, max_number_of_threads, object_type)
        if get_tags:
            metadata_list = self._extend_metadata_with_tags(metadata_list, max_number_of_threads, object_type)
        return metadata_list
    
    def _filter_storageintegrations_by_ownership(self, metadata_list: List[Dict], max_number_of_threads: int) -> List[Dict]:
        """
        SHOW STORAGE INTEGRATIONS does not have information about the ownership.
        The Storage Integrations are filtered by Storage Integrations for which the executing Snowflake role has ownership on.
        """

        start_time_filter_storageintegrations_by_ownership = time.time()

        if max_number_of_threads<=1:
            # without threading
            metadata_list_filtered_by_ownership=self._get_storageintegrations_filtered_by_ownership(metadata_list)
        else:
            # with threading
            metadata_list_filtered_by_ownership=parallelization_util.execute_func_in_parallel(self._get_storageintegrations_filtered_by_ownership, metadata_list, max_number_of_threads)

        end_time_filter_storageintegrations_by_ownership = time.time()


        log.info(f"============= Execution Time get_all_account_objects_metadata -> _filter_storageintegrations_by_ownership: {round(end_time_filter_storageintegrations_by_ownership - start_time_filter_storageintegrations_by_ownership, 2)} seconds")

        return metadata_list_filtered_by_ownership
        
    
    def _get_storageintegrations_filtered_by_ownership(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        SHOW STORAGE INTEGRATIONS does not have information about the ownership.
        Here, each integration is queried individually in order to retrieve the ownership roles.
        The Storage Integrations are then filtered by Storage Integrations for which the executing Snowflake role has ownership on.
        """
        
        metadata_list_filtered_by_ownership=[]
        for metadata_entry in metadata_list:
             
            ownership_role = ''
        
            query_template = 'SHOW GRANTS ON INTEGRATION "{name}";'

            query = query_template.format(
                name=metadata_entry["name"],
            )

            result = self._snow_client.execute_query(query, use_dict_cursor=True)

            for row in result:
                if row["privilege"] == 'OWNERSHIP':
                    ownership_role = row["grantee_name"]

            if not ownership_role:
                raise ValueError(f'Ownership on Storage Integration {metadata_entry["name"]} could not be retrieved!')
            
            # filter by executing Snowflake role coincides with the ownership role
            if ownership_role != self._snow_client.connection.role:
                continue
            metadata_list_filtered_by_ownership.append(metadata_entry)

        return metadata_list_filtered_by_ownership
    
    def _extend_metadata_storageintegrations(self, metadata_list: List[Dict], max_number_of_threads: int) -> List[Dict]:
        """
        SHOW STORAGE INTEGRATIONS does not return all required metadata.
        Here, each integration is queried individually.
        """
        start_time_extend_metadata_storageintegrations = time.time()

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extend_metadata_storageintegrations=self._get_extended_metadata_storageintegrations(metadata_list)
        else:
            # with threading
            metadata_list_extend_metadata_storageintegrations=parallelization_util.execute_func_in_parallel(self._get_extended_metadata_storageintegrations, metadata_list, max_number_of_threads)

        end_time_extend_metadata_storageintegrations = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_storageintegrations: {round(end_time_extend_metadata_storageintegrations - start_time_extend_metadata_storageintegrations, 2)} seconds")

        return metadata_list_extend_metadata_storageintegrations
    
    def _get_extended_metadata_storageintegrations(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        SHOW STORAGE INTEGRATIONS does not return all required metadata.
        Here, each integration is queried individually.
        """
        query_template = 'DESC STORAGE INTEGRATION "{name}";'
        for metadata_entry in metadata_list:
            query = query_template.format(
                name=metadata_entry["name"],
            )
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            for row in result:
                if row["property_type"] == 'List' and row["property_value"] == '':
                    metadata_entry.update({row["property"].lower(): []})
                elif row["property_type"] == 'List':
                    metadata_entry.update({row["property"].lower(): row["property_value"].split(",")})
                else:
                    metadata_entry.update({row["property"].lower(): row["property_value"]})
        return metadata_list


    def _get_metadata_warehouses(self, max_number_of_threads: int=1, get_grants: bool=True, get_tags: bool=True):
        """
        Get all metadata information for warehouses from the Snowflake account.
        """

        template_path = os.path.join(
            self._sql_files_path, "get_metadata_warehouses.sql"
        )
        object_type = AccountObjectType.WAREHOUSE
        metadata_list_ = self._query_metadata(
            object_type, template_path
        )

        metadata_list_ = self._extend_metadata_warehouses(metadata_list_, max_number_of_threads)

        metadata_list=[]
        for metadata_object in metadata_list_:
            # filter on warehouses for which the executing Snowflake role has ownership on
            if metadata_object["owner"] != self._snow_client.connection.role:
                continue
            metadata_list.append(metadata_object)

        if get_grants:
            metadata_list = self._extend_metadata_with_grants(metadata_list, max_number_of_threads, object_type)
        if get_tags:
            metadata_list = self._extend_metadata_with_tags(metadata_list, max_number_of_threads, object_type)
        return metadata_list
    
    def _extend_metadata_warehouses(self, metadata_list: List[Dict], max_number_of_threads: int) -> List[Dict]:
        """
        SHOW WAREHOUSES does not return all required metadata.
        Here, each warehouse is queried individually.
        """
        start_time_extend_metadata_warehouses = time.time()

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extended_warehouses=self._get_extended_metadata_warehouses(metadata_list)
        else:
            # with threading
            metadata_list_extended_warehouses=parallelization_util.execute_func_in_parallel(self._get_extended_metadata_warehouses, metadata_list, max_number_of_threads)

        end_time_extend_metadata_warehouses = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_warehouses: {round(end_time_extend_metadata_warehouses - start_time_extend_metadata_warehouses, 2)} seconds")
        
        return metadata_list_extended_warehouses
    
    def _get_extended_metadata_warehouses(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        SHOW WAREHOUSES does not return all required metadata.
        Here, each warehouse is queried individually.
        """
        for metadata_entry in metadata_list:
            query = f'SHOW PARAMETERS IN WAREHOUSE "{metadata_entry["name"]}";'
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            for row in result:
                if row["key"].lower()=="max_concurrency_level" or  row["key"].lower()=="statement_queued_timeout_in_seconds" or row["key"].lower()=="statement_timeout_in_seconds":
                    row_value=int(row["value"])
                else:
                    row_value=row["value"]
                metadata_entry.update({row["key"].lower(): row_value})

        return metadata_list
    
    def _get_metadata_shares(self, max_number_of_threads: int=1, get_grants: bool=True, get_tags: bool=True):
        """
        Get all metadata information for shares from the Snowflake account. Ignore inbound shares.
        """
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_shares.sql"
        )
        object_type = AccountObjectType.SHARE
        metadata_list_ = self._query_metadata(
            object_type, template_path
        )

        metadata_list=[]
        for metadata_object in metadata_list_:

            # filter on shares for which the executing Snowflake role has ownership on
            if metadata_object["owner"] != self._snow_client.connection.role:
                continue 

            # filter on outbound shares and ignore inbound shares
            if metadata_object["kind"] == "OUTBOUND":

                metadata_object["name"]=metadata_object["name"].split('.')[-1]
                if metadata_object["to"]:
                    metadata_object["accounts"]=list(map(str.strip, metadata_object["to"].split(',')))
                else:
                    metadata_object["accounts"]=[]
                
                metadata_list.append(metadata_object)

        if get_tags:
            metadata_list = self._extend_metadata_with_tags(metadata_list, max_number_of_threads, object_type)

        return metadata_list
    
    def _get_metadata_databases(self, max_number_of_threads: int=1, get_grants: bool=True, get_tags: bool=True):
        """
        Get all metadata information for databases from the Snowflake account.
        """
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_databases.sql"
        )
        object_type = AccountObjectType.DATABASE
        metadata_list_ = self._query_metadata(
            object_type, template_path
        )
        metadata_list_ = self._extend_metadata_databases(metadata_list_, max_number_of_threads)

        metadata_list=[]
        for metadata_object in metadata_list_:

            # filter on databases for which the executing Snowflake role has ownership on
            if metadata_object["owner"] != self._snow_client.connection.role:
                continue 
            #ignore system-defined databases
            if metadata_object["name"]=='SNOWFLAKE' or metadata_object["name"]=='SNOWFLAKE_SAMPLE_DATA':
                continue
            #ignore imported databases
            if not metadata_object["kind"]=='STANDARD':
                continue

            if metadata_object["options"]=='TRANSIENT':
                metadata_object["transient"]='TRANSIENT'
            else:
                metadata_object["transient"]=''

            metadata_list.append(metadata_object)

        if get_grants:
            metadata_list = self._extend_metadata_with_grants(metadata_list, max_number_of_threads, object_type)
        if get_tags:
            metadata_list = self._extend_metadata_with_tags(metadata_list, max_number_of_threads, object_type)

        return metadata_list
    
    def _get_metadata_externalvolumes(self, max_number_of_threads: int=1, get_grants: bool=True, get_tags: bool=True):
        """
        Get all metadata information for externalvolumes from the Snowflake account.
        """
        template_path = os.path.join(
            self._sql_files_path, "get_metadata_externalvolumes.sql"
        )
        object_type = AccountObjectType.EXTERNALVOLUME
        metadata_list_ = self._query_metadata(
            object_type, template_path
        )

        metadata_list_ = self._extend_metadata_externalvolumes(metadata_list_, max_number_of_threads)

        # filter on external volumes for which the executing Snowflake role has ownership on
        metadata_list = self._filter_externalvolumes_by_ownership(metadata_list_, max_number_of_threads)

        if get_grants:
            metadata_list = self._extend_metadata_with_grants(metadata_list, max_number_of_threads, object_type)

        # in case of a dryrun get information about iceberg tables that are using the external volumes -> in order to raise an error in the dryrun when trying to drop or "create or replace" external volumes used by iceberg tables
        if self._dryrun:
            metadata_list = self._extend_metadata_external_volumes_used_by_iceberg_tables(metadata_list)

        return metadata_list

    def _filter_externalvolumes_by_ownership(self, metadata_list: List[Dict], max_number_of_threads: int) -> List[Dict]:
        """
        SHOW EXTERNAL VOLUMES does not have information about the ownership.
        The External Volumes are filtered by External Volumes for which the executing Snowflake role has ownership on.
        """

        start_time_filter_externalvolumes_by_ownership = time.time()

        if max_number_of_threads<=1:
            # without threading
            metadata_list_filtered_by_ownership=self._get_externalvolumes_filtered_by_ownership(metadata_list)
        else:
            # with threading
            metadata_list_filtered_by_ownership=parallelization_util.execute_func_in_parallel(self._get_externalvolumes_filtered_by_ownership, metadata_list, max_number_of_threads)

        end_time_filter_externalvolumes_by_ownership = time.time()


        log.info(f"============= Execution Time get_all_account_objects_metadata -> _filter_externalvolumes_by_ownership: {round(end_time_filter_externalvolumes_by_ownership - start_time_filter_externalvolumes_by_ownership, 2)} seconds")

        return metadata_list_filtered_by_ownership
        
    def _get_externalvolumes_filtered_by_ownership(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        SHOW EXTERNAL VOLUMES does not have information about the ownership.
        Here, each integration is queried individually in order to retrieve the ownership roles.
        The External Volumes are then filtered by External Volumes for which the executing Snowflake role has ownership on.
        """
        
        metadata_list_filtered_by_ownership=[]
        for metadata_entry in metadata_list:
             
            ownership_role = ''
        
            query_template = 'SHOW GRANTS ON EXTERNAL VOLUME "{name}";'

            query = query_template.format(
                name=metadata_entry["name"],
            )

            result = self._snow_client.execute_query(query, use_dict_cursor=True)

            for row in result:
                if row["privilege"] == 'OWNERSHIP':
                    ownership_role = row["grantee_name"]

            if not ownership_role:
                raise ValueError(f'Ownership on External Volume {metadata_entry["name"]} could not be retrieved!')
            
            # filter by executing Snowflake role coincides with the ownership role
            if ownership_role != self._snow_client.connection.role:
                continue
            metadata_list_filtered_by_ownership.append(metadata_entry)

        return metadata_list_filtered_by_ownership
    
    def _extend_metadata_externalvolumes(self, metadata_list: List[Dict], max_number_of_threads: int) -> List[Dict]:
        """
        SHOW EXTERNAL VOLUMES does not return all required metadata.
        Here, each external volume is queried individually.
        """
        start_time_extend_metadata_externalvolumes = time.time()

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extended_externalvolumes=self._get_extended_metadata_externalvolumes(metadata_list)
        else:
            # with threading
            metadata_list_extended_externalvolumes=parallelization_util.execute_func_in_parallel(self._get_extended_metadata_externalvolumes, metadata_list, max_number_of_threads)

        end_time_extend_metadata_externalvolumes = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_externalvolumes: {round(end_time_extend_metadata_externalvolumes - start_time_extend_metadata_externalvolumes, 2)} seconds")
    
        return metadata_list_extended_externalvolumes
    
    def _get_extended_metadata_externalvolumes(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        SHOW EXTERNAL VOLUMES does not return all required metadata.
        Here, each external volume is queried individually.
        """

        for metadata_entry in metadata_list:
            metadata_entry["storage_locations"]={}
            query = f'DESCRIBE EXTERNAL VOLUME "{metadata_entry["name"]}";'
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            for row in result:
                if row["property"].lower()=="allow_writes":
                    metadata_entry.update({row["property"].lower(): row["property_value"]})
                elif row["property"].lower()=="active":
                    metadata_entry.update({row["property"].lower(): row["property_value"]})
                elif row["property"].lower().startswith("storage_location_"):
                    storage_location_params = json.loads(row["property_value"])
                    storage_location={}
                    for storage_location_param in storage_location_params:
                        if storage_location_param.lower() in AccountObjectType.get_supported_externalvolume_storage_location_params():
                            if storage_location_param.lower() == "encryption_type":
                                encryption = {"type": storage_location_params["ENCRYPTION_TYPE"] }
                                if "ENCRYPTION_KMS_KEY_ID" in storage_location_params:
                                    encryption["kms_key_id"] = storage_location_params["ENCRYPTION_KMS_KEY_ID"]
                                storage_location["encryption"] = encryption
                            else:
                                storage_location[storage_location_param.lower()] = storage_location_params[storage_location_param]

                    metadata_entry["storage_locations"][storage_location["name"]] = storage_location
                    metadata_entry["storage_locations"][storage_location["name"]].pop("name")
                    
        return metadata_list
    
    def _extend_metadata_external_volumes_used_by_iceberg_tables(self, metadata_list: List[Dict]):
        """
        Get information about external volumes for further validation in regards to Iceberg Tables using the external volumes.
        In case of an dryrun, an error will be raised at a later stage when trying to drop or "create or replace" external volumes used by iceberg tables.
        Note: Executing Snowflake Role needs SELECT privilege on Iceberg Tables.
        """    
        start_time_extend_metadata_external_volumes_used_by_iceberg_tables = time.time()

        query_iceberg_tables_metadata = 'SHOW ICEBERG TABLES IN ACCOUNT;'

        result = self._snow_client.execute_query(query_iceberg_tables_metadata, use_dict_cursor=True)

        for metadata_entry in metadata_list:
            metadata_entry["used_by_iceberg_tables"] = False
            for iceberg_table in result:
                if  metadata_entry["name"].upper() == iceberg_table["external_volume_name"].upper():
                    metadata_entry["used_by_iceberg_tables"] = True

        end_time_extend_metadata_external_volumes_used_by_iceberg_tables = time.time()

        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_external_volumes_used_by_iceberg_tables: {round(end_time_extend_metadata_external_volumes_used_by_iceberg_tables - start_time_extend_metadata_external_volumes_used_by_iceberg_tables, 2)} seconds")

        return metadata_list

    def _extend_metadata_databases(self, metadata_list: List[Dict], max_number_of_threads: int) -> List[Dict]:
        """
        SHOW DATABASES does not return all required metadata.
        Here, each database is queried individually.
        """
        start_time_extend_metadata_databases = time.time()

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extended_databases=self._get_extended_metadata_databases(metadata_list)
        else:
            # with threading
            metadata_list_extended_databases=parallelization_util.execute_func_in_parallel(self._get_extended_metadata_databases, metadata_list, max_number_of_threads)

        end_time_extend_metadata_databases = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_databases: {round(end_time_extend_metadata_databases - start_time_extend_metadata_databases, 2)} seconds")
        
        return metadata_list_extended_databases
    
    def _get_extended_metadata_databases(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        SHOW DATABASES does not return all required metadata.
        Here, each database is queried individually.
        """
        for metadata_entry in metadata_list:
            query = f'SHOW PARAMETERS IN DATABASE "{metadata_entry["name"]}";'
            result = self._snow_client.execute_query(query, use_dict_cursor=True)
            for row in result:
                if row["key"].lower()=="data_retention_time_in_days" or  row["key"].lower()=="max_data_extension_time_in_days" or row["key"].lower()=="suspend_task_after_num_failures" or row["key"].lower()=="user_task_timeout_ms":
                    row_value=int(row["value"])
                else:
                    row_value=row["value"]
                metadata_entry.update({row["key"].lower(): row_value})

        return metadata_list

    def _extend_metadata_with_grants(
        self, metadata_list: List[Dict], max_number_of_threads: int, object_type: AccountObjectType
    ) -> List[Dict]:
        """
        Extend the metadata information of the account objects with grants.
        Here, each account object is queried individually -> optionally with parallelization.
        """
        start_time_extend_metadata_with_grants = time.time()

        object_domain = AccountObjectType.get_object_domain_from_object_type(object_type)

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extended_with_grants=self._get_metadata_grants(object_domain, metadata_list)
        else:
            metadata_list_extended_with_grants=parallelization_util.execute_func_in_parallel(self._get_metadata_grants,metadata_list, max_number_of_threads, object_domain)

        end_time_extend_metadata_with_grants = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_with_grants for object_type {object_type}: {round(end_time_extend_metadata_with_grants - start_time_extend_metadata_with_grants, 2)} seconds")

        return metadata_list_extended_with_grants
    
    def _get_metadata_grants(self, object_domain: str, metadata_list: list[Dict])-> list[Dict]:
        """
        Get all grants on a list of account objects and add them to the metadata information.
        """
        for metadata_entry in metadata_list:
            query = f'SHOW GRANTS ON {object_domain} {metadata_entry["name"]};'
            result = self._snow_client.execute_query(query, use_dict_cursor=True)

            grants={}

            for row in result:
                if not row["privilege"] == 'OWNERSHIP' and row["granted_to"] == 'ROLE':
                    grants.setdefault(row["privilege"].lower(),[]).append(row["grantee_name"])
            
            metadata_entry["grants"]=grants

        return metadata_list
    
    def _extend_metadata_with_tags(        
            self, metadata_list: List[Dict], max_number_of_threads: int, object_type: AccountObjectType, 
    ) -> List[Dict]:
        """
        Get all tags on an account object.
        Here, each account object is queried individually.
        """
        start_time_extend_metadata_with_tags = time.time()
        object_domain = AccountObjectType.get_object_domain_from_object_type(object_type)

        if max_number_of_threads<=1:
            # without threading
            metadata_list_extended_with_tags=self._get_metadata_tags(object_domain, metadata_list)
        else:
            # with threading
            metadata_list_extended_with_tags=parallelization_util.execute_func_in_parallel(self._get_metadata_tags, metadata_list, max_number_of_threads, object_domain)

        end_time_extend_metadata_with_tags = time.time()
        log.info(f"============= Execution Time get_all_account_objects_metadata -> _extend_metadata_with_tags for object_type {object_type}: {round(end_time_extend_metadata_with_tags - start_time_extend_metadata_with_tags, 2)} seconds")

        return metadata_list_extended_with_tags
    
    def _get_metadata_tags(self, object_domain: str, metadata_list: list[Dict])-> list[Dict]:
        """
        Get all tags on a list of account objects and add them to the metadata information.
        """
        for metadata_entry in metadata_list:
            metadata_entry_name=metadata_entry["name"]
            query = f"SELECT * FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.TAG_REFERENCES('{metadata_entry_name}', '{object_domain}'));"
            result = self._snow_client.execute_query(query, use_dict_cursor=True)

            tags={}

            for row in result:
                tags[f'{row["TAG_DATABASE"].lower()}.{row["TAG_SCHEMA"].lower()}.{row["TAG_NAME"].lower()}'] = row["TAG_VALUE"]
            
            metadata_entry["tags"]=tags

        return metadata_list
          
    def get_object_by_object(self, obj: AccountObjectInstance) -> AccountObjectInstance:
        """
        Return the matching InstanceObject for the given obj.
        Compares the id of the object.
        """
        return self.get_object_by_id(obj.id)

    def get_object_by_id(self, object_id: str) -> AccountObjectInstance:
        """
        Return the AccountObjectInstance for the given object_id.
        """
        result = [o for o in self.all_account_objects if (o.compare_id(object_id))]
        if len(result) == 0:
            log.debug(
                f"OBJECT with [ id='{object_id}' ] NOT in FOUND in AccountMetadataService"
            )
            return None
        elif len(result) > 1:
            raise ValueError(
                f"OBJECT with [ id='{object_id}' ] NOT UNIQUE in AccountMetadataService. Found [ '{len(result)}' ]"
            )
        else:
            return result[0]

    def get_account_objects_dict(self, json_schema_relative_path:str) -> dict:
        """
        Get parameter representation as a dict of account objects instances for all object types.
        """

        for object_type in AccountObjectType:
            parameter_representation, object_type_key = self._get_parameter_representation(object_type)
            self.account_objects_parameter_representation[object_type]={
                "$schema":json_schema_relative_path,
                 object_type_key: parameter_representation
            }
        return self.account_objects_parameter_representation

    def _get_parameter_representation(self, object_type: AccountObjectType):
        """
        Return parameter representation of account objects instances for a specific object type.
        """
        mapping_object_type_object_type_key = {
            AccountObjectType.STORAGEINTEGRATION: "storage_integrations",
            AccountObjectType.WAREHOUSE: "warehouses",
            AccountObjectType.SHARE: "shares",
            AccountObjectType.DATABASE: "databases",
            AccountObjectType.EXTERNALVOLUME: "external_volumes",
        }

        object_type_key=mapping_object_type_object_type_key[object_type]

        object_instances=self.get_account_objects_subset(object_type)
        
        parameter_representation={}
        for object_instance in object_instances:

            parameter_representation_={
                object_instance.name:{
                    key:value for key, value in object_instance.__dict__.items() if not key.startswith('__') and not callable(key) and not key=="_object_type" and not key=="_name"
                }                                           
            }

            parameter_representation= parameter_representation | parameter_representation_

        return parameter_representation, object_type_key