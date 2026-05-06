from typing import Any, Dict, List, Optional, Tuple, Union

import pytest
from typing_extensions import assert_type

from skelet import F, Field, Storage


@pytest.mark.mypy_testing
def test_field_scalar_defaults() -> None:
    class Config(Storage):
        age: int = Field(0)
        name: str = Field('default')
        ratio: float = Field(1.5)
        debug: bool = Field(False)

    config = Config()
    assert_type(config.age, int)
    assert_type(config.name, str)
    assert_type(config.ratio, float)
    assert_type(config.debug, bool)


@pytest.mark.mypy_testing
def test_field_no_default() -> None:
    class Config(Storage):
        name: str = Field()

    config = Config(name='hello')
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_short_alias() -> None:
    class Config(Storage):
        name: str = F()

    config = Config(name='hello')
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_optional_type() -> None:
    class Config(Storage):
        name: Optional[str] = Field(None)

    config = Config()
    assert_type(config.name, Optional[str])


@pytest.mark.mypy_testing
def test_field_union_type() -> None:
    class Config(Storage):
        value: Union[int, str] = Field(42)

    config = Config()
    assert_type(config.value, Union[int, str])


@pytest.mark.mypy_testing
def test_field_union_alias() -> None:
    class Config(Storage):
        value: Union[int, str] = Field(42)

    config = Config()
    assert_type(config.value, Union[int, str])


@pytest.mark.mypy_testing
def test_field_optional_alias() -> None:
    class Config(Storage):
        name: Optional[str] = Field(None)

    config = Config()
    assert_type(config.name, Optional[str])


@pytest.mark.mypy_testing
def test_field_any_type() -> None:
    class Config(Storage):
        payload: Any = Field({})

    config = Config()
    assert_type(config.payload, Any)


@pytest.mark.mypy_testing
def test_field_list_type() -> None:
    class Config(Storage):
        items: List[int] = Field(default_factory=list)

    config = Config()
    assert_type(config.items, List[int])


@pytest.mark.mypy_testing
def test_field_dict_type() -> None:
    def make_empty_dict() -> Dict[str, int]:
        return {}

    class Config(Storage):
        mapping: Dict[str, int] = Field(default_factory=make_empty_dict)

    config = Config()
    assert_type(config.mapping, Dict[str, int])


@pytest.mark.mypy_testing
def test_field_tuple_type() -> None:
    class Config(Storage):
        coords: Tuple[int, int] = Field((0, 0))

    config = Config()
    assert_type(config.coords, Tuple[int, int])


@pytest.mark.mypy_testing
def test_field_with_default_factory() -> None:
    class Config(Storage):
        items: List[Any] = Field(default_factory=list)

    config = Config()
    assert_type(config.items, List[Any])


@pytest.mark.mypy_testing
def test_field_with_typed_default_factory() -> None:
    def make_default_age() -> int:
        return 18

    class Config(Storage):
        age: int = Field(default_factory=make_default_age)

    config = Config()
    assert_type(config.age, int)


@pytest.mark.mypy_testing
def test_multiple_fields() -> None:
    class Config(Storage):
        name: str = Field('default')
        age: int = Field(0)
        debug: bool = Field(False)

    config = Config()
    assert_type(config.name, str)
    assert_type(config.age, int)
    assert_type(config.debug, bool)


@pytest.mark.mypy_testing
def test_field_with_doc() -> None:
    class Config(Storage):
        name: str = Field('default', doc='The user name')

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_with_validation() -> None:
    class Config(Storage):
        age: int = Field(18, validation=lambda x: x >= 0)

    config = Config()
    assert_type(config.age, int)


@pytest.mark.mypy_testing
def test_field_with_variadic_validation() -> None:
    def variadic_validator(*args: Any) -> bool:
        return bool(args)

    class Config(Storage):
        age: int = Field(18, validation=variadic_validator)

    config = Config()
    assert_type(config.age, int)


@pytest.mark.mypy_testing
def test_field_with_dict_validation() -> None:
    class Config(Storage):
        age: int = Field(18, validation={'Must be positive': lambda x: x >= 0})

    config = Config()
    assert_type(config.age, int)


@pytest.mark.mypy_testing
def test_field_secret() -> None:
    class Config(Storage):
        password: str = Field('secret', secret=True)

    config = Config()
    assert_type(config.password, str)


@pytest.mark.mypy_testing
def test_field_read_only() -> None:
    class Config(Storage):
        version: str = Field('1.0', read_only=True)

    config = Config()
    assert_type(config.version, str)


@pytest.mark.mypy_testing
def test_field_with_alias() -> None:
    class Config(Storage):
        name: str = Field('default', alias='NAME')

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_with_conversion() -> None:
    class Config(Storage):
        value: int = Field(0, conversion=lambda x: x * 2)

    config = Config()
    assert_type(config.value, int)


@pytest.mark.mypy_testing
def test_field_with_typed_conversion() -> None:
    def double(value: int) -> int:
        return value * 2

    class Config(Storage):
        value: int = Field(0, conversion=double)

    config = Config()
    assert_type(config.value, int)


@pytest.mark.mypy_testing
def test_field_conversion_type_widening() -> None:
    def make_raw_value() -> Union[str, int]:
        return '0'

    def normalize(value: Union[str, int]) -> Union[str, int]:
        return int(value)

    class Config(Storage):
        value: Union[str, int] = Field(default_factory=make_raw_value, conversion=normalize)

    config = Config()
    assert_type(config.value, Union[str, int])
