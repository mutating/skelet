from typing import Any, Union

from skelet.sources.abstract import AbstractSource

__all__ = ['EllipsisType', 'InstanceSourceItem']

# EllipsisType was added to the types module in Python 3.10.
try:
    from types import EllipsisType  # type: ignore[attr-defined, unused-ignore]
except ImportError:  # pragma: no cover
    EllipsisType = type(...)  # type: ignore[misc, unused-ignore]

InstanceSourceItem = Union[AbstractSource[Any], EllipsisType]
