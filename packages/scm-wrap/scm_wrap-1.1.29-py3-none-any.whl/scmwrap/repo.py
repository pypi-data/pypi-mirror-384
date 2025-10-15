# SPDX-License-Identifier: GPL-2.0-or-later
# pylint: disable=R0801
"""
repository helpers
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Union, List, Optional
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


def shortest_path(path: Path) -> Path:
    """
    return the shortest representation of input path:
    - a relative path if it is inside current directory
    - absolute path otherwise
    """
    try:
        return path.resolve().relative_to(Path(".").resolve())
    except ValueError:
        return path.resolve()


class Repo(ABC):
    # pylint: disable=too-many-public-methods,too-many-instance-attributes
    """
    base abstract class for repository helper implementations, defines the
    required public methods
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        url: Optional[str],
        path: Path,
        target_commit: Optional[str] = None,
        tag: Optional[str | List[str]] = None,
        branch: Optional[str] = None,
        remote_path: Optional[str] = None,
        options: Optional[List[str]] = None,
        quiet: Optional[bool] = False,
    ):
        self.url = url
        self.path = path
        self.target_commit = target_commit
        self.tag = tag
        self.branch = branch
        self.remote_path = remote_path
        self.options = []
        self.quiet = quiet
        if isinstance(options, list):
            self.options = options

    @property
    @abstractmethod
    def vcs(self) -> str:
        """
        return vcs type string
        """

    global_options: List[str] = []
    """
    optional list of cmdline options to be used for each command
    """

    @property
    @abstractmethod
    def vcs_dir(self) -> Path:
        """
        return resolved vcs private directory
        """

    def __str__(self):
        res = f"{shortest_path(self.path)} ("
        if self.remote_path is not None:
            res += f"{self.remote_path} "
        res += f"{self.vcs}: {self.url} -"
        if self.tag is not None:
            res += f" T'{self.tag}'"
        elif self.branch is not None:
            res += f" b'{self.branch}'"
        if self.target_commit is not None:
            res += f" r{self.target_commit}"
        res += f" {self.options})"
        return res

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return (
            self.url == other.url
            and self.path == other.path
            and self.target_commit == other.target_commit
            and self.tag == other.tag
            and self.branch == other.branch
            and self.remote_path == other.remote_path
            and self.options == other.options
        )

    @abstractmethod
    def load_repo_info(self):
        """
        Try and load all local info from local or remote repo, this should include:
            - branch
            - tag
            - target_commit
            - url
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def add(self, file: Path):
        """
        Add a file/directory to current local repo,
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def remove(self, file: Path):
        """
        Remove a file/directory from current local repo,
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def checkout(self):
        """
        perform a fresh checkout of the remote repository into local path,
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def update(self):
        """
        update the local copy of the repository pulling remote changes
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def status(self):
        """
        print out the local repository status message
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def has_externals(self, relpath: str = ".", recursive: bool = True):
        """
        return True if local repository has implementation defined externals
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def is_dirty(self, relpath: str = "."):
        """
        return True if repository has local modification
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def list_externals(self, relpath: str = "."):
        """
        return a list of external subprojects defined in this repository as a list of Repo
        instances
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def list_files(self, printout: bool = True):
        """
        return the list of files handled by this repository prefixed by the repo path
        if printout is true also print to console
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def list_folders(self, printout: bool = True):
        """
        return list of folder commited in this repository
        if printout is true also print to console
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def list_tags(self, printout: bool = True):
        """
        return a list of tags from this repository
        if printout is true also print to console
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def rm_externals(self, relpath: str = "."):
        """
        remove external subprojects defined in this repository
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def reset_externals(self, relpath: str = "."):
        """
        reset externals to remote original state
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def add_ignores(self, *patterns: Path):
        """
        add ignore patterns to local repository ignores list
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def del_ignores(self, *patterns: Path):
        """
        delete ignore patterns from local repository ignores list
        MUST be implemented by actual Repo helper implementation
        """

    @abstractmethod
    def commit(self, message: str, files: List[Path]):
        """
        commit files with defined message
        MUST be implemented by actual Repo helper implementation
        """

    def execute(self, command_and_args: Union[str, List[str]], **subprocess_kwargs):
        """
        execute a command in the local repository path
        """
        if isinstance(command_and_args, str):
            command_and_args = [command_and_args]
        cmd = [self.vcs]
        cmd.extend(self.global_options)
        cmd.extend([str(arg) for arg in command_and_args])
        if "cwd" not in subprocess_kwargs:
            subprocess_kwargs["cwd"] = self.path
        if "check" not in subprocess_kwargs:
            subprocess_kwargs["check"] = True
        if self.quiet:
            subprocess_kwargs["capture_output"] = True
        _logger.debug(
            "executing command: '%s', (env: %s)", " ".join(cmd), subprocess_kwargs
        )
        # pylint: disable=subprocess-run-check
        return subprocess.run(cmd, **subprocess_kwargs)

    def exists(self):
        """
        return True if local repository exists
        """
        return self.path.exists()

    def _return_local_files(self, output_list: str, printout: bool):
        return_list = [str(self.path / line) for line in output_list.splitlines(False)]

        if printout:
            _logger.info(
                "Listing %s files:\n%s",
                shortest_path(self.path),
                "\n".join(return_list),
            )
        return return_list

    def _return_local_folders(self, output_list: str, printout: bool):
        return_list = []
        for line in output_list.splitlines(False):
            if os.path.isdir(self.path / line):
                return_list.append(str(self.path / line))

        if printout:
            _logger.info(
                "Listing %s folders:\n%s",
                shortest_path(self.path),
                "\n".join(return_list),
            )
        return return_list

    def _return_tags(self, taglist: str, printout: bool):
        return_list = []
        for line in taglist.splitlines(False):
            if "tags/" in line:
                line = line[line.find("tags/") + len("tags/") :]
            return_list.append(line.rstrip("/"))

        if printout:
            _logger.info("Listing %s tags:\n%s", self.url, "\n".join(return_list))
        return return_list

    @staticmethod
    @abstractmethod
    def check_remote(url: str):
        """
        return True if remote url is a valid repository,
        MUST be implemented by actual Repo helper implementation
        """
