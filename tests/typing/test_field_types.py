from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from skelet import Field, Storage


@pytest.mark.mypy_testing
def test_field_scalar_defaults() -> None:
    class Config(Storage):
        age: int = Field(0)
        name: str = Field('default')
        ratio: float = Field(1.5)
        debug: bool = Field(False)

    config = Config()
    reveal_type(config.age)  # R: builtins.int
    reveal_type(config.name)  # R: builtins.str
    reveal_type(config.ratio)  # R: builtins.float
    reveal_type(config.debug)  # R: builtins.bool


@pytest.mark.mypy_testing
def test_field_no_default() -> None:
    class Config(Storage):
        name: str = Field()

    config = Config(name='hello')
    reveal_type(config.name)  # R: builtins.str


@pytest.mark.mypy_testing
def test_field_optional_type() -> None:
    class Config(Storage):
        name: Optional[str] = Field(None)

    config = Config()
    reveal_type(config.name)  # R: Union[builtins.str, None]


@pytest.mark.mypy_testing
def test_field_union_type() -> None:
    class Config(Storage):
        value: Union[int, str] = Field(42)

    config = Config()
    reveal_type(config.value)  # R: Union[builtins.int, builtins.str]


@pytest.mark.mypy_testing
def test_field_pep604_union() -> None:
    class Config(Storage):
        value: int | str = Field(42)

    config = Config()
    reveal_type(config.value)  # R: Union[builtins.int, builtins.str]


@pytest.mark.mypy_testing
def test_field_pep604_optional() -> None:
    class Config(Storage):
        name: str | None = Field(None)

    config = Config()
    reveal_type(config.name)  # R: Union[builtins.str, None]


@pytest.mark.mypy_testing
def test_field_any_type() -> None:
    class Config(Storage):
        payload: Any = Field({})

    config = Config()
    reveal_type(config.payload)  # R: Any


@pytest.mark.mypy_testing
def test_field_list_type() -> None:
    class Config(Storage):
        items: List[int] = Field(default_factory=list)

    config = Config()
    reveal_type(config.items)  # R: builtins.list[builtins.int]


def _make_empty_dict() -> Dict[str, int]:
    return {}


@pytest.mark.mypy_testing
def test_field_dict_type() -> None:
    class Config(Storage):
        mapping: Dict[str, int] = Field(default_factory=_make_empty_dict)

    config = Config()
    reveal_type(config.mapping)  # R: builtins.dict[builtins.str, builtins.int]


@pytest.mark.mypy_testing
def test_field_tuple_type() -> None:
    class Config(Storage):
        coords: Tuple[int, int] = Field((0, 0))

    config = Config()
    reveal_type(config.coords)  # R: tuple[builtins.int, builtins.int]


@pytest.mark.mypy_testing
def test_field_with_default_factory() -> None:
    class Config(Storage):
        items: List[Any] = Field(default_factory=list)

    config = Config()
    reveal_type(config.items)  # R: builtins.list[Any]


@pytest.mark.mypy_testing
def test_multiple_fields() -> None:
    class Config(Storage):
        name: str = Field('default')
        age: int = Field(0)
        debug: bool = Field(False)

    config = Config()
    reveal_type(config.name)  # R: builtins.str
    reveal_type(config.age)  # R: builtins.int
    reveal_type(config.debug)  # R: builtins.bool


@pytest.mark.mypy_testing
def test_field_with_doc() -> None:
    class Config(Storage):
        name: str = Field('default', doc='The user name')

    config = Config()
    reveal_type(config.name)  # R: builtins.str


@pytest.mark.mypy_testing
def test_field_with_validation() -> None:
    class Config(Storage):
        age: int = Field(18, validation=lambda x: x >= 0)

    config = Config()
    reveal_type(config.age)  # R: builtins.int


@pytest.mark.mypy_testing
def test_field_with_dict_validation() -> None:
    class Config(Storage):
        age: int = Field(18, validation={'Must be positive': lambda x: x >= 0})

    config = Config()
    reveal_type(config.age)  # R: builtins.int


@pytest.mark.mypy_testing
def test_field_secret() -> None:
    class Config(Storage):
        password: str = Field('secret', secret=True)

    config = Config()
    reveal_type(config.password)  # R: builtins.str


@pytest.mark.mypy_testing
def test_field_read_only() -> None:
    class Config(Storage):
        version: str = Field('1.0', read_only=True)

    config = Config()
    reveal_type(config.version)  # R: builtins.str


@pytest.mark.mypy_testing
def test_field_with_alias() -> None:
    class Config(Storage):
        name: str = Field('default', alias='NAME')

    config = Config()
    reveal_type(config.name)  # R: builtins.str


@pytest.mark.mypy_testing
def test_field_with_conversion() -> None:
    class Config(Storage):
        value: int = Field(0, conversion=lambda x: x * 2)

    config = Config()
    reveal_type(config.value)  # R: builtins.int


def _str_to_int(x: Any) -> int:
    return int(x)


@pytest.mark.mypy_testing
def test_field_conversion_type_widening() -> None:
    class Config(Storage):
        value: Union[str, int] = Field('0', conversion=_str_to_int)

    config = Config()
    reveal_type(config.value)  # R: Union[builtins.str, builtins.int]
