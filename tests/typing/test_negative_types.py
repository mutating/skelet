from __future__ import annotations

from typing import Any, List, Optional, Union

import pytest

from skelet import Field, Storage, asdict


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
    config.host = 123  # E: Incompatible types in assignment (expression has type "int", variable has type "str | None")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_union_field() -> None:
    class Config(Storage):
        value: Union[int, str] = Field(42)

    config = Config()
    config.value = None  # E: Incompatible types in assignment (expression has type "None", variable has type "int | str")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_non_optional_none() -> None:
    class Config(Storage):
        name: str = Field('default')

    config = Config()
    config.name = None  # E: Incompatible types in assignment (expression has type "None", variable has type "str")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_pep604_union() -> None:
    class Config(Storage):
        value: int | str = Field(42)

    config = Config()
    config.value = None  # E: Incompatible types in assignment (expression has type "None", variable has type "int | str")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_pep604_optional() -> None:
    class Config(Storage):
        name: str | None = Field(None)

    config = Config()
    config.name = 123  # E: Incompatible types in assignment (expression has type "int", variable has type "str | None")  [assignment]


@pytest.mark.mypy_testing
def test_wrong_assignment_container_none() -> None:
    class Config(Storage):
        items: List[int] = Field(default_factory=list)

    config = Config()
    config.items = None  # E: Incompatible types in assignment (expression has type "None", variable has type "list[int]")  [assignment]


@pytest.mark.mypy_testing
def test_asdict_wrong_argument() -> None:
    asdict(123)  # E: Argument 1 to "asdict" has incompatible type "int"; expected "Storage"  [arg-type]


@pytest.mark.mypy_testing
def test_field_read_only_wrong_type() -> None:
    Field(read_only='yes')  # E: Argument "read_only" to "Field" has incompatible type "str"; expected "bool"  [arg-type]


@pytest.mark.mypy_testing
def test_field_secret_wrong_type() -> None:
    Field(secret=1)  # E: Argument "secret" to "Field" has incompatible type "int"; expected "bool"  [arg-type]


@pytest.mark.mypy_testing
def test_field_validate_default_wrong_type() -> None:
    Field(validate_default='no')  # E: Argument "validate_default" to "Field" has incompatible type "str"; expected "bool"  [arg-type]


@pytest.mark.mypy_testing
def test_field_read_lock_wrong_type() -> None:
    Field(read_lock='yes')  # E: Argument "read_lock" to "Field" has incompatible type "str"; expected "bool"  [arg-type]


@pytest.mark.mypy_testing
def test_field_validation_wrong_type() -> None:
    Field(validation=42)  # E: Argument "validation" to "Field" has incompatible type "int"; expected "dict[str, Callable[[Any], bool]] | Callable[[Any], bool] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_action_wrong_type() -> None:
    Field(action=42)  # E: Argument "action" to "Field" has incompatible type "int"; expected "Callable[[Any, Any, Storage], Any] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_conversion_wrong_type() -> None:
    Field(conversion=42)  # E: Argument "conversion" to "Field" has incompatible type "int"; expected "Callable[[Any], Any] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_conflicts_wrong_type() -> None:
    Field(conflicts=42)  # E: Argument "conflicts" to "Field" has incompatible type "int"; expected "dict[str, Callable[[Any, Any, Any, Any], bool]] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_default_factory_wrong_type() -> None:
    Field(default_factory=42)  # E: Argument "default_factory" to "Field" has incompatible type "int"; expected "Callable[[], Any] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_doc_wrong_type() -> None:
    Field(doc=42)  # E: Argument "doc" to "Field" has incompatible type "int"; expected "str | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_alias_wrong_type() -> None:
    Field(alias=42)  # E: Argument "alias" to "Field" has incompatible type "int"; expected "str | None"  [arg-type]


def _zero_arg_validator() -> bool:
    return True


def _one_arg_action(x: Any) -> Any:
    return x


def _zero_arg_conversion() -> int:
    return 42


def _two_arg_conflict(x: Any, y: Any) -> bool:
    return True


@pytest.mark.mypy_testing
def test_field_validation_wrong_arity() -> None:
    Field(validation=_zero_arg_validator)  # E: Argument "validation" to "Field" has incompatible type "Callable[[], bool]"; expected "dict[str, Callable[[Any], bool]] | Callable[[Any], bool] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_action_wrong_arity() -> None:
    Field(action=_one_arg_action)  # E: Argument "action" to "Field" has incompatible type "Callable[[Any], Any]"; expected "Callable[[Any, Any, Storage], Any] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_conversion_wrong_arity() -> None:
    Field(conversion=_zero_arg_conversion)  # E: Argument "conversion" to "Field" has incompatible type "Callable[[], int]"; expected "Callable[[Any], Any] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_conflicts_wrong_arity() -> None:
    Field(conflicts={'a': _two_arg_conflict})  # E: Dict entry 0 has incompatible type "str": "Callable[[Any, Any], bool]"; expected "str": "Callable[[Any, Any, Any, Any], bool]"  [dict-item]


@pytest.mark.mypy_testing
def test_sources_wrong_type_str() -> None:
    class Config(Storage):
        name: str = Field('default')

    Config(_sources='bad')  # E: Argument "_sources" to "Config" has incompatible type "str"; expected "Sequence[AbstractSource[Any] | EllipsisType] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_sources_wrong_type_int() -> None:
    class Config(Storage):
        name: str = Field('default')

    Config(_sources=42)  # E: Argument "_sources" to "Config" has incompatible type "int"; expected "Sequence[AbstractSource[Any] | EllipsisType] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_sources_wrong_list_element() -> None:
    class Config(Storage):
        name: str = Field('default')

    Config(_sources=['not_a_source'])  # E: List item 0 has incompatible type "str"; expected "AbstractSource[Any] | EllipsisType"  [list-item]


@pytest.mark.mypy_testing
def test_wrong_assignment_dict_to_list() -> None:
    class Config(Storage):
        items: List[int] = Field(default_factory=list)

    config = Config()
    config.items = {'a': 1}  # E: Incompatible types in assignment (expression has type "dict[str, int]", variable has type "list[int]")  [assignment]


@pytest.mark.mypy_testing
def test_field_sources_wrong_element_type() -> None:
    Field(sources=[42])  # E: Argument "sources" to "Field" has incompatible type "list[int]"; expected "list[AbstractSource[Never] | EllipsisType] | None"  [arg-type]


@pytest.mark.mypy_testing
def test_field_share_mutex_with_wrong_element_type() -> None:
    Field(share_mutex_with=[42])  # E: List item 0 has incompatible type "int"; expected "str"  [list-item]
