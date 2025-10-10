import sys

import pytest
from full_match import match
from locklib import LockTraceWrapper

from skelet import Storage, Field


def test_try_to_get_descriptor_object_from_class_inherited_from_storage():
    class SomeClass(Storage):
        field = Field(42)

    assert isinstance(SomeClass.field, Field)


def test_try_to_use_field_outside_storage():
    if sys.version_info < (3, 12):
        with pytest.raises(RuntimeError):
            class SomeClass:
                field = Field(42)
    else:
        with pytest.raises(TypeError):
            class SomeClass:
                field = Field(42)


def test_try_to_use_one_field_in_two_storage_classes():
    class FirstClass(Storage):
        field = Field(42)

    if sys.version_info < (3, 12):
        with pytest.raises(RuntimeError):
            class SecondClass(Storage):
                field = FirstClass.__dict__['field']

    else:
        with pytest.raises(TypeError):
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

    with pytest.raises(AttributeError, match=match("You can't delete the \"field\" attribute.")):
        del SomeClass().field


def test_try_to_set_new_value_to_read_only_attribute():
    class SomeClass(Storage):
        field = Field(42, read_only=True)

    object = SomeClass()

    with pytest.raises(AttributeError, match=match('Field "field" is read-only.')):
        object.field = 43

    assert object.field == 42


def test_all_storage_childs_have_their_own_lists_with_names():
    class FirstClass(Storage):
        field_1 = Field(42)
        field_2 = Field(43)
        field_3 = Field(44)

    class SecondClass(Storage):
        field_1 = Field(42)
        field_2 = Field(43)
        field_3 = Field(44)

    assert FirstClass.__field_names__ == ['field_1', 'field_2', 'field_3']
    assert SecondClass.__field_names__ == ['field_1', 'field_2', 'field_3']

    assert FirstClass.__field_names__ is not SecondClass.__field_names__

    assert FirstClass().field_1 == 42
    assert FirstClass().field_2 == 43
    assert FirstClass().field_3 == 44
    assert SecondClass().field_1 == 42
    assert SecondClass().field_2 == 43
    assert SecondClass().field_3 == 44


def test_inheritance_of_fields():
    class FirstClass(Storage):
        field_1 = Field(42)
        field_2 = Field(43)
        field_3 = Field(44)

    class SecondClass(FirstClass):
        ...

    assert FirstClass.__field_names__ == ['field_1', 'field_2', 'field_3']
    assert SecondClass.__field_names__ == FirstClass.__field_names__

    assert FirstClass().field_1 == 42
    assert FirstClass().field_2 == 43
    assert FirstClass().field_3 == 44
    assert SecondClass().field_1 == 42
    assert SecondClass().field_2 == 43
    assert SecondClass().field_3 == 44


def test_inheritance_of_fields_and_adding_new_fields():
    class FirstClass(Storage):
        field_1 = Field(42)
        field_2 = Field(43)
        field_3 = Field(44)

    class SecondClass(FirstClass):
        field_4 = Field(45)

    assert FirstClass.__field_names__ == ['field_1', 'field_2', 'field_3']
    assert SecondClass.__field_names__ == FirstClass.__field_names__ + ['field_4']

    assert FirstClass().field_1 == 42
    assert FirstClass().field_2 == 43
    assert FirstClass().field_3 == 44
    assert SecondClass().field_1 == 42
    assert SecondClass().field_2 == 43
    assert SecondClass().field_3 == 44
    assert SecondClass().field_4 == 45


def test_inheritance_of_fields_and_adding_new_fields_two_times():
    class FirstClass(Storage):
        field_1 = Field(42)
        field_2 = Field(43)
        field_3 = Field(44)

    class SecondClass(FirstClass):
        field_4 = Field(45)

    class ThirdClass(SecondClass):
        field_5 = Field(46)

    assert FirstClass.__field_names__ == ['field_1', 'field_2', 'field_3']
    assert SecondClass.__field_names__ == FirstClass.__field_names__ + ['field_4']
    assert ThirdClass.__field_names__ == SecondClass.__field_names__ + ['field_5']

    assert FirstClass().field_1 == 42
    assert FirstClass().field_2 == 43
    assert FirstClass().field_3 == 44
    assert SecondClass().field_1 == 42
    assert SecondClass().field_2 == 43
    assert SecondClass().field_3 == 44
    assert SecondClass().field_4 == 45
    assert ThirdClass().field_1 == 42
    assert ThirdClass().field_2 == 43
    assert ThirdClass().field_3 == 44
    assert ThirdClass().field_4 == 45
    assert ThirdClass().field_5 == 46


