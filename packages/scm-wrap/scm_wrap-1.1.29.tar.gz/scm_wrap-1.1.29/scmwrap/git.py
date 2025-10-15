# SPDX-License-Identifier: GPL-2.0-or-later
# pylint: disable=R0801
"""
repository helpers
"""

import os
import subprocess
import shutil
import json
import tempfile
from pathlib import Path
from typing import List, Optional, Type, Set
from configparser import ConfigParser
from .repo import Repo, _logger, shortest_path
from .svn import SvnRepo


class GitRepo(Repo):
    """
    git repository helper implementation
    """

    vcs = "git"
    global_options = ["-c", "advice.detachedHead=false"]
    ignore_file_name = ".gitignore"
    _ignores_head = """### automatic handled block START, do not edit following lines"""
    _ignores_tail = """### automatic handled block END, do not edit previous lines"""

    @property
    def vcs_dir(self):
        return self.path / ".git"

    def load_repo_info(self):
        if self.url is None:
            self.url = self._get_url()

        if self.path is None and self.url is None:
            # no info can be retrieved, exit now
            return

        repo = self
        path = self.path
        cleanup_path = False
        if path is None or not os.path.isdir(self.vcs_dir):
            path = tempfile.mkdtemp()
            repo = GitRepo(
                self.url,
                Path(path),
                self.target_commit,
                self.tag,
                self.branch,
                self.remote_path,
                self.options,
                self.quiet,
            )
            cleanup_path = True

        if not os.path.isdir(path) or not os.path.isdir(repo.vcs_dir):
            # if no checkout is available, perform a shallow check out in a temp directory
            # to access metadata
            cmd = "clone --filter=blob:none --no-checkout --depth 1 "

            if self._get_tag() is not None:
                cmd += f"-b {self._get_tag()} "
            elif self.branch is not None:
                cmd += f"-b {self.branch} "
            cmd += f"{self.url} {path}"
            repo.execute(
                cmd.split(),
                capture_output=True,
                check=False,
            )

        if self.target_commit is None:
            self.target_commit = (
                repo.execute("rev-parse HEAD".split(), capture_output=True)
                .stdout.decode()
                .strip()
            )
            if self.target_commit == "":
                self.target_commit = None
        if self.branch is None:
            self.branch = (
                repo.__get_current_branch()  # pylint: disable=protected-access
            )
        if self.tag is None:
            _tag = (
                repo.execute(
                    "tag --points-at".split(),
                    capture_output=True,
                    check=False,
                )
                .stdout.decode()
                .strip()
            )

            self.tag = self._parse_tags(_tag)

        if cleanup_path:
            shutil.rmtree(path, ignore_errors=True)

    def _parse_tags(self, tag: str) -> Optional[str | List[str]]:
        _tag = tag.split()

        if len(_tag) == 0:
            _tag = None
        elif len(tag) == 1:
            _tag = tag[0]

        return _tag

    def _get_tag(self) -> Optional[str]:
        if isinstance(self.tag, list):
            return self.tag[0]

        return self.tag

    def _get_url(self) -> Optional[str]:
        remotes = (
            self.execute(
                "remote".split(),
                capture_output=True,
                check=False,
            )
            .stdout.decode()
            .strip()
            .split()
        )

        if len(remotes) < 1:
            return None

        remote = remotes[0]

        if "origin" in remotes:
            remote = "origin"

        return (
            self.execute(
                f"remote get-url {remote}".split(),
                capture_output=True,
                check=False,
            )
            .stdout.decode()
            .strip()
        )

    def add(self, file: Path):
        _logger.info("Adding %s", file)
        self.execute(f"add {file}".split())

    def remove(self, file: Path):
        _logger.info("Removing %s", file)
        self.execute(f"rm -r --ignore-unmatch {file}".split())

    def checkout(self):
        cmd = ["clone"]
        cmd.extend(self.options)
        if self._get_tag() is not None:
            cmd.extend(["-b", self._get_tag()])
        elif self.branch is not None:
            cmd.extend(["-b", self.branch])
        if self.remote_path is not None:
            cmd.extend(["--filter=blob:none", "--no-checkout"])
        cmd.append(self.url)
        cmd.append(self.path)
        _logger.info("Cloning %s into %s", self.url, shortest_path(self.path))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.execute(cmd, cwd=self.path.parent)

        if self.remote_path is not None:
            self.execute(["sparse-checkout", "set", "--no-cone", self.remote_path])

        if self.target_commit is not None or self.remote_path is not None:
            cmd = ["checkout"]
            if self.target_commit is not None:
                cmd.append(self.target_commit)
            self.execute(cmd)

    def update(self):
        _logger.info("Updating %s", shortest_path(self.path))
        self.execute("fetch")
        if self._get_tag() is not None:
            self.execute(f"checkout {self._get_tag()}".split())
        elif self.target_commit is not None:
            self.execute(f"checkout {self.target_commit}".split())
        else:
            if self.branch is not None:
                self.execute(f"checkout {self.branch}".split())
            self.execute("merge")

    def status(self):
        stat = ""
        cmd = ["status", "-s"]
        if self.__get_current_branch() is None:
            if self._get_tag() is not None:
                # Use self.tag instead of self._get_tag() in order to print all related tags
                stat = f" tag: {self.tag}"
            else:
                stat = f" @{self.target_commit}"
            stat += "\n"
        else:
            cmd.append("-b")

        stat += self.execute(cmd, capture_output=True).stdout.decode()

        dirty = ""
        if self.is_dirty():
            dirty = "[D] "

        _logger.info("%s: %s%s\n", shortest_path(self.path), dirty, stat.strip())

    def has_externals(self, relpath: str = ".", recursive: bool = True):
        return (self.path / relpath / ".gitmodules").exists() or (
            self.path / relpath / "git_externals.json"
        ).exists()

    def is_dirty(self, relpath: str = "."):
        return (
            # local modifications
            self.execute("status -s".split(), capture_output=True)
            .stdout.decode()
            .strip()
            != ""
            # unpushed commit
            or self.execute(
                "log --branches --not --remotes --no-walk --oneline".split(),
                capture_output=True,
            )
            .stdout.decode()
            .strip()
            != ""
            # local commit out of tree
            or self.execute(
                "describe --contains --all HEAD".split(),
                capture_output=True,
                check=False,
            ).returncode
            != 0
        )

    def __list_git_submodules(self, relpath: str = ".") -> List[Repo]:
        return_list: List[Repo] = []
        config = ConfigParser()
        config.read(f"{relpath}/.gitmodules")
        for section in config.sections():
            options = []
            if "path" not in config[section]:
                raise ValueError("Can't find path option in .gitmodule config")
            path = config[section]["path"].strip()

            if "url" not in config[section]:
                raise ValueError("Can't find url option in .gitmodule config")
            url = config[section]["url"].strip()

            if "branch" in config[section]:
                branch = config[section]["branch"].strip()
                if branch == ".":
                    branch = self.__get_current_branch()
                if branch is not None:
                    options.extend(["-b", branch])

            out = self.execute(
                f"-C {relpath} ls-tree -d HEAD {path}".split(),
                capture_output=True,
            )
            tree_props = out.stdout.decode().strip().split()
            if not tree_props[-1] == path:
                raise ValueError("Can't find commit sha1 with ls-tree")
            commit = tree_props[-2]
            return_list.append(
                GitRepo(
                    url,
                    self.path / relpath / path,
                    target_commit=commit,
                    options=options,
                )
            )
        return return_list

    def __list_git_externals(self, jdata, relpath: str = ".") -> List[Repo]:
        return_list: List[Repo] = []
        for url, cfg in json.loads(jdata.read()).items():
            target_commit = cfg.get("ref", None)
            tag = cfg.get("tag", None)
            branch = cfg.get("branch", None)
            options: List[str] = []

            if "targets" not in cfg:
                _logger.info("incomplete external, missing targets for repo: %s", url)
                continue

            # targets object contains actual external data
            for src, targets in cfg["targets"].items():
                remote_path = src
                if src in [".", "./"]:
                    remote_path = None
                for target in targets:
                    # here we generate single externals for each target directory
                    # in output repository
                    repoclass: Optional[Type[Repo]] = None
                    if cfg["vcs"] == "git":
                        repoclass = GitRepo
                        if src not in [".", "./"]:
                            _logger.warning(
                                "converting external '%s' with custom source path '%s', "
                                "check out project configs, something might need an update",
                                url,
                                src,
                            )
                    elif cfg["vcs"] == "svn":
                        repoclass = SvnRepo

                    if repoclass is None:
                        _logger.warning(
                            "unable to handle vcs '%s' for external: %s",
                            cfg["vcs"],
                            url,
                        )
                    else:
                        return_list.append(
                            repoclass(
                                url,
                                self.path / relpath / target,
                                target_commit=target_commit,
                                tag=tag,
                                branch=branch,
                                remote_path=remote_path,
                                options=options,
                            )
                        )

        return return_list

    def list_externals(self, relpath: str = ".") -> List[Repo]:
        return_list: List[Repo] = []
        if os.path.exists(f"{relpath}/.gitmodules"):
            try:
                return_list = self.__list_git_submodules(relpath)
            except (subprocess.CalledProcessError, ValueError) as error:
                _logger.error("unable to read submodule properties: %s", error)
        if os.path.exists(f"{relpath}/git_externals.json"):
            try:
                with open(  # pylint: disable=unspecified-encoding
                    f"{relpath}/git_externals.json", "r"
                ) as jdata:
                    return_list = self.__list_git_externals(jdata, relpath)
            except (subprocess.CalledProcessError, ValueError) as error:
                _logger.error("unable to read git_externals properties: %s", error)

        return return_list

    def list_files(self, printout: bool = True):
        return self._return_local_files(
            self.execute("ls-files", capture_output=True).stdout.decode(),
            printout,
        )

    def list_folders(self, printout: bool = True):
        return self._return_local_folders(
            self.execute(
                "ls-tree -rd --name-only HEAD".split(), capture_output=True
            ).stdout.decode(),
            printout,
        )

    def list_tags(self, printout: bool = True):
        cmd = ["ls-remote", "--tags"]
        if self.url is not None:
            cmd.append(self.url)
        return self._return_tags(
            self.execute(cmd, capture_output=True).stdout.decode(),
            printout,
        )

    def rm_externals(self, relpath: str = "."):
        if os.path.exists(f"{relpath}/.gitmodules"):
            _logger.info(
                "Delete git submodules from %s/%s", shortest_path(self.path), relpath
            )
            try:
                self.execute(f"-C {relpath} submodule deinit .".split())
                config = ConfigParser()
                config.read(f"{relpath}/.gitmodules")
                paths = []
                for section in config.sections():
                    if "path" not in config[section]:
                        raise ValueError("Can't find path option in .gitmodule config")
                    paths.append(config[section]["path"].strip())

                self.execute(f"-C {relpath} rm .gitmodules".split())
                for path in paths:
                    self.execute(f"-C {relpath} rm {path}".split())
                shutil.rmtree(f"{relpath}/.git/modules", ignore_errors=True)

            except (subprocess.CalledProcessError, ValueError) as error:
                _logger.info("unable to read submodule properties: %s", error)
        if os.path.exists(f"{relpath}/git_externals.json"):
            _logger.info(
                "Delete git externals from %s/%s", shortest_path(self.path), relpath
            )
            with open(  # pylint: disable=unspecified-encoding
                f"{relpath}/git_externals.json", "r"
            ) as jdata:
                for cfg in json.loads(jdata.read()).values():
                    if "targets" not in cfg:
                        continue
                    # targets object contains actual external data
                    for targets in cfg["targets"].values():
                        for target in targets:
                            shutil.rmtree(f"{relpath}/{target}", ignore_errors=True)
            self.execute(f"-C {relpath} rm git_externals.json".split())
            shutil.rmtree(f"{relpath}/.git_externals", ignore_errors=True)

    def reset_externals(self, relpath: str = "."):
        _logger.info(
            "try restoring git_externals.json and .gitmodules %s/%s",
            shortest_path(self.path),
            relpath,
        )
        try:
            self.execute(
                f"restore --staged --worktree {relpath}/git_externals.json".split(),
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass
        try:
            self.execute(
                f"restore --staged --worktree {relpath}/.gitmodules".split(),
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass

    def _get_ignores(self):
        ignore_file_path = self.path / self.ignore_file_name

        ignores_content = []
        if Path(ignore_file_path).is_file():
            with open(  # pylint: disable=unspecified-encoding
                ignore_file_path, "r"
            ) as ignore_file:
                head_found = False
                for line in ignore_file.read().splitlines():
                    line = line.strip()
                    if line == self._ignores_head:
                        head_found = True
                    elif line == self._ignores_tail:
                        break
                    elif head_found:
                        ignores_content.append(line)
        return set(ignores_content)

    def _update_ignores(self, ignore_set: Set[str]):
        if self._get_ignores() == ignore_set:
            _logger.debug("ignores unchanged")
            return

        ignore_file_path = self.path / self.ignore_file_name
        ignores = sorted(list(ignore_set))

        ignore_head = []
        ignore_tail = []
        if Path(ignore_file_path).is_file():
            with open(  # pylint: disable=unspecified-encoding
                ignore_file_path, "r"
            ) as ignore_file:
                head_found = False
                tail_found = False
                for line in ignore_file.read().splitlines():
                    line = line.strip()
                    if line not in ignores:
                        if line == self._ignores_head:
                            head_found = True
                        elif line == self._ignores_tail:
                            tail_found = True
                        else:
                            if not head_found:
                                ignore_head.append(line)
                            elif tail_found:
                                ignore_tail.append(line)

        with open(  # pylint: disable=unspecified-encoding
            ignore_file_path, "w"
        ) as ignore_file:
            ignore_file.write("\n".join(ignore_head))
            ignore_file.write(f"\n{self._ignores_head}\n")
            ignore_file.write("\n".join(ignores))
            ignore_file.write(f"\n{self._ignores_tail}\n")
            ignore_file.write("\n".join(ignore_tail))

        self.add(ignore_file_path)

    def add_ignores(self, *patterns: Path):
        self._update_ignores(
            self._get_ignores()
            | set(str(p.relative_to(self.path)).strip() for p in patterns)
        )

    def del_ignores(self, *patterns: Path):
        self._update_ignores(
            self._get_ignores()
            - set(str(p.relative_to(self.path)).strip() for p in patterns)
        )

    def commit(self, message: str, files: List[Path]):
        raise NotImplementedError()

    def __get_current_branch(self):
        branch = (
            self.execute(
                "rev-parse --abbrev-ref --symbolic-full-name HEAD".split(),
                capture_output=True,
            )
            .stdout.decode()
            .strip()
        )
        if branch == "HEAD":
            return None
        return branch

    @staticmethod
    def check_remote(url):
        cmd = f"git ls-remote {url}".split()
        # pylint: disable=subprocess-run-check
        return subprocess.run(cmd, capture_output=True).returncode == 0
