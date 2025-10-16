#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""
Unified Dependency Manager is a simple yet powerful tool aimed at simplifying dependency handling
of nested projects and vcs interoperability.

This tool lets users define the dependencies of each project in a simple and clean fashion
inspired by svn:externals syntax and performs all the routine operations needed to checkout,
update and track supbrojects
"""

import logging
import logging.handlers
import sys
from queue import SimpleQueue
from typing import Union
from rich.logging import RichHandler
from rich.highlighter import ReprHighlighter
from rich.text import Text

_logger = logging.getLogger(__name__)


class OutputFormatter(logging.Formatter):
    """
    custom logging formatter to unify output across all modules
    """

    def __init__(self):
        super().__init__()
        self._infoformatter = logging.Formatter(fmt="[UDM] %(message)s")
        self._levelformatter = logging.Formatter(
            fmt="[UDM] <%(levelname)s> %(message)s"
        )

    def format(self, record):
        if record.levelno == logging.INFO:
            return self._infoformatter.format(record)
        return self._levelformatter.format(record)


class OutputHighlighter(ReprHighlighter):
    # pylint: disable=too-few-public-methods
    """
    custom logging highlighter for color output
    """

    def highlight(self, text: Text):
        text.highlight_words(["[UDM]"], "bold green")
        text.highlight_words(["[WARNING]"], "underline bold yellow")
        super().highlight(text)


def main():
    # pylint: disable=invalid-name,import-outside-toplevel
    """
    main entry point
    """
    from udm.commandline import cmdline
    from udm.configs import configs

    parsed_args, other_args = cmdline().parse_known_args()

    loghdl: Union[logging.Handler, RichHandler]
    if parsed_args.no_color:
        loghdl = logging.StreamHandler()
    else:
        loghdl = RichHandler(
            show_time=False,
            show_level=False,
            show_path=False,
            rich_tracebacks=True,
            highlighter=OutputHighlighter(),
        )
    loghdl.setFormatter(OutputFormatter())
    warnqueue: SimpleQueue = SimpleQueue()
    warnhdl = logging.handlers.QueueHandler(warnqueue)
    warnhdl.setLevel(logging.WARNING)
    LOGLEVEL = logging.INFO
    if parsed_args.quiet:
        LOGLEVEL = logging.ERROR
    if parsed_args.debug:
        LOGLEVEL = logging.DEBUG
    logging.basicConfig(level=LOGLEVEL, handlers=[loghdl, warnhdl])

    _logger.debug("args: %s, cmdline: %s", parsed_args, cmdline)
    configs().log_debug()

    try:
        if "func" not in parsed_args:
            cmdline().parser.print_usage()
        elif callable(parsed_args.func):
            parsed_args.func(parsed_args, other_args)
    except KeyboardInterrupt:
        pass
    except Exception as e:  # pylint: disable=broad-except
        if parsed_args.debug:
            import traceback

            traceback.print_exc(file=sys.stderr)
        if callable(parsed_args.func):
            _logger.error(e)
            sys.exit(1)

    loghdl.setFormatter(logging.Formatter(fmt="[WARNING] %(message)s"))
    while not warnqueue.empty():
        msg: logging.LogRecord = warnqueue.get_nowait()
        if msg is not None and msg.levelno == logging.WARNING:
            msg.msg = ":".join(msg.msg.split(":")[2:])
            loghdl.handle(msg)


if __name__ == "__main__":
    main()
