"""Module containing tests for the different types of Storage"""

import json
import os

import pytest

from abllib import _storage, error
from abllib._storage._base_storage import _BaseStorage
from abllib.storage import (_CacheStorage, _PersistentStorage, _StorageView,
                            _ThreadsafeStorage, _VolatileStorage)

# pylint: disable=protected-access, missing-class-docstring, pointless-statement, expression-not-assigned

def test_threadsafestorage_name_custom():
    """Ensure that custom storages need to overwrite _STORAGE_NAME"""

    ThreadsafeStorage = _ThreadsafeStorage.__new__(_ThreadsafeStorage)
    ThreadsafeStorage._store = {}

    with pytest.raises(error.UninitializedFieldError):
        class _TestStorage(_ThreadsafeStorage):
            def __init__(self):
                pass

    with pytest.raises(error.WrongTypeError):
        class _TestStorage2(_ThreadsafeStorage):
            def __init__(self):
                pass
            _STORAGE_NAME = 42

    with pytest.raises(error.UninitializedFieldError):
        class _TestStorage3(_ThreadsafeStorage):
            def __init__(self):
                pass
            _STORAGE_NAME = "BaseStorage"

    with pytest.raises(error.UninitializedFieldError):
        class _TestStorage4(_ThreadsafeStorage):
            def __init__(self):
                pass
            _STORAGE_NAME = "ThreadsafeStorage"

    class _TestStorage5(_ThreadsafeStorage):
        def __init__(self):
            pass
        _STORAGE_NAME = "TestStorage5"

def test_volatilestorage_inheritance():
    """Ensure the VolatileStorage inherits from _BaseStorage"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}

    assert isinstance(VolatileStorage, _BaseStorage)
    assert not isinstance(VolatileStorage, _PersistentStorage)
    assert not isinstance(VolatileStorage, _CacheStorage)

def test_volatilestorage_instantiation():
    """Ensure that VolatileStorage behaves like a singleton"""

    with pytest.raises(error.SingletonInstantiationError):
        _VolatileStorage()

    with pytest.raises(error.SingletonInstantiationError):
        _VolatileStorage()

def test_volatilestorage_valuetype():
    """Test the VolatileStorages' support for different value types"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}

    VolatileStorage["key1"] = ["1", 2, None]
    assert VolatileStorage["key1"] == ["1", 2, None]

    class CustomType():
        pass
    custom_item = CustomType()
    VolatileStorage["key1"] = custom_item
    assert VolatileStorage["key1"] == custom_item

def test_volatilestorage_noinit_error():
    """Ensure the VolatileStorage methods don't work before initialization is complete"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = None

    with pytest.raises(error.NotInitializedError):
        VolatileStorage["testkey"]
    with pytest.raises(error.NotInitializedError):
        VolatileStorage["testkey"] = "testvalue"
    with pytest.raises(error.NotInitializedError):
        del VolatileStorage["testkey"]
    with pytest.raises(error.NotInitializedError):
        VolatileStorage.contains("testkey")
    with pytest.raises(error.NotInitializedError):
        VolatileStorage.contains_item("testkey", "testvalue")

    try:
        VolatileStorage["testkey"]
    except error.NotInitializedError as exc:
        assert "VolatileStorage is not yet initialized" in str(exc)
    else:
        pytest.fail("expected exception")

def test_volatilestorage_del_autoremovedict():
    """Test that AutoremoveDicts are correctly deleted on del"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}

    VolatileStorage["key1.key2.key3.key4.key5.key6"] = "values"
    del VolatileStorage["key1.key2.key3.key4.key5.key6"]
    assert "key1.key2.key3.key4.key5" not in VolatileStorage
    assert "key1.key2.key3.key4" not in VolatileStorage
    assert "key1.key2.key3" not in VolatileStorage
    assert "key1.key2" not in VolatileStorage
    assert "key1" not in VolatileStorage

