"""Pytest fixtures"""

import os
import shutil

import pytest

from abllib import _storage, fs, log, onexit, storage

# pylint: disable=protected-access

logger = log.get_logger("test")

@pytest.fixture(scope="session", autouse=True)
def setup():
    """Setup the PersistentStorage, VolatileStorage and StorageView for test usage"""

    # setup testing dirs
    TESTING_DIR = fs.absolute(os.path.dirname(__file__), "..", "..", "test_run")
    shutil.rmtree(TESTING_DIR, ignore_errors=True)
    os.makedirs(TESTING_DIR, exist_ok=True)
    os.chdir(TESTING_DIR)

    #  setup logging
    log.initialize(log.LogLevel.DEBUG)
    log.add_console_handler()

    if os.path.isfile("test.json"):
        os.remove("test.json")

    storage.initialize("test.json")

    yield None

    storage.PersistentStorage.save_to_disk()

@pytest.fixture(scope="function", autouse=True)
def clean_after_function():
    """
    Release all held locks / semaphores.

    Clean up the PersistentStorage, VolatileStorage and StorageView, removing all keys.

    Remove all onexit callbacks.
    """

    yield None

    if "_locks" in _storage.InternalStorage:
        for name in _storage.InternalStorage["_locks"]:
            for lock in _storage.InternalStorage[f"_locks.{name}"].values():
                lock.release()

    for key in list(storage.PersistentStorage._store.keys()):
        del storage.PersistentStorage[key]

    for key in list(storage.VolatileStorage._store.keys()):
        del storage.VolatileStorage[key]

    for key in list(_storage.InternalStorage._store.keys()):
        if key not in ["_storage_file", "_onexit"]:
            del _storage.InternalStorage[key]

    onexit.reset()

@pytest.fixture(scope="function", autouse=False)
def capture_logs():
    """Save all log output to a new file test.log in the root dir"""

    log.initialize(log.LogLevel.DEBUG)
    log.add_file_handler("test.log")

    yield None

    log.initialize()
    log.add_console_handler()
    # file is created lazily
    if os.path.isfile("test.log"):
        os.remove("test.log")
