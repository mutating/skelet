import os
from typing import List, Type, TypeVar, Optional, Any, cast
from argparse import ArgumentParser
from contextlib import redirect_stderr

from simtypes import from_string
from printo import descript_data_object
from denial import InnerNoneType

from skelet.sources.abstract import AbstractSource
from skelet.errors import CLIFormatError


ExpectedType = TypeVar('ExpectedType')
sentinel = InnerNoneType()

class FixedCLISource(AbstractSource):
    def __init__(self, position_arguments: Optional[List[str]] = None, named_arguments: Optional[List[str]] = None) -> None:
        if named_arguments is None and position_arguments is None:
            raise ValueError("You need to pass a list of named arguments or a list of positional arguments, you haven't passed anything.")

        if named_arguments is not None:
            for parameter in named_arguments:
                if not parameter.isidentifier() or parameter == '_' or '__' in parameter:
                    raise ValueError(f'The "{parameter}" parameter is not valid for use on the command line (most likely, it is also not a valid Python name).')
        if position_arguments is not None:
            for parameter in position_arguments:
                if not parameter.isidentifier():
                    raise ValueError(f'The "{parameter}" parameter is not a valid Python identifier.')

        arguments_intersection = set([] if position_arguments is None else position_arguments) & set([] if named_arguments is None else named_arguments)
        if arguments_intersection:
            raise ValueError(f"The following parameters overlap among positional and named command line arguments: {', '.join(sorted(arguments_intersection))}")

        self.position_arguments = position_arguments if position_arguments is not None else []
        self.named_arguments = named_arguments if named_arguments is not None else []

        self.parser = ArgumentParser(add_help=False)

        for parameter in self.named_arguments:
            if len(parameter) == 1:
                full_parameter = f'-{parameter}'
            else:
                full_parameter = f'--{parameter.replace("_", "-")}'
            self.parser.add_argument(full_parameter, nargs='?', const=None, default=sentinel)

        for parameter in self.position_arguments:
            self.parser.add_argument(parameter, nargs='?', const=None, default=sentinel)

    def __getitem__(self, key: str) -> Any:
        with open(os.devnull, 'w') as devnull, redirect_stderr(devnull):
            try:
                result = vars(self.parser.parse_args())[key]
                if result is sentinel:
                    raise KeyError(key)
                return result
            # TODO: from python 3.9 use exit_on_error
            except SystemExit as e:
                raise KeyError(key) from e  # pragma: no cover

    def __repr__(self) -> str:
        return descript_data_object(
            type(self).__name__,
            (),
            {
                'position_arguments': self.position_arguments,
                'named_arguments': self.named_arguments
            },
            filters={
                'position_arguments': lambda x: x,
                'named_arguments': lambda x: x,
            },
        )

    def type_awared_get(self, key: str, hint: Type[ExpectedType], default: Any = sentinel) -> Optional[ExpectedType]:
        subresult = self.get(key, default)

        if hint is bool and key in self.named_arguments:
            if subresult is None:
                return cast(ExpectedType, True)
            elif subresult is sentinel:
                return cast(ExpectedType, False)
            else:
                raise CLIFormatError("You can't pass values for boolean named fields to the CLI.")

        if subresult is default:
            if default is not sentinel:
                return default
            return None

        return from_string(subresult, hint)

    @classmethod
    def for_library(cls, library_name: str) -> List['FixedCLISource']:
        if not library_name.isidentifier():
            raise ValueError('The library name can only be a valid Python identifier.')

        return []
