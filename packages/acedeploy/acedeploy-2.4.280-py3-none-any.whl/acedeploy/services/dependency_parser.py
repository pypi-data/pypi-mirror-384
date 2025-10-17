import logging
import re
from typing import List

import networkx as nx

import aceutils.graphtools as graphtools
import aceutils.string_util as string_util
from acedeploy.core.model_solution_entities import SolutionFunction, SolutionObject
from acedeploy.core.model_sql_entities import DbFunctionType, DbObjectType
from acedeploy.services.solution_service import SolutionClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class DependencyParser(object):
    """
    Parser which enables searching for dependencies in sql DDL statements.
    """

    def __init__(self, solution_client: SolutionClient):
        """
            Inits a new dependency parser client
        Args:
            solution_client: SolutionClient
        """
        self._solution_client = solution_client
        self._dependency_graph = nx.DiGraph()
        self._dependency_subgraphs = []

    def build_full_dependency_graph(
        self,
        object_types=(
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
            DbObjectType.TASK,
            DbObjectType.DYNAMICTABLE,
            DbObjectType.NETWORKRULE
        ),
    ):
        """
        Build a dependency graph for all objects in the solution client
        """
        relevant_objects = [
            o
            for o in self._solution_client.all_objects
            if o.object_type in object_types
        ]
        self.function_name_list = [
            f"{o.schema}.{o.name}"
            for o in relevant_objects
            if o.object_type == DbObjectType.FUNCTION
        ]
        log.info(f"BUILD dependency GRAPH for [ '{len(relevant_objects)}' ] objects")
        for obj in relevant_objects:
            self._dependency_graph.add_node(obj)
            dependencies = self._get_dependencies(obj)
            for dependency in dependencies:
                log.debug(f"DEPENDENCY for [ '{obj.id}' ] FOUND [ '{dependency.id}' ]")
                self._dependency_graph.add_edge(dependency, obj)
        self._dependency_graph = graphtools.remove_self_loops(self._dependency_graph)

    def _get_dependencies(self, obj: SolutionObject):
        """
        Given an SolutionObject, return all objects that this object depends on.
        """
        dependencies_objects_names = self._parse_object_dependencies(
            obj.content, obj.object_type
        )
        dependencies_objects = []
        for dependency_object_name in dependencies_objects_names:
            dependency = self._solution_client.get_object_by_full_name(
                full_name=dependency_object_name,
                include_schemas=False,
            )
            if dependency:
                dependencies_objects.append(dependency)
            else:
                dependency = (
                    self._solution_client.get_parameterobject_by_name_without_params(
                        dependency_object_name
                    )
                )
                if dependency:
                    dependencies_objects.append(dependency)
                else:
                    log.info(
                        f"DEPENDENCY [ '{dependency_object_name}' ] for [ '{obj.id}' ] NOT in solution"
                    )

        return dependencies_objects

    def filter_graph_by_object_ids(self, object_ids, mode):
        """
        Given a list of object IDs, remove all objects from the graph which are not required for the creation of those objects.
        mode = 'meta_deployment' selects objects required for meta deployment.
        mode = 'target_deployment' selects objects required for target deployment.
        mode = 'plot' selects objects for plotting.
        """
        objects = [self._solution_client.get_object_by_id(oid) for oid in object_ids]
        log.info(
            f"FILTER dependency GRAPH with MODE [ '{mode}' ] for [ '{len(object_ids)}' ] objects"
        )
        self.filter_graph(objects, mode)

    def filter_graph_by_object_names(self, full_object_names, mode):
        """
        Given a list of full object names, remove all objects from the graph which are not required for the creation of those objects.
        mode = 'meta_deployment' selects objects required for meta deployment.
        mode = 'target_deployment' selects objects required for target deployment.
        mode = 'plot' selects objects for plotting.
        """
        objects = [
            self._solution_client.get_object_by_full_name(
                full_name=full_name,
                include_schemas=False,
            )
            for full_name in full_object_names
        ]
        log.info(
            f"FILTER dependency GRAPH with MODE [ '{mode}' ] for [ '{len(full_object_names)}' ] objects"
        )
        self.filter_graph(objects, mode)

    def filter_graph(self, objects, mode):
        """
        Given a list of objects, remove all objects from the graph which are not required for the creation of those objects.
        mode = 'meta_deployment' selects objects required for meta deployment.
        mode = 'target_deployment' selects objects required for target deployment.
        mode = 'plot' selects objects for plotting.
        """
        if set(objects) == set(self._dependency_graph.nodes()):
            # no need to filter if all nodes will be used
            log.debug("SKIP filter dependency graph: no objects need to be removed")
        elif mode.lower() == "meta_deployment":
            log.debug(f"GET dependency graph succesors for [ {len(objects)} ] objects")
            dependency_graph_successors = graphtools.filter_graph(
                self._dependency_graph, objects, "include_successors"
            )
            successor_nodes = [n for n in dependency_graph_successors.nodes()]
            log.debug(
                f"GET dependency graph predecessors for [ {len(successor_nodes)} ] objects"
            )
            self._dependency_graph = graphtools.filter_graph(
                self._dependency_graph, successor_nodes, "include_predecessors"
            )
        elif mode.lower() == "target_deployment":
            # in a target deployment, we assume that 'objects' contains all views that were deployed in the meta deployment.
            # therefore, it is not necessary to add successors in a target deployment, since all views that might need to be
            # updated already appear in 'objects'.
            log.debug(
                f"GET dependency graph for given objects ([ {len(objects)} ] objects)"
            )
            self._dependency_graph = graphtools.filter_graph(
                self._dependency_graph, objects, "given_nodes_only"
            )
        elif mode.lower() == "plot":
            # when plotting a graph, we want to look at all objects that directly depend on the given object
            # and that are a prerequisite of a given object
            log.debug(f"GET dependency graph succesors for [ {len(objects)} ] objects")
            dependency_graph_successors = graphtools.filter_graph(
                self._dependency_graph, objects, "include_successors"
            )
            successor_nodes = [n for n in dependency_graph_successors.nodes()]
            log.debug(
                f"GET dependency graph predecessors for [ {len(objects)} ] objects"
            )
            dependency_graph_predecessors = graphtools.filter_graph(
                self._dependency_graph, objects, "include_predecessors"
            )
            predecessors_nodes = [n for n in dependency_graph_predecessors.nodes()]
            relevant_nodes = set().union(successor_nodes, predecessors_nodes)
            self._dependency_graph = graphtools.filter_graph(
                self._dependency_graph, relevant_nodes, "given_nodes_only"
            )
        else:
            raise ValueError(
                f"Mode [ '{mode}' ] is unknown. Valid modes: [ 'meta_deployment', 'target_deployment', 'plot' ]"
            )

    def build_subgraphs(self):
        """
        Build dependency subgraphs (graphs with no interdependencies).
        """
        log.info("BUILD independent SUBGRAPHS")
        self._dependency_subgraphs = graphtools.split_graph_into_subgraphs(
            self._dependency_graph
        )

    def get_ordered_objects(self):
        """
        For each subgraph, return a list of ordered objects.
        """
        log.info(f"ORDER [ '{len(self._dependency_subgraphs)}' ] SUBGRAPHS")
        return [graphtools.get_ordered_objects(g) for g in self._dependency_subgraphs]

    def _parse_object_dependencies(
        self, statement: str, object_type: DbObjectType
    ) -> List[str]:
        """
        For a given statement and object type, return all dependent object names
        """
        mapping = {
            DbObjectType.SCHEMA: DependencyParser._dummy_parser_empty_result,
            DbObjectType.TABLE: DependencyParser._parse_object_dependencies_tables,
            DbObjectType.EXTERNALTABLE: DependencyParser._parse_object_dependencies_externaltables,
            DbObjectType.VIEW: self._parse_object_dependencies_views,
            DbObjectType.MATERIALIZEDVIEW: self._parse_object_dependencies_views,
            DbObjectType.FUNCTION: self._parse_object_dependencies_functions,
            DbObjectType.PROCEDURE: DependencyParser._dummy_parser_empty_result,
            DbObjectType.STAGE: DependencyParser._parse_object_dependencies_stages,
            DbObjectType.FILEFORMAT: DependencyParser._dummy_parser_empty_result,
            DbObjectType.STREAM: DependencyParser._parse_object_dependencies_streams,
            DbObjectType.TASK: DependencyParser._parse_object_dependencies_tasks,
            DbObjectType.PIPE: DependencyParser._parse_object_dependencies_pipes,
            DbObjectType.SEQUENCE: DependencyParser._dummy_parser_empty_result,
            DbObjectType.MASKINGPOLICY: self._parse_object_dependencies_policies,
            DbObjectType.ROWACCESSPOLICY: self._parse_object_dependencies_policies,
            DbObjectType.DYNAMICTABLE: self._parse_object_dependencies_dynamictables,
            DbObjectType.NETWORKRULE: self._dummy_parser_empty_result
        }
        return mapping[object_type](statement)

    @staticmethod
    def _dummy_parser_empty_result(*_, **__) -> List[str]:
        """
        For all objects without dependencies, return an empty list
        """
        return []

    def _parse_object_dependencies_functions(self, statement: str) -> List[str]:
        """
        Parses function dependencies from a given statement
        Will only parse for SQL UDFs, all other types do not need to be validated.
        """
        return DependencyParser._parse_object_dependencies_functions_static(
            statement, self.function_name_list
        )

    @staticmethod
    def _parse_object_dependencies_functions_static(
        statement: str, function_name_list: List[str]
    ) -> List[str]:
        """
        Parses function dependencies from a given statement
        Will only parse for SQL UDFs, all other types do not need to be validated.
        """
        if SolutionFunction.get_function_type(statement) in (DbFunctionType.SQL,):
            definition_regex = re.compile(
                r"(?:\$\$|')(?P<definition>.*)(?:\$\$|')", re.IGNORECASE | re.DOTALL
            )
            definition = definition_regex.search(statement).group("definition")
            return DependencyParser._parse_object_dependencies_views_functions_policies_static(
                definition, function_name_list
            )
        else:
            return []

    def _parse_object_dependencies_views(self, statement: str) -> List[str]:
        """
        Parses view dependencies from a given statement
        Will check for FROM statements, explicit and implicit joins and functions
        """
        return DependencyParser._parse_object_dependencies_views_static(
                statement, self.function_name_list
            )

    def _parse_object_dependencies_policies(self, statement: str) -> List[str]:
        """
        Parses policy dependencies from a given statement
        Will check for FROM statements, explicit and implicit joins and functions
        """
        return (
            DependencyParser._parse_object_dependencies_views_functions_policies_static(
                statement, self.function_name_list
            )
        )

    @staticmethod
    def _parse_object_dependencies_views_static(
        statement: str, function_name_list: List[str] = None
    ) -> List[str]:
        """
            Parses view dependencies from a given statement
            Will check for FROM statements, explicit and implicit joins, and policies
        Args:
            statement: str - the whole sql statement (multiple lines)
            function_name_list: List[str] - (optional) list of function names which might be a dependency for this statement
        """
        if function_name_list is None:
            function_name_list = []

        dependencies = []
        row_access_policy_pattern = re.compile(
            r"(?:[\s\)])ROW\s+ACCESS\s+POLICY\s+(?P<referenced_policy>[\w\.\"]+)\s+ON\s*",
            re.IGNORECASE | re.DOTALL,
        )
        row_access_policy_matches = row_access_policy_pattern.findall(statement)
        dependencies.extend(row_access_policy_matches)

        masking_policy_pattern = re.compile(
            r"(?:[\s\)])MASKING\s+POLICY\s+(?P<referenced_policy>[\w\.\"]+)\s*",
            re.IGNORECASE | re.DOTALL,
        )
        masking_policy_matches = masking_policy_pattern.findall(statement)
        dependencies.extend(masking_policy_matches)

        dependencies.extend(
            DependencyParser._parse_object_dependencies_views_functions_policies_static(
                statement, function_name_list
            )
        )
    
        return dependencies

    @staticmethod
    def _parse_object_dependencies_views_functions_policies_static(
        statement: str, function_name_list: List[str]
    ) -> List[str]:
        """
            Parses view and function dependencies from a given statement
            Will check for FROM statements, explicit and implicit joins
        Args:
            statement: str - the whole sql statement (multiple lines)
            function_name_list: List[str] = [] - list of function names which might be a dependency for this statement
        """
        statement_without_comment = string_util.remove_comment(statement)
        statement_clean = string_util.remove_text_in_quotes(statement_without_comment)

        explicit_pattern = re.compile(
            r"(?:\s|^)(?:FROM|JOIN)\s+(?:\(\s*?(?!SELECT))?@?([\"\w\-\_\.]+)",
            re.IGNORECASE | re.DOTALL,
        )
        implicit_pattern1 = re.compile(
            r"(?:\s|^)FROM\s+?(?P<listOfObjects>[\"\w\-\_\.]+(?:\s*?AS)?\s*?\w*?(\s*?,\s*?([\"\w\-\_\.]+)(\s*?AS)?\s*\w*\s?)+)",
            re.IGNORECASE | re.DOTALL,
        )
        implicit_pattern2 = re.compile(
            r"(?:^|,)\s*?(?P<objectname>[\"\w\-\_\.]+)", re.IGNORECASE | re.DOTALL
        )

        object_dependencies = []
        object_dependencies.extend(explicit_pattern.findall(statement_clean))

        implicit_objects = implicit_pattern1.finditer(statement_clean)
        for implicit_object in implicit_objects:
            object_dependencies.extend(
                implicit_pattern2.findall(implicit_object.groupdict()["listOfObjects"])
            )

        # find file formats
        fileformat_pattern = re.compile(
            r"file_format\s*=>\s*'?([\"\w\-\_\.]+)'?",
            re.IGNORECASE | re.DOTALL,
        )
        object_dependencies.extend(
            fileformat_pattern.findall(statement_without_comment)
        )

        # find streams
        stream_pattern = re.compile(
            r"stream\s*=>\s*'([\"\w\-\_\.]+)'",
            re.IGNORECASE | re.DOTALL,
        )
        object_dependencies.extend(stream_pattern.findall(statement_without_comment))

        if function_name_list:
            function_names = f"{'|'.join([re.escape(n) for n in function_name_list])}"
            function_pattern = re.compile(
                r"\b(?P<functionName>{function_names})\s*\(".format(
                    function_names=function_names
                ),
                re.IGNORECASE | re.DOTALL,
            )
            object_dependencies.extend(
                function_pattern.findall(statement_clean.replace('"', ""))
            )  # replace double quotes to match functions referenced with double quotes

        # remove duplicates
        object_dependencies = list(
            dict.fromkeys(object_dependencies)
        )  # remove duplicates

        # matches to be skipped:
        # finds constructs like "WHERE EXTRACT(YEAR FROM DAT_BESTAETIGUNG) >= YEAR(CURRENT_TIMESTAMP)"
        extract_function_pattern = re.compile(
            r"(?<=EXTRACT)\s?\([\"\w\-\_\.\s]*(?:FROM|JOIN)\s+?([\"\w\-\_\.]+)",
            re.IGNORECASE | re.DOTALL,
        )
        extract_matches = set(extract_function_pattern.findall(statement_clean))
        # finds references to INFORMATION_SCHEMA
        system_objects = re.compile(r"information_schema", re.IGNORECASE)
        # function to remove matches to be skipped
        false_dependencies = lambda obj: (
            system_objects.match(obj) or (obj in extract_matches)
        )

        object_dependencies = [
            obj for obj in object_dependencies if not false_dependencies(obj)
        ]

        return object_dependencies

    @staticmethod
    def _parse_object_dependencies_tables(statement: str) -> List[str]:
        """
            Parses table dependencies from a given statement
            Will check for foreign keys and sequences and policies
        Args:
            statement: str - the whole sql statement (multiple lines)
        """
        statement = string_util.remove_comment(statement)
        statement = string_util.remove_text_in_quotes(statement)

        dependencies = []

        sequence_pattern = re.compile(
            r"\sDEFAULT\s+?([\"\w\-\_\.]+)\.NEXTVAL", re.IGNORECASE | re.DOTALL
        )
        sequence_matches = sequence_pattern.findall(statement)
        dependencies.extend(sequence_matches)

        fk_pattern = re.compile(
            r"(?:[\s\)])REFERENCES\s+(?P<referenced_table>[\w\.\"]+)\s*\([\w, ]+\)",
            re.IGNORECASE | re.DOTALL,
        )
        fk_matches = fk_pattern.findall(statement)
        dependencies.extend(fk_matches)

        masking_policy_pattern = re.compile(
            r"(?:[\s\)])MASKING\s+POLICY\s+(?P<referenced_policy>[\w\.\"]+)\s*",
            re.IGNORECASE | re.DOTALL,
        )
        masking_policy_matches = masking_policy_pattern.findall(statement)
        dependencies.extend(masking_policy_matches)

        row_access_policy_pattern = re.compile(
            r"(?:[\s\)])ROW\s+ACCESS\s+POLICY\s+(?P<referenced_policy>[\w\.\"]+)\s+ON\s*",
            re.IGNORECASE | re.DOTALL,
        )
        row_access_policy_matches = row_access_policy_pattern.findall(statement)
        dependencies.extend(row_access_policy_matches)

        return list(set(dependencies))

    @staticmethod
    def _parse_object_dependencies_externaltables(statement: str) -> List[str]:
        """
            Parses external table dependencies from a given statement
        Args:
            statement: str - the whole sql statement (multiple lines)
        """
        statement = string_util.remove_comment(statement)
        statement = string_util.remove_text_in_quotes(statement)

        dependencies = []

        fileformat_pattern = re.compile(
            r"\b(?:FILE_FORMAT|FORMAT_NAME)\s*=\s*\'?(?P<fileformat>[\w\.\"]+)",
            re.IGNORECASE | re.DOTALL,
        )
        s = fileformat_pattern.search(statement)
        if s:
            dependencies.append(s.group("fileformat"))

        stage_pattern = re.compile(
            r"\bLOCATION\s*=\s*\@?(?P<stage>[\w\.\"]+)",
            re.IGNORECASE | re.DOTALL,
        )
        s = stage_pattern.search(statement)
        if s:
            dependencies.append(s.group("stage"))

        return list(set(dependencies))

    @staticmethod
    def _parse_object_dependencies_streams(statement: str) -> List[str]:
        """
        Parses dependencies for streams (tables, views, stages, directories, external tables, dynamic tables).
        """
        statement = string_util.remove_comment(statement)

        dependencies = []

        # Table/View/External Table/Dynamic Table dependencies
        object_types = "table|view|external table|dynamic table"
        object_pattern = re.compile(
            rf"on\s+({object_types})\s+((?:\"[^\"]+\"\.)?\"?[a-zA-Z0-9_]+\"?(?:\.[a-zA-Z0-9_]+|(?:\"\.[^\"]+\")?)*)",
            re.IGNORECASE,
        )
        for match in object_pattern.finditer(statement):
            dependencies.append(match.group(2).strip())

        # Stage dependencies
        stage_pattern = re.compile(
            r"on\s+stage\s+(@?(?:\"[^\"]+\"\.)?\"?[a-zA-Z0-9_]+\"?(?:\.[a-zA-Z0-9_]+|(?:\"\.[^\"]+\")?)*)",
            re.IGNORECASE,
        )
        for match in stage_pattern.finditer(statement):
            dependencies.append(match.group(1).lstrip("@").strip())

        # Directory dependencies (with @)
        directory_pattern = re.compile(
            r"on\s+directory\s*\(\s*@((?:\"[^\"]+\"\.)?\"?[a-zA-Z0-9_]+\"?(?:\.[a-zA-Z0-9_]+|(?:\"\.[^\"]+\")?)*)\s*\)",
            re.IGNORECASE,
        )
        for match in directory_pattern.finditer(statement):
            dependencies.append(match.group(1).strip())

        return dependencies

    @staticmethod
    def _parse_object_dependencies_tasks(statement: str) -> List[str]:
        """
            Parses table or view dependencies from a given TASK definition
        Args:
            statement: str - the whole sql statement (multiple lines)
        """
        statement = string_util.remove_comment(statement)
        statement = string_util.remove_text_in_quotes(statement)

        pattern = re.compile(
            r"\sAFTER\s+(?P<previous_tasks>(([\w\.\"]+\s*,\s*)*[\w\.\"]+))",
            re.IGNORECASE | re.DOTALL,
        )
        s = pattern.search(statement)
        if s:
            previous_tasks = s.group("previous_tasks")
            previous_tasks_list = [t.strip() for t in previous_tasks.split(",")]
            return previous_tasks_list
        else:
            return []

    @staticmethod
    def _parse_object_dependencies_stages(statement: str) -> List[str]:
        """
            Parses table or view dependencies from a given STAGE definition
        Args:
            statement: str - the whole sql statement (multiple lines)
        """
        statement = string_util.remove_comment(statement)

        pattern = re.compile(
            r"\b(?:FILE_FORMAT|FORMAT_NAME)\s*=\s*\'?(?P<fileformat>[\w\.\"]+)",
            re.IGNORECASE | re.DOTALL,
        )
        s = pattern.search(statement)
        if s:
            return [s.group("fileformat")]
        else:
            return []

    @staticmethod
    def _parse_object_dependencies_pipes(statement: str) -> List[str]:
        """
            Parses table or view dependencies from a given PIPE definition
        Args:
            statement: str - the whole sql statement (multiple lines)
        """
        dependencies = []
        statement = string_util.remove_comment(statement)

        pattern_stages = re.compile(
            r"\sFROM\s+\@(?P<stage>[\w\.\"]+)", re.IGNORECASE | re.DOTALL
        )
        s = pattern_stages.search(statement)
        if s:
            dependencies.append(s.group("stage"))

        pattern_copy_into = re.compile(
            r"\bCOPY\s+INTO\s+(?P<table>[\w\.\"]+)", re.IGNORECASE | re.DOTALL
        )
        s = pattern_copy_into.search(statement)
        if s:
            dependencies.append(s.group("table"))

        pattern_fileformat = re.compile(
            r"\b(?:FILE_FORMAT|FORMAT_NAME)\s*=\s*\'?(?P<fileformat>[\w\.\"]+)",
            re.IGNORECASE | re.DOTALL,
        )
        s = pattern_fileformat.search(statement)
        if s:
            dependencies.append(s.group("fileformat"))

        return dependencies

    def _parse_object_dependencies_dynamictables(self, statement: str) -> List[str]:
        """
        Parses dynamic table dependencies from a given statement
        Will check for FROM statements, explicit and implicit joins and functions
        """
        return DependencyParser._parse_object_dependencies_dynamictables_static(
                statement, self.function_name_list
            )

    @staticmethod
    def _parse_object_dependencies_dynamictables_static(
        statement: str, function_name_list: List[str] = None
    ) -> List[str]:
        """
            Parses dynamic table dependencies from a given statement
            Will check for FROM statements, explicit and implicit joins, and policies
        Args:
            statement: str - the whole sql statement (multiple lines)
            function_name_list: List[str] - (optional) list of function names which might be a dependency for this statement
        """
        if function_name_list is None:
            function_name_list = []

        dependencies = []
        
        # TODO is this the best way of getting the dependencies? -> use column INPUTS from DYNAMIC_TABLE_GRAPH_HISTORY instead?
        dependencies.extend(
            DependencyParser._parse_object_dependencies_views_static(
                statement, function_name_list
            )
        )
    
        return dependencies