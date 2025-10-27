from typing import List, Union, Optional, Any
from pathlib import Path
from functools import cached_property

try:
    from tomllib import load
except ImportError:
    from tomli import load

from skelet.sources.abstract import AbstractSource


class TOMLSource(AbstractSource):
    def __init__(self, path: Union[str, Path], table: Optional[Union[str, List[str]]] = None, allow_non_existent_files: bool = True) -> None:
        self.path = path
        self.allow_non_existent_files = allow_non_existent_files

        if isinstance(table, str):
            self.table = table.split('.')
        elif isinstance(table, list):
            self.table = []
            for subtable in table:
                self.table.extend(subtable.split('.'))
        else:
            self.table = []

        for subtable in self.table:
            if not subtable.isidentifier():
                raise ValueError(f'You can only use a subset of all valid TOML format identifiers that can be used as a Python identifier. You used "{subtable}".')

    @cached_property
    def data(self):
        try:
            with open(self.path, 'rb') as file:
                return load(file)
        except FileNotFoundError as e:
            if self.allow_non_existent_files:
                return {}
            else:
                raise e

    def __getitem__(self, key: str) -> Any:
        data = self.data

        for subtable in self.table:
            data = data[subtable]

        return data[key]

    @classmethod
    def for_library(cls, library_name: str) -> List['TOMLSource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return [cls(f'{library_name}.toml'), cls(f'.{library_name}.toml'), cls('pyproject.toml', table=f'tool.{library_name}')]
