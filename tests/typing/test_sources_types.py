from typing import Any, List, Union

import pytest
from typing_extensions import assert_type

from skelet import (
    EnvSource,
    Field,
    FixedCLISource,
    JSONSource,
    MemorySource,
    Storage,
    TOMLSource,
    YAMLSource,
    for_tool,
)
from skelet.sources.abstract import AbstractSource
from skelet.types import EllipsisType

FieldSources = List[Union[AbstractSource[Any], EllipsisType]]


@pytest.mark.mypy_testing
def test_class_level_sources_for_tool() -> None:
    class Config(Storage, sources=for_tool('my_tool')):
        name: str = Field('default')

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_level_sources_memory() -> None:
    sources: FieldSources = [MemorySource({'name': 'val'})]

    class Config(Storage):
        name: str = Field('default', sources=sources)

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_instance_sources_list() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config(_sources=[MemorySource({'name': 'from_memory'})])
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_instance_sources_tuple() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config(_sources=(MemorySource({'name': 'from_memory'}),))
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_instance_sources_with_ellipsis() -> None:
    class Config(Storage, sources=for_tool('my_tool')):
        name: str = Field('default')

    config = Config(_sources=[MemorySource({'name': 'from_memory'}), ...])
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_env_source_typing() -> None:
    class Config(Storage, sources=for_tool('test')):
        name: str = Field('default')

    config = Config(_sources=[EnvSource()])
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_toml_source_typing() -> None:
    sources: FieldSources = [TOMLSource('pyproject.toml', table='tool.test')]

    class Config(Storage):
        name: str = Field('default', sources=sources)

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_json_source_typing() -> None:
    sources: FieldSources = [JSONSource('config.json')]

    class Config(Storage):
        name: str = Field('default', sources=sources)

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_yaml_source_typing() -> None:
    sources: FieldSources = [YAMLSource('config.yaml')]

    class Config(Storage):
        name: str = Field('default', sources=sources)

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_fixed_cli_source_typing() -> None:
    sources: FieldSources = [FixedCLISource(['name', 'val'])]

    class Config(Storage):
        name: str = Field('default', sources=sources)

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_sources_with_ellipsis() -> None:
    field_sources: FieldSources = [MemorySource({'name': 'val'}), ...]

    class Config(Storage, sources=for_tool('my_tool')):
        name: str = Field('default', sources=field_sources)

    config = Config()
    assert_type(config.name, str)
