"""Module containing the _VolatileStorage class"""

from abllib import error
from abllib.storage._storage_view import _StorageView
from abllib.storage._threadsafe_storage import _ThreadsafeStorage

class _VolatileStorage(_ThreadsafeStorage):
    """Storage that is not saved across restarts"""

    def __init__(self) -> None:
        if _VolatileStorage._instance is not None:
            raise error.SingletonInstantiationError.with_values(_VolatileStorage)

        _VolatileStorage._instance = self

    def initialize(self):
        """
        Initialize only the VolatileStorage.

        Not needed if you already called abllib.storage.initialize().
        """

        if _VolatileStorage._store is not None:
            # this is a re-initialization
            return

        _VolatileStorage._store = self._store = {}

        # we cannot use StorageView defined in __init__.py because of circular imports
        # pylint: disable-next=protected-access
        _StorageView._instance.add_storage(self)

    _STORAGE_NAME = "VolatileStorage"

    def _ensure_initialized(self):
        try:
            super()._ensure_initialized()
        except error.NotInitializedError as exc:
            raise error.NotInitializedError("VolatileStorage is not yet initialized, "
                                            + "are you sure you called storage.initialize() "
                                            + "or VolatileStorage.initialize()?") \
                                           from exc
