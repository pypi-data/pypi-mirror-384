"""Module containing the _PersistentStorage class"""

from typing import Any

from abllib import error, wrapper
from abllib._storage._base_storage import _BaseStorage

class _ThreadsafeStorage(_BaseStorage):
    def __init__(self):
        raise NotImplementedError()

    _STORAGE_NAME = "ThreadsafeStorage"

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def contains_item(self, key, item):
        return super().contains_item(key, item)

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def contains(self, key):
        return super().contains(key)

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def get(self, key, default = None):
        return super().get(key, default)

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def items(self):
        return super().items()

    @wrapper.NamedLock(_STORAGE_NAME)
    def pop(self, key) -> Any:
        return super().pop(key)

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def keys(self):
        return super().keys()

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def values(self):
        return super().values()

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def __getitem__(self, key):
        return super().__getitem__(key)

    @wrapper.NamedLock(_STORAGE_NAME)
    def __setitem__(self, key: str, item: Any) -> None:
        return super().__setitem__(key, item)

    @wrapper.NamedLock(_STORAGE_NAME)
    def __delitem__(self, key):
        return super().__delitem__(key)

    @wrapper.NamedSemaphore(_STORAGE_NAME)
    def __contains__(self, key):
        return super().__contains__(key)

    def __init_subclass__(cls):
        if cls._STORAGE_NAME in ("BaseStorage", "ThreadsafeStorage"):
            raise error.UninitializedFieldError.with_values(cls, "_STORAGE_NAME")

        if not isinstance(cls._STORAGE_NAME, str):
            raise error.WrongTypeError.with_values(cls._STORAGE_NAME, str)
