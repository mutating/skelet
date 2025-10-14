import sys
from typing import Any, Optional

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

    with pytest.raises(AttributeError, match=match('You can\'t delete the "field" field value.')):
        del SomeClass().field


def test_try_to_delete_field_with_doc():
    class SomeClass(Storage):
        field = Field(42, doc='some doc')

    with pytest.raises(AttributeError, match=match('You can\'t delete the "field" field (some doc) value.')):
        del SomeClass().field


def test_try_to_set_new_value_to_read_only_attribute():
    class SomeClass(Storage):
        field = Field(42, read_only=True)

    object = SomeClass()

    with pytest.raises(AttributeError, match=match('"field" field is read-only.')):
        object.field = 43

    assert object.field == 42


def test_try_to_set_new_value_to_read_only_attribute_with_doc():
    class SomeClass(Storage):
        field = Field(42, read_only=True, doc='some doc')

    object = SomeClass()

    with pytest.raises(AttributeError, match=match('"field" field (some doc) is read-only.')):
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


def test_simple_type_check_failed_when_set_bool_if_expected_int():
    class SomeClass(Storage):
        field: int = Field(15)

    instance = SomeClass()

    instance.field = True

    assert instance.field is True


def test_simple_type_check_failed_when_set():
    class SomeClass(Storage):
        field: int = Field(15)

    instance = SomeClass()

    with pytest.raises(TypeError, match=match('The value "15" (str) of the "field" field does not match the type int.')):
        instance.field = '15'

    with pytest.raises(TypeError, match=match('The value "15.0" (float) of the "field" field does not match the type int.')):
        instance.field = 15.0

    assert instance.field == 15
    assert type(instance.field) is int


def test_simple_type_check_failed_when_set_with_doc():
    class SomeClass(Storage):
        field: int = Field(15, doc='some doc')

    instance = SomeClass()

    with pytest.raises(TypeError, match=match('The value "15" (str) of the "field" field (some doc) does not match the type int.')):
        instance.field = '15'

    with pytest.raises(TypeError, match=match('The value "15.0" (float) of the "field" field (some doc) does not match the type int.')):
        instance.field = 15.0

    assert instance.field == 15
    assert type(instance.field) is int


def test_simple_type_check_not_failed_when_set():
    class SomeClass(Storage):
        field: int = Field(15)

    instance = SomeClass()

    instance.field = 16

    assert instance.field == 16
    assert type(instance.field) is int


def test_type_check_when_define_default_failed():
    if sys.version_info < (3, 12):
        with pytest.raises(RuntimeError):
            class SomeClass(Storage):
                field: int = Field('15')
    else:
        with pytest.raises(TypeError, match=match('The value "15" (str) of the "field" field does not match the type int.\nError calling __set_name__ on \'Field\' instance \'field\' in \'SomeClass\'')):
            class SomeClass(Storage):
                field: int = Field('15')


def test_type_check_when_define_default_failed_with_doc():
    if sys.version_info < (3, 12):
        with pytest.raises(RuntimeError):
            class SomeClass(Storage):
                field: int = Field('15', doc='some doc')
    else:
        with pytest.raises(TypeError, match=match('The value "15" (str) of the "field" field (some doc) does not match the type int.\nError calling __set_name__ on \'Field\' instance \'field\' in \'SomeClass\'')):
            class SomeClass(Storage):
                field: int = Field('15', doc='some doc')


def test_type_check_when_define_default_not_failed():
    class SomeClass(Storage):
        field: int = Field(15)

    assert SomeClass().field == 15
    assert type(SomeClass().field) is int


def test_type_check_when_redefine_defaults_initing_new_object_failed():
    class SomeClass(Storage):
        field: int = Field(15)

    with pytest.raises(TypeError, match=match('The value "kek" (str) of the "field" field does not match the type int.')):
        SomeClass(field='kek')


def test_type_check_when_redefine_defaults_initing_new_object_failed_with_doc():
    class SomeClass(Storage):
        field: int = Field(15, doc='some doc')

    with pytest.raises(TypeError, match=match('The value "kek" (str) of the "field" field (some doc) does not match the type int.')):
        SomeClass(field='kek')


def test_type_check_when_redefine_defaults_initing_new_object_not_failed():
    class SomeClass(Storage):
        field: int = Field(15)

    instance = SomeClass(field=16)

    assert instance.field == 16
    assert type(instance.field) is int

    instance = SomeClass(field=-100)

    assert instance.field == -100
    assert type(instance.field) is int


