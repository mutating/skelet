from typing import Any

import pytest
from typing_extensions import assert_type

from skelet import Field, Storage


@pytest.mark.mypy_testing
def test_field_with_action() -> None:
    def on_change(old: str, new: str, storage: Storage) -> None:
        pass

    class Config(Storage):
        name: str = Field('default', action=on_change)

    config = Config()
    assert_type(config.name, str)


@pytest.mark.mypy_testing
def test_field_with_conflicts() -> None:
    def check_conflict(_old: Any, new: Any, _other_old: Any, other_new: Any) -> bool:
        return bool(new == other_new)

    class Config(Storage):
        a: int = Field(1)
        b: int = Field(2, conflicts={'a': check_conflict})

    config = Config()
    assert_type(config.a, int)
    assert_type(config.b, int)


@pytest.mark.mypy_testing
def test_field_with_conversion_and_validation() -> None:
    class Config(Storage):
        value: int = Field(
            5,
            conversion=lambda x: x * 2,
            validation=lambda x: x >= 0,
        )

    config = Config()
    assert_type(config.value, int)


@pytest.mark.mypy_testing
def test_field_share_mutex_with() -> None:
    class Config(Storage):
        a: int = Field(1, share_mutex_with=['b'])
        b: int = Field(2)

    config = Config()
    assert_type(config.a, int)
    assert_type(config.b, int)


@pytest.mark.mypy_testing
def test_field_read_lock() -> None:
    class Config(Storage):
        value: int = Field(0, read_lock=True)

    config = Config()
    assert_type(config.value, int)


@pytest.mark.mypy_testing
def test_field_reverse_conflicts_false() -> None:
    def never_conflict(_old: Any, _new: Any, _other_old: Any, _other_new: Any) -> bool:
        return False

    class Config(Storage):
        a: int = Field(1)
        b: int = Field(
            2,
            conflicts={'a': never_conflict},
            reverse_conflicts=False,
        )

    config = Config()
    assert_type(config.a, int)
    assert_type(config.b, int)
