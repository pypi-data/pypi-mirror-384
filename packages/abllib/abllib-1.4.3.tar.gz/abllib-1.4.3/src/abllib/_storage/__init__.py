"""An internal module containing json-like storages"""

from abllib._storage._base_storage import _BaseStorage
from abllib._storage._internal_storage import _InternalStorage

# pylint: disable=protected-access

InternalStorage = _InternalStorage()
# pylint: disable-next=protected-access
InternalStorage._init()

__exports__ = [
    _BaseStorage,
    InternalStorage
]
