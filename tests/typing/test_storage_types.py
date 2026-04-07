from typing import Optional

import pytest

from skelet import Field, Storage


@pytest.mark.mypy_testing
def test_storage_attribute_assignment() -> None:
    class Config(Storage):
        name: str = Field('default')
        age: int = Field(0)

    config = Config()
    config.name = 'new_name'
    config.age = 42


@pytest.mark.mypy_testing
def test_storage_inheritance() -> None:
    class BaseConfig(Storage):
        name: str = Field('default')

    class ExtendedConfig(BaseConfig):
        age: int = Field(0)

    config = ExtendedConfig()
    reveal_type(config.name)  # R: builtins.str
    reveal_type(config.age)  # R: builtins.int


@pytest.mark.mypy_testing
def test_storage_repr() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config()
    reveal_type(repr(config))  # R: builtins.str


@pytest.mark.mypy_testing
def test_storage_optional_field() -> None:
    class Config(Storage):
        host: Optional[str] = Field(None)

    config = Config()
    reveal_type(config.host)  # R: Union[builtins.str, None]
    config.host = None
    config.host = 'localhost'


@pytest.mark.mypy_testing
def test_storage_with_validate_default_false() -> None:
    class Config(Storage):
        count: int = Field(0, validate_default=False)

    config = Config()
    reveal_type(config.count)  # R: builtins.int
