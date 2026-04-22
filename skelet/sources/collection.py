from typing import Any, List, Optional, Type, Union, cast

from denial import InnerNoneType
from printo import repred

from skelet.sources.abstract import AbstractSource, ExpectedType

sentinel = InnerNoneType()

@repred(prefer_positional=True)
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

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Union[ExpectedType, InnerNoneType] = sentinel) -> Optional[ExpectedType]:
        for source in self.sources:
            maybe_result = source.type_awared_get(key, hint, default=default)
            if maybe_result is not default:
                return maybe_result

        if default is not sentinel:
            return cast(ExpectedType, default)

        return None
