from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union

from skelet.sources.abstract import AbstractSource

if TYPE_CHECKING:
    from skelet.storage import Storage

__all__ = ['ChangeAction', 'EllipsisType', 'InstanceSourceItem', 'StorageType', 'ValueType']

# EllipsisType was added to the types module in Python 3.10.
try:
    from types import EllipsisType  # type: ignore[attr-defined, unused-ignore]
except ImportError:  # pragma: no cover
    EllipsisType = type(...)  # type: ignore[misc, unused-ignore]

InstanceSourceItem = Union[AbstractSource[Any], EllipsisType]

ValueType = TypeVar('ValueType')
StorageType = TypeVar('StorageType', bound='Storage')
ChangeAction = Callable[[ValueType, ValueType, StorageType], Any]
