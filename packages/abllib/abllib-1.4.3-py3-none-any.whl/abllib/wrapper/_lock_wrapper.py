"""Module containing the NamedLock and NamedSemaphore classes"""

from __future__ import annotations

import functools
import traceback
from time import sleep

from abllib import error, log
from abllib._storage import InternalStorage
from abllib.wrapper._deprecated import deprecated
from abllib.wrapper._lock import Lock, Semaphore

logger = log.get_logger("LockWrapper")

class NamedLock():
    """
    Make a function require a lock to be held during execution.

    Only a single NamedLock can hold the lock, but only if the NamedSemaphore is not currently held.

    Optionally provide a timeout in seconds,
    after which an LockAcquisitionTimeoutError is thrown (disabled if timeout is None).
    """

    def __init__(self, lock_name: str, timeout: int | float | None = None):
        if isinstance(timeout, int):
            timeout = float(timeout)

        # TODO: add type validation
        if not isinstance(lock_name, str):
            raise error.WrongTypeError.with_values(lock_name, str)
        if not isinstance(timeout, float) and timeout is not None:
            raise error.WrongTypeError.with_values(timeout, (float, None))

        self._name = lock_name
        self._timeout = timeout
        self._corresponding_semaphore = None

        if f"_locks.{lock_name}.l" not in InternalStorage:
            InternalStorage[f"_locks.{lock_name}.l"] = Lock()

        self._lock = InternalStorage[f"_locks.{lock_name}.l"]

    _name: str
    _lock: Lock | Semaphore
    _timeout: float | None
    _corresponding_semaphore: NamedSemaphore | None

    @property
    def name(self) -> str:
        """Return the lock's name"""

        return self._name

    def acquire(self) -> None:
        """Acquire the lock, or throw an LockAcquisitionTimeoutError if timeout is not None"""

        _log_callstack(f"NamedLock '{self.name}' was acquired here:")

        if self._timeout is None:
            # ensure the corresponding semaphore is not held
            other = self._get_corresponding_semaphore()
            if other is not None:
                other.block()
                while other.locked():
                    sleep(0.025)

            if not self._lock.acquire():
                if other is not None:
                    other.unblock()
                raise error.LockAcquisitionTimeoutError()

            if other is not None:
                other.unblock()
            return

        elapsed_time = 0.0
        # ensure the corresponding semaphore is not held
        other = self._get_corresponding_semaphore()
        if other is not None:
            while other.locked():
                sleep(0.025)
                elapsed_time += 0.025
                if elapsed_time > self._timeout:
                    other.unblock()
                    raise error.LockAcquisitionTimeoutError()

        if not self._lock.acquire(timeout=self._timeout - elapsed_time):
            if other is not None:
                other.unblock()
            raise error.LockAcquisitionTimeoutError()

        if other is not None:
            other.unblock()

    def release(self) -> None:
        """Release the lock"""

        _log_callstack(f"NamedLock '{self.name}' was released here:")

        self._lock.release()

    def locked(self) -> bool:
        """Return whether the lock is currently held"""

        return self._lock.locked()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __call__(self, func):
        """Called when instance is used as a decorator"""

        def wrapper(*args, **kwargs):
            """The wrapped function that is called on function execution"""

            with self:
                ret = func(*args, **kwargs)

            return ret

        # https://stackoverflow.com/a/17705456/15436169
        functools.update_wrapper(wrapper, func)

        return wrapper

    def _get_corresponding_semaphore(self) -> NamedSemaphore | None:
        if self._corresponding_semaphore is not None:
            return self._corresponding_semaphore

        if f"_locks.{self.name}.s" in InternalStorage:
            self._corresponding_semaphore = InternalStorage[f"_locks.{self.name}.s"]
            return self._corresponding_semaphore

        return None

