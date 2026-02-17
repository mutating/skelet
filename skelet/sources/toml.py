from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    # TODO: This appeared in Python 3.11, this condition needs to be removed when there are no earlier versions in CI.
    from tomllib import load  # type: ignore[import-not-found, unused-ignore]
except ImportError:  # pragma: no cover
    from tomli import (  # type: ignore[import-not-found, no-redef, assignment, unused-ignore]
        load,  # type: ignore[assignment, import-not-found, no-redef, unused-ignore]
    )

from printo import descript_data_object

from skelet.sources.abstract import AbstractSource, ExpectedType


class TOMLSource(AbstractSource[ExpectedType]):
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

    def __getitem__(self, key: str) -> ExpectedType:
        return self.data[key]

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (self.path,), {'table': self.table, 'allow_non_existent_files': self.allow_non_existent_files}, filters={'allow_non_existent_files': lambda x: x != True, 'table': lambda x: bool(x)})

    @cached_property
    def data(self) -> Dict[str, ExpectedType]:
        try:
            with open(self.path, 'rb') as file:
                table = load(file)

            for subtable_name in self.table:
                table = table[subtable_name]

            return table  # type: ignore[no-any-return, unused-ignore]

        except FileNotFoundError:
            if self.allow_non_existent_files:
                return {}
            raise

        except KeyError:
            return {}

    @classmethod
    def for_library(cls, library_name: str) -> List['TOMLSource[ExpectedType]']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return [cls(f'{library_name}.toml'), cls(f'.{library_name}.toml'), cls('pyproject.toml', table=f'tool.{library_name}')]