def test_more_examples_of_type_check_when_redefine_defaults_initing_new_object_failed():
    class SomeClass(Storage):
        field: Optional[int] = Field(15)

    if sys.version_info < (3, 10):
        with pytest.raises(AttributeError):
            SomeClass(field='kek')
    elif sys.version_info < (3, 14):
        with pytest.raises(TypeError, match=match('The value "kek" (str) of the "field" field does not match the type Optional.')):
            SomeClass(field='kek')
    else:
        with pytest.raises(TypeError, match=match('The value "kek" (str) of the "field" field does not match the type Union.')):
            SomeClass(field='kek')


    instance = SomeClass(field=None)

    assert instance.field is None

    instance = SomeClass(field=1000)

    assert instance.field == 1000

    class SecondClass(Storage):
        field: Any = Field(15)

    instance = SecondClass(field='kek')

    assert instance.field == 'kek'

    instance = SecondClass(field=None)

    assert instance.field is None

    instance = SecondClass(field=1000)

    assert instance.field == 1000


def test_more_examples_of_type_check_when_redefine_defaults_initing_new_object_failed_with_doc():
    class SomeClass(Storage):
        field: Optional[int] = Field(15, doc='some doc')

    if sys.version_info < (3, 10):
        with pytest.raises(AttributeError):
            SomeClass(field='kek')
    elif sys.version_info < (3, 14):
        with pytest.raises(TypeError, match=match('The value "kek" (str) of the "field" field (some doc) does not match the type Optional.')):
            SomeClass(field='kek')
    else:
        with pytest.raises(TypeError, match=match('The value "kek" (str) of the "field" field (some doc) does not match the type Union.')):
            SomeClass(field='kek')


def test_try_to_use_underscored_name_for_field():
    if sys.version_info < (3, 12):
        with pytest.raises(RuntimeError):
            class SomeClass(Storage):
                _field: int = Field(15)
    else:
        with pytest.raises(ValueError, match=match('Field name "_field" cannot start with an underscore.\nError calling __set_name__ on \'Field\' instance \'_field\' in \'SomeClass\'')):
            class SomeClass(Storage):
                _field: int = Field(15)


def test_try_to_use_underscored_name_for_field_with_doc():
    if sys.version_info < (3, 12):
        with pytest.raises(RuntimeError):
            class SomeClass(Storage):
                _field: int = Field(15, doc='some doc')
    else:
        with pytest.raises(ValueError, match=match('Field name "_field" cannot start with an underscore.\nError calling __set_name__ on \'Field\' instance \'_field\' in \'SomeClass\'')):
            class SomeClass(Storage):
                _field: int = Field(15, doc='some doc')


def test_validation_function_failed_when_set():
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match('The value "-1" (int) of the "field" field does not match the validation.')):
        instance.field = -1


def test_validation_function_failed_when_set_with_doc():
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, doc='some doc')

    instance = SomeClass()

    with pytest.raises(ValueError, match=match('The value "-1" (int) of the "field" field (some doc) does not match the validation.')):
        instance.field = -1


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_validation_functions_dict_failed_when_set(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation={'some message': lambda x: x > 0}, **addictional_parameters)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match('some message')):
        instance.field = -1


def test_validation_function_not_failed_when_set():
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0)

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1


def test_validation_functions_dict_not_failed_when_set():
    class SomeClass(Storage):
        field: int = Field(15, validation={'some message': lambda value: value > 0})

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1


def test_validation_function_failed_when_init():
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0)

    with pytest.raises(ValueError, match=match('The value "-1" (int) of the "field" field does not match the validation.')):
        SomeClass(field=-1)


def test_validation_function_failed_when_init_with_doc():
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, doc='some doc')

    with pytest.raises(ValueError, match=match('The value "-1" (int) of the "field" field (some doc) does not match the validation.')):
        SomeClass(field=-1)


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_validation_functions_dict_failed_when_init(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation={'some message': lambda value: value > 0}, **addictional_parameters)

    with pytest.raises(ValueError, match=match('some message')):
        SomeClass(field=-1)


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_validation_function_not_failed_when_init(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, **addictional_parameters)

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_validation_functions_dict_not_failed_when_init(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation={'some message': lambda value: value > 0}, **addictional_parameters)

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1
