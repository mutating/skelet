from typing import Any, List, Optional, Union

import pytest

from skelet import Field, Storage, asdict
from skelet.sources.abstract import AbstractSource


@pytest.mark.mypy_testing
def test_wrong_assignment_int_field() -> None:
    class Config(Storage):
        age: int = Field(0)

    config = Config()
    config.age = 'abc'  # E: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_str_field() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config()
    config.name = 42  # E: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_optional_field() -> None:
    class Config(Storage):
        host: Optional[str] = Field(None)

    config = Config()
    config.host = 123  # E: [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_union_field() -> None:
    class Config(Storage):
        value: Union[int, str] = Field(42)

    config = Config()
    config.value = None  # E: [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_non_optional_none() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config()
    config.name = None  # E: Incompatible types in assignment (expression has type "None", variable has type "str")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_union_alias() -> None:
    class Config(Storage):
        value: Union[int, str] = Field(42)

    config = Config()
    config.value = None  # E: [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_optional_alias() -> None:
    class Config(Storage):
        name: Optional[str] = Field(None)

    config = Config()
    config.name = 123  # E: [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_container_none() -> None:
    class Config(Storage):
        items: List[int] = Field(default_factory=list)

    config = Config()
    config.items = None  # E: [assignment]


@pytest.mark.mypy_testing
def test_asdict_wrong_argument() -> None:
    asdict(123)  # E: Argument 1 to "asdict" has incompatible type "int"; expected "Storage"  [arg-type]


@pytest.mark.mypy_testing
def test_field_validation_wrong_arity() -> None:
    def zero_arg_validator() -> bool:
        return True

    Field(validation=zero_arg_validator)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_dict_validation_wrong_arity() -> None:
    def zero_arg_validator() -> bool:
        return True

    Field(validation={'message': zero_arg_validator})  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_validation_non_bool_return() -> None:
    def one_arg_validator_returns_int(_value: Any) -> int:
        return 1

    Field(validation=one_arg_validator_returns_int)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_dict_validation_non_bool_return() -> None:
    def one_arg_validator_returns_int(_value: Any) -> int:
        return 1

    Field(validation={'message': one_arg_validator_returns_int})  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_action_wrong_arity() -> None:
    def one_arg_action(x: Any) -> Any:
        return x

    Field(action=one_arg_action)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_action_wrong_storage_type() -> None:
    def wrong_storage_action(_old_value: Any, _new_value: Any, _storage: int) -> None:
        pass

    Field(action=wrong_storage_action)  # E: [type-var]


@pytest.mark.mypy_testing
def test_field_conversion_wrong_arity() -> None:
    def zero_arg_conversion() -> int:
        return 42

    Field(conversion=zero_arg_conversion)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_conversion_wrong_return_type() -> None:
    def conversion_returns_str(_value: Any) -> str:
        return 'bad'

    class Config(Storage):
        value: int = Field(1, conversion=conversion_returns_str)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_conversion_does_not_allow_raw_default_outside_field_type() -> None:
    def keep_str(value: str) -> str:
        return value

    class Config(Storage):
        value: int = Field('1', conversion=keep_str)  # E: [assignment]


@pytest.mark.mypy_testing
def test_field_conflicts_wrong_arity() -> None:
    def two_arg_conflict(x: Any, y: Any) -> bool:
        return True

    Field(conflicts={'a': two_arg_conflict})  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_conflicts_non_bool_return() -> None:
    def four_arg_conflict_returns_int(_old: Any, _new: Any, _other_old: Any, _other_new: Any) -> int:
        return 1

    Field(conflicts={'a': four_arg_conflict_returns_int})  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_default_factory_wrong_arity() -> None:
    def default_factory_with_arg(_value: Any) -> int:
        return 1

    Field(default_factory=default_factory_with_arg)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_field_default_factory_wrong_return_type() -> None:
    def default_factory_returns_str() -> str:
        return 'bad'

    class Config(Storage):
        value: int = Field(default_factory=default_factory_returns_str)  # E: [assignment]


@pytest.mark.mypy_testing
def test_sources_wrong_type_str() -> None:
    class Config(Storage):
        name: str = Field('default')

    sources: List[AbstractSource[Any]] = 'bad'  # E: [assignment]
    Config(_sources=sources)


@pytest.mark.mypy_testing
def test_sources_wrong_type_int() -> None:
    class Config(Storage):
        name: str = Field('default')

    Config(_sources=42)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_sources_wrong_list_element() -> None:
    class Config(Storage):
        name: str = Field('default')

    sources: List[AbstractSource[Any]] = ['not_a_source']  # E: [list-item]
    Config(_sources=sources)


@pytest.mark.mypy_testing
def test_wrong_assignment_dict_to_list() -> None:
    class Config(Storage):
        items: List[int] = Field(default_factory=list)

    config = Config()
    config.items = {'a': 1}  # E: [assignment]


@pytest.mark.mypy_testing
def test_field_share_mutex_with_wrong_element_type() -> None:
    Field(share_mutex_with=[42])  # E: List item 0 has incompatible type "int"; expected "str"  [list-item]
