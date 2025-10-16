# SPDX-License-Identifier: GPL-2.0-or-later
"""
dependency file and structure handling
"""
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Union
from scmwrap.scmwrap import ScmWrap
from scmwrap.repo import Repo
import yaml
from .configs import configs

_logger = logging.getLogger(__name__)

DEFAULT_DEPS_FILE = Path(".deps.udm")


class ExternalsDefined(Exception):
    """Exception class notifying an unhaled exception is presenti in repo"""

    def __init__(self, repo):
        super().__init__()
        self.repo = repo

    def __str__(self):
        return f"repository {self.repo.path} ({self.repo.url}) has externals defined"


class Dependency:
    """
    class representing a single dependency
    """

    def __init__(
        self,
        parentrepo: Repo,
        path: Union[Path, str] = Path(),
        url: Optional[str] = "",
        options: List[str] = [],
        repo: Optional[Repo] = None,
        indent: int = 80,
        tag: Optional[str] = None,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        remote_path: Optional[str] = None,
    ):
        # pylint: disable=too-many-arguments,dangerous-default-value
        """
        initialize dependency with automatic repository detection if repo is None,
        use repo parameter otherwise
        """
        if isinstance(path, str):
            path = Path(path)

        self.indent: int = indent
        self.parentrepo = parentrepo
        if repo is None:
            self.path = path
            self.repo = ScmWrap(
                url,
                path,
                target_commit=commit,
                tag=tag,
                branch=branch,
                remote_path=remote_path,
                options=options,
            )
        else:
            self.path = repo.path
            self.repo = repo

    def __eq__(self, other):
        return self.repo == other.repo and self.parentrepo == other.parentrepo

    def __str__(self):
        return str(self.repo)

    def __repr__(self):
        return str(self.repo)

    def to_yaml_data(self):
        """
        return a simple dict containing current dependency structure suitable for
        yaml dumping
        """
        path = self.path
        if self.path.is_absolute():
            path = self.path.relative_to(self.parentrepo.path)
        data = {"url": self.repo.url}
        if self.repo.tag is not None:
            data["tag"] = self.repo.tag
        if self.repo.branch is not None:
            data["branch"] = self.repo.branch
        if self.repo.target_commit is not None:
            data["commit"] = self.repo.target_commit
        if self.repo.remote_path is not None:
            data["path"] = self.repo.remote_path
        if self.repo.options is not None and len(self.repo.options) > 0:
            data["options"] = self.repo.options
        return (str(path), data)

    @staticmethod
    def from_yaml_data(parentrepo: Repo, path: str, data: dict):
        """
        instantiate a Dependency object using yaml parsed data
        """
        return Dependency(
            parentrepo,
            parentrepo.path / path,
            data["url"],
            options=data.get("options", None),
            tag=data.get("tag", None),
            branch=data.get("branch", None),
            commit=data.get("commit", None),
            remote_path=data.get("path", None),
        )

    def remove(self):
        """
        remove local dependency, if dirty and force is not specified will raise an exception
        """
        _logger.debug("trying to remove local dependency: %s", str(self))
        if self.path.exists():
            if self.repo.is_dirty() and not configs().flag("force"):
                raise RuntimeError(
                    f"repository at '{self.path}' contains local modifications"
                )

            _logger.debug("fixing ignores for previous dependency: %s", str(self))

            # Remove ignores before removing files to avoid svn errors on missing directories
            self.parentrepo.del_ignores(self.path.absolute())

            shutil.rmtree(self.path, ignore_errors=True)
            try:
                os.removedirs(self.path.parent)

                # Remove this directory from repository only when empty
                path = self.path.parent
                while not path.parent.exists():
                    path = path.parent

                self.parentrepo.remove(path)
            except OSError:
                pass


