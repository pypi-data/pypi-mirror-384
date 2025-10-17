"""Module containing the log_io wrapper"""

import functools
from logging import Logger
from typing import Callable

from abllib import log
from abllib.error import WrongTypeError

class BaseLogWrapper():
    """
    Base class for all decorators that log something.

    If the optional argument logger is set and of type logging.Logger, use that logger.

    If the optional argument logger is set and of type str, request and use that loggers.

    Otherwise, use the root logger.
    """

    def __new__(cls, logger: str | Logger | Callable | None = None):
        inst = super().__new__(cls)

        # used directly as a wrapper
        if callable(logger):
            inst.logger = log.get_logger()
            return inst(logger)

        # logger is the loggers' name
        if isinstance(logger, str):
            _logger = log.get_logger(logger)
        # logger is a logging.Logger object
        elif isinstance(logger, Logger):
            _logger = logger
        elif logger is None:
            _logger = None
        else:
            raise WrongTypeError.with_values(logger, (str, Logger, Callable, None))

        inst.logger = _logger
        return inst

    logger: Logger | None

    def __call__(self, func: Callable):
        """Called when the class instance is used as a decorator"""

        def wrapper(*args, **kwargs):
            """The wrapped function that is called on function execution"""

            raise NotImplementedError()

        # https://stackoverflow.com/a/17705456/15436169
        functools.update_wrapper(wrapper, func)

        return wrapper
