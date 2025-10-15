# SPDX-License-Identifier: GPL-2.0-or-later
# pylint: disable=R0801
"""
repository helpers
"""

import subprocess
import re
from pathlib import Path
from typing import List, Optional, Union
from bs4 import BeautifulSoup  # type: ignore
from .repo import Repo, _logger, shortest_path


class SvnInfo:
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """
    container class obtaining and holding svn repository information

    Attributes
    ----------
    kind : str
      node kind of TARGET
    url : str
        URL of TARGET in the repository
    relative_url : str
        repository-relative URL of TARGET
    repos_root_url : str
        root URL of repository
    repos_uuid : str
        UUID of repository
    revision : str
        specified or implied revision
    last_changed_revision : str
        last change of TARGET at or before revision
    last_changed_date : str
        date of last_changed_revision
    last_changed_author : str
        author of last_changed_revision
    wc_root : str
        root of TARGETs working copy
    schedule : str
        normal,add,delete,replace
    depth : str
        checkout depth of TARGET in WC
    """

    def __init__(self, uri: Union[str, Path]):
        self.update(uri)

    def update(self, uri: Optional[Union[str, Path]] = None):
        """
        update svn info using data scraped from uri, which can be both a
        local checkout or a remote repository
        """
        if uri is not None:
            self.uri = uri
        info = BeautifulSoup(
            subprocess.run(
                ["svn", "info", "--xml", self.uri], capture_output=True, check=False
            ).stdout.decode(),
            "xml",
        ).find("entry")
        repo = info.find("repository")
        workingcopy = info.find("wc-info")
        commit = info.find("commit")

        self.kind = info["kind"]
        self.url = info.find("url").text
        self.relative_url = info.find("relative-url").text
        self.revision = info["revision"]
        if repo is not None:
            self.repos_root_url = repo.find("root").text
            self.repos_uuid = repo.find("uuid").text
        else:
            self.repos_root_url = ""
            self.repos_uuid = ""

        if commit is not None:
            self.last_changed_revision = commit["revision"]
            self.last_changed_date = commit.find("date").text
            self.last_changed_author = commit.find("author").text
        else:
            self.last_changed_revision = ""
            self.last_changed_date = ""
            self.last_changed_author = ""

        if workingcopy is not None:
            self.wc_root = workingcopy.find("wcroot-abspath").text
            self.schedule = workingcopy.find("schedule").text
            self.depth = workingcopy.find("depth").text
        else:
            self.wc_root = ""
            self.schedule = ""
            self.depth = ""


