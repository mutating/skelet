from typing import Any
from abc import ABC, abstractmethod


class AbstractSource(ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        ...  # pragma: no cover
