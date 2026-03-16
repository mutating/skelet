from typing import Dict, List

from printo import repred

from skelet.sources.abstract import AbstractSource, ExpectedType


@repred(prefer_positional=True)
class MemorySource(AbstractSource[ExpectedType]):
    def __init__(self, data: Dict[str, ExpectedType]) -> None:
        self.data = data

    def __getitem__(self, key: str) -> ExpectedType:
        return self.data[key]

    @classmethod
    def for_library(cls, library_name: str) -> List['MemorySource[ExpectedType]']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')
        return []
