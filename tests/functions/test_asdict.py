import pytest
from full_match import match

from skelet import Field, MemorySource, Storage, asdict


def test_pass_not_storage_object():
    with pytest.raises(TypeError, match=match('asdict() should be called on Storage class instances')):
        asdict(1)


def test_default_values_as_dict():
    class SomeClass(Storage):
        field = Field(42)
        second_field = Field(43)

    assert asdict(SomeClass()) == {'field': 42, 'second_field': 43}


def test_default_factory_values_as_dict():
    class SomeClass(Storage):
        field = Field(default_factory=lambda: 42)
        second_field = Field(default_factory=lambda: 43)

    assert asdict(SomeClass()) == {'field': 42, 'second_field': 43}


def test_new_values_as_dict():
    class SomeClass(Storage):
        field = Field()
        second_field = Field()

    instance = SomeClass(field=42, second_field=43)

    assert asdict(instance) == {'field': 42, 'second_field': 43}


def test_memory_source_values_as_dict():
    class SomeClass(Storage, sources=[MemorySource({'field': 42, 'second_field': 43})]):
        field = Field()
        second_field = Field()

    assert asdict(SomeClass()) == {'field': 42, 'second_field': 43}
