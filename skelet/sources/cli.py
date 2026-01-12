import os
import sys
from typing import List, Type, TypeVar, Optional, Any
from optparse import OptionParser, OptionValueError, BadOptionError
from contextlib import redirect_stderr

from simtypes import from_string
from printo import descript_data_object

from skelet.sources.abstract import AbstractSource, SecondNone


ExpectedType = TypeVar('ExpectedType')

class CLISource(AbstractSource):
    def __init__(self) -> None:
        pass

    def __getitem__(self, key: str) -> Any:
        if len(key) != 1:
            wrapped_key = key.replace("_", "-")
        else:
            wrapped_key = key

        dashed_key = f'-{wrapped_key}' if len(wrapped_key) == 1 else f'--{wrapped_key}'

        parser = OptionParser()
        parser.add_option(dashed_key, action="store", type="string")

        with open(os.devnull, 'w') as devnull, redirect_stderr(devnull):
            try:
                print(dashed_key, parser.parse_args(sys.argv[1:])[0])

                result = getattr(parser.parse_args(sys.argv[1:])[0], key)
                if result is None:
                    raise KeyError(dashed_key)
                return result
            except (OptionValueError, BadOptionError, SystemExit) as e:
                print('another', dashed_key, sys.argv[1:])
                #raise e
                raise KeyError(dashed_key) from e

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (), {})

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Any = SecondNone()) -> Optional[ExpectedType]:
        subresult = self.get(key, default)

        if subresult is default:
            if not isinstance(default, SecondNone):
                return default
            return None

        return from_string(subresult, hint)

    @classmethod
    def for_library(cls, library_name: str) -> List['CLISource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return []
