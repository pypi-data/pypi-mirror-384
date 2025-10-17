import logging
import os
import re

import git
from acedeploy.core.model_git_entities import GitFile
from aceutils.logger import LoggingAdapter, LogOperation, LogStatus

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class GitClient(object):
    """
    Client for any operation regarding the underlying git repository
    """

    def __init__(
        self, solution_root_path: str, git_tag_regex: str, deployment_mode: str
    ) -> None:
        """
            Inits a new git client.
        Args:
            solution_root_path: str - root path of git repo
            git_tag_regex: str - regular expression by which to find the starting commit
            deployment_mode: str - 'validate' or any other string
        """
        self.git_tag_regex = git_tag_regex
        self.deployment_mode = deployment_mode
        self.solution_root_path = solution_root_path
        self.repository = git.Repo(self.solution_root_path)
        self.commit_start = None
        self.commit_end = None

    def get_diff_filelist(self):
        """
        Evaluates the changes found in the solution git repository
        and returns a collection of changes with meta information.

        Will take latest commit that matches git_tag_regex as first commit.
        Will take current commit as last commit.

        For influence of deployment_mode, see doc/deployment_settings.md
        """
        # region get commit start and commit end information
        tags_sorted = sorted(
            self.repository.tags, key=lambda t: t.commit.committed_datetime
        )
        commit_start = None
        self.commit_end = self.repository.commit("HEAD")
        for tag in reversed(tags_sorted):
            if re.search(self.git_tag_regex, tag.name):
                commit_start = tag.commit
                break
        if commit_start is None:
            raise ValueError(
                f"ERROR: GIT mode REQUIRES at least one tag WITH format [ '{self.git_tag_regex}' ]"
            )
        else:
            self.commit_start = commit_start
        # endregion get commit start and commit end information

        # region get changes
        if self.deployment_mode.casefold() == "validate":
            common_ancestor = self.repository.merge_base(
                self.commit_start, self.commit_end
            )
            log.info(
                f"FOUND start commit: {self.commit_start.name_rev} AND end commit: {self.commit_end.name_rev} WITH common ancestor(s) {[c.name_rev for c in common_ancestor]}",
                operation=LogOperation.GIT,
                status=LogStatus.SUCCESS,
            )
            log.info(
                f"USE diff from {[c.name_rev for c in common_ancestor]} to {self.commit_end.name_rev} (equivalent to 'git diff {self.commit_start.hexsha}...{self.commit_end.hexsha}')"
            )
            diffs = self.commit_end.diff(common_ancestor, R=True)
        else:
            log.info(
                f"FOUND start commit: {self.commit_start.name_rev} AND end commit: {self.commit_end.name_rev}",
                operation=LogOperation.GIT,
                status=LogStatus.SUCCESS,
            )
            log.info(
                f"USE diff from {self.commit_start.name_rev} to {self.commit_end.name_rev} (equivalent to 'git diff {self.commit_start.hexsha}..{self.commit_end.hexsha}')"
            )
            diffs = self.commit_start.diff(self.commit_end)

        git_changed_files_list = [
            GitFile(
                os.path.join(
                    self.solution_root_path, diff.b_rawpath.decode(encoding="UTF-8")
                ),
                diff.change_type,
            )
            for diff in diffs
        ]
        # endregion get changes

        log.info(
            f"SUMMARY git: ADDED {len([f for f in git_changed_files_list if f.change_type == 'A'])} file(s), MODIFIED {len([f for f in git_changed_files_list if f.change_type in ('M', 'R')])} file(s), DELETED {len([f for f in git_changed_files_list if f.change_type == 'D'])} file(s)",
            operation=LogOperation.GIT,
            status=LogStatus.SUCCESS,
        )

        for f in git_changed_files_list:
            if f.change_type == "A":
                change_verb = "ADDED"
            elif f.change_type in ("M", "R"):
                change_verb = "MODIFIED"
            elif f.change_type == "D":
                change_verb = "DELETED"
            log.debug(f"{change_verb} file [ '{f.file_name}' ]")

        return git_changed_files_list
