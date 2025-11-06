from typing import Any
from abc import ABC, abstractmethod
from typing import TypeVar, Type


ExpectedType = TypeVar('ExpectedType')

class AbstractSource(ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        ...  # pragma: no cover

    def type_awared_get(self, key: str, type: Type[ExpectedType]) -> ExpectedType:
        return self[key]
