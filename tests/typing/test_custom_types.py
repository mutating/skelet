import pytest

from skelet import Field, NaturalNumber, NonNegativeInt, Storage


@pytest.mark.mypy_testing
def test_natural_number_field() -> None:
    class Config(Storage):
        count: NaturalNumber = Field(1)

    config = Config()
    reveal_type(config.count)  # R: simtypes.types.ints.natural.NaturalNumber


@pytest.mark.mypy_testing
def test_non_negative_int_field() -> None:
    class Config(Storage):
        count: NonNegativeInt = Field(0)

    config = Config()
    reveal_type(config.count)  # R: simtypes.types.ints.non_negative.NonNegativeInt
