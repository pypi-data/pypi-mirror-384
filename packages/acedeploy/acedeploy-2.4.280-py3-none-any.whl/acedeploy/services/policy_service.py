import logging
import os
import datetime
import json
import re
import requests
import base64

from typing import Dict, Union, Tuple
from pathlib import PurePath
from enum import Enum

from aceutils.logger import LoggingAdapter
from aceutils.file_util import load_json
from acedeploy.core.model_instance_objects import InstanceObject, ColumnInstance
from acedeploy.core.model_sql_entities import DbActionType, DbObjectType
import aceutils.string_util as string_util

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)

class PolicyAssignmentObjectTypes(Enum):
    """
    Enum for valid object types for policy assignments. 
    Subset of DbObjectType.
    Policy handling type PolicyHandlingTypes.NEW_OBJECT is supported for these objects.
    """
    VIEW = "VIEW"
    TABLE = "TABLE"
    DYNAMICTABLE = "DYNAMICTABLE"
    TAG = "TAG"

class PolicyAssignmentLevel(Enum):
    """
    Enum for valid policy assignment levels.
    """
    TABLE_LEVEL_ASSIGNMENT = "TABLE_LEVEL_ASSIGNMENT"
    SCHEMA_LEVEL_ASSIGNMENT = "SCHEMA_LEVEL_ASSIGNMENT"

class PolicyAssignmentType(Enum):
    """
    Enum for valid policy assignment types.
    """
    TABLECOLUMNS = "TABLE_COLUMNS"
    VIEWCOLUMNS = "VIEW_COLUMNS"
    DYNAMICTABLECOLUMNS = "DYNAMICTABLE_COLUMNS"
    VIEWS = "VIEWS"
    TABLES = "TABLES"
    DYNAMICTABLES = "DYNAMICTABLES"
    TAGS = "TAGS"

    @staticmethod
    def get_object_type_from_assignment_type(assignment_type) -> PolicyAssignmentObjectTypes:
        """
        Returns the corresponding object type for a policy assignment type.
        """
        if assignment_type.upper() == PolicyAssignmentType.TABLECOLUMNS.value:
            return PolicyAssignmentObjectTypes.TABLE
        if assignment_type.upper() == PolicyAssignmentType.VIEWCOLUMNS.value:
            return PolicyAssignmentObjectTypes.VIEW
        if assignment_type.upper() == PolicyAssignmentType.DYNAMICTABLECOLUMNS.value:
            return PolicyAssignmentObjectTypes.DYNAMICTABLE
        if assignment_type.upper() == PolicyAssignmentType.VIEWS.value:
            return PolicyAssignmentObjectTypes.VIEW
        if assignment_type.upper() == PolicyAssignmentType.TABLES.value:
            return PolicyAssignmentObjectTypes.TABLE
        if assignment_type.upper() == PolicyAssignmentType.TAGS.value:
            return PolicyAssignmentObjectTypes.TAG
        if assignment_type.upper() == PolicyAssignmentType.DYNAMICTABLES.value:
            return PolicyAssignmentObjectTypes.DYNAMICTABLE
        else:
            raise ValueError(f"Policy assignment type {assignment_type} not supported")
        
    @staticmethod
    def get_policy_assignment_level(policy_assignment_type) -> PolicyAssignmentLevel:
        """
        Returns object level of the desired policy assignment type.
        Currently supported are table-level objects (like columns) and schema-level objects like tables.
        """
        policy_assignment_level = {
            PolicyAssignmentType.TABLECOLUMNS: PolicyAssignmentLevel.TABLE_LEVEL_ASSIGNMENT,
            PolicyAssignmentType.VIEWCOLUMNS: PolicyAssignmentLevel.TABLE_LEVEL_ASSIGNMENT,
            PolicyAssignmentType.DYNAMICTABLECOLUMNS: PolicyAssignmentLevel.TABLE_LEVEL_ASSIGNMENT,
            PolicyAssignmentType.VIEWS: PolicyAssignmentLevel.SCHEMA_LEVEL_ASSIGNMENT,
            PolicyAssignmentType.TABLES: PolicyAssignmentLevel.SCHEMA_LEVEL_ASSIGNMENT,
            PolicyAssignmentType.TAGS: PolicyAssignmentLevel.SCHEMA_LEVEL_ASSIGNMENT,
            PolicyAssignmentType.DYNAMICTABLES: PolicyAssignmentLevel.SCHEMA_LEVEL_ASSIGNMENT,
        }

        return policy_assignment_level[policy_assignment_type]
    
class PolicyHandlingTypes(Enum):
    """
    Enum for valid policy handling types for which policy assignments are managed during deployment.
    """
    NEW_OBJECT = "NEW_OBJECT" # only when object type in PolicyAssignmentObjectTypes
    ALTER_VIEW = "ALTER_VIEW"
    ALTER_DYNAMICTABLE = "ALTER_DYNAMICTABLE" # only when alter query_text or alter refresh_mode
    ADD_TABLECOLUMN = "ADD_TABLECOLUMN"



class PolicyAssignmentAlterObjectTypes(Enum):
    """
    Enum for object types for which policy assignments are lost on deployment when altered. 
    Subset of PolicyAssignmentObjectTypes.
    Policy handling type can be retrieved with get_policy_handling_type.
    """
    VIEW = "VIEW"
    TABLE = "TABLE" # only when columns_to_add
    DYNAMICTABLE = "DYNAMICTABLE" # only when alter query_text or alter refresh_mode
    
    @staticmethod
    def get_policy_handling_type(policy_assignment_alter_object_type) -> PolicyHandlingTypes:
        """
        Returns the policy handling type for a given member of PolicyAssignmentAlterObjectTypes.
        """
        policy_handling_types = {
            PolicyAssignmentAlterObjectTypes.VIEW: PolicyHandlingTypes.ALTER_VIEW,
            PolicyAssignmentAlterObjectTypes.TABLE: PolicyHandlingTypes.ADD_TABLECOLUMN,
            PolicyAssignmentAlterObjectTypes.DYNAMICTABLE: PolicyHandlingTypes.ALTER_DYNAMICTABLE
        }
        return policy_handling_types[policy_assignment_alter_object_type]

def get_policy_assignments_info_from_object(
        object_schema: str, 
        object_name: str, 
        object_type: DbObjectType, 
        action_type: DbActionType, 
        policy_assignments_info: dict) -> list[Dict]:
    """
    Given an object action for which the policy assignments need to be handled, 
    get the policy assignments info for a specific object from the policy assignments info for all objects.
    """
    object_identifier = f"{object_schema}.{object_name}"
    policy_assignments_info_from_object={}
    
    if (
        (
            ( object_type.name in PolicyAssignmentAlterObjectTypes.__members__ and action_type.name == 'ALTER')
            or (object_type.name in PolicyAssignmentObjectTypes.__members__ and action_type.name == 'ADD')
        )
        and object_type.name in policy_assignments_info 
        and object_identifier in policy_assignments_info[object_type.name]
        ):
        if "desired_instance" not in policy_assignments_info[object_type.name][object_identifier]:
            raise ValueError(f"No desired_instance found in policy_assignments_info for object {object_identifier} with object type {object_type.name}")
        elif "assignments" in policy_assignments_info[object_type.name][object_identifier]["desired_instance"]:
            policy_assignments_info_from_object['assignments']=policy_assignments_info[object_type.name][object_identifier]["desired_instance"]["assignments"]
            policy_assignments_info_from_object['policy_handling_type']=policy_assignments_info[object_type.name][object_identifier]['policy_handling_type']
            policy_assignments_info_from_object['object_identifier']=object_identifier
    return policy_assignments_info_from_object