def test_persistentstorage_inheritance():
    """Ensure the PersistentStorage inherits from _BaseStorage"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    assert isinstance(PersistentStorage, _BaseStorage)
    assert not isinstance(PersistentStorage, _VolatileStorage)
    assert not isinstance(PersistentStorage, _CacheStorage)

def test_persistentstorage_instantiation():
    """Ensure that PersistentStorage behaves like a singleton"""

    with pytest.raises(error.SingletonInstantiationError):
        _PersistentStorage()

    with pytest.raises(error.SingletonInstantiationError):
        _PersistentStorage()

def test_persistentstorage_valuetype():
    """Test the PersistentStorages' support for different value types"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    PersistentStorage["key1"] = True
    assert PersistentStorage["key1"] is True
    PersistentStorage["key1"] = 10
    assert PersistentStorage["key1"] == 10
    PersistentStorage["key1"] = 10.1
    assert PersistentStorage["key1"] == 10.1
    PersistentStorage["key1"] = "value"
    assert PersistentStorage["key1"] == "value"
    PersistentStorage["key1"] = ["1", "2"]
    assert PersistentStorage["key1"] == ["1", "2"]
    PersistentStorage["key1"] = {"key": "item"}
    assert PersistentStorage["key1"] == {"key": "item"}
    PersistentStorage["key1"] = ("1", "2")
    assert PersistentStorage["key1"] == ("1", "2")
    PersistentStorage["key1"] = None
    assert PersistentStorage["key1"] is None

    class CustomType():
        pass

    with pytest.raises(TypeError):
        PersistentStorage["key1"] = CustomType()

def test_persistentstorage_load_file():
    """Test the PersistentStorage._load_from_disk() method"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    filepath = _storage.InternalStorage["_storage_file"]

    with open(filepath, "w", encoding="utf8") as f:
        json.dump({
            "key1": "value",
            "key2": [
                "value21",
                "value22",
                "value23"
            ],
            "key3": 10
        }, f)

    PersistentStorage.load_from_disk()

    assert PersistentStorage["key1"] == "value"
    assert PersistentStorage["key2"] == ["value21", "value22", "value23"]
    assert PersistentStorage["key3"] == 10

    os.remove(filepath)

def test_persistentstorage_save_file():
    """Test the PersistentStorage._save_to_disk() method"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    filepath = _storage.InternalStorage["_storage_file"]

    PersistentStorage["key1"] = "value"
    PersistentStorage["key2"] = ["value21", "value22", "value23"]
    PersistentStorage["key4"] = 10

    PersistentStorage.save_to_disk()

    assert os.path.isfile(filepath)
    with open(filepath, "r", encoding="utf8") as f:
        data = json.load(f)
    assert data["key1"] == "value"
    assert data["key2"] == ["value21", "value22", "value23"]
    assert data["key4"] == 10

    os.remove(filepath)

def test_persistentstorage_save_file_empty():
    """
    Ensure the PersistentStorage._save_to_disk() method doesn't overwrite an existing file
    if the PersistentStorage is empty
    """

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    filepath = _storage.InternalStorage["_storage_file"]

    with open(filepath, "w", encoding="utf8") as f:
        json.dump({
            "key1": "newvalue"
        }, f)

    PersistentStorage.save_to_disk()

    with open(filepath, "r", encoding="utf8") as f:
        assert json.load(f)["key1"] == "newvalue"

def test_persistentstorage_noinit_error():
    """Ensure the PersistentStorage methods don't work before initialization is complete"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = None

    with pytest.raises(error.NotInitializedError):
        PersistentStorage["testkey"]
    with pytest.raises(error.NotInitializedError):
        PersistentStorage["testkey"] = "testvalue"
    with pytest.raises(error.NotInitializedError):
        del PersistentStorage["testkey"]
    with pytest.raises(error.NotInitializedError):
        PersistentStorage.contains("testkey")
    with pytest.raises(error.NotInitializedError):
        PersistentStorage.contains_item("testkey", "testvalue")

    try:
        PersistentStorage["testkey"]
    except error.NotInitializedError as exc:
        assert "PersistentStorage is not yet initialized" in str(exc)
    else:
        pytest.fail("expected exception")

def test_persistentstorage_del_autoremovedict():
    """Test that AutoremoveDicts are correctly deleted on del"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    PersistentStorage["key1.key2.key3.key4.key5.key6"] = "values"
    del PersistentStorage["key1.key2.key3.key4.key5.key6"]
    assert "key1.key2.key3.key4.key5" not in PersistentStorage
    assert "key1.key2.key3.key4" not in PersistentStorage
    assert "key1.key2.key3" not in PersistentStorage
    assert "key1.key2" not in PersistentStorage
    assert "key1" not in PersistentStorage

def test_persistentstorage_non_ascii():
    """Ensure that non-ascii characters are saved and loaded correctly"""

    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}

    PersistentStorage["testkey"] = "ÄöÜ"
    PersistentStorage["testkey2"] = "ハウルの動く城"

    PersistentStorage.save_to_disk()

    PersistentStorage._store = {}
    PersistentStorage.load_from_disk()

    assert PersistentStorage["testkey"] == "ÄöÜ"
    assert PersistentStorage["testkey2"] == "ハウルの動く城"

