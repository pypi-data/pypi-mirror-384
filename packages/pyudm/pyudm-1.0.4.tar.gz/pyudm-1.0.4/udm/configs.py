# SPDX-License-Identifier: GPL-2.0-or-later
"""
global configurations singleton module
"""

import os
import logging
from typing import Any, Optional
from argparse import Namespace
from typing_extensions import override
import yaml

_logger = logging.getLogger(__name__)


class Configs:
    """global configurations, uses a global config file overridden by commandline args"""

    __instance = None
    __config_file_paths = [
        "/etc/udm.conf",
        "/etc/default/udm.conf",
        "~/.config/udm.conf",
        "~/.udm.conf",
        # optional input file path
    ]

    def __init__(self, cfgfile: Optional[str] = None):
        files = self.__config_file_paths[:]

        if cfgfile is not None:
            files.append(cfgfile)

        self.__base_configs = {}
        for fpath in files:
            fpath = os.path.expanduser(fpath)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf8") as cfile:
                    self.__base_configs.update(yaml.safe_load(cfile))

        self.__active_configs = self.__base_configs

        Configs.__instance = self

    @override
    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        if __name in self.__active_configs:
            return self.__active_configs[__name]
        return super().__getattribute__(__name)

    def flag(self, flag_name):
        """
        get a boolean flag value, returns False if flag is not specified
        """
        if flag_name in self.__active_configs:
            return self.__active_configs[flag_name]
        return False

    def set_args(self, namespace: Namespace):
        """
        set the arguments namespace which will override global configs
        """
        self.__active_configs = dict(self.__base_configs)
        for key, val in namespace.__dict__.items():
            if (
                isinstance(val, bool)
                and key in self.__active_configs
                and isinstance(self.__active_configs[key], bool)
            ):
                # flags will always be set in namespace and are meaningful only if True
                # so merge should be done with an or to preserve global configs because
                # the only possible override value is True
                self.__active_configs[key] |= val
            else:
                self.__active_configs[key] = val

    def log_debug(self):
        """
        print debug informations about the active configurations using standard logger
        """
        _logger.debug("base configs: %s", self.__base_configs)
        _logger.debug("active configs: %s", self.__active_configs)

    @staticmethod
    def get_instance():
        """
        obtain the Args instance
        """
        if Configs.__instance is None:
            Configs()
        return Configs.__instance


def configs():
    """
    obtain the Args instance
    """

    return Configs.get_instance()
