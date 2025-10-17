"""Module containing the timeit wrapper"""

import functools
from time import perf_counter_ns
from typing import Callable

from abllib.wrapper._base_log_wrapper import BaseLogWrapper

class timeit(BaseLogWrapper):
    """
    Decorate a function, which logs the execution time of this function.
    The values are logged with log level DEBUG, so make sure you configured your logger properly.

    If the optional argument logger is set and of type logging.Logger, log the time to that logger.

    If the optional argument logger is set and of type str, request that logger and log the time.

    Otherwise, the time is logged to the root logger.
    """

    def __call__(self, func: Callable):
        """Called when the class instance is used as a decorator"""

        def wrapper(*args, **kwargs):
            """The wrapped function that is called on function execution"""

            start = perf_counter_ns()

            res = func(*args, **kwargs)

            elapsed = perf_counter_ns() - start

            log_msg = f"{func.__name__}: "

            for unit in ["ns", "μs", "ms"]:
                if elapsed < 1000:
                    log_msg += f"{elapsed:3.2f} {unit} elapsed"
                    self.logger.debug(log_msg)
                    return res

                elapsed /= 1000

            for unit in ["s", "min"]:
                if elapsed < 60:
                    log_msg += f"{elapsed:2.2f} {unit} elapsed"
                    self.logger.debug(log_msg)
                    return res

                elapsed /= 60

            if elapsed < 24:
                log_msg += f"{elapsed:2.2f} hours elapsed"
                self.logger.debug(log_msg)
                return res

            elapsed /= 24
            log_msg += f"{elapsed:.2f} days elapsed"
            self.logger.debug(log_msg)
            return res

        # https://stackoverflow.com/a/17705456/15436169
        functools.update_wrapper(wrapper, func)

        return wrapper
