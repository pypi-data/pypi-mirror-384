"""Module containing the _CacheStorage class"""

from abllib import error
from abllib._storage._base_storage import _BaseStorage

class _CacheStorage(_BaseStorage):
    """Storage used for caching values"""

    def __init__(self) -> None:
        if _CacheStorage._instance is not None:
            raise error.SingletonInstantiationError.with_values(_CacheStorage)

        _CacheStorage._instance = self
        _CacheStorage._store = self._store = {}

    _STORAGE_NAME = "CacheStorage"

    def _ensure_initialized(self):
        # the storage is always initialized
        pass
