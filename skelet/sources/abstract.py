from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar, cast

from denial import InnerNoneType
from simtypes import check

ExpectedType = TypeVar('ExpectedType')
sentinel = InnerNoneType()

class AbstractSource(Generic[ExpectedType], ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> ExpectedType:
        ...  # pragma: no cover

    def get(self, key: str, default: Optional[ExpectedType] = None) -> Optional[ExpectedType]:
        try:
            result: ExpectedType = self[key]
        except KeyError:
            return default

        return result

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: ExpectedType = cast(ExpectedType, sentinel)) -> Optional[ExpectedType]:  # noqa: B008
        result = self.get(key, default)

        if result is default:
            if default is sentinel:
                return None
            return default

        if not check(result, hint, strict=True):
            raise TypeError(f'The value of the "{key}" field did not pass the type check.')

        return result
