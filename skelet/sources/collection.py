from typing import Any, List, Optional, Type, cast

from denial import InnerNoneType
from printo import descript_data_object

from skelet.sources.abstract import AbstractSource, ExpectedType

sentinel = InnerNoneType()

class SourcesCollection(AbstractSource[ExpectedType]):
    def __init__(self, sources: List[AbstractSource[ExpectedType]]) -> None:
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

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: ExpectedType = cast(ExpectedType, sentinel)) -> Optional[ExpectedType]:  # noqa: B008
        for source in self.sources:
            maybe_result = source.type_awared_get(key, hint, default=default)
            if maybe_result is not default:
                return maybe_result

        if default is not sentinel:
            return default

        return None
