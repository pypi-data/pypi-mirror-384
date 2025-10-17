"""Module containing the log_io wrapper"""

import functools
from typing import Any, Callable

from abllib.wrapper._base_log_wrapper import BaseLogWrapper

class log_io(BaseLogWrapper):
    """
    Decorate a function, which logs any passed arguments and return values.
    The values are logged with log level DEBUG, so make sure you configured your logger properly.

    If the optional argument logger is set and of type logging.Logger, log the values to that logger.

    If the optional argument logger is set and of type str, request that logger and log the values.

    Otherwise, the values are logged to the root logger.
    """

    def __call__(self, func: Callable):
        """Called when the class instance is used as a decorator"""

        def wrapper(*args, **kwargs):
            """The wrapped function that is called on function execution"""

            res = func(*args, **kwargs)

            self.logger.debug(f"func: {func.__name__}")
            form_args = [self._format(item) for item in args]
            form_kwargs = [f"{key}={self._format(value)}" for key, value in kwargs.items()]
            arg_str = ", ".join(form_args + form_kwargs)
            self.logger.debug(f"in  : {arg_str}")
            self.logger.debug(f"out : {self._format(res)}")

            return res

        # https://stackoverflow.com/a/17705456/15436169
        functools.update_wrapper(wrapper, func)

        return wrapper

    def _format(self, arg: Any) -> str:
        if isinstance(arg, str):
            return f"\"{arg}\""

        return str(arg)
