# SPDX-License-Identifier: GPL-2.0-or-later
"""
commandline and status singleton module
"""
import argparse
import inspect
from typing import List, Tuple, Callable
import argcomplete  # type: ignore
from .dependency import Dependencies, clone, _logger
from .configs import configs


class Commandline:
    """commandline handling, defines parser options and holds execution configs and state"""

    __instance = None

    def __init__(self):
        if Commandline.__instance is not None:
            raise RuntimeError("Can't re-instantiate singleton class")

        Commandline.__instance = self
        self._args = None
        self._cmdline = None

        self.parser = argparse.ArgumentParser(
            description="udm", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self.parser.add_argument(
            "-f",
            "--force",
            help="force execution of destructive operations",
            action="store_true",
        )
        self.parser.add_argument(
            "-v", "--version", help="print version information", action="store_true"
        )
        self.parser.add_argument(
            "-q",
            "--quiet",
            help="print only errors and required output, avoid status logs",
            action="store_true",
        )
        self.parser.add_argument(
            "-d", "--debug", help="enable verbose output", action="store_true"
        )
        self.parser.add_argument(
            "--no-color", help="disable color output", action="store_true"
        )
        self.parser.add_argument(
            "--prohibit-externals",
            dest="prohibit_externals",
            help="stop at the first dependency with local externals/submodules",
            action="store_true",
        )
        self.parser.add_argument(
            "--ignore-deps",
            dest="ignore",
            help="Do not act on dependencies",
            action="store_true",
        )

        self._subparsers = self.parser.add_subparsers()
        self.__add_subparsers__()

    def __add_subparsers__(self):
        # clone
        parser_clone = self.__add_subparser__(
            self.__clone__,
            "clone",
            aliases=["co", "checkout"],
            description="clone repository",
        )
        parser_clone.add_argument(
            "--convert",
            dest="convert",
            action="store_true",
            help="After checkout, automatically convert reporitory dependencies to udm deps",
        )
        parser_clone.add_argument("url", help="Url to clone")
        parser_clone.add_argument("destination", help="Destination directory")

        # convert
        parser_convert = self.__add_subparser__(
            self.__convert__,
            "convert",
            description="convert repository dependencies to udm deps",
        )
        parser_convert.add_argument(
            "--no-update",
            dest="noupdate",
            action="store_true",
            help="avoid performing an update operation after succesful conversion",
        )

        # local
        self.__add_subparser__(
            self.__local__,
            "local",
            aliases=["l"],
            description="Pass additional arguments directly to local repository structure, "
            + "print local repository type if no argument is specified",
        )

        # ls_files
        self.__add_subparser__(
            self.__ls_files__,
            "ls-files",
            aliases=["ls"],
            description="list tracked files",
        )

        # ls_deps
        self.__add_subparser__(
            self.__ls_deps__,
            "ls-deps",
            aliases=["show", "deps"],
            description="list configured dependencies",
        )

        # status
        self.__add_subparser__(
            self.__status__,
            "status",
            aliases=["st", "stat"],
            description="show current workspace status",
        )

        # update
        parser_update = self.__add_subparser__(
            self.__update__,
            "update",
            aliases=["up", "pull"],
            description="update current workspace",
        )
        parser_update.add_argument(
            "--only-deps",
            dest="only_deps",
            help="update only dependencies",
            action="store_true",
        )
        parser_update.add_argument(
            "--no-deps",
            dest="no_deps",
            help="do not update dependencies",
            action="store_true",
        )

        # edit-deps
        parser_edit_deps = self.__add_subparser__(
            self.__edit_deps__,
            "edit-deps",
            aliases=["ed"],
            description="edit dependencies of current workspace",
        )
        parser_edit_deps.add_argument(
            "--editor-cmd", dest="editor", help="Specify external editor"
        )

    def __add_subparser__(
        self,
        subparser_callback: Callable,
        subparser_name: str,
        **subparser_kwargs,
    ):
        subparser_args = len(inspect.getfullargspec(subparser_callback).args)

        def check_and_call(args, extra):
            if extra is None or len(extra) == 0:
                if subparser_args == 1:
                    subparser_callback(args)
                else:
                    subparser_callback()
            else:
                self.parser.error(f'unknown argument "{extra[0]}"')

        subparser = self._subparsers.add_parser(subparser_name, **subparser_kwargs)
        if subparser_args > 1:
            # if subparser callback expects more than one argument, it will make use of
            # extra cmdline args, so no checks must be performed
            subparser.set_defaults(func=subparser_callback)
        else:
            # else ensure no extra args are present and return an error on unknown parameters
            subparser.set_defaults(func=check_and_call)
        return subparser

    def __clone__(self, args, options):
        clone(args.destination, args.url, options, configs().flag("convert"))

    def __convert__(self, _, __):
        Dependencies(parentsearch=True).convert(not configs().flag("noupdate"))

    def __local__(self, _, cmdline_args):
        Dependencies(parentsearch=True).local(cmdline_args)

    def __ls_files__(self, _, __):
        Dependencies(parentsearch=True).ls_files(not configs().flag("ignore"))

    def __ls_deps__(self, _, __):
        _logger.info("Local dependencies:")
        for dependency in Dependencies(parentsearch=True).deps:
            _logger.info("- %s", dependency)

    def __status__(self, _, __):
        Dependencies(parentsearch=True).status(not configs().flag("ignore"))

    def __update__(self, _, __):
        Dependencies(parentsearch=True).update(
            configs().flag("only_deps"), configs().flag("no_deps")
        )

    def __edit_deps__(self, _, __):
        Dependencies(parentsearch=True).open_editor(configs().flag("editor"))

    def parse_known_args(
        self, args=None, namespace=None
    ) -> Tuple[argparse.Namespace, List[str]]:
        """
        parse commandline arguments and return parsed args and remaining commandline
        """
        argcomplete.autocomplete(self.parser)
        self._args, self._cmdline = self.parser.parse_known_args(args, namespace)
        configs().set_args(self._args)
        return self._args, self._cmdline

    @staticmethod
    def get_instance():
        """
        obtain the Commandline instance
        """
        if Commandline.__instance is None:
            Commandline()
        return Commandline.__instance

    @property
    def args(self) -> argparse.Namespace:
        """
        parsed arguments namespace
        """
        if self._args is None:
            raise RuntimeError("commandline has not been parsed yet")
        return self._args

    @property
    def cmdline(self) -> List[str]:
        """
        extra commandline arguments (not handled by active subparser)
        """
        if self._cmdline is None:
            raise RuntimeError("commandline has not been parsed yet")
        return self._cmdline


def cmdline() -> Commandline:
    """
    obtain the Commandline instance
    """
    return Commandline.get_instance()
