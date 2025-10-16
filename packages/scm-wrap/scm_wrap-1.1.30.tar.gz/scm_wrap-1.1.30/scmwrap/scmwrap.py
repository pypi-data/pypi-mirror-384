# SPDX-License-Identifier: GPL-2.0-or-later
"""
SCM Wrapper module
"""

from pathlib import Path
from typing import List, Optional, Type
from .repo import Repo
from .git import GitRepo
from .svn import SvnRepo


# pylint: disable=too-many-positional-arguments
def ScmWrap(
    url: Optional[str],
    path: Path,
    target_commit: Optional[str] = None,
    tag: Optional[str] = None,
    branch: Optional[str] = None,
    remote_path: Optional[str] = None,
    options: Optional[List[str]] = None,
    parentsearch: bool = False,
    quiet: bool = False,
) -> Repo:
    """
    This function will infer the correct repository type using local path
    (if checkout is present) and remote repo information and return an
    initialized instance

    if paretnsearch is True, search for local repository also in parent
    directories relative to path
    """
    # pylint: disable=too-many-arguments,invalid-name,duplicate-code

    cls: Optional[Type[Repo]] = None
    first_try = True
    curpath = path.absolute()
    lastpath = None
    while (
        curpath.exists()
        and (first_try or parentsearch)
        and (cls is None and curpath != lastpath)
    ):
        if (curpath / ".git").is_dir():
            cls = GitRepo
            break
        if (curpath / ".svn").is_dir():
            cls = SvnRepo
            break
        lastpath = curpath
        curpath = curpath.parent
        first_try = False

    if cls is None and url is not None:
        # If path exists, but is not a checkout, reset curpath
        curpath = path.absolute()

        if GitRepo.check_remote(url):
            cls = GitRepo
        elif SvnRepo.check_remote(url):
            cls = SvnRepo

    if cls is None:
        raise RuntimeError(
            f"Unable to determine repo type from url {url} (path: {path})"
        )

    return cls(
        url,
        curpath,
        target_commit=target_commit,
        tag=tag,
        branch=branch,
        remote_path=remote_path,
        options=options,
        quiet=quiet,
    )
