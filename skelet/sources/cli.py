import os
from typing import List, Type, TypeVar, Optional, Any
from argparse import ArgumentParser
from contextlib import redirect_stderr

from simtypes import from_string
from printo import descript_data_object
from denial import InnerNone

from skelet.sources.abstract import AbstractSource
from skelet.errors import CLIFormatError


ExpectedType = TypeVar('ExpectedType')

class FixedCLISource(AbstractSource):
    def __init__(self, parameters: List[str]) -> None:
        for parameter in parameters:
            if not parameter.isidentifier() or parameter == '_' or '__' in parameter:
                raise ValueError(f'The "{parameter}" parameter is not valid for use on the command line (most likely, it is also not a valid Python name).')

        self.parameters = parameters
        self.parser = ArgumentParser()
        for parameter in self.parameters:
            if len(parameter) == 1:
                full_parameter = f'-{parameter}'
            else:
                full_parameter = f'--{parameter.replace("_", "-")}'
            self.parser.add_argument(full_parameter, nargs='?', const=None, default=InnerNone)

    def __getitem__(self, key: str) -> Any:
        with open(os.devnull, 'w') as devnull, redirect_stderr(devnull):
            try:
                result = vars(self.parser.parse_args())[key]
                if result is InnerNone:
                    raise KeyError(key)
                return result
            # TODO: from python 3.9 use exit_on_error
            except SystemExit as e:
                raise KeyError(key) from e

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, (self.parameters,), {})

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Any = InnerNone) -> Optional[ExpectedType]:
        subresult = self.get(key, default)

        if hint is bool:
            if subresult is None:
                return True
            elif subresult is InnerNone:
                return False
            else:
                raise CLIFormatError("You can't pass values for boolean fields to the CLI.")

        if subresult is default:
            if default is not InnerNone:
                return default
            return None

        return from_string(subresult, hint)

    @classmethod
    def for_library(cls, library_name: str) -> List['FixedCLISource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return []
