from typing import List, Type, TypeVar, Optional, Any

from printo import descript_data_object
from denial import InnerNoneType

from skelet.sources.abstract import AbstractSource


ExpectedType = TypeVar('ExpectedType')
sentinel = InnerNoneType()

class SourcesCollection(AbstractSource):
    def __init__(self, sources: List[AbstractSource]) -> None:
        self.sources = sources

    def __getitem__(self, key: str) -> Any:
        for source in self.sources:
            try:
                return source[key]
            except KeyError:
                pass

        raise KeyError(key)

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (self.sources,), {})

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Any = sentinel) -> Optional[ExpectedType]:
        for source in self.sources:
            maybe_result = source.type_awared_get(key, hint, default=default)
            if maybe_result is not default:
                return maybe_result

        if default is not sentinel:
            return default

        return None
