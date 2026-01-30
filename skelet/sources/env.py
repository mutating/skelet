import os
import platform
from typing import List, Dict, Type, TypeVar, Optional, Any, cast
from functools import cached_property
from copy import copy

from printo import descript_data_object
from simtypes import from_string
from denial import InnerNoneType

from skelet.sources.abstract import AbstractSource
from skelet.errors import CaseError


ExpectedType = TypeVar('ExpectedType')
sentinel = InnerNoneType()

class EnvSource(AbstractSource):
    def __init__(self, prefix: Optional[str] = '', postfix: Optional[str] = '', case_sensitive: bool = False) -> None:
        if platform.system() == 'Windows' and case_sensitive:
            raise OSError('On Windows, the environment variables are case-independent.')  # pragma: no cover

        self.prefix = prefix
        self.postfix = postfix
        self.case_sensitive = case_sensitive

    def __getitem__(self, key: str) -> Any:
        full_key = f'{self.prefix}{key}{self.postfix}'
        if not self.case_sensitive:  # pragma: no cover
            full_key = full_key.upper()

        return self.data[full_key]

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (), {'prefix': self.prefix, 'postfix': self.postfix, 'case_sensitive': self.case_sensitive}, filters={'prefix': lambda x: x != '', 'postfix': lambda x: x != '', 'case_sensitive': lambda x: x != False})

    @cached_property
    def data(self) -> Dict[str, str]:
        if self.case_sensitive:  # pragma: no cover
            return cast(Dict[str, str], copy(os.environ))

        result = {}
        seen_keys: Dict[str, str] = {}
        for key, value in os.environ.items():
            capitalized_key = key.upper()
            if capitalized_key in seen_keys:
                if os.environ[key] != os.environ[seen_keys[capitalized_key]]:  # pragma: no cover
                    raise CaseError(f'There are 2 environment variables that are written the same way when capitalized: "{key}" and "{seen_keys[capitalized_key]}".')
            seen_keys[capitalized_key] = key
            result[capitalized_key] = value

        return result

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Any = sentinel) -> Optional[ExpectedType]:
        subresult = self.get(key, default)

        if subresult is default:
            if default is not sentinel:
                return default
            return None

        return from_string(subresult, hint)

    @classmethod
    def for_library(cls, library_name: str) -> List['EnvSource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return [cls(prefix=f'{library_name}_'.upper())]