def test_storageview_instantiation():
    """Ensure that instantiating StorageView only works with valid arguments"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    CacheStorage = _CacheStorage.__new__(_CacheStorage)
    CacheStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)
    StorageView.add_storage(CacheStorage)

    class FakeStorage():
        pass

    with pytest.raises(error.MissingInheritanceError):
        StorageView.add_storage(FakeStorage)

def test_storageview_getitem():
    """Test the Storage.__getitem__() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert StorageView["key1"] == "value"
    assert StorageView["key2"] == "value2"

    del VolatileStorage["key1"]
    del PersistentStorage["key2"]

    VolatileStorage["key1.key2.key3"] = "value"
    PersistentStorage["key2.key3.key4.key5.key6.key7"] = "value2"
    assert StorageView["key1.key2.key3"] == "value"
    assert StorageView["key2.key3.key4.key5.key6.key7"] == "value2"

def test_storageview_keys():
    """Test the Storage.keys() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    assert len(StorageView.keys()) == 0
    assert "key1" not in StorageView.keys()
    assert "key2" not in StorageView.keys()

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert len(StorageView.keys()) == 2
    assert "key1" in StorageView.keys()
    assert "key2" in StorageView.keys()
    assert list(StorageView.keys())[0] in ["key1", "key2"]

def test_storageview_values():
    """Test the Storage.values() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    assert len(StorageView.values()) == 0
    assert "value" not in StorageView.values()
    assert "value2" not in StorageView.values()

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert len(StorageView.values()) == 2
    assert "value" in StorageView.values()
    assert "value2" in StorageView.values()
    assert list(StorageView.values())[0] in ["value", "value2"]

def test_storageview_items():
    """Test the Storage.items() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    assert len(StorageView.items()) == 0
    assert ("key1", "value") not in StorageView.items()
    assert ("key2", "value2") not in StorageView.items()

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert len(StorageView.items()) == 2
    assert ("key1", "value") in StorageView.items()
    assert ("key2", "value2") in StorageView.items()

def test_storageview_contains():
    """Test the Storage.contains() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert StorageView.contains("key1")
    assert "key1" in StorageView
    assert StorageView.contains("key2")
    assert "key2" in StorageView

    del VolatileStorage["key1"]
    del PersistentStorage["key2"]

    VolatileStorage["key1.key2.key3"] = "value"
    PersistentStorage["key2.key3.key4.key5.key6.key7"] = "value2"
    assert StorageView.contains("key1.key2.key3")
    assert "key1.key2.key3" in StorageView
    assert StorageView.contains("key2.key3.key4.key5.key6.key7")
    assert "key2.key3.key4.key5.key6.key7" in StorageView

def test_storageview_contains_item():
    """Test the Storage.contains_item() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert StorageView.contains_item("key1", "value")
    assert StorageView.contains_item("key2", "value2")

    del VolatileStorage["key1"]
    del PersistentStorage["key2"]

    VolatileStorage["key1.key2.key3"] = "value"
    PersistentStorage["key2.key3.key4.key5.key6.key7"] = "value2"
    assert StorageView.contains_item("key1.key2.key3", "value")
    assert StorageView.contains_item("key2.key3.key4.key5.key6.key7", "value2")

def test_storageview_get():
    """Test the Storage.get() method"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    assert not StorageView.contains("key1")
    assert StorageView.get("key1") is None

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert StorageView.contains("key1")
    assert StorageView.get("key1") == "value"
    assert StorageView.contains("key2")
    assert StorageView.get("key2") == "value2"

