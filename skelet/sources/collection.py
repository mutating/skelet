from typing import List, Any

from printo import descript_data_object

from skelet.sources.abstract import AbstractSource


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
