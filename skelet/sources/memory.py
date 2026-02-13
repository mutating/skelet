from typing import Any, Dict, List

from printo import descript_data_object

from skelet.sources.abstract import AbstractSource


class MemorySource(AbstractSource):
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (self.data,), {})

    @classmethod
    def for_library(cls, library_name: str) -> List['MemorySource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')
        return []
