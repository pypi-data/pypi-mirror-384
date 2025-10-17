"""Module containing the _StorageView class"""

from __future__ import annotations

from typing import Any

from abllib import error
from abllib._storage._base_storage import _BaseStorage
from abllib.storage._cache_storage import _CacheStorage

# pylint: disable=protected-access
# mypy: ignore-errors

class _StorageView():
    """A read-only view on both the PersistentStorage and VolatileStorage"""

    def __init__(self):
        pass

    def _init(self) -> None:
        if _StorageView._instance is not None:
            raise error.SingletonInstantiationError.with_values(_StorageView)

        _StorageView._instance = self

        # CacheStorage needs to be added like this to avoid circular imports
        _StorageView._storages = self._storages = [_CacheStorage._instance]

    _instance: _StorageView = None
    _storages: list[_BaseStorage] = None

    def add_storage(self, storage: _BaseStorage) -> None:
        """
        Add a new storage to the StorageView.

        The storage has to inherit from _BaseStorage.

        If the exact same storage object is registered twice, a RegisteredMultipleTimesError error is raised.
        """

        if not isinstance(storage, _BaseStorage):
            raise error.MissingInheritanceError.with_values(storage, _BaseStorage)

        for item in self._storages:
            if id(item) == id(storage):
                raise error.RegisteredMultipleTimesError.with_values(storage)

        self._storages.append(storage)

    def contains_item(self, key: str, item: Any) -> bool:
        """
        Checks whether a key within the storage equals an item.

        If 'key' contains a '.', also checks if all sub-dicts exist.
        """

        for storage in self._storages:
            if storage.contains_item(key, item):
                return True
        return False

    def contains(self, key: str) -> bool:
        """
        Checks whether a key exists within the storage.

        If 'key' contains a '.', also checks if all sub-dicts exist.
        """

        for storage in self._storages:
            if storage.contains(key):
                return True
        return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Return the value of an key if it exists in the storage.

        If the key is not found, return the default value instead.
        """

        for storage in self._storages:
            if storage.contains(key):
                return storage[key]

        return default

    def items(self) -> list[tuple[str, Any]]:
        """
        Return the top-level keys and values in the storage.
        """

        items = []

        for storage in self._storages:
            items += list(storage.items())

        return items

    def keys(self):
        """
        Return the top-level keys in the storage.
        """

        keys = []

        for storage in self._storages:
            keys += list(storage.keys())

        return keys

    def values(self):
        """
        Return the top-level items in the storage.
        """

        values = []

        for storage in self._storages:
            values += list(storage.values())

        return values

    def __getitem__(self, key: str) -> Any:
        for storage in self._storages:
            if key in storage:
                return storage[key]
        raise error.KeyNotFoundError.with_values(key)

    def __contains__(self, key: str) -> bool:
        return self.contains(key)