def test_redefine_field_in_child_class():
    class FirstClass(Storage):
        field = Field(42)

    class SecondClass(Storage):
        field = Field(43)

    assert FirstClass.__field_names__ == ['field']
    assert SecondClass.__field_names__ == ['field']

    assert FirstClass().field == 42
    assert SecondClass().field == 43


def test_redefine_field_in_child_class_and_change_value():
    class FirstClass(Storage):
        field = Field(42)

    class SecondClass(Storage):
        field = Field(43)

    assert FirstClass.__field_names__ == ['field']
    assert SecondClass.__field_names__ == ['field']

    first = FirstClass()
    second = SecondClass()

    assert first.field == 42
    assert second.field == 43

    first.field = 44

    assert first.field == 44
    assert second.field == 43

    second.field = 45

    assert first.field == 44
    assert second.field == 45


def test_storage_child_has_fields_list():
    class StorageChild(Storage):
        ...

    assert StorageChild.__field_names__ == []


def test_repr_without_fields():
    class StorageChild(Storage):
        ...

    assert repr(StorageChild()) == 'StorageChild()'


def test_repr_with_fields():
    class StorageChild(Storage):
        field_1 = Field(42)
        field_2 = Field(43)

    assert repr(StorageChild()) == 'StorageChild(field_1=42, field_2=43)'


def test_repr_with_fields_and_values():
    class StorageChild(Storage):
        field_1 = Field(42)
        field_2 = Field(43)

    assert repr(StorageChild()) == 'StorageChild(field_1=42, field_2=43)'
    assert repr(StorageChild(field_1=44, field_2=45)) == 'StorageChild(field_1=44, field_2=45)'


def test_set_some_values_in_init():
    class StorageChild(Storage):
        field_1 = Field(42)
        field_2 = Field(43)

    storage = StorageChild(field_1=44)

    assert storage.field_1 == 44
    assert storage.field_2 == 43

    assert repr(storage) == 'StorageChild(field_1=44, field_2=43)'


def test_try_to_set_not_defined_field_in_init():
    class StorageChild(Storage):
        field_1 = Field(42)
        field_2 = Field(43)

    with pytest.raises(KeyError, match=r'The "field_3" field is not defined.'):
        StorageChild(field_3=44)


def test_get_from_inner_dict_is_thread_safe_and_use_per_instance_locks():
    class SomeClass(Storage):
        field = Field(42)

    storage = SomeClass()
    field = SomeClass.field

    field.lock = LockTraceWrapper(field.lock)
    storage._lock = LockTraceWrapper(storage._lock)
    class PseudoDict:
        def get(self, key, default):
            storage._lock.notify('get')
            field.lock.notify('get')
            return 43
    storage.__fields__ = PseudoDict()

    assert storage.field == 43
    assert storage._lock.was_event_locked('get')

    assert not field.lock.was_event_locked('get') and field.lock.trace


def test_that_set_is_thread_safe_and_use_per_instance_locks():
    class SomeClass(Storage):
        field = Field(42)

    storage = SomeClass()
    field = SomeClass.field

    field.lock = LockTraceWrapper(field.lock)
    storage._lock = LockTraceWrapper(storage._lock)
    class PseudoDict:
        def __setitem__(self, key, default):
            storage._lock.notify('get')
            field.lock.notify('get')
    storage.__fields__ = PseudoDict()

    storage.field = 44

    assert storage._lock.was_event_locked('get')

    assert not field.lock.was_event_locked('get') and field.lock.trace


def test_set_name_uses_per_field_lock():
    class SomeClass(Storage):
        ...

    field = Field(42)
    field.lock = LockTraceWrapper(field.lock)

    field.set_field_names = lambda x, y: field.lock.notify('get')

    field.__set_name__(SomeClass, 'field')

    assert field.lock.was_event_locked('get') and field.lock.trace
