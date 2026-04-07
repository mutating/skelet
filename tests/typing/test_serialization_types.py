"""Tests for asdict typing."""
import pytest

from skelet import Field, Storage, asdict


@pytest.mark.mypy_testing
def test_asdict_return_type() -> None:
    class Config(Storage):
        name: str = Field('default')
        age: int = Field(0)

    config = Config()
    result = asdict(config)
    reveal_type(result)  # R: builtins.dict[builtins.str, Any]


@pytest.mark.mypy_testing
def test_asdict_accepts_subclass() -> None:
    class Base(Storage):
        name: str = Field('default')

    class Child(Base):
        age: int = Field(0)

    child = Child()
    result = asdict(child)
    reveal_type(result)  # R: builtins.dict[builtins.str, Any]
