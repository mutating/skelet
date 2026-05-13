from typing import Any, ClassVar, List, Optional, Union

import pytest
from typing_extensions import assert_type

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
    assert_type(config.name, str)
    assert_type(config.age, int)


@pytest.mark.mypy_testing
def test_storage_repr() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config()
    assert_type(repr(config), str)


@pytest.mark.mypy_testing
def test_storage_optional_field() -> None:
    class Config(Storage):
        host: Optional[str] = Field(None)

    config = Config()
    assert_type(config.host, Optional[str])
    config.host = None
    config.host = 'localhost'


@pytest.mark.mypy_testing
def test_storage_with_validate_default_false() -> None:
    class Config(Storage):
        count: int = Field(0, validate_default=False)

    config = Config()
    assert_type(config.count, int)


@pytest.mark.mypy_testing
def test_required_shorthand_field_usage():
    def takes_str(value: str) -> None:
        pass

    class Config(Storage):
        name: str

    config = Config(name='Ann')
    takes_str(config.name)
    config.name = 'Bob'


@pytest.mark.mypy_testing
def test_annotated_default_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    class Config(Storage):
        port: int = 8080

    config = Config()
    takes_int(config.port)
    config.port = 8081


@pytest.mark.mypy_testing
def test_untyped_default_shorthand_usage():
    def takes_str(value: str) -> None:
        pass

    class Config(Storage):
        name = 'Ann'

    config = Config()
    takes_str(config.name)
    config.name = 'Bob'


@pytest.mark.mypy_testing
def test_any_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    def takes_str(value: str) -> None:
        pass

    class Config(Storage):
        payload: Any = 'x'

    config = Config()
    config.payload = 1
    takes_int(config.payload)
    config.payload = 'x'
    takes_str(config.payload)


@pytest.mark.mypy_testing
def test_optional_none_shorthand_usage():
    def takes_str(value: str) -> None:
        pass

    class Config(Storage):
        host: Optional[str] = None

    config = Config()
    config.host = 'localhost'
    if config.host is not None:
        takes_str(config.host)
    config.host = None


@pytest.mark.mypy_testing
def test_union_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    def takes_str(value: str) -> None:
        pass

    class Config(Storage):
        value: Union[int, str] = 1

    config = Config()
    if isinstance(config.value, int):
        takes_int(config.value)
    config.value = 'x'
    if isinstance(config.value, str):
        takes_str(config.value)


@pytest.mark.mypy_testing
def test_container_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    def takes_int_list(value: List[int]) -> None:
        pass

    class Config(Storage):
        items: List[int] = []  # noqa: RUF012

    config = Config()
    config.items.append(1)
    for item in config.items:
        takes_int(item)
    takes_int_list(config.items)


@pytest.mark.mypy_testing
def test_mixed_explicit_and_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    def takes_str(value: str) -> None:
        pass

    def takes_bool(value: bool) -> None:
        pass

    class Config(Storage):
        count: int = Field(1)
        name: str
        flag = True

    config = Config(name='Ann')
    takes_int(config.count)
    takes_str(config.name)
    takes_bool(config.flag)
    config.count = 2
    config.name = 'Bob'
    config.flag = False


@pytest.mark.mypy_testing
def test_inherited_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    def takes_str(value: str) -> None:
        pass

    class BaseConfig(Storage):
        count: int = 1

    class Config(BaseConfig):
        name: str = 'Ann'

    config = Config()
    takes_int(config.count)
    takes_str(config.name)


@pytest.mark.mypy_testing
def test_override_shorthand_with_explicit_usage():
    def takes_int(value: int) -> None:
        pass

    class BaseConfig(Storage):
        value: int = 1

    class Config(BaseConfig):
        value: int = Field(2)

    config = Config()
    takes_int(config.value)
    config.value = 3


@pytest.mark.mypy_testing
def test_override_explicit_with_shorthand_usage():
    def takes_int(value: int) -> None:
        pass

    class BaseConfig(Storage):
        value: int = Field(1)

    class Config(BaseConfig):
        value: int = 2

    config = Config()
    takes_int(config.value)
    config.value = 3


@pytest.mark.mypy_testing
def test_classvar_usage():
    def takes_str(value: str) -> None:
        pass

    class Config(Storage):
        kind: ClassVar[str] = 'config'
        name: str = 'Ann'

    takes_str(Config.kind)
    config = Config()
    takes_str(config.name)
