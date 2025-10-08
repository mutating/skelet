from skelet import Storage, Field

import pytest
import full_match


def test_try_to_get_default_value_from_class_inherited_from_storage():
    class SomeClass(Storage):
        field = Field(42)

    with pytest.raises(TypeError, match=full_match('Field "field" can only be used in Storage instances.')):
        SomeClass.field


def test_try_to_use_field_outside_storage():
    with pytest.raises(RuntimeError):
        class SomeClass:
            field = Field(42)


def test_try_to_use_one_field_in_two_storage_classes():
    field = Field(42)

    class FirstClass(Storage):
        field = Field(42)

    with pytest.raises(RuntimeError):
        class SecondClass(Storage):
            field = FirstClass.__dict__['field']


def test_set_default_value_and_read_it():
    class SomeClass(Storage):
        field = Field(42)

    some_object = SomeClass()

    assert some_object.field == 42


def test_set_not_default_value_and_read_it():
    class SomeClass(Storage):
        field = Field(42)

    object_1 = SomeClass()
    object_2 = SomeClass()

    assert object_1.field == 42
    assert object_2.field == 42

    object_1.field = 100
    object_2.field = 200

    assert object_1.field == 100
    assert object_2.field == 200


def test_set_not_default_value_and_read_multiple_times():
    class SomeClass(Storage):
        field = Field(0)

    object = SomeClass()

    for index in range(10):
        assert object.field == index
        object.field += 1


def test_changing_value_is_not_changing_the_default_value():
    class SomeClass(Storage):
        field = Field(42)

    object = SomeClass()

    assert object.field == 42

    object.field += 1

    assert object.field == 43

    assert SomeClass().field == 42


def test_try_to_delete_field():
    class SomeClass(Storage):
        field = Field(42)

    with pytest.raises(AttributeError, match=full_match("You can't delete the \"field\" attribute.")):
        del SomeClass().field


def test_try_to_set_new_value_to_read_only_attribute():
    class SomeClass(Storage):
        field = Field(42, read_only=True)

    object = SomeClass()

    with pytest.raises(AttributeError, match=full_match('Field "field" is read-only.')):
        object.field = 43

    assert object.field == 42


# TODO: test thread safety