def create_columns_string_of_dynamictable_with_policy_assignments(columns:list[ColumnInstance], policy_assignments_of_object:list[Dict], always_create: bool = False) -> Tuple[str, str]:
    """
    Create a string defining the columns of a dynamic table containing CMP assignments on those columns.
    """
    if policy_assignments_of_object:
        policy_assignments_on_columns=[policy_assignment for policy_assignment in policy_assignments_of_object if policy_assignment["assignment_type"] == 'dynamictable_columns']
    else:
        policy_assignments_on_columns=[]
    
    #sort columns by ordinal position
    columns=sorted(columns, key=lambda x: x.ordinal_position)

    if policy_assignments_on_columns or always_create:
        columns_string='('

        for n_column, column in enumerate(columns):
            if n_column+1 != column.ordinal_position:
                raise ValueError(f"While creating a columns-string for the dynamic table {column.object_schema}.{column.object_name} the ordinal position of the column {column.column_name} does not match the position in the columns string.")
            column_identifier= f"{column.object_schema}.{column.object_name}.{column.column_name}"

            policy_assignment_on_column=next((assignment for assignment in policy_assignments_on_columns if assignment["assignment"] == column_identifier), None)
            if policy_assignment_on_column:
                if policy_assignment_on_column["argument_columns"]:
                    using_string=f"{column.column_name}"
                    for arg_column in policy_assignment_on_column["argument_columns"]:
                        using_string = f"{using_string}, {arg_column}"
                    using_string = f"USING ({using_string})"
                else:
                    using_string=''
                column_definition= f'{column.column_name} WITH MASKING POLICY {policy_assignment_on_column["policy_database"]}.{policy_assignment_on_column["policy_schema"]}.{policy_assignment_on_column["policy"]} {using_string}, '
            else:
                column_definition=f"{column.column_name}, "
            columns_string=columns_string + column_definition

        columns_string=columns_string[:-2] + ')'
    else:
        columns_string = '' 

    return columns_string

def create_columns_string_of_view_with_policy_assignments(columns:list[ColumnInstance], policy_assignments_of_object:list[Dict], always_create: bool = False) -> Tuple[str, str]:
    """
    Create a string defining the columns of a view containing CMP assignments on those columns.
    """
    if policy_assignments_of_object:
        policy_assignments_on_columns=[policy_assignment for policy_assignment in policy_assignments_of_object if policy_assignment["assignment_type"] == 'view_columns']
    else:
        policy_assignments_on_columns=[]
    
    #sort columns by ordinal position
    columns=sorted(columns, key=lambda x: x.ordinal_position)

    if policy_assignments_on_columns or always_create:
        columns_string='('
        columns_string_without_database_reference='('
        for n_column, column in enumerate(columns):
            if n_column+1 != column.ordinal_position:
                raise ValueError(f"While creating a columns-string for the view {column.object_schema}.{column.object_name} the ordinal position of the column {column.column_name} does not match the position in the columns string.")
            column_identifier= f"{column.object_schema}.{column.object_name}.{column.column_name}"
            if column.comment:
                comment_string= f"COMMENT '{column.comment}'"
            else:
                comment_string=''

            policy_assignment_on_column=next((assignment for assignment in policy_assignments_on_columns if assignment["assignment"] == column_identifier), None)
            if policy_assignment_on_column:
                if policy_assignment_on_column["argument_columns"]:
                    using_string=f"{column.column_name}"
                    for arg_column in policy_assignment_on_column["argument_columns"]:
                        using_string = f"{using_string}, {arg_column}"
                    using_string = f"USING ({using_string})"
                else:
                    using_string=''
                column_definition= f'{column.column_name} WITH MASKING POLICY {policy_assignment_on_column["policy_database"]}.{policy_assignment_on_column["policy_schema"]}.{policy_assignment_on_column["policy"]} {using_string} {comment_string}, '
                column_definition_without_database_reference= f'{column.column_name} WITH MASKING POLICY {policy_assignment_on_column["policy_schema"]}.{policy_assignment_on_column["policy"]} {using_string} {comment_string}, '
            else:
                column_definition=f"{column.column_name} {comment_string}, "
                column_definition_without_database_reference=f"{column.column_name} {comment_string}, "
            columns_string=columns_string + column_definition
            columns_string_without_database_reference=columns_string_without_database_reference + column_definition_without_database_reference

        columns_string=columns_string[:-2] + ')'
        columns_string_without_database_reference=columns_string_without_database_reference[:-2] + ')'
    else:
        columns_string = '' 
        columns_string_without_database_reference = ''

    return columns_string, columns_string_without_database_reference

def check_object_statement_for_columns_string(object_statement: str, columns: list[ColumnInstance]) -> Union[str, None]:
    """
    Check if the DDL statement of an view contains a columns_string. 
    Returns the columns string or None if no columns string was found.
    """
    columns_string=None

    for column in columns:
        if column.ordinal_position != 1:
            continue
        else:
            column_name = column.column_name
            columns_string=extract_columns_string(object_statement, column_name)
            
    return columns_string

def extract_columns_string(object_statement: str, column: str) -> Union[str, None]:
    """
    Extracts the substring between the first open bracket and the corresponding closing bracket
    that contains the given column name in the object statement.
    Ignores matches in comments.

    Args:
        s (str): The input string to extract the substring from.
        column (str): The name of the column to search for.

    Returns:
        Union[str, None]: The extracted substring, or None if the pattern is not found.
    """
    if not column:
        raise ValueError(f"While trying to extract columns string from view definition missing information about column with ordinal position 1. View definition: {object_statement}")
     
    regex = r'\(\s*' + re.escape(column) + r'\s*'
    stack = []
    ignore = False
    for i, char in enumerate(object_statement):
        if char == "'" and (i == 0 or object_statement[i-1] != "\\"):
            ignore = not ignore
        if ignore:
            continue
        if char == '(':
            stack.append('(')
        elif char == ')':
            stack.pop()
        if not stack and re.search(regex, object_statement[:i], re.IGNORECASE):
            start = re.search(regex, object_statement[:i], re.IGNORECASE).start()
            end = i
            return object_statement[start:end+1]
    return None

