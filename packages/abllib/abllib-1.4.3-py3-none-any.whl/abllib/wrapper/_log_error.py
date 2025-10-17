"""Module containing the log_error wrapper"""

import functools
from logging import Logger
from typing import Callable

from abllib.error import ArgumentCombinationError
from abllib.wrapper._base_log_wrapper import BaseLogWrapper

class log_error(BaseLogWrapper):
    """
    Decorate a function, which logs any exception occurring during execution.

    If the optional argument logger is set and of type logging.Logger, log the error to that logger.

    If the optional argument logger is set and of type str, request that logger and log the error.

    If the optional argument handler is set, forwards the error message to that function.

    Otherwise, the error is logged to the root logger.
    """

    def __new__(cls, logger: str | Logger | None | Callable = None, handler: Callable | None = None):
        if logger is None and handler is None:
            raise ArgumentCombinationError("Either logger or handler need to be provided")

        # handler is given
        if handler is not None:
            inst = super().__new__(cls)
            # pylint: disable-next=unnecessary-lambda-assignment
            inst.logger = handler
            return inst

        return super().__new__(cls, logger)

    def __call__(self, func: Callable):
        """Called when the class instance is used as a decorator"""

        def wrapper(*args, **kwargs):
            """The wrapped function that is called on function execution"""

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(self.logger, Logger):
                    self.logger.exception(e)
                else:
                    self.logger(f"{e.__class__.__name__}: {e}")
                raise

        # https://stackoverflow.com/a/17705456/15436169
        functools.update_wrapper(wrapper, func)

        return wrapper
