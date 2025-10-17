"""A module containing a custom Lock and Semaphore class"""

import threading
from time import sleep

from abllib import error

class Lock():
    """
    Extends threading.Lock by allowing timeout to be None.

    threading.Lock cannot be subclassed as it is a factory function.
    https://stackoverflow.com/a/6781398
    """

    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self, blocking: bool = True, timeout: float | None = None):
        """
        Try to acquire the Lock.

        If blocking is disabled, it doesn't wait for the timeout.

        If timeout is set, wait for n seconds before returning.
        """

        return self._lock.acquire(blocking, -1 if timeout is None else timeout)

    def locked(self) -> bool:
        """Returns whether the Lock is held"""

        return self._lock.locked()

    def release(self):
        """Release the lock if it is currently held"""

        if not self.locked():
            return

        self._lock.release()

    def __enter__(self):
        self.acquire()

    # keep signature the same as threading.Lock
    # pylint: disable-next=redefined-builtin
    def __exit__(self, type, value, traceback):
        self.release()

# we can't use the default threading.Semaphore
# because we need a semaphore with value == 0 if it isn't held
# This is the opposite behaviour of threading.Semaphore
class Semaphore(threading.BoundedSemaphore):
    """
    Extends threading.BoundedSemaphore by adding a locked() function.

    This makes it equivalent to threading.Lock method signature-wise.
    """

    def __init__(self, value: int = 1) -> None:
        super().__init__(value)
        self._blocked = False

    _value: int
    _initial_value: int
    _blocked: bool

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        if timeout is None:
            while self._blocked:
                sleep(0.025)

            return super().acquire(blocking, timeout)

        elapsed_time = 0.0
        while self._blocked:
            sleep(0.025)
            elapsed_time += 0.025
            if elapsed_time > timeout:
                raise error.LockAcquisitionTimeoutError()

        return super().acquire(blocking, timeout)

    def acquire_unsafe(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """Acquire this semaphore without checking if it's blocked"""

        return super().acquire(blocking, timeout)

    def release(self, n: int = 1) -> None:
        if not self.locked():
            return None

        # release all remaining
        if self._value + n > self._initial_value:
            n = self._initial_value - self._value

        return super().release(n)

    def locked(self) -> bool:
        """Returns whether the Semaphore is held at least once"""

        return self._value != self._initial_value

    def block(self) -> None:
        """Prevent this semaphore from being acquired"""

        self._blocked = True

    def unblock(self) -> None:
        """Allow this semaphore to be acquired again"""

        self._blocked = False

    def blocked(self) -> bool:
        """Return whether this semaphore is blocked"""

        return self._blocked
