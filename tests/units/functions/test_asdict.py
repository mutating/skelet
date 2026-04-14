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


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_source_values_as_dict(collection_type):
    class SomeClass(Storage):
        field = Field(0)
        second_field = Field(0)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42, 'second_field': 43})]))

    assert asdict(instance) == {'field': 42, 'second_field': 43}


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_source_with_ellipsis_hierarchy_as_dict(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'class_field': 30})]):
        instance_field = Field(0)
        field_field = Field(0, sources=[MemorySource({'field_field': 20}), ...])
        class_field = Field(0)

    instance = SomeClass(_sources=collection_type([MemorySource({'instance_field': 10}), ...]))

    assert asdict(instance) == {'instance_field': 10, 'field_field': 20, 'class_field': 30}


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_source_ellipsis_does_not_reach_class_when_field_has_no_ellipsis_as_dict(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 99})]):
        field = Field(0, sources=[MemorySource({'other': 1})])

    instance = SomeClass(_sources=collection_type([MemorySource({'other': 2}), ...]))

    assert asdict(instance) == {'field': 0}