def replace_ignore(input_string: str, replace_pattern: str, replace_with: str, ignore_substring: str=None) -> str:
    """
    Replaces all occurences of a pattern in a string but ignores all occurences in a specified sub-string.
    This function is case insensitive.

    Args:
        input_string (str): The input string .
        replace_pattern (str): The pattern which should be replaced.
        replace_with (str): The string which should be inserted during replacement.
        ignore_substring (str): The sub-string which should be ignored.
    """
    if ignore_substring:
        replace_pattern=replace_pattern+fr'|{re.escape(ignore_substring)}'
    # TODO move function to string utils
    output_string = re.sub(
        replace_pattern,
        lambda match: match.group() if match.group() == ignore_substring else replace_with,
        input_string,
        flags=re.I
    )

    return output_string

def remove_comment_from_view_statement(object_statement: str, view_comment: str , columns_string: str=None) -> Union[str, None]:
    """
    Remove the comment string (e.g. "COMMENT= 'This is a View'") of an object statement and replace it with a whitespace.
    Ignores comments in the columns definition.
    Ignores SQL-comments.

    Args:
        object_statement (str): The input string representing the object_statement.
        comment_string (str): The comment string of the object statement.
        columns_string (str): The columns definition of the object_statement.

    Returns:
        Union[str, None]: The object_statement without the columns string.
    """
    #TODO does this function need to ignore occurences of the comment_string in SQL comments (--, //, /* */) ?
    if view_comment:
        pattern=fr"\s*comment\s*=\s*'{re.escape(view_comment)}'\s*"
        object_statement_without_comment_string = replace_ignore(input_string=object_statement, replace_pattern=pattern, replace_with=' ', ignore_substring=columns_string)
    else:
        object_statement_without_comment_string = object_statement
    return object_statement_without_comment_string

def remove_database_name_from_view_statement(view_definition: str) -> str:
    """
    Remove the database reference from the view identifier in a Snowflake View DDL statement.
    """
    pattern = fr"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(?:RECURSIVE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?{string_util.REGEX_OBJ_IDENTIFIER_3}"

    m = re.match(pattern, view_definition, re.I)

    if m:
        view_definition=view_definition.replace(m.group('database'), "", 1)

    return view_definition

def prepare_view_statement_comparison_independent_of_columns_string(view_definition: str, columns: list[ColumnInstance], comment: str, policy_assignments_info_from_object: dict = {}) -> Tuple[str, str, str]:
    """
    Prepares the comparison of the current view definition and the desired view definition during for ALTER VIEW ACTIONS.
    If the current view definition contains a columns string, creates an alternative version without the columns string.
    If the current view definition does not contain a columns string, creates an alternative version with a columns string.

    Notes:
        - Removes the database reference from the view definition.
        - Adds OR REPLACE if not already in the view definiton.
        - Removes SQL-comments at the beginning of the view definition.

    Background: 
    When querying the definition of a view (that was created without a columns definition) the columns definition is sometimes omitted 
    (e.g. INFORMATION_SCHEMA.VIEWS, or SHOW VIEWS) and sometimes included (e.g. SELECT GET_DDL) depending on the query.
    """

    view_definition = string_util.remove_comment(view_definition)

    #TODO should this function be moved to model_object_action_entitites?
    current_instance_view_definition_with_columns_string = 'current view definition with columns string not defined'
    current_instance_view_definition_without_columns_string = 'current view definition without columns string not defined'

    current_instance_view_definition = remove_database_name_from_view_statement(string_util.add_create_or_replace(view_definition) )
    current_instance_columns_string = check_object_statement_for_columns_string(object_statement=view_definition, columns=columns)

    current_instance_view_definition = remove_comment_from_view_statement(current_instance_view_definition, comment, current_instance_columns_string)
    
    if not current_instance_columns_string:
        current_instance_columns_string, _ = create_columns_string_of_view_with_policy_assignments(columns=columns, policy_assignments_of_object={}, always_create = True)
        if current_instance_columns_string:
            current_instance_view_definition_with_columns_string = string_util.add_create_or_replace(add_string_to_object_ddl(object_type=PolicyAssignmentObjectTypes.VIEW, object_statement=view_definition, input_string=current_instance_columns_string))
    else:
        current_instance_view_definition_without_columns_string = string_util.add_create_or_replace(replace_columns_string(object_statement=view_definition, old_columns_string=current_instance_columns_string, new_columns_string=''))

    current_instance_view_definition_with_columns_string = remove_database_name_from_view_statement(current_instance_view_definition_with_columns_string )
    current_instance_view_definition_without_columns_string = remove_database_name_from_view_statement(current_instance_view_definition_without_columns_string )

    return current_instance_view_definition, current_instance_view_definition_with_columns_string, current_instance_view_definition_without_columns_string

def add_policies_to_columns(object_type: PolicyAssignmentObjectTypes, object_statement: str, columns: list[ColumnInstance], policy_assignments_of_object: list[Dict]) -> Tuple[str, str]:
    """
    Add CMP assignments to the columns of a "table-like" object statement. Replaces existing columns string or adds a new columns string.
    Currently supported object types: VIEW, TABLE, DYNAMICTABLE
    """
    object_statement_with_policies_on_columns=object_statement
    
    if object_type==PolicyAssignmentObjectTypes.VIEW:
        object_statement_with_policies_on_columns_without_database_reference=object_statement
        columns_string = check_object_statement_for_columns_string(object_statement, columns)
            
        if columns_string:
            columns_string_with_policy_assignments, columns_string_with_policies_without_database_reference = add_policy_assignments_to_columns_string(columns_string=columns_string, columns=columns, policy_assignments_of_object=policy_assignments_of_object)
            if columns_string_with_policy_assignments:
                object_statement_with_policies_on_columns=replace_columns_string(object_statement, columns_string, columns_string_with_policy_assignments)
                object_statement_with_policies_on_columns_without_database_reference=replace_columns_string(object_statement, columns_string, columns_string_with_policies_without_database_reference)
        else:
            columns_string_, columns_string_without_database_reference_ =create_columns_string_of_view_with_policy_assignments(columns=columns, policy_assignments_of_object=policy_assignments_of_object)
            if columns_string_:
                object_statement_with_policies_on_columns=add_string_to_object_ddl(object_type, object_statement, columns_string_)
            if columns_string_without_database_reference_:
                object_statement_with_policies_on_columns_without_database_reference=add_string_to_object_ddl(object_type, object_statement, columns_string_without_database_reference_)

    elif object_type==PolicyAssignmentObjectTypes.DYNAMICTABLE:
        object_statement_with_policies_on_columns_without_database_reference = ''
        columns_string = check_object_statement_for_columns_string(object_statement, columns)
        
        if columns_string:
            columns_string_with_policy_assignments, _ = add_policy_assignments_to_columns_string(columns_string=columns_string, columns=columns, policy_assignments_of_object=policy_assignments_of_object)
            if columns_string_with_policy_assignments:
                object_statement_with_policies_on_columns = replace_columns_string(object_statement, columns_string, columns_string_with_policy_assignments)
        else:
            columns_string_ = create_columns_string_of_dynamictable_with_policy_assignments(columns=columns, policy_assignments_of_object=policy_assignments_of_object)
            if columns_string_:
                object_statement_with_policies_on_columns = add_string_to_object_ddl(object_type, object_statement, columns_string_)

    elif object_type==PolicyAssignmentObjectTypes.TABLE:
        object_statement_with_policies_on_columns_without_database_reference = ''
        columns_string = check_object_statement_for_columns_string(object_statement, columns)
        if not columns_string:
             raise ValueError('Columns definition not found in table DDL -> Something went wrong here!')
        else:
            columns_string_with_policy_assignments, _ = add_policy_assignments_to_columns_string(columns_string=columns_string, columns=columns, policy_assignments_of_object=policy_assignments_of_object)

            if columns_string_with_policy_assignments:
                object_statement_with_policies_on_columns=replace_columns_string(object_statement, columns_string, columns_string_with_policy_assignments)

    else:
        raise ValueError(f'Object type {object_type.value} not supported for policy assignment handling on columns!')
            
    return object_statement_with_policies_on_columns, object_statement_with_policies_on_columns_without_database_reference

