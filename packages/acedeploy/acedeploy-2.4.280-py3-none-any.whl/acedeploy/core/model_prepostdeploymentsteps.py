import re
from enum import Enum
from typing import Dict, List

import git

import aceutils.file_util as file_util
import aceutils.string_util as string_util


class PreOrPostDeploymentScriptsExecutionOptions(Enum):
    """
    Available option for the execution of pre/postdeployment scripts.
    Applies to all scripts.
    """
    ALL = "all"
    GIT = "git"
    NONE = "none"


class PreOrPostDeploymentScriptTarget(Enum):
    TARGET = "targetDatabase"
    META = "metaDatabase"


class PreOrPostDeploymentScriptType(Enum):
    """
    Enum for valid types of post deployment scripts
    """

    PYTHON = "PYTHON"
    SQL = "SQL"

    @classmethod
    def get_type_from_path(cls, script_path: str) -> "PreOrPostDeploymentScriptType":
        """
            Converts a file path based on file extension to a DeploymentScriptType instance
        Args:
            script_type: str - absolute script path to file
        Raises:
            ValueError - If file path is None or empty
            NotImplementedError - If file extension is not supported
        Returns:
            Instance of PreOrPostDeploymentScriptType
        """
        if script_path is None or script_path == "":
            raise ValueError("script_path should not be empty")

        if script_path.lower().endswith(".sql"):
            return PreOrPostDeploymentScriptType.SQL
        if script_path.lower().endswith(".py"):
            return PreOrPostDeploymentScriptType.PYTHON
        raise NotImplementedError(f"script type not supported for '{script_path}'.")


class PreOrPostDeploymenStep(object):
    """
    Descripts a post deployment step as part of the acedeploy deployment
    """

    def __init__(
        self,
        path: str,
        git_change_type: git.DiffIndex.change_type = None,
        string_replace_dict: Dict[str, str] = None,
        regex_filter_list: List[str] = None,
    ):
        """
            Inits a new instance
        Args:
            path: str - absolute path to file
            git_change_type: git.DiffIndex.change_type - type of git change associated to this file (None if no change or unknown)
            string_replace_dict: Dict[str,str] - optional, contains information about strings which need to be replaced in SQL DDLs
            regex_filter_list: List[str] - optional, contains a list of regular expressions (case insensitive). If any regex matches against the content, an exception will be raised
        """
        if string_replace_dict is None:
            string_replace_dict = {}
        if regex_filter_list is None:
            regex_filter_list = []
        self.path = path
        self.git_change_type = git_change_type
        self.type = PreOrPostDeploymentScriptType.get_type_from_path(self.path)
        if self.type == PreOrPostDeploymentScriptType.PYTHON:
            raise Exception("Python pre/postdeployment files are not allowed")
        content = self._load_sql_file(path)
        self.content = string_util.string_replace_by_dict(content, string_replace_dict)
        unapproved_command = self._contains_forbidden_command(
            self.content, regex_filter_list
        )
        if unapproved_command:
            raise Exception(
                f"Pre/Postdeployment script [ '{self.path}' ] contains forbidden statement [ '{unapproved_command}' ]."
            )
        self.execute_step = None  # boolean: can be set later to indicate if this step should be run during deployment
        self.target = PreOrPostDeploymentScriptTarget.TARGET # PreOrPostDeploymentScriptTarget: inidicates if this step should be run on the target database or the meta database


    def set_target(self, target: PreOrPostDeploymentScriptTarget) -> None:
        self.target = target


    def set_execute_step(self, pre_and_postdeployment_execution: PreOrPostDeploymentScriptsExecutionOptions, step_condition: str) -> None:
        if pre_and_postdeployment_execution == PreOrPostDeploymentScriptsExecutionOptions.NONE:
            self.execute_step = False
        elif pre_and_postdeployment_execution == PreOrPostDeploymentScriptsExecutionOptions.ALL:
            if step_condition == "onChange":
                raise ValueError("It is not allowed to use 'onChange' when 'all' pre/postdeployment scripts should be executed (ignoreGitInformation = True)")
            elif step_condition == "never":
                self.execute_step = False
            else:
                self.execute_step = True
        elif pre_and_postdeployment_execution == PreOrPostDeploymentScriptsExecutionOptions.GIT:
            if step_condition == "always":
                self.execute_step = True
            elif step_condition == "onChange":
                self.execute_step = self.git_change_type in ("A", "R", "M")
            elif step_condition == "never":
                self.execute_step = False
            else:
                raise ValueError("step_condition must be one of 'always', 'onChange', 'never'.")


    @staticmethod
    def _load_sql_file(file_path: str) -> str:
        """
        Load a sql file from a given file path.
        """
        content = file_util.load(file_path)
        return string_util.remove_comment_after_statement(content)

    @staticmethod
    def _contains_forbidden_command(content: str, filter_list: List[str]) -> str:
        """
        Check if given sql file content matches against one of the regular expressions given in filter_list (case insensitive).
        If yes, return that command.
        """
        cleaned_content = string_util.remove_text_in_quotes(
            string_util.remove_comment(content)
        )
        for forbidden_words in filter_list:
            result = re.search(forbidden_words, cleaned_content, re.IGNORECASE)
            if result:
                return result.group()
        return False
