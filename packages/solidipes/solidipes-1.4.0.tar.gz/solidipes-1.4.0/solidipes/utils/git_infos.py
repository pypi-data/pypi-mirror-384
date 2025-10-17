import os

from git import InvalidGitRepositoryError, Repo

from solidipes.utils import get_git_repository, get_git_root


class GitInfos:
    def __init__(self) -> None:
        """Create an object with the git information of the current repository.
        If the current directory is not a git repository, the attributes will be None.
        """
        self.origin = None
        self.root = None
        self.repository = None

        try:
            self.root = get_git_root()
            self.repository = get_git_repository()
            self._set_gitlab_uri()

        except InvalidGitRepositoryError:
            pass

    def _set_gitlab_uri(self) -> None:
        dir_path = os.getcwd()
        self.repository = Repo(dir_path, search_parent_directories=True)
        remotes = self.repository.remotes

        if "origin" not in remotes:
            return

        origin = [e for e in remotes.origin.urls][0]

        if origin.startswith("git@"):
            origin = origin.replace("git@", "")
            _split = origin.split(":")
            origin = "https://" + _split[0] + "/" + _split[1]

        self.origin = origin.replace(".git", "")
