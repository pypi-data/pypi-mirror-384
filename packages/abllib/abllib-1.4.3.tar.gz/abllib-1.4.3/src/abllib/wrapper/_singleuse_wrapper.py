"""Module containing the singleuse wrapper function"""

import functools

from abllib.error import CalledMultipleTimesError

def singleuse(func):
    """
    Make a function single-use only.
    If the function raised an exception, it is not seen as called and can be used again.

    Calling the function twice raises an error.CalledMultipleTimesError.
    """

    was_called = [False]

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """The wrapped function that is called on function execution"""

        if was_called[0]:
            raise CalledMultipleTimesError()

        res = func(*args, **kwargs)

        was_called[0] = True

        return res

    return wrapper
