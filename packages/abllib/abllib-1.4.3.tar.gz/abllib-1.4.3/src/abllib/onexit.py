"""Module for running code on application exit"""

import atexit
import functools
import signal
import threading
from typing import Callable

from abllib import error, log
from abllib._storage import InternalStorage

logger = log.get_logger("onexit")

def _ensure_is_main_thread(func):
    """Ensure that function is only callable from main thread"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            logger.warning("Tried to use onexit module from non-main thread")
            return None

        return func(*args, **kwargs)

    return wrapper

@_ensure_is_main_thread
def register(name: str, callback: Callable) -> None:
    """
    Run the given callback regardless of how the application exits.

    Does not work if the application is killed with SIGKILL.
    """

    if "." in name:
        name = name.replace(".", "_")

    registered = False

    if f"_onexit.atexit.{name}" not in InternalStorage:
        register_normal_exit(name, callback)
        registered = True

    if f"_onexit.signal.{name}" not in InternalStorage:
        register_sigterm(name, callback)
        registered = True

    if not registered:
        raise error.RegisteredMultipleTimesError.with_values(name)

@_ensure_is_main_thread
def register_normal_exit(name: str, callback: Callable) -> None:
    """
    Run the given callback if the application exits normally or with an exception.

    Does not work if the application is killed with SIGTERM or SIGKILL.
    """

    if "." in name:
        name = name.replace(".", "_")

    if f"_onexit.atexit.{name}" in InternalStorage:
        raise error.RegisteredMultipleTimesError.with_values(name)

    InternalStorage[f"_onexit.atexit.{name}"] = callback

@_ensure_is_main_thread
def register_sigterm(name: str, callback: Callable) -> None:
    """
    Run the given callback if the application is killed with SIGTERM.

    Does not work if the application exits normally, exits with an exception or is killed with SIGKILL.
    """

    _ensure_signal_handler()

    if "." in name:
        name = name.replace(".", "_")

    if f"_onexit.signal.{name}" in InternalStorage:
        raise error.RegisteredMultipleTimesError.with_values(name)

    InternalStorage[f"_onexit.signal.{name}"] = callback

    # set handler if first signal callback is registered
    if len(InternalStorage["_onexit.signal"]) == 1:
        signal.signal(signal.SIGTERM, _signal_func)

@_ensure_is_main_thread
def deregister(name: str) -> None:
    """
    Deregister the callback with the given name.

    Raises an NameNotFoundError if the name is not yet registered.
    """

    deleted = False

    if f"_onexit.atexit.{name}" in InternalStorage:
        deregister_normal_exit(name)
        deleted = True
    if f"_onexit.signal.{name}" in InternalStorage:
        deregister_sigterm(name)
        deleted = True

    if not deleted:
        # no callback was deleted
        raise error.NameNotFoundError.with_values(name)

@_ensure_is_main_thread
def deregister_normal_exit(name: str) -> None:
    """
    Deregister the callback with the given name.

    Raises an NameNotFoundError if the name is not yet registered.
    """

    if f"_onexit.atexit.{name}" not in InternalStorage:
        raise error.NameNotFoundError.with_values(name)

    del InternalStorage[f"_onexit.atexit.{name}"]

@_ensure_is_main_thread
def deregister_sigterm(name: str) -> None:
    """
    Deregister the callback with the given name.

    Raises an NameNotFoundError if the name is not yet registered.
    """

    _ensure_signal_handler()

    if f"_onexit.signal.{name}" not in InternalStorage:
        raise error.NameNotFoundError.with_values(name)

    del InternalStorage[f"_onexit.signal.{name}"]

    # reset handler if no signal callback is registered anymore
    if "_onexit.signal" not in InternalStorage:
        signal.signal(signal.SIGTERM, InternalStorage["_onexit.orig.signal"])

def reset() -> None:
    """Reset all registered callbacks"""

    if "_onexit.atexit" in InternalStorage:
        for name in list(InternalStorage["_onexit.atexit"].keys()):
            deregister_normal_exit(name)

    if "_onexit.signal" in InternalStorage:
        for name in list(InternalStorage["_onexit.signal"].keys()):
            deregister_sigterm(name)

def _atexit_func():
    if "_onexit.atexit" not in InternalStorage:
        return

    for callback in InternalStorage["_onexit.atexit"].values():
        try:
            callback()
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            logger.exception(e)

# pylint: disable-next=unused-argument
def _signal_func(signum, frame):
    if "_onexit.signal" not in InternalStorage:
        return

    for callback in InternalStorage["_onexit.signal"].values():
        try:
            callback()
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            logger.exception(e)

def _ensure_signal_handler():
    if "_onexit.signal" not in InternalStorage:
        if signal.getsignal(signal.SIGTERM) is not InternalStorage["_onexit.orig.signal"]:
            raise RuntimeError("signal handler was overwritten, "
                               + "make sure to only use this module to set signal handlers")
    else:
        if signal.getsignal(signal.SIGTERM) is not _signal_func:
            raise RuntimeError("signal handler was overwritten, "
                               + "make sure to only use this module to set signal handlers")

InternalStorage["_onexit.orig.signal"] = signal.getsignal(signal.SIGTERM)

atexit.register(_atexit_func)
