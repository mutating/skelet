from typing import Any, Dict

import pytest
from typing_extensions import assert_type

from skelet import Field, Storage, asdict


@pytest.mark.mypy_testing
def test_asdict_return_type() -> None:
    class Config(Storage):
        name: str = Field('default')
        age: int = Field(0)

    config = Config()
    result = asdict(config)
    assert_type(result, Dict[str, Any])


@pytest.mark.mypy_testing
def test_asdict_accepts_subclass() -> None:
    class Base(Storage):
        name: str = Field('default')

    class Child(Base):
        age: int = Field(0)

    child = Child()
    result = asdict(child)
    assert_type(result, Dict[str, Any])
