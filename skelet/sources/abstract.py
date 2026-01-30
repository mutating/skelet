from typing import Optional, Any
from abc import ABC, abstractmethod
from typing import TypeVar, Type

from simtypes import check
from denial import InnerNoneType


sentinel = InnerNoneType()

ExpectedType = TypeVar('ExpectedType')

class AbstractSource(ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        ...  # pragma: no cover

    def get(self, key: str, default: Any = None) -> Any:
        try:
            result = self[key]
        except KeyError:
            return default

        return result

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Any = sentinel) -> Optional[ExpectedType]:
        result = self.get(key, default)

        if result is default:
            if default is sentinel:
                return None
            return default

        if not check(result, hint, strict=True):
            raise TypeError(f'The value of the "{key}" field did not pass the type check.')

        return result
