import git


class GitFile(object):
    """
    New object to store git information on a file
    """

    def __init__(
        self, file_name: str, git_change_type: git.DiffIndex.change_type
    ) -> None:
        self.file_name = str(file_name)
        self.change_type = git_change_type.upper()
