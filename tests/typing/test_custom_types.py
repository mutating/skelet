from typing import cast

import pytest
from typing_extensions import assert_type

from skelet import Field, NaturalNumber, NonNegativeInt, Storage


@pytest.mark.mypy_testing
def test_natural_number_field() -> None:
    class Config(Storage):
        count: NaturalNumber = Field(cast(NaturalNumber, 1))

    config = Config()
    assert_type(config.count, NaturalNumber)


@pytest.mark.mypy_testing
def test_non_negative_int_field() -> None:
    class Config(Storage):
        count: NonNegativeInt = Field(cast(NonNegativeInt, 0))

    config = Config()
    assert_type(config.count, NonNegativeInt)