def test_storageview_uniqueness():
    """Test that StorageView.add_storage() only accepts each storage instance once"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    PersistentStorage2 = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage2._store = {}
    StorageView = _StorageView()
    StorageView._storages = []

    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    with pytest.raises(error.RegisteredMultipleTimesError):
        StorageView.add_storage(PersistentStorage)

    StorageView.add_storage(PersistentStorage2)

    with pytest.raises(error.RegisteredMultipleTimesError):
        StorageView.add_storage(PersistentStorage2)
    with pytest.raises(error.RegisteredMultipleTimesError):
        StorageView.add_storage(PersistentStorage2)

def test_storageview_get_default():
    """Test the Storage.get() methods' optional default argument"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = {}
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = {}
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    assert not StorageView.contains("key1")
    assert StorageView.get("key1") is None

    assert StorageView.get("key1", None) is None
    assert StorageView.get("key1", default=None) is None

    assert StorageView.get("key1", 45) == 45
    assert StorageView.get("key1", default=45) == 45

    assert StorageView.get("key1", "test") == "test"
    assert StorageView.get("key1", default="test") == "test"

    VolatileStorage["key1"] = "value"
    PersistentStorage["key2"] = "value2"
    assert StorageView.contains("key1")
    assert StorageView.get("key1") == "value"
    assert StorageView.contains("key2")
    assert StorageView.get("key2") == "value2"

    assert StorageView.get("key1", None) == "value"
    assert StorageView.get("key1", default=None) == "value"
    assert StorageView.get("key2", None) == "value2"
    assert StorageView.get("key2", default=None) == "value2"

    assert StorageView.get("key1", 45) == "value"
    assert StorageView.get("key1", default=45) == "value"
    assert StorageView.get("key2", 45) == "value2"
    assert StorageView.get("key2", default=45) == "value2"

    assert StorageView.get("key1", "test") == "value"
    assert StorageView.get("key1", default="test") == "value"
    assert StorageView.get("key2", "test") == "value2"
    assert StorageView.get("key2", default="test") == "value2"

def test_storageview_noinit_error():
    """Ensure the StorageView methods don't work before initialization is complete"""

    VolatileStorage = _VolatileStorage.__new__(_VolatileStorage)
    VolatileStorage._store = None
    PersistentStorage = _PersistentStorage.__new__(_PersistentStorage)
    PersistentStorage._store = None
    StorageView = _StorageView()
    StorageView._storages = []
    StorageView.add_storage(VolatileStorage)
    StorageView.add_storage(PersistentStorage)

    with pytest.raises(error.NotInitializedError):
        StorageView["testkey"]
    with pytest.raises(error.NotInitializedError):
        StorageView.contains("testkey")
    with pytest.raises(error.NotInitializedError):
        StorageView.contains_item("testkey", "testvalue")

    try:
        StorageView["testkey"]
    except error.NotInitializedError as exc:
        # the first storage should raise an error
        assert "VolatileStorage is not yet initialized" in str(exc)
    else:
        pytest.fail("expected exception")

    VolatileStorage._store = {}

    try:
        StorageView["testkey"]
    except error.NotInitializedError as exc:
        # the second storage should raise an error
        assert "PersistentStorage is not yet initialized" in str(exc)
    else:
        pytest.fail("expected exception")

    PersistentStorage._store = {"testkey": "testval"}

    assert StorageView.contains_item("testkey", "testval")

def test_cachestorage_inheritance():
    """Ensure the CacheStorage inherits from _BaseStorage"""

    CacheStorage = _CacheStorage.__new__(_CacheStorage)
    CacheStorage._store = {}

    assert isinstance(CacheStorage, _BaseStorage)
    assert not isinstance(CacheStorage, _VolatileStorage)
    assert not isinstance(CacheStorage, _PersistentStorage)

def test_cachestorage_instantiation():
    """Ensure that CacheStorage behaves like a singleton"""

    with pytest.raises(error.SingletonInstantiationError):
        _CacheStorage()

    with pytest.raises(error.SingletonInstantiationError):
        _CacheStorage()

def test_cachestorage_valuetype():
    """Test the CacheStorages' support for different value types"""

    CacheStorage = _CacheStorage.__new__(_CacheStorage)
    CacheStorage._store = {}

    CacheStorage["key1"] = ["1", 2, None]
    assert CacheStorage["key1"] == ["1", 2, None]

    class CustomType():
        pass
    custom_item = CustomType()
    CacheStorage["key1"] = custom_item
    assert CacheStorage["key1"] == custom_item

def test_cachestorage_del_autoremovedict():
    """Test that AutoremoveDicts are correctly deleted on del"""

    CacheStorage = _CacheStorage.__new__(_CacheStorage)
    CacheStorage._store = {}

    CacheStorage["key1.key2.key3.key4.key5.key6"] = "values"
    del CacheStorage["key1.key2.key3.key4.key5.key6"]
    assert "key1.key2.key3.key4.key5" not in CacheStorage
    assert "key1.key2.key3.key4" not in CacheStorage
    assert "key1.key2.key3" not in CacheStorage
    assert "key1.key2" not in CacheStorage
    assert "key1" not in CacheStorage
