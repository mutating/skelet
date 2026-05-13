from typing import List

from pristan import slot

from skelet.sources.abstract import AbstractSource, ExpectedType
from skelet.sources.env import EnvSource
from skelet.sources.json import JSONSource
from skelet.sources.toml import TOMLSource
from skelet.sources.yaml import YAMLSource


@slot(entrypoint_group='skelet')
def for_tool(tool_name: str) -> List[AbstractSource[ExpectedType]]:  # noqa: ARG001
    return []


def validate_tool_name(tool_name: str) -> str:
    if not tool_name.isidentifier():
        raise ValueError('The library name can only be a valid Python identifier.')

    return tool_name


@for_tool.plugin
def env(tool_name: str) -> EnvSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return EnvSource(prefix=f'{tool_name}_'.upper())


@for_tool.plugin
def toml(tool_name: str) -> TOMLSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return TOMLSource(f'{tool_name}.toml')


@for_tool.plugin
def hidden_toml(tool_name: str) -> TOMLSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return TOMLSource(f'.{tool_name}.toml')


@for_tool.plugin
def pyproject_toml(tool_name: str) -> TOMLSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return TOMLSource('pyproject.toml', table=f'tool.{tool_name}')


@for_tool.plugin
def yaml(tool_name: str) -> YAMLSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return YAMLSource(f'{tool_name}.yaml')


@for_tool.plugin
def hidden_yaml(tool_name: str) -> YAMLSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return YAMLSource(f'.{tool_name}.yaml')


@for_tool.plugin
def json(tool_name: str) -> JSONSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return JSONSource(f'{tool_name}.json')


@for_tool.plugin
def hidden_json(tool_name: str) -> JSONSource[ExpectedType]:
    tool_name = validate_tool_name(tool_name)
    return JSONSource(f'.{tool_name}.json')