def add_policy_assignments_to_columns_string(columns_string: str, columns: list[ColumnInstance], policy_assignments_of_object: list[Dict]) -> str:
    """
    Add CMP assignments to the columns definition of a table.
    """
    policy_assignments_on_columns=[policy_assignment for policy_assignment in policy_assignments_of_object if PolicyAssignmentType.get_policy_assignment_level(PolicyAssignmentType(policy_assignment["assignment_type"].upper()))==PolicyAssignmentLevel.TABLE_LEVEL_ASSIGNMENT]
    
    #sort columns by ordinal position
    columns=sorted(columns, key=lambda x: x.ordinal_position)

    if policy_assignments_on_columns:

        columns_string_without_sqlcomment = string_util.remove_comment(columns_string)
        columns_definitions=split_columns_string(columns_string_without_sqlcomment)

        #TODO write as function and align with create_columns_string_of_view_with_policy_assignments
        columns_string_with_policies='('
        columns_string_with_policies_without_database_reference='('
        for n_column, column in enumerate(columns):

            
            column_definition = columns_definitions[n_column]
            column_definition_without_database_reference = columns_definitions[n_column]
            
            # This regex_object defines all possible parameters that can be defined after the "WITH MASKING POLICY ..." part of the columns string
            regex_object=r"\s+with\s+projection\s+policy\s+|\s+projection\s+policy\s+|\s+with\s+tag\s*\(|\s+tag\s*\(|\s+comment\s*\'"
            column_definition_pre, column_definition_after = split_string_by_regex_match(regex_object, column_definition)
            
            
            column_name=get_column_name_from_column_definition(column_definition)
            if n_column+1 != column.ordinal_position:
                raise ValueError(f"While creating a columns-string for the view {column.object_schema}.{column.object_name} the ordinal position of the column {column.column_name} does not match the position in the columns string.")
            if column_name.upper() != column.column_name.upper():
                raise ValueError(f"The column name {column_name} from the column_definition does not match with the column name {column.column_name} from the list of column instances.")

            column_identifier= f"{column.object_schema}.{column.object_name}.{column.column_name}"

            policy_assignment_on_column=next((assignment for assignment in policy_assignments_on_columns if assignment["assignment"] == column_identifier), None)
            if policy_assignment_on_column:
                if policy_assignment_on_column["argument_columns"]:
                    using_string=f"{column.column_name}"
                    for arg_column in policy_assignment_on_column["argument_columns"]:
                        using_string = f"{using_string}, {arg_column}"
                    using_string = f"USING ({using_string})"
                else:
                    using_string=''
                column_definition= f'{column_definition_pre} WITH MASKING POLICY {policy_assignment_on_column["policy_database"]}.{policy_assignment_on_column["policy_schema"]}.{policy_assignment_on_column["policy"]} {using_string} {column_definition_after}, '
                column_definition_without_database_reference= f'{column_definition_pre} WITH MASKING POLICY {policy_assignment_on_column["policy_schema"]}.{policy_assignment_on_column["policy"]} {using_string}  {column_definition_after}, '            
            else:
                column_definition=f'{column_definition}, '
                column_definition_without_database_reference=f'{column_definition_without_database_reference}, '
            columns_string_with_policies=columns_string_with_policies + column_definition
            columns_string_with_policies_without_database_reference=columns_string_with_policies_without_database_reference + column_definition_without_database_reference

        columns_string_with_policies=columns_string_with_policies[:-2] + ')'
        columns_string_with_policies_without_database_reference=columns_string_with_policies_without_database_reference[:-2] + ')'

    else:
        columns_string_with_policies=''
        columns_string_with_policies_without_database_reference=''

    return columns_string_with_policies, columns_string_with_policies_without_database_reference

def get_column_name_from_column_definition(column_definition: str) -> str:
    """
    Returns the column name from a column definition.
    E.g. with column_definition = "column_1 INT" -> column_name = "column_1".
    """
    regex_column_name=r'^\s*(\S+)'
    match=re.match(regex_column_name, column_definition, flags=re.IGNORECASE)
    if match:
        column_name = match.group(1)
    return column_name

def split_columns_string(columns_string: str) -> list:
    """
    Splits a columns string by columns and ignores characters in single quotation marks and in brackets.

    Args:
        columns_string (str): The input columns string.

    Returns:
        list: List of column definitions.
    """
    columns=[]
    columns_string=columns_string[1:-1]
    stack = []
    ignore = False
    offset=0
    
    for i, char in enumerate(columns_string):
        if char == "'" and (i == 0 or columns_string[i-1] != "\\"):
            ignore = not ignore
        if ignore:
            continue
        if char == '(':
            stack.append('(')
        elif char == ')':
            stack.pop()
        if not stack and char == ',':
            end = i
            columns.append(columns_string[offset:end].strip())
            offset =  i+1
    if columns_string[offset:]:
        columns.append(columns_string[offset:].strip())
    return columns

def split_string_by_regex_match(regex_object: str, input_string: str) -> Tuple[str, str]:
    """
    Split string by regex match and ignores characters in single quotation marks and in brackets.
    Matches case-insensitive.
    """
    stack = []
    ignore = False
    ignore_i = 0

    substring_pre_match = input_string
    substring_after_match = ''
    
    for i, char in enumerate(input_string):
        if char == "'" and (i == 0 or input_string[i-1] != "\\"):
            if not ignore and not stack:
                string=input_string[ignore_i:i+1]
                match=re.search(regex_object, string , flags=re.IGNORECASE)
                if match:
                    substring_pre_match = input_string[:ignore_i+match.start()]
                    substring_after_match = input_string[ignore_i+match.start():]
                    break
            ignore = not ignore
            ignore_i = i
        if not ignore and char == ')':
            stack.pop()
            if not stack:
                ignore_i = i
        if not ignore and not stack:
            string=input_string[ignore_i:i+1]
            match=re.search(regex_object, string , flags=re.IGNORECASE)
            if match:
                substring_pre_match = input_string[:ignore_i+match.start()]
                substring_after_match = input_string[ignore_i+match.start():]
                break

        if not ignore and char == '(':
            stack.append('(')

    return substring_pre_match, substring_after_match

