# noqa: A005
from functools import cached_property
from json import load
from pathlib import Path
from typing import Any, List, Union

from printo import descript_data_object

from skelet.sources.abstract import AbstractSource


class JSONSource(AbstractSource):
    def __init__(self, path: Union[str, Path], allow_non_existent_files: bool = True) -> None:
        self.path = path
        self.allow_non_existent_files = allow_non_existent_files

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (self.path,), {'allow_non_existent_files': self.allow_non_existent_files}, filters={'allow_non_existent_files': lambda x: x != True})

    @cached_property
    def data(self):
        try:
            with open(self.path, 'r') as file:
                return load(file)

        except FileNotFoundError:
            if self.allow_non_existent_files:
                return {}
            raise

    @classmethod
    def for_library(cls, library_name: str) -> List['JSONSource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return [cls(f'{library_name}.json'), cls(f'.{library_name}.json')]
