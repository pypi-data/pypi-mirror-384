"""Module containing the _PersistentStorage class"""

import json
import os
from typing import Any

from abllib import error, fs, onexit
from abllib._storage import InternalStorage
from abllib.storage._storage_view import _StorageView
from abllib.storage._threadsafe_storage import _ThreadsafeStorage

# pylint: disable=protected-access
# mypy: ignore-errors

class _PersistentStorage(_ThreadsafeStorage):
    """Storage that persists across restarts"""

    def __init__(self) -> None:
        if _PersistentStorage._instance is not None:
            raise error.SingletonInstantiationError.with_values(_PersistentStorage)

        _PersistentStorage._instance = self

    def initialize(self, filename: str = "storage.json", save_on_exit: bool = False):
        """
        Initialize only the PersistentStorage.

        Not needed if you already called abllib.storage.initialize().

        If save_on_exit is set to True, automatically calls save_to_disk on application exit.
        """

        full_filepath = fs.absolute(filename)
        if not os.path.isdir(os.path.dirname(full_filepath)):
            raise error.DirNotFoundError.with_values(os.path.dirname(full_filepath))

        if _PersistentStorage._store is not None:
            # this is a re-initialization
            if save_on_exit:
                try:
                    onexit.register("PersistentStorage.save", self.save_to_disk)
                except error.RegisteredMultipleTimesError:
                    pass
            else:
                try:
                    onexit.deregister("PersistentStorage.save")
                except error.NameNotFoundError:
                    pass

            if InternalStorage.contains_item("_storage_file", full_filepath):
                # the storage file didn't change
                pass
            else:
                # the storage file changed
                # save current store to old file
                self.save_to_disk()

                InternalStorage["_storage_file"] = full_filepath
                self.load_from_disk()

            return

        _PersistentStorage._store = self._store = {}

        _StorageView._instance.add_storage(self)

        InternalStorage["_storage_file"] = full_filepath
        self.load_from_disk()

        if save_on_exit:
            onexit.register("PersistentStorage.save", self.save_to_disk)

    _STORAGE_NAME = "PersistentStorage"

    def __setitem__(self, key: str, item: Any) -> None:
        # TODO: type check list / dict content types

        if not isinstance(item, (bool, int, float, str, list, dict, tuple)) and item is not None:
            raise TypeError(f"Tried to add item with type {type(item)} to PersistentStorage")

        return super().__setitem__(key, item)

    def load_from_disk(self) -> None:
        """Load the data from the storage file"""

        if "_storage_file" not in InternalStorage:
            raise error.KeyNotFoundError()

        path = InternalStorage["_storage_file"]
        if not os.path.isfile(path):
            return

        with open(path, "r", encoding="utf8") as f:
            self._store = json.load(f)

    def save_to_disk(self) -> None:
        """Save the data to the storage file"""

        if "_storage_file" not in InternalStorage:
            raise error.KeyNotFoundError()

        path = InternalStorage["_storage_file"]
        if len(self._store) == 0 and os.path.isfile(path):
            return

        with open(path, "w", encoding="utf8") as f:
            json.dump(self._store, f)

    def _ensure_initialized(self):
        try:
            super()._ensure_initialized()
        except error.NotInitializedError as exc:
            raise error.NotInitializedError("PersistentStorage is not yet initialized, "
                                            + "are you sure you called storage.initialize()?") \
                                           from exc