def add_column_with_policy(
        table_identifier: str, 
        column_name: str, 
        column_definition_without_comment: str, 
        column_comment_string: str, 
        policy_assignment_on_column: dict
        ) -> str:
    """
    Generate a statement to add a column with a policy assignment.
    """
    using_string = ""
    if policy_assignment_on_column['argument_columns']:
        using_string = f"{column_name}"
        for arg_column in policy_assignment_on_column['argument_columns']:
            using_string = f"{using_string}, {arg_column}"
        using_string = f"USING ({using_string})"

    add_column_with_policy_statement = f"ALTER TABLE {table_identifier} ADD COLUMN {column_definition_without_comment} WITH MASKING POLICY {policy_assignment_on_column['policy_database']}.{policy_assignment_on_column['policy_schema']}.{policy_assignment_on_column['policy']} {using_string} {column_comment_string}"
    return add_column_with_policy_statement

def add_policies_to_object(object_type: PolicyAssignmentObjectTypes, object_statement: str, columns: list[ColumnInstance], policy_assignments_of_object: list[Dict]) -> Tuple[str, str]:
    """
    Add an RAP assignment to a DDL statement of an Snowflake object (view or table).
    Currently supported object types: VIEW, TABLE, DYNAMICTABLE
    """
    object_statement_with_policies=object_statement
    object_statement_with_policies_without_database_reference=object_statement
    object_statement_with_policies_alternative=object_statement
    object_statement_with_policies_without_database_reference_alternative=object_statement

    if object_type==PolicyAssignmentObjectTypes.VIEW:

        columns_string = check_object_statement_for_columns_string(object_statement, columns)

        policy_assignment_on_objects=[policy_assignment for policy_assignment in policy_assignments_of_object if policy_assignment["assignment_type"]== 'views']
    
        if len(policy_assignment_on_objects) > 1:
            raise ValueError(f'There are multiple RAP assignments definied for the object {policy_assignment_on_objects[0]["assignment"]}.')
        elif len(policy_assignment_on_objects) == 1: 
            if not policy_assignment_on_objects[0]["argument_columns"]:
                raise ValueError(f'There are no assignment columns defined for the assignement of the RAP {policy_assignment_on_objects[0]["policy_database"]}.{policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} on the object {policy_assignment_on_objects["assignment"]}.')
            arg_columns_string=''
            for arg_column in policy_assignment_on_objects[0]["argument_columns"]:
                arg_columns_string = f"{arg_columns_string}, {arg_column}"
            arg_columns_string = f"ON ({arg_columns_string[2:]})"

            policy_string = f' WITH ROW ACCESS POLICY {policy_assignment_on_objects[0]["policy_database"]}.{policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} {arg_columns_string}'
            policy_string_without_database_reference = f' WITH ROW ACCESS POLICY {policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} {arg_columns_string}'

            object_statement_with_policies = add_string_to_object_ddl(object_type, object_statement, policy_string)
            object_statement_with_policies_without_database_reference = add_string_to_object_ddl(object_type, object_statement, policy_string_without_database_reference)

            #TODO write as function create_object_statement_with_policies_alternative and move to higher level
            if columns_string:
                if object_statement_with_policies.count(policy_string) ==1 and object_statement_with_policies.count(policy_string) == 1:
                    object_statement_with_policies_alternative=object_statement_with_policies.replace(policy_string, "{temp}").replace(columns_string, policy_string).replace("{temp}", columns_string)
                    object_statement_with_policies_without_database_reference_alternative=object_statement_with_policies_without_database_reference.replace(policy_string_without_database_reference, "{temp}").replace(columns_string, policy_string_without_database_reference).replace("{temp}", columns_string)
                else:
                    log.warning(f"Could not parse view definition such that the columns string is in front of the row access policy-assignment -> The policy assignments info might contain redundant information.")
                    object_statement_with_policies_alternative=object_statement_with_policies
                    object_statement_with_policies_without_database_reference_alternative=object_statement_with_policies_without_database_reference
            else:
                object_statement_with_policies_alternative=object_statement_with_policies
                object_statement_with_policies_without_database_reference_alternative=object_statement_with_policies_without_database_reference

    elif object_type==PolicyAssignmentObjectTypes.TABLE:
        policy_assignment_on_objects=[policy_assignment for policy_assignment in policy_assignments_of_object if policy_assignment["assignment_type"]== 'tables']

        #TODO write as function and align with object type 'VIEW' and 'DYNAMICTABLE'
        if len(policy_assignment_on_objects) > 1:
            raise ValueError(f'There are multiple RAP assignments definied for the object {policy_assignment_on_objects[0]["assignment"]}.')
        elif len(policy_assignment_on_objects) == 1: 
            if not policy_assignment_on_objects[0]["argument_columns"]:
                raise ValueError(f'There are no assignment columns defined for the assignement of the RAP {policy_assignment_on_objects[0]["policy_database"]}.{policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} on the object {policy_assignment_on_objects["assignment"]}.')
            arg_columns_string=''
            for arg_column in policy_assignment_on_objects[0]["argument_columns"]:
                arg_columns_string = f"{arg_columns_string}, {arg_column}"
            arg_columns_string = f"ON ({arg_columns_string[2:]})"

            policy_string = f' WITH ROW ACCESS POLICY {policy_assignment_on_objects[0]["policy_database"]}.{policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} {arg_columns_string}'

            object_statement_with_policies = add_string_to_object_ddl(object_type, object_statement, policy_string)

    elif object_type==PolicyAssignmentObjectTypes.DYNAMICTABLE:
        policy_assignment_on_objects=[policy_assignment for policy_assignment in policy_assignments_of_object if policy_assignment["assignment_type"]== 'dynamictables']

        #TODO write as function and align with object type 'VIEW' and 'TABLE'
        if len(policy_assignment_on_objects) > 1:
            raise ValueError(f'There are multiple RAP assignments definied for the object {policy_assignment_on_objects[0]["assignment"]}.')
        elif len(policy_assignment_on_objects) == 1: 
            if not policy_assignment_on_objects[0]["argument_columns"]:
                raise ValueError(f'There are no assignment columns defined for the assignement of the RAP {policy_assignment_on_objects[0]["policy_database"]}.{policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} on the object {policy_assignment_on_objects["assignment"]}.')
            arg_columns_string=''
            for arg_column in policy_assignment_on_objects[0]["argument_columns"]:
                arg_columns_string = f"{arg_columns_string}, {arg_column}"
            arg_columns_string = f"ON ({arg_columns_string[2:]})"

            policy_string = f' WITH ROW ACCESS POLICY {policy_assignment_on_objects[0]["policy_database"]}.{policy_assignment_on_objects[0]["policy_schema"]}.{policy_assignment_on_objects[0]["policy"]} {arg_columns_string}'

            object_statement_with_policies = add_string_to_object_ddl(object_type, object_statement, policy_string)

    else:
        raise ValueError(f'Object type {object_type.value} not supported for policy assignment handling on object!')
    
    return object_statement_with_policies, object_statement_with_policies_alternative, object_statement_with_policies_without_database_reference, object_statement_with_policies_without_database_reference_alternative

