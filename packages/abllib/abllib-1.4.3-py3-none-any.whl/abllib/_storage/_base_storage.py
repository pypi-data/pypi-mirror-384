"""Module containing the _BaseStorage base class"""

from __future__ import annotations

from typing import Any

from abllib import error

# mypy: ignore-errors

class _AutoremoveDict(dict):
    """An internal class representing auto-removable subdicts within the storage"""

class _BaseStorage():
    def __init__(self) -> None:
        raise NotImplementedError()

    _instance: _BaseStorage | None = None
    _store: dict[str, Any] | None = None

    _STORAGE_NAME = "BaseStorage"

    @property
    def name(self) -> str:
        """Provide a human-readable name for this storage"""

        return self._STORAGE_NAME

    @name.setter
    def name(self, _) -> None:
        raise error.ReadonlyError.with_values("Storage.name")

    def contains_item(self, key: str, item: Any) -> bool:
        """
        Check whether a key within the storage equals an item.

        If 'key' contains a '.', also checks if all sub-dicts exist.
        """

        if not self._contains(key):
            return False
        return item == self[key]

    def contains(self, key: str) -> bool:
        """
        Check whether a key exists within the storage.

        If 'key' contains a '.', also checks if all sub-dicts exist.
        """

        return self._contains(key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Return the value of an key if it exists in the storage.

        If the key is not found, return the default value instead.
        """

        if self._contains(key):
            return self._get(key)

        return default

    def items(self):
        """
        Return a view on the top-level keys and values in the storage.
        """

        return self._store.items()

    def pop(self, key: str) -> Any:
        """
        Return the value of an key if it exists in the storage.
        """

        val = self._get(key)
        self._del(key)
        return val

    def keys(self):
        """
        Return a view on the top-level keys in the storage.
        """

        self._ensure_initialized()

        return self._store.keys()

    def values(self):
        """
        Return a view on the top-level items in the storage.
        """

        self._ensure_initialized()

        return self._store.values()

    def __getitem__(self, key: str) -> Any:
        return self._get(key)

    def __setitem__(self, key: str, item: Any) -> None:
        return self._set(key, item)

    def __delitem__(self, key: str) -> None:
        return self._del(key)

    def __contains__(self, key: str) -> bool:
        return self._contains(key)

    def __str__(self) -> str:
        return str(self._store)

    def _contains(self, key: str) -> bool:
        self._ensure_initialized()
        self._ensure_key_validity(key)

        if "." not in key:
            return key in self._store

        parts = key.split(".")
        curr_dict: dict[str, Any] = self._store
        for c, part in enumerate(parts):
            if part not in curr_dict:
                return False
            # if it isn't the last part
            if c < len(parts) - 1:
                curr_dict: dict[str, Any] = curr_dict[part]

        return parts[-1] in curr_dict

    def _get(self, key: str) -> Any:
        self._ensure_initialized()
        self._ensure_key_validity(key)

        if "." not in key:
            if key not in self._store:
                raise error.KeyNotFoundError.with_values(key)
            return self._store[key]

        parts = key.split(".")
        curr_dict = self._store
        for c, part in enumerate(parts):
            if part not in curr_dict:
                invalid_key = ""
                for item in parts:
                    invalid_key += f"{item}" if invalid_key == "" else f".{item}"
                    if item == part:
                        break
                raise error.KeyNotFoundError.with_values(invalid_key)
            # if it isn't the last part
            if c < len(parts) - 1:
                curr_dict = curr_dict[part]

        return curr_dict[parts[-1]]

    def _set(self, key: str, item: Any) -> None:
        self._ensure_initialized()
        self._ensure_key_validity(key)

        if "." not in key:
            self._store[key] = item
            return

        parts = key.split(".")
        curr_dict = self._store
        for c, part in enumerate(parts):
            # if it isn't the last part
            if c < len(parts) - 1:
                # add a missing dictionary
                if part not in curr_dict:
                    curr_dict[part] = _AutoremoveDict()
                curr_dict = curr_dict[part]
            else:
                # add the actual item
                curr_dict[part] = item

    def _del(self, key: str) -> None:
        self._ensure_initialized()
        self._ensure_key_validity(key)

        if "." not in key:
            if key not in self._store:
                raise error.KeyNotFoundError.with_values(key)
            del self._store[key]
            return

        parts = key.split(".")
        curr_dict = self._store
        for c, part in enumerate(parts):
            if part not in curr_dict:
                invalid_key = ""
                for item in parts:
                    invalid_key += f"{item}" if invalid_key == "" else f".{item}"
                    if item == part:
                        break
                raise error.KeyNotFoundError.with_values(invalid_key)

            # if it isn't the last part
            if c < len(parts) - 1:
                curr_dict = curr_dict[part]
            else:
                # delete the actual item
                del curr_dict[part]

        # delete empty autogenerated dicts
        key = key.rsplit(".", maxsplit=1)[0]
        parts = key.split(".")

        while True:
            curr_dict = self._store

            for c, part in enumerate(parts):
                # if it isn't the last part
                if c < len(parts) - 1:
                    curr_dict = curr_dict[part]
                else:
                    # pylint: disable-next=unidiomatic-typecheck
                    if type(curr_dict[part]) == _AutoremoveDict and len(curr_dict[part]) == 0:
                        # delete the actual item
                        del curr_dict[part]
                    else:
                        # we are done
                        return

            if "." in key:
                key = key.rsplit(".", maxsplit=1)[0]
                parts = key.split(".")
            else:
                # we deleted every subkey
                return

    def _ensure_initialized(self) -> None:
        if self._store is None:
            raise error.NotInitializedError()

    def _ensure_key_validity(self, key: Any) -> None:
        if not isinstance(key, str):
            raise error.WrongTypeError.with_values(key, str)

        if "." in key:
            if key[0] == ".":
                raise error.InvalidKeyError("Key cannot start with '.'")
            if key[-1] == ".":
                raise error.InvalidKeyError("Key cannot end with '.'")
            if ".." in key:
                raise error.InvalidKeyError("Key cannot contain '..'")

    def __init_subclass__(cls):
        if cls._STORAGE_NAME == "BaseStorage":
            raise error.UninitializedFieldError.with_values(cls, "_STORAGE_NAME")

        if not isinstance(cls._STORAGE_NAME, str):
            raise error.WrongTypeError.with_values(cls._STORAGE_NAME, str)