class Dependencies:
    """
    Dependencies classhold dependencies list and handle dependency tree operations recursively
    """

    def __init__(
        self,
        deps_file: Path = DEFAULT_DEPS_FILE,
        parentsearch: bool = False,
        repo: Optional[Repo] = None,
    ):
        if repo is None:
            self.repo = ScmWrap(None, deps_file.parent, parentsearch=parentsearch)
        else:
            self.repo = repo
        self.deps: List[Dependency] = []
        self.deps_file = self.repo.path / deps_file.name
        if deps_file.exists():
            with open(
                deps_file, "r", encoding="utf8"
            ) as fin:  # pylint: disable=unspecified-encoding
                yaml_data = yaml.safe_load(fin)
                if not isinstance(yaml_data, dict):
                    raise RuntimeError(f"invalid deps file {deps_file}")
                for path, cfg in yaml_data.items():
                    self.append(Dependency.from_yaml_data(self.repo, path, cfg))

    def __get_inner_deps(self, repo: Repo):
        """
        search for nested dependencies and return the inner instance or an empty one if none found
        """
        if (repo.path / self.deps_file.name).exists():
            return Dependencies(repo.path / self.deps_file.name, repo=repo)
        return Dependencies(repo.path / DEFAULT_DEPS_FILE, repo=repo)

    @property
    def prevfile(self):
        """
        path of the cache file containing previous dependency status
        """
        if self.repo is not None and self.repo.vcs_dir.exists():
            return self.repo.vcs_dir / DEFAULT_DEPS_FILE
        return self.repo.path / f"{DEFAULT_DEPS_FILE}.old"

    def update(self, onlydeps: bool = False, nodeps: bool = False):
        """
        update all dependencies recursively
        """
        _logger.debug(
            "update: onlydeps = %s, nodeps = %s, repo = %s",
            onlydeps,
            nodeps,
            self.repo,
        )

        if not onlydeps:
            self.repo.update()

        if not nodeps:
            if self.prevfile.exists():
                prevdeps = Dependencies(self.prevfile, parentsearch=True)
                _ = [d.remove() for d in prevdeps.deps if d not in self.deps]

            for dep in self.deps:
                if not dep.repo.exists():
                    dep.repo.checkout()

                self.repo.add_ignores(dep.path.absolute())

                if dep.repo.has_externals(recursive=False):
                    if (
                        configs().flag("prohibit_externals")
                        and configs().flag("convert")
                        and dep.repo.has_externals(recursive=False)
                    ):
                        raise ExternalsDefined(dep.repo)

                    _logger.warning(ExternalsDefined(dep.repo))

                self.__get_inner_deps(dep.repo).update()

            self.writeout(self.prevfile)

    def _clean_repo_externals(self, repo: Repo, add_deps: bool):
        def process_folder(folder):
            _logger.debug(
                "clean externals in folder %s, add deps: %s", folder, add_deps
            )
            externals = repo.list_externals(folder)
            for ext in externals:
                _logger.debug("processing folder %s external %s", folder, ext)
                if add_deps:
                    _logger.debug("Import externals from %s: %s", folder, ext)
                    self.append(Dependency(repo, repo=ext))
                self._clean_repo_externals(ext, False)

            if len(externals) > 0:
                _logger.debug("remove local externals %s", folder)
                repo.rm_externals(folder)
                repo.update()
                if not add_deps:
                    _logger.debug("revert to let parent cleanup correctly: %s", folder)
                    repo.reset_externals(folder)

        _logger.debug("clean repo externals for repo %s", repo)
        folders = repo.list_folders(False)
        if str(repo.path) not in folders:
            folders.append(str(repo.path))
        for folder in folders:
            process_folder(folder)

    def convert(self, doupdate: bool = False):
        """
        convert externals to dependencies, if doupdate is True, perform
        an update after conversion
        """
        if self.repo.has_externals():
            self._clean_repo_externals(self.repo, True)

            self.writeout()
            self.repo.add(self.deps_file)
            if doupdate:
                self.update()
        else:
            _logger.info("Conversion not needed")

    def local(self, cmdline_args):
        """
        run a command using local repository vcs tool
        """
        if len(cmdline_args) <= 0:
            _logger.info("%s repository at '%s'", self.repo.vcs, self.repo.path)
        else:
            self.repo.execute(cmdline_args)

    def ls_files(self, list_deps: bool = True):
        """
        list tracked files, optionally along with dependencies ones
        """
        self.repo.list_files()
        if list_deps:
            for dep in self.deps:
                if dep.repo.exists():
                    self.__get_inner_deps(dep.repo).ls_files()

    def status(self, status_deps: bool = True):
        """
        get status message for all dependencies recursively
        """
        self.repo.status()

        if status_deps:
            for dep in self.deps:
                if dep.repo.exists():
                    try:
                        self.__get_inner_deps(dep.repo).status()
                    except RuntimeError as e_msg:
                        _logger.warning(
                            "Exception '%s' for path '%s'",
                            e_msg,
                            dep.repo.path,
                        )

                else:
                    _logger.warning("Status error: %s is not a working copy", dep.path)

    def open_editor(self, editor: Optional[str] = None):
        """
        open dependencies file in external editor
        """
        if editor is None:
            if "EDITOR" in os.environ:
                cmd = [os.environ["EDITOR"]]
            else:
                cmd = ["vim"]
        else:
            cmd = [editor]

        cmd.append(self.deps_file.name)
        _logger.info("Edit %s", self.deps_file.name)
        subprocess.run(cmd, check=True)

    def append(self, dep: Dependency):
        """
        append a dependency rule to udm deps avoiding duplicates
        """
        if dep not in self.deps:
            self.deps.append(dep)

    def writeout(self, outfile: Optional[Path] = None):
        """
        write current dependencies list to file, defaults to dependencies file
        """
        deps_data = {}
        for dependency in self.deps:
            path, data = dependency.to_yaml_data()
            deps_data[path] = data

        if outfile is None:
            outfile = self.deps_file
        _logger.debug(
            "write out dependencies file '%s':\n%s",
            outfile,
            "\n".join([str(d) for d in self.deps]),
        )
        with open(
            outfile, "w", encoding="utf8"
        ) as fout:  # pylint: disable=unspecified-encoding
            yaml.dump(deps_data, fout)


def clone(
    destination: Union[Path, str],
    url: str,
    options: List[str],
    convert: bool = False,
) -> Dependencies:
    """
    clone subparser action function: clones a remote repository and updates dependencies
    """
    _logger.debug(
        "cloning repo '%s' into '%s', options: %s, convert: %s",
        url,
        destination,
        options,
        convert,
    )
    if not isinstance(destination, Path):
        destination = Path(destination)
    ScmWrap(url=url, path=destination, options=options).checkout()
    deps = Dependencies(destination / DEFAULT_DEPS_FILE)
    deps.update()

    if convert:
        _logger.debug("starting conversion procedure")
        deps.convert(True)

    return deps