def replace_columns_string(object_statement: str, old_columns_string: str, new_columns_string: str) -> str:
    """
    Replace an columns_string with a new columns_string in the DDL of a Snowflake View.
    """
    object_statement = object_statement.replace(old_columns_string,new_columns_string,1)
    return object_statement

def add_string_to_object_ddl(object_type: PolicyAssignmentObjectTypes, object_statement: str, input_string: str) -> str:
    """
    Add a columns_string or an "with policy" statement to a DDL of a Snowflake object.
    Currently supported object types: VIEW, TABLE, DYNAMICTABLE
    """
    if object_type == PolicyAssignmentObjectTypes.VIEW:
        regex_object=fr"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(?:RECURSIVE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?{string_util.REGEX_OBJ_IDENTIFIER_2}"
    elif object_type == PolicyAssignmentObjectTypes.TABLE:
        regex_object=fr"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:TRANSIENT\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{string_util.REGEX_OBJ_IDENTIFIER_1}"
    elif object_type == PolicyAssignmentObjectTypes.DYNAMICTABLE:
        regex_object=fr"\s*CREATE\s+(?:OR\s+REPLACE\s+)?DYNAMIC\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{string_util.REGEX_OBJ_IDENTIFIER_1}"
    else:
        raise ValueError(f"Object type {object_type.value} not supported for add_string_to_object_ddl.")
    
    match=re.match(regex_object, object_statement, flags=re.IGNORECASE)

    if not match:
        raise ValueError(f"Object signature not found in DDL of object type {object_type.value}. Is this a valid DDL statement?\n{object_statement}")
    
    match=match[0]
    added_columns_string=f"{match} {input_string} "
    object_statement_with_columns_string, count=re.subn(
            regex_object,
            added_columns_string,
            object_statement,
            count=1,
            flags=re.IGNORECASE,
        )
    
    if count == 0:
        raise ValueError(
            f"FAILED to identify table signature in DDL. Is this a valid DDL statement?\n{object_statement}"
        )

    return object_statement_with_columns_string

def handle_policy_assignments_for_object_creation(object_type: PolicyAssignmentObjectTypes, object_statement: str, columns: list[ColumnInstance], policy_assignments_of_object: list[Dict]) -> list:
    """
    Handle the policy assignments for a new object creation based on predefined policy assignments.
    Adds the policy assignments directly to the DDL of the object.
    """
    statements=[f'USE SECONDARY ROLES {policy_assignments_of_object[0]["policy_pipeline_role"]};']
    
    object_statement, _ = add_policies_to_columns(
        object_type= object_type, 
        object_statement=object_statement, 
        columns=columns, 
        policy_assignments_of_object=policy_assignments_of_object
        )
    object_statement, _, _, _ = add_policies_to_object(
        object_type= object_type, 
        object_statement=object_statement, 
        columns=columns, 
        policy_assignments_of_object=policy_assignments_of_object
        )

    statements.append(object_statement)

    statements.append(f"USE SECONDARY ROLES NONE;")

    return statements

def handle_policy_assignments_for_alter_view_action(view_statement: str, columns: list[ColumnInstance], policy_assignments_info_from_object: dict) -> Tuple[list, str, str, str, str]:
    """
    Handle the policy assignments when altering a view.
    Adds the policy assignments directly to the DDL of the view.

    Background:
    Views are altered with CREATE OR REPLACE,
    and policy assignments need to be included in the CREATE OR REPLACE statement - otherwise they would be lost on re-creation!
    """

    statements=[f'USE SECONDARY ROLES {policy_assignments_info_from_object["assignments"][0]["policy_pipeline_role"]};']
    
    (
        view_statement_with_policies, 
        view_statement_with_policies_without_db_reference
    ) = add_policies_to_columns(
        object_type= PolicyAssignmentObjectTypes.VIEW,
        object_statement=view_statement,
        columns=columns,
        policy_assignments_of_object=policy_assignments_info_from_object["assignments"]
    )
    
    (
        _, 
        _, 
        view_statement_with_policies_without_db_reference, 
        view_statement_with_policies_without_db_reference_alternative
    )  = add_policies_to_object(
        object_type= PolicyAssignmentObjectTypes.VIEW,
        object_statement=view_statement_with_policies_without_db_reference,
        columns=columns,
        policy_assignments_of_object=policy_assignments_info_from_object["assignments"]
    )
    
    (
        view_statement_with_policies, 
        view_statement_with_policies_alternative, 
        _, 
        _
    ) = add_policies_to_object(
        object_type= PolicyAssignmentObjectTypes.VIEW,
        object_statement=view_statement_with_policies,
        columns=columns,
        policy_assignments_of_object=policy_assignments_info_from_object["assignments"]
    )

    statements.append(view_statement_with_policies)

    statements.append(f"USE SECONDARY ROLES NONE;")

    return statements, view_statement_with_policies, view_statement_with_policies_alternative, view_statement_with_policies_without_db_reference, view_statement_with_policies_without_db_reference_alternative

def handle_policy_assignments_for_alter_table_add_column_action(table_identifier: str, column: str, column_comment: str, column_definition: str, policy_assignments_info_from_object: dict= {}):
    """
    Handle the policy assignments when altering a table such that a column is added.
    Includes the policy assignments directly in the ADD COULMN statement.
    """
    statements=[]
    if column_comment:
        regex_column_comment= f"\s*comment\s*'{re.escape(column_comment)}'"
        column_definition_escaped = column_definition.replace('\\','')
        match=re.search(regex_column_comment, column_definition, flags=re.IGNORECASE)
        if not match:
            match_=re.search(regex_column_comment, column_definition_escaped, flags=re.IGNORECASE)
    else:
        match=None
        match_=None

    if match:
        column_comment_string = match.group(0)
        column_definition_without_comment = column_definition.replace(column_comment_string, '')
    elif match_:
        column_comment_string = match_.group(0)
        column_definition_without_comment = column_definition_escaped.replace(column_comment_string, '')
    else:
        column_comment_string = ''
        column_definition_without_comment = column_definition

    policy_assignment_on_column= next(
        (assignment for assignment in policy_assignments_info_from_object['assignments'] 
        if assignment['policy_type']=='column_masking_policies' 
        and assignment['assignment'].split('.')[2].upper()==column.upper()),
        None
        )

    if policy_assignment_on_column:
        
        statements.append(f'USE SECONDARY ROLES {policy_assignment_on_column["policy_pipeline_role"]}')

        statements.append(
            add_column_with_policy(
                table_identifier=table_identifier,
                column_name = column,
                column_definition_without_comment=column_definition_without_comment,
                column_comment_string=column_comment_string,
                policy_assignment_on_column=policy_assignment_on_column,
            )
        )
        statements.append(f"USE SECONDARY ROLES NONE")
    else:
        statements.append(
                    f"ALTER TABLE {table_identifier} ADD COLUMN {column_definition}"
                )
    
    return statements

