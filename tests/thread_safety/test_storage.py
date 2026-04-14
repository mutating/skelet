import pytest

from skelet import Field, Storage

pytestmark = pytest.mark.thread_safety


def test_share_mutex_with_is_transitive():
    class SomeClass(Storage):
        first_field = Field(1, share_mutex_with=['second_field'])
        second_field = Field(2, share_mutex_with=['third_field'])
        third_field = Field(3)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is instance.__locks__['second_field']
    assert instance.__locks__['second_field'] is instance.__locks__['third_field']


def test_share_mutex_with_and_conflicts_merge_into_one_group():
    def fields_conflict(
        _old_first: int,
        new_first: int,
        _old_third: int,
        new_third: int,
    ) -> bool:
        return new_first > 0 and new_third > 0

    class SomeClass(Storage):
        first_field = Field(
            0,
            share_mutex_with=['second_field'],
            conflicts={'third_field': fields_conflict},
        )
        second_field = Field(0)
        third_field = Field(0)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is instance.__locks__['second_field']
    assert instance.__locks__['second_field'] is instance.__locks__['third_field']


def test_independent_fields_use_different_mutexes():
    class SomeClass(Storage):
        first_field = Field(1)
        second_field = Field(2)
        third_field = Field(3)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is not instance.__locks__['second_field']
    assert instance.__locks__['first_field'] is not instance.__locks__['third_field']
    assert instance.__locks__['second_field'] is not instance.__locks__['third_field']


def test_two_instances_do_not_share_mutex_groups():
    class SomeClass(Storage):
        field = Field(1, conflicts={'other_field': lambda *_: False})
        other_field = Field(2)

    first = SomeClass()
    second = SomeClass()

    assert first.__locks__['field'] is not second.__locks__['field']
    assert first.__locks__['other_field'] is not second.__locks__['other_field']
