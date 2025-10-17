"""A module containing general-purpose functions that dont warrant an extra module."""

import importlib
import sys
from types import ModuleType

from abllib.error import MissingRequiredModuleError
from abllib.log import get_logger

# pylint: disable=raise-missing-from

logger = get_logger("general")

def try_import_module(module_name: str, error_msg: str | None = None, enforce: bool = False) -> ModuleType | None:
    """
    Try to import the given module and return whether importing was successful.

    If error_msg is given, log an error message on failure.

    If enforce is True, raise an exception with given error_msg on failure instead.
    """

    module = None

    try:
        # optional module for japanese character transliterating
        module = importlib.import_module(module_name)
        sys.modules[module_name] = module
    except ImportError:
        if enforce:
            if error_msg is None:
                raise MissingRequiredModuleError.with_values(module_name)

            raise MissingRequiredModuleError(error_msg)

        if error_msg is not None:
            logger.warning(error_msg)

    return module