class NamedSemaphore():
    """
    Make a function require a lock to be held during execution.

    Multiple NamedSemaphores can hold the same lock concurrently, but only if the NamedLock is not currently held.

    Optionally provide a timeout in seconds,
    after which an LockAcquisitionTimeoutError is thrown (disabled if timeout is None).
    """

    def __init__(self, lock_name: str, timeout: int | float | None = None):
        if isinstance(timeout, int):
            timeout = float(timeout)

        # TODO: add type validation
        if not isinstance(lock_name, str):
            raise error.WrongTypeError.with_values(lock_name, str)
        if not isinstance(timeout, float) and timeout is not None:
            raise error.WrongTypeError.with_values(timeout, (float, None))

        self._name = lock_name
        self._timeout = timeout
        self._corresponding_lock = None

        if f"_locks.{lock_name}.s" not in InternalStorage:
            InternalStorage[f"_locks.{lock_name}.s"] = Semaphore(999)

        self._semaphore = InternalStorage[f"_locks.{lock_name}.s"]

    _name: str
    _semaphore: Semaphore
    _timeout: float | None
    _corresponding_lock: NamedLock | None

    @property
    def name(self) -> str:
        """Return the lock's name"""

        return self._name

    def acquire(self) -> None:
        """Acquire the lock, or throw an LockAcquisitionTimeoutError if timeout is not None"""

        _log_callstack(f"NamedSemaphore '{self.name}' was acquired here:")

        if self._timeout is None:
            while self._semaphore.blocked():
                sleep(0.025)

            # ensure the other lock is not held
            other = self._get_corresponding_lock()
            if other is not None:
                while other.locked():
                    sleep(0.025)

            if not self._semaphore.acquire_unsafe():
                raise error.LockAcquisitionTimeoutError()

            return

        elapsed_time = 0.0
        while self._semaphore.blocked():
            sleep(0.025)
            elapsed_time += 0.025
            if elapsed_time > self._timeout:
                raise error.LockAcquisitionTimeoutError()

        # ensure the other lock is not held
        other = self._get_corresponding_lock()
        if other is not None:
            while other.locked():
                sleep(0.025)
                elapsed_time += 0.025
                if elapsed_time > self._timeout:
                    raise error.LockAcquisitionTimeoutError()

        if not self._semaphore.acquire_unsafe(timeout=self._timeout - elapsed_time):
            raise error.LockAcquisitionTimeoutError()

    def release(self) -> None:
        """Release the lock"""

        _log_callstack(f"NamedSemaphore '{self.name}' was released here:")

        self._semaphore.release()

    def locked(self) -> bool:
        """Return whether the lock is currently held"""

        return self._semaphore.locked()

    def block(self) -> None:
        """Prevent this semaphore from being acquired"""

        self._semaphore.block()

    def unblock(self) -> None:
        """Allow this semaphore to be acquired again"""

        self._semaphore.unblock()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __call__(self, func):
        """Called when instance is used as a decorator"""

        def wrapper(*args, **kwargs):
            """The wrapped function that is called on function execution"""

            with self:
                ret = func(*args, **kwargs)

            return ret

        # https://stackoverflow.com/a/17705456/15436169
        functools.update_wrapper(wrapper, func)

        return wrapper

    def _get_corresponding_lock(self) -> NamedLock | None:
        if self._corresponding_lock is not None:
            return self._corresponding_lock

        if f"_locks.{self.name}.l" in InternalStorage:
            self._corresponding_lock = InternalStorage[f"_locks.{self.name}.l"]
            return self._corresponding_lock

        return None

def _log_callstack(message: str):
    """Log the current callstack"""

    if log.get_loglevel() != log.LogLevel.ALL:
        return

    traces = traceback.format_list(traceback.extract_stack())
    traces.reverse()

    for line in traces:
        ignore = False
        for filename in ["_lock_wrapper.py", "_persistent_storage.py", "_volatile_storage.py", "_storage_view.py"]:
            if filename in line:
                ignore = True

        if not ignore:
            logger.debug(message + "\n" + line.strip())
            return

@deprecated
class WriteLock(NamedLock):
    """Deprecated alias for NamedLock"""

@deprecated
class ReadLock(NamedSemaphore):
    """Deprecated alias for NamedSemaphore"""