class PolicyService:
    """
    Class to handle the interaction with SNOWFLAKE POLICIES.
    An instance of this class is scoped to a single database (defined by the given snow_client).
    """

    def __init__(
        self,
        policy_assignments_handler: Dict,
        policy_assignments_target_database: str,
        policy_assignments_config_file_path: str,
        policy_assignments_project: str,
        policy_assignments_info_output_folder_path: str,
        policy_assignments_repo_path: str = ''
    ):
        """
        Initializes a policy service.
        """
        self.policy_assignments_handler = policy_assignments_handler
        self.policy_assignments_info = {}
        self.policy_assignments_target_database = policy_assignments_target_database
        self.policy_assignments_config_file_path = policy_assignments_config_file_path
        self.policy_assignments_project = policy_assignments_project
        self.policy_assignments_info_output_folder_path = policy_assignments_info_output_folder_path
        self.policy_assignments_repo_path = policy_assignments_repo_path
        self.module_root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.project_config = self._get_project_config()
        self._check_target_db_in_policy_config()
        self.load_devops_variables()

    def load_devops_variables(self):
        self.build_reason = os.environ.get("BUILD_REASON")
        self.build_repository_name = os.environ.get("BUILD_REPOSITORY_NAME")
        self.system_accesstoken = os.environ.get("SYSTEM_ACCESSTOKEN")
        self.system_teamprojectid = os.environ.get("SYSTEM_TEAMPROJECTID")
        self.system_teamfoundationcollectionuri = os.environ.get("SYSTEM_TEAMFOUNDATIONCOLLECTIONURI")
        self.system_pullrequest_pullrequestid = os.environ.get("SYSTEM_PULLREQUEST_PULLREQUESTID")

    @staticmethod
    def parse_instance_for_policy_assignments_handler(instance_object: Union[InstanceObject,None]) -> Union[str,Dict]:
        """
        Parse instance object for policy assignments handler.
        """
        if not instance_object:
            return "", {}
        else:
            if 'table_columns' in instance_object.__dict__.keys():
                columns=[f"{instance_object.full_name}.{column.column_name}" for column in instance_object.table_columns]
            else:
                columns=[]

            return instance_object.full_name, columns
         
    def get_policy_assignments_info(self, get_all_assignments: bool = False) -> Dict:
        """
        Get the policy assignments configured in the SNOWFLAKE POLICIES repo for all objects in the policy assignment handler.
        """
        self._check_target_db_in_policy_config()

        self.project_config = self._get_project_config()

        policy_assignments_file_paths=self.project_config["POLICY_ASSIGNMENTS_FILES"]

        self._load_policy_assignments(policy_assignments_file_paths, get_all_assignments = get_all_assignments)

        self.policy_assignments_info = self.policy_assignments_handler
    
    def create_policy_assignments_review_page(self):
        """
        Create policy assignments review page for the pipeline log.
        """
        # TODO
        log.info()

    def save_policy_assignments_info(self):
        """
        Save policy assignments information to output folder.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M_%S")
        if self.policy_assignments_info_output_folder_path:
            os.makedirs(self.policy_assignments_info_output_folder_path, exist_ok=True)
            filename = os.path.join(self.policy_assignments_info_output_folder_path, f"policy_assignments_info.{timestamp}.json")
            log.info(f"SAVING policy assignments info as JSON file in '{filename}'")
            with open(filename, 'w') as f:
                json.dump(self.policy_assignments_info, f, indent=4)

    def _create_pr_comment(self, comment_markdown: str):
        """
        Create a comment in an Azure DevOps Pull Request.
        """
        if self.system_accesstoken:
            authorization = str(
                base64.b64encode(bytes(":" + self.system_accesstoken, "ascii")),
                "ascii",
            )
        else:
            raise ValueError(f"System Accesstoken for Azure DevOps not found while trying to create a comment in a Pull Request.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + authorization,
        }

        data = {
            "comments": [
                {"parentCommentId": 0, "content": comment_markdown, "commentType": 1}
            ],
            "status": 1,
        }

        url = f"{self.system_teamfoundationcollectionuri}{self.system_teamprojectid}/_apis/git/repositories/{self.build_repository_name}/pullRequests/{self.system_pullrequest_pullrequestid}/threads?api-version=7.0"

        response = requests.post(url=url, headers=headers, verify=True, json=data)

        if response.status_code == 200:
            api_response = json.loads(response.text)
            return api_response, True
        else:
            log.info(f"request url: {url}")
            log.info(f"request response.status_code: {response.status_code}")
            log.info(f"request response.text: {response.text}")
            raise EnvironmentError(
                f"Error while trying to create a comment on pull request {self.system_pullrequest_pullrequestid} - Pull Request Threads Rest API!"
            )

    def _check_target_db_in_policy_config(self):
        """
        Check if the target database is configured in the policy assignments config file.
        """
        if self.policy_assignments_target_database not in self.project_config["ENVIRONMENTS"].values():
            raise ValueError(f"Error while initializing the policy service. \
                            The target database {self.policy_assignments_target_database} is not defined for project {self.policy_assignments_project} in the config file {self.policy_assignments_config_file_path} !" 
                            )
        else:
            return True
                
    def _get_project_config(self):
        """
        Get list of the policy assignments JSON file paths from the config file.
        """
        config_dict = load_json(self.policy_assignments_config_file_path)
        if self.policy_assignments_project not in config_dict["PROJECT_CONFIGS"]:
            raise ValueError(f"Error while initializing the policy service. \
                             The project name {self.policy_assignments_project} is not defined in the config file {self.policy_assignments_config_file_path} !"
                             )
        else:
            project_config=config_dict["PROJECT_CONFIGS"][self.policy_assignments_project]
        return project_config
    
    def _load_policy_assignments(self, policy_assignments_file_paths: str, get_all_assignments: bool = False) -> None:
        """
        Load the policy assignments from JSON files for all objects in the policy_assignments_handler.
        """
        for policy_assignments_relative_file_path in policy_assignments_file_paths:
            
            if self.policy_assignments_repo_path:
                policy_assignments_absolute_file_path = PurePath(self.policy_assignments_repo_path).joinpath(policy_assignments_relative_file_path)

            else:
                policy_assignments_absolute_file_path = policy_assignments_relative_file_path

            if not os.path.isfile(policy_assignments_absolute_file_path):
                raise EnvironmentError(
                    f"Policy assignments file path [ '{policy_assignments_absolute_file_path}' ] is not valid."
                )

            log.debug(f"------------- LOAD policy assignments from [ '{policy_assignments_absolute_file_path}' ]")
            
            
            policy_assignments = load_json(policy_assignments_absolute_file_path)
            policy_assignments.pop("$schema")

            log.debug(f"------------- Policy assignments information from [ '{policy_assignments_absolute_file_path}' ]: {policy_assignments}\n") 

            for policy_type in ["column_masking_policies", "row_access_policies"]:
                for policy, assignments_groups in policy_assignments[policy_type].items():

                    for assignment_type, assignments_group in assignments_groups.items():

                        if assignment_type == "annotations":
                            if "person_responsible" in assignments_group:
                                person_responsible = assignments_group["person_responsible"]
                            else:
                                person_responsible = ''
                            continue

                        object_type=PolicyAssignmentType.get_object_type_from_assignment_type(assignment_type).value

                        if object_type not in self.policy_assignments_handler:
                            continue

                        if assignment_type.upper() != PolicyAssignmentType.TAGS.value or get_all_assignments:
                            for assignment, argument_columns in assignments_group.items():

                                for instance in ["current_instance", "desired_instance"]:
                                    
                                    if get_all_assignments:
                                        if policy_type == "column_masking_policies":
                                            object_identifier = assignment.rsplit('.',1)[0].upper()
                                        else:
                                            object_identifier = assignment.upper()
                                        assignment_info = {
                                                "policy_type": policy_type, 
                                                "assignment_type":assignment_type, 
                                                "policy": policy, 
                                                "assignment":assignment,
                                                "argument_columns": argument_columns,
                                                "policy_pipeline_role": self.project_config["SNOWFLAKE_CREDENTIALS"]["ROLE"], 
                                                "policy_schema":self.project_config["POLICY_SCHEMA"], 
                                                "policy_database":self.policy_assignments_target_database,
                                                "person_responsible": person_responsible}
                                        
                                        if not object_identifier in self.policy_assignments_handler[object_type]:
                                            self.policy_assignments_handler[object_type][object_identifier]={"policy_handling_type": "NEW_OBJECT", "current_instance":{"assignments":[]},"desired_instance":{"assignments":[]}}

                                        self.policy_assignments_handler[object_type][object_identifier][instance]["assignments"].append(assignment_info)

                                    elif PolicyAssignmentType.get_policy_assignment_level(PolicyAssignmentType(assignment_type.upper())) == PolicyAssignmentLevel.TABLE_LEVEL_ASSIGNMENT:

                                        object_name = assignment.rsplit('.',1)[0].upper()

                                        if (object_name in self.policy_assignments_handler[object_type]
                                            and instance in self.policy_assignments_handler[object_type][object_name]
                                            and assignment in self.policy_assignments_handler[object_type][object_name][instance]["columns"]):

                                            if "assignments" not in self.policy_assignments_handler[object_type][object_name][instance]:
                                                self.policy_assignments_handler[object_type][object_name][instance]["assignments"]=[]

                                            self.policy_assignments_handler[object_type][object_name][instance]["assignments"].append({
                                                "policy_type": policy_type, 
                                                "assignment_type":assignment_type, 
                                                "policy": policy, 
                                                "assignment":assignment,
                                                "argument_columns": argument_columns,
                                                "policy_pipeline_role": self.project_config["SNOWFLAKE_CREDENTIALS"]["ROLE"], 
                                                "policy_schema":self.project_config["POLICY_SCHEMA"], 
                                                "policy_database":self.policy_assignments_target_database,
                                                "person_responsible": person_responsible})
                                            
                                    else:
                                        object_name = assignment
                                        if (object_name in self.policy_assignments_handler[object_type]
                                            and instance in self.policy_assignments_handler[object_type][object_name]):

                                            if "assignments" not in self.policy_assignments_handler[object_type][object_name][instance]:
                                                self.policy_assignments_handler[object_type][object_name][instance]["assignments"]=[]

                                            self.policy_assignments_handler[object_type][object_name][instance]["assignments"].append({
                                                "policy_type": policy_type, 
                                                "assignment_type":assignment_type, 
                                                "policy": policy, 
                                                "assignment":assignment, 
                                                "argument_columns": argument_columns,
                                                "policy_pipeline_role": self.project_config["SNOWFLAKE_CREDENTIALS"]["ROLE"], 
                                                "policy_schema":self.project_config["POLICY_SCHEMA"], 
                                                "policy_database":self.policy_assignments_target_database,
                                                "person_responsible": person_responsible})
                                            
                        elif assignment_type.upper() == PolicyAssignmentType.TAGS.value:
                            for assignment in assignments_group:
                                for instance in ["current_instance", "desired_instance"]:
                                    object_name = assignment
                                    if (object_name in self.policy_assignments_handler[object_type]
                                        and instance in self.policy_assignments_handler[object_type][object_name]):

                                        if "assignments" not in self.policy_assignments_handler[object_type][object_name][instance]:
                                            self.policy_assignments_handler[object_type][object_name][instance]["assignments"]=[]

                                        self.policy_assignments_handler[object_type][object_name][instance]["assignments"].append({
                                            "policy_type": policy_type, 
                                            "assignment_type":assignment_type, 
                                            "policy": policy, 
                                            "assignment":assignment, 
                                            "policy_pipeline_role": self.project_config["SNOWFLAKE_CREDENTIALS"]["ROLE"], 
                                            "policy_schema":self.project_config["POLICY_SCHEMA"], 
                                            "policy_database":self.policy_assignments_target_database,
                                            "person_responsible": person_responsible})
                                        
        log.debug(f"------------- Policy assignments information for handler objects:\n {self.policy_assignments_handler}")                            

    def create_azure_devops_pr_comment_from_policy_assignments_info(self):
        """
        Create a comment a pull request in Azure DevOps containing the policy assignments info.
        """
        if self.build_reason == "PullRequest":
            comment_markdown_policy_assignments_info = self._parse_policy_assignments_info()
            if comment_markdown_policy_assignments_info:
                self._create_pr_comment(comment_markdown_policy_assignments_info)
                             
    def _parse_policy_assignments_info(
        self
    ) -> str:
        """
        Parse the policy assignments info in the format of a markdown table.
        """
        comment_markdown_policy_assignments_info = ""

        if self.policy_assignments_info:

            comment_markdown_policy_assignments_info = f"""
            The following policy assignments are handled during the deployment on target database {self.policy_assignments_target_database} in projetct {self.policy_assignments_project} 
            (Note: This is a summary. Please see the pipeline artifacts for the full information in JSON format!): \n"""

            for object_type in self.policy_assignments_info.keys():

                for object_identifier, policy_handling in self.policy_assignments_info[object_type].items():

                    for instance in ['current_instance', 'desired_instance']:

                        table = "| Policy Type | Policy | Assignment |\n"
                        table += "| --- | --- | --- |\n"

                        if instance in policy_handling and "assignments" in policy_handling[instance]:
                            for assignment in policy_handling[instance]["assignments"]:
                                row = f"| {assignment['policy_type']} | {assignment['policy']} | {assignment['assignment']} |\n"
                                table += row

                        if instance == 'current_instance':
                            table_current_assignments=table
                        else:
                            table_desired_assignments=table

                    comment_markdown_policy_assignments_info += (
                        f"##  {policy_handling['policy_handling_type']} {object_type} {object_identifier}\n\n ### current assignments \n {table_current_assignments}\n\n ### future assignments \n {table_desired_assignments}"
                    )

        return comment_markdown_policy_assignments_info
        
