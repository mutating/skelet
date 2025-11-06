import os
from typing import List, Dict, Type, TypeVar, Optional, Any, cast
from threading import Lock
from functools import cached_property
from copy import copy
from collections import defaultdict

from printo import descript_data_object, not_none
from simtypes import from_string

from skelet.sources.abstract import AbstractSource
from skelet.errors import CaseError


ExpectedType = TypeVar('ExpectedType')

class EnvSource(AbstractSource):
    def __init__(self, prefix: Optional[str] = '', postfix: Optional[str] = '', case_sensitive: bool = False) -> None:
        self.prefix = prefix
        self.postfix = postfix
        self.case_sensitive = case_sensitive

    def __getitem__(self, key: str) -> Any:
        full_key = f'{self.prefix}{key}{self.postfix}'
        if not self.case_sensitive:
            full_key = full_key.upper()

        return self.data[full_key]

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (), {'prefix': self.prefix, 'postfix': self.postfix, 'case_sensitive': self.case_sensitive}, filters={'prefix': lambda x: x != '', 'postfix': lambda x: x != '', 'case_sensitive': lambda x: x != False})

    @cached_property
    def data(self) -> Dict[str, str]:
        if self.case_sensitive:
            return cast(Dict[str, str], copy(os.environ))

        result = {}
        seen_keys = {}
        for key, value in os.environ.items():
            capitalized_key = key.upper()
            if capitalized_key in seen_keys:
                if os.environ[key] != os.environ[seen_keys[capitalized_key]]:
                    raise CaseError(f'There are 2 environment variables that are written the same way when capitalized: "{key}" and "{seen_keys[capitalized_key]}".')
            seen_keys[capitalized_key] = key
            result[capitalized_key] = value

        return result

    def type_awared_get(self, key: str, type: Type[ExpectedType]) -> ExpectedType:
        return from_string(self[key], type)

    @classmethod
    def for_library(cls, library_name: str) -> List['EnvSource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return [cls(prefix=f'{library_name}_'.upper())]
