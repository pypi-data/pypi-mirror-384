"""A module containing the WorkerThread class"""

from threading import Thread
from typing import Any, Callable

# original code from https://stackoverflow.com/a/6894023
class WorkerThread(Thread):
    """Wrapper around `threading.Thread` that stores and returns resulting values and exceptions on join."""

    def __init__(self,
                 group=None,
                 target=None,
                 name=None,
                 args=(),
                 kwargs=None,
                 daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self._return = None

    _target: Callable | None
    _return: Any | None
    _args: Any
    _kwargs: Any

    def run(self) -> None:
        """Invoke the callable object."""

        if self._target is not None:
            try:
                self._return = self._target(*self._args, **self._kwargs)
            # pylint: disable-next=broad-exception-caught
            except BaseException as e:
                self._return = e

    def join(self, timeout: float | None = None, reraise: bool = False) -> Any | BaseException: # type:ignore[override]
        """Wait until the thread terminates and return any stored values."""

        super().join(timeout)

        if reraise and isinstance(self._return, BaseException):
            raise self._return

        return self._return

    def failed(self) -> bool:
        """Return whether target execution raised an exception."""

        return isinstance(self._return, BaseException)
