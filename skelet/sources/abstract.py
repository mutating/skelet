from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar, Union, cast

from denial import InnerNoneType
from simtypes import check

ExpectedType = TypeVar('ExpectedType')
sentinel = InnerNoneType()

class AbstractSource(Generic[ExpectedType], ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> ExpectedType:
        ...  # pragma: no cover

    def get(self, key: str, default: Union[ExpectedType, InnerNoneType, None] = None) -> Union[ExpectedType, InnerNoneType, None]:
        try:
            result: ExpectedType = self[key]
        except KeyError:
            return default

        return result

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Union[ExpectedType, InnerNoneType] = sentinel) -> Optional[ExpectedType]:
        result = self.get(key, default)

        if result is default:
            if default is sentinel:
                return None
            return cast(ExpectedType, default)

        result = cast(ExpectedType, result)
        if not check(result, hint, strict=True):
            raise TypeError(f'The value of the "{key}" field did not pass the type check.')

        return result
