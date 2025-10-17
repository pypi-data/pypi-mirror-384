"""Module containing the _InternalStorage class"""

from typing import Any

from abllib import error
from abllib._storage._base_storage import _BaseStorage

class _InternalStorage(_BaseStorage):
    """Internal storage that is not saved across restarts"""

    def __init__(self) -> None:
        pass

    def _init(self):
        if _InternalStorage._instance is not None:
            raise error.SingletonInstantiationError.with_values(_InternalStorage)

        _InternalStorage._store = self._store = {}
        _InternalStorage._instance = self

    _STORAGE_NAME = "InternalStorage"

    def __setitem__(self, key: str, item: Any) -> None:
        if not key.startswith("_"):
            raise error.InternalFunctionUsedError("Please use storage.VolatileStorage")

        return super().__setitem__(key, item)