class SvnRepo(Repo):
    """
    svn repository helper implementation
    """

    vcs = "svn"

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        url: Optional[str],
        path: Path,
        target_commit: Optional[str] = None,
        tag: Optional[str] = None,
        branch: Optional[str] = None,
        remote_path: Optional[str] = None,
        options: Optional[List[str]] = None,
        quiet: Optional[bool] = False,
    ):
        rurl = url
        rpath = remote_path
        infotarget = ""
        if (path / ".svn").exists():
            infotarget = str(path)
        elif url is not None:
            infotarget = url
        self.info = SvnInfo(infotarget)
        if url is not None:
            rurl = self.info.repos_root_url
            toks = self.info.relative_url[2:].split("/")
            if toks[0] == "tags" and len(toks) > 1:
                tag = toks[1]
                rpath = "/".join(toks[2:])
            elif toks[0] == "branches" and len(toks) > 1:
                branch = toks[1]
                rpath = "/".join(toks[2:])
            elif toks[0] == "trunk":
                rpath = "/".join(toks[1:])
            if rpath == "":
                rpath = remote_path
        super().__init__(
            rurl,
            path,
            target_commit=target_commit,
            tag=tag,
            branch=branch,
            remote_path=rpath,
            options=options,
            quiet=quiet,
        )

    @property
    def vcs_dir(self):
        return self.path / ".svn"

    def load_repo_info(self):
        if self.url is None:
            self.url = self.info.url
        self.target_commit = self.info.revision

    def add(self, file: Path):
        _logger.info("Adding %s", file)
        self.execute(f"add --parents {file}".split(), check=False, capture_output=True)

    def remove(self, file: Path):
        _logger.info("Removing %s", file)
        self.execute(f"rm --force {file}".split(), check=False, capture_output=True)

    def checkout(self):
        cmd = ["co"]
        if self.target_commit is not None:
            cmd.append("-r" + self.target_commit)
        cmd.extend(self.options)

        url = self.url
        if self.tag is not None:
            url += f"/tags/{self.tag}"
        elif self.branch is not None:
            if self.branch == "trunk":
                url += "/trunk"
            else:
                url += f"/branches/{self.branch}"
        else:
            url += "/trunk"
        if self.remote_path is not None:
            url += f"/{self.remote_path}"
        cmd.append(url)

        cmd.append(self.path)
        _logger.info("Checking out %s into %s", url, shortest_path(self.path))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.execute(cmd, cwd=self.path.parent)
        self.info.update(self.path)

    def update(self):
        _logger.info("Updating %s", shortest_path(self.path))
        cmd = ["update"]
        if self.target_commit is not None:
            cmd.append(f"-r{self.target_commit}")
        self.execute(cmd)
        self.info.update(self.path)

    def status(self):
        stat = (
            self.info.relative_url
            + "\n"
            + self.execute("status", capture_output=True).stdout.decode()
        )

        dirty = ""
        if self.is_dirty():
            dirty = "[D] "

        _logger.info("%s: %s%s\n", shortest_path(self.path), dirty, stat.strip())

    def has_externals(self, relpath: str = ".", recursive: bool = True):
        if not (self.path / relpath).exists():
            return False
        if recursive:
            cmd = "pget -R".split()
        else:
            cmd = "pget".split()
        cmd.append("svn:externals")
        cmd.append(relpath)

        if recursive:
            return (
                self.execute(cmd, capture_output=True).stdout.decode().strip() != ". -"
            )

        return self.execute(cmd, check=False, capture_output=True).returncode == 0

    def is_dirty(self, relpath: str = "."):
        out = self.execute(
            f"st --xml --depth immediates {relpath}".split(),
            capture_output=True,
        ).stdout
        soup = BeautifulSoup(out, "xml")
        regex = re.compile("unversioned|modified|added|deleted")
        return bool(soup.find_all("wc-status", attrs={"item": regex}))

    def list_externals(self, relpath: str = ".") -> List[Repo]:
        return_list: List[Repo] = []

        if not (self.path / relpath).exists():
            return return_list

        try:
            out = self.execute(
                f"pget svn:externals {relpath}".split(), capture_output=True
            )

            for line in out.stdout.decode().split("\n"):
                if len(line.strip()) > 0:
                    _logger.debug("processing external: '%s'", line)
                    ext = line.split()
                    options = []
                    target_commit = None
                    for opt in ext[1:-1]:
                        if re.match("^-r[0-9]+$", opt):
                            target_commit = opt[2:]
                        else:
                            options.append(opt)

                    return_list.append(
                        SvnRepo(
                            ext[-1],
                            self.path / relpath / ext[0],
                            target_commit=target_commit,
                            options=options,
                        )
                    )
        except subprocess.CalledProcessError:
            pass

        return return_list

    def list_files(self, printout: bool = True):
        return self._return_local_files(
            self.execute("ls -R".split(), capture_output=True).stdout.decode(), printout
        )

    def list_folders(self, printout: bool = True):
        return self._return_local_folders(
            self.execute("ls -R".split(), capture_output=True).stdout.decode(), printout
        )

    def list_tags(self, printout: bool = True):
        target = "^"
        if self.url is not None:
            target = self.url
        return self._return_tags(
            self.execute(["ls", target + "/tags"], capture_output=True).stdout.decode(),
            printout,
        )

    def rm_externals(self, relpath: str = "."):
        _logger.info("Delete svn:externals property from %s", relpath)
        self.execute(f"pdel svn:externals {relpath}".split())

    def reset_externals(self, relpath: str = "."):
        _logger.info("Restore svn:externals property for %s", relpath)
        self.execute(f"revert --depth empty {relpath}".split())

    def add_ignores(self, *patterns: Path):
        ignores_map = {}
        for pattern in patterns:
            relpath = pattern.relative_to(self.path).parent
            if relpath not in ignores_map:
                ignores_map[relpath] = (
                    False,
                    [
                        i.strip()
                        for i in self.execute(
                            f"pget svn:ignore {relpath}".split(),
                            check=False,
                            capture_output=True,
                        )
                        .stdout.decode()
                        .splitlines()
                    ],
                )
            if pattern.name in ignores_map[relpath][1]:
                _logger.info(
                    "Ignore rule %s already exists in %s", pattern.name, relpath
                )
            else:
                _logger.info("Append ignore rule %s to %s", pattern.name, relpath)
                ignores_map[relpath] = (True, [*ignores_map[relpath][1], pattern.name])

        for relpath, ignores in ignores_map.items():
            if ignores[0]:
                self.add(relpath)

                cmd = "pset svn:ignore".split()
                cmd.append("\n".join([i for i in sorted(ignores[1]) if i]))
                cmd.append(str(relpath))
                self.execute(cmd)

    def del_ignores(self, *patterns: Path):
        ignores_map = {}
        for pattern in patterns:
            relpath = pattern.relative_to(self.path).parent
            if relpath not in ignores_map:
                ignores_map[relpath] = (
                    False,
                    [
                        i.strip()
                        for i in self.execute(
                            f"pget svn:ignore {relpath}".split(),
                            check=False,
                            capture_output=True,
                        )
                        .stdout.decode()
                        .splitlines()
                    ],
                )
            if pattern.name in ignores_map[relpath][1]:
                _logger.info("Delete ignore rule %s from %s", pattern, relpath)
                ignores_map[relpath] = (
                    True,
                    [i for i in ignores_map[relpath][1] if i != pattern.name],
                )

        for relpath, ignores in ignores_map.items():
            if ignores[0]:
                cmd = "pset svn:ignore".split()
                cmd.append("\n".join([i for i in sorted(ignores[1]) if i]))
                cmd.append(str(relpath))
                self.execute(cmd)

    def commit(self, message: str, files: List[Path]):
        raise NotImplementedError()

    @staticmethod
    def check_remote(url):
        cmd = f"svn info {url}".split()
        # pylint: disable=subprocess-run-check
        return subprocess.run(cmd, capture_output=True).returncode == 0
