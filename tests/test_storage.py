import sys
from typing import List, Any, Union, Optional

import pytest
from full_match import match
from locklib import LockTraceWrapper

from skelet import Storage, Field, TOMLSource, JSONSource, YAMLSource, EnvSource, MemorySource, NaturalNumber, NonNegativeInt


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


def test_get_from_inner_dict_is_thread_safe_and_use_per_fields_locks():
    class SomeClass(Storage):
        field = Field(42)

    storage = SomeClass()
    field = SomeClass.field

    field.lock = LockTraceWrapper(field.lock)
    storage.__locks__['field'] = LockTraceWrapper(storage.__locks__['field'])
    class PseudoDict:
        def get(self, key):
            storage.__locks__['field']
            field.lock.notify('get')
            return 43
    storage.__values__ = PseudoDict()

    assert storage.field == 43
    assert storage.__locks__['field'].was_event_locked('get')

    assert not field.lock.was_event_locked('get') and field.lock.trace


def test_that_set_is_thread_safe_and_use_per_field_locks():
    class SomeClass(Storage):
        field = Field(42)

    storage = SomeClass()
    field = SomeClass.field

    field.lock = LockTraceWrapper(field.lock)
    storage.__locks__['field'] = LockTraceWrapper(storage.__locks__['field'])
    class PseudoDict:
        def __setitem__(self, key, default):
            storage.__locks__['field'].notify('set')
            field.lock.notify('set')

        def get(self, key):
            storage.__locks__['field'].notify('get')
            field.lock.notify('get')
            return 42

    storage.__values__ = PseudoDict()

    storage.field = 44

    assert storage.__locks__['field'].was_event_locked('set')
    assert storage.__locks__['field'].was_event_locked('get')

    assert not field.lock.was_event_locked('set') and field.lock.trace
    assert not field.lock.was_event_locked('get') and field.lock.trace


def test_set_name_uses_per_field_object_lock():
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


@pytest.mark.parametrize(
    ['int_value', 'float_value', 'secret'],
    [
        ('***', '***', True),
        ("'15'", '15.0', False),
    ],
)
def test_simple_type_check_failed_when_set(int_value, float_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, secret=secret)

    instance = SomeClass()

    with pytest.raises(TypeError, match=match(f'The value {int_value} (str) of the "field" field does not match the type int.')):
        instance.field = '15'

    with pytest.raises(TypeError, match=match(f'The value {float_value} (float) of the "field" field does not match the type int.')):
        instance.field = 15.0

    assert instance.field == 15
    assert type(instance.field) is int


@pytest.mark.parametrize(
    ['int_value', 'float_value', 'secret'],
    [
        ('***', '***', True),
        ("'15'", "15.0", False),
    ],
)
def test_simple_type_check_failed_when_set_with_doc(int_value, float_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, doc='some doc', secret=secret)

    instance = SomeClass()

    with pytest.raises(TypeError, match=match(f'The value {int_value} (str) of the "field" field (some doc) does not match the type int.')):
        instance.field = '15'

    with pytest.raises(TypeError, match=match(f'The value {float_value} (float) of the "field" field (some doc) does not match the type int.')):
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


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ("'15'", False),
    ],
)
def test_type_check_when_define_default_failed(wrong_value, secret):
    with pytest.raises(TypeError, match=match(f'The value {wrong_value} (str) of the "field" field does not match the type int.')):
        class SomeClass(Storage):
            field: int = Field('15', secret=secret)


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ("'15'", False),
    ],
)
def test_type_check_when_define_default_failed_with_doc(wrong_value, secret):
    with pytest.raises(TypeError, match=match(f'The value {wrong_value} (str) of the "field" field (some doc) does not match the type int.')):
        class SomeClass(Storage):
            field: int = Field('15', doc='some doc', secret=secret)


def test_type_check_when_define_default_not_failed():
    class SomeClass(Storage):
        field: int = Field(15)

    assert SomeClass().field == 15
    assert type(SomeClass().field) is int


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ("'kek'", False),
    ],
)
def test_type_check_when_redefine_defaults_initing_new_object_failed(wrong_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, secret=secret)

    with pytest.raises(TypeError, match=match(f'The value {wrong_value} (str) of the "field" field does not match the type int.')):
        SomeClass(field='kek')


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ("'kek'", False),
    ],
)
def test_type_check_when_redefine_defaults_initing_new_object_failed_with_doc(wrong_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, doc='some doc', secret=secret)

    with pytest.raises(TypeError, match=match(f'The value {wrong_value} (str) of the "field" field (some doc) does not match the type int.')):
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


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ("'kek'", False),
    ],
)
def test_more_examples_of_type_check_when_redefine_defaults_initing_new_object_failed(wrong_value, secret):
    class SomeClass(Storage):
        field: Optional[int] = Field(15, secret=secret)

    if sys.version_info < (3, 10):
        type_representation = 'typing.Union'
    else:
        type_representation = 'Union'

    with pytest.raises(TypeError, match=match(f'The value {wrong_value} (str) of the "field" field does not match the type {type_representation}.')):
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


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ("'kek'", False),
    ],
)
def test_more_examples_of_type_check_when_redefine_defaults_initing_new_object_failed_with_doc(wrong_value, secret):
    class SomeClass(Storage):
        field: Optional[int] = Field(15, doc='some doc', secret=secret)

    if sys.version_info < (3, 10):
        type_representation = 'typing.Union'
    else:
        type_representation = 'Union'

    with pytest.raises(TypeError, match=match(f'The value {wrong_value} (str) of the "field" field (some doc) does not match the type {type_representation}.')):
        SomeClass(field='kek')


def test_try_to_use_underscored_name_for_field():
    with pytest.raises(ValueError, match=match('Field name "_field" cannot start with an underscore.')):
        class SomeClass(Storage):
            _field: int = Field(15)


def test_try_to_use_underscored_name_for_field_with_doc():
    with pytest.raises(ValueError, match=match('Field name "_field" cannot start with an underscore.')):
        class SomeClass(Storage):
            _field: int = Field(15, doc='some doc')


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ('-1', False),
    ],
)
def test_validation_function_failed_when_set(wrong_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, secret=secret)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field does not match the validation.')):
        instance.field = -1


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ('-1', False),
    ],
)
def test_validation_function_failed_when_set_with_doc(wrong_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, doc='some doc', secret=secret)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field (some doc) does not match the validation.')):
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


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ('-1', False),
    ],
)
def test_validation_function_failed_when_init(wrong_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, secret=secret)

    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field does not match the validation.')):
        SomeClass(field=-1)


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ('-1', False),
    ],
)
def test_validation_function_failed_when_init_with_doc(wrong_value, secret):
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, doc='some doc', secret=secret)

    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field (some doc) does not match the validation.')):
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


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ('-15', False),
    ],
)
def test_validation_function_failed_when_default(wrong_value, secret):
    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field does not match the validation.')):
        class SomeClass(Storage):
            field: int = Field(-15, validation=lambda value: value > 0, secret=secret)


@pytest.mark.parametrize(
    ['wrong_value', 'secret'],
    [
        ('***', True),
        ('-15', False),
    ],
)
def test_validation_function_failed_when_default_with_doc(wrong_value, secret):
    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field (some doc) does not match the validation.')):
        class SomeClass(Storage):
            field: int = Field(-15, validation=lambda value: value > 0, doc='some doc', secret=secret)


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_validation_function_not_failed_when_default_because_no_check_first_time(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(-15, validation=lambda value: value > 0, validate_default=False, **addictional_parameters)

    assert SomeClass().field == -15


def test_validation_when_set_is_not_under_lock():
    class SomeClass(Storage):
        field: int = Field(10, validation=lambda value: value > 0)

    instance = SomeClass()

    instance.__locks__['field'] = LockTraceWrapper(instance.__locks__['field'])
    SomeClass.field.validation = lambda x: instance.__locks__['field'].notify('kek') is None
    instance.field = 5

    assert instance.field == 5

    assert not instance.__locks__['field'].was_event_locked('kek')


def test_type_check_when_set_is_not_under_lock():
    class SomeClass(Storage):
        field: int = Field(10, validation=lambda value: value > 0)

    instance = SomeClass()

    instance.__locks__['field'] = LockTraceWrapper(instance.__locks__['field'])
    SomeClass.field.check_type_hints = lambda x, y, z, raise_all: instance.__locks__['field'].notify('kek')
    instance.field = 5

    assert instance.field == 5

    assert not instance.__locks__['field'].was_event_locked('kek')


def test_type_check_when_set_is_before_validation():
    flags = []
    start_check = False

    def validation(value):
        nonlocal flags
        if start_check:
            flags.append('validation')

        return isinstance(value, int)

    class SomeClass(Storage):
        field: int = Field(10, validation=validation)

    instance = SomeClass()

    old_check_type_hints = SomeClass.field.check_type_hints
    SomeClass.field.check_type_hints = lambda x, y, z, raise_all: flags.append('type_check') is old_check_type_hints(x, y, z, raise_all=raise_all)
    start_check = True

    with pytest.raises(TypeError):
        instance.field = 'kek'

    assert instance.field == 10
    assert flags == ['type_check']

    SomeClass.field.check_type_hints = old_check_type_hints


def test_repr_for_secret_fields():
    class SomeClass(Storage):
        field: int = Field(10, secret=True)
        second_field: int = Field(100)

    instance = SomeClass()

    assert repr(instance) == 'SomeClass(field=***, second_field=100)'

    instance.field = instance.field * 2
    instance.second_field = instance.second_field * 2

    assert repr(instance) == 'SomeClass(field=***, second_field=200)'


def test_change_value_of_secret_field():
    class SomeClass(Storage):
        field: int = Field(10, secret=True)

    instance = SomeClass()

    assert instance.field == 10

    instance.field = 20

    assert instance.field == 20


def test_change_value_of_secret_field_in_init():
    class SomeClass(Storage):
        field: int = Field(10, secret=True)

    instance = SomeClass(field=20)

    assert instance.field == 20


def test_set_action_for_set():
    flags = []

    class SomeClass(Storage):
        field: int = Field(10, secret=True, change_action=lambda old, new, storage: flags.append(True))

    instance = SomeClass()

    assert not flags

    instance.field = 13

    assert flags == [True]

    instance.field = 14

    assert flags == [True, True]


def test_action_doesnt_work_when_new_value_is_same():
    flags = []

    class SomeClass(Storage):
        field: int = Field(10, secret=True, change_action=lambda old, new, storage: flags.append(True))

    instance = SomeClass()

    assert not flags

    instance.field = 10

    assert not flags
    assert instance.field == 10


@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({'read_lock': True},),
    ],
)
def test_read_lock_on(addictional_arguments):
    class SomeClass(Storage):
        field: int = Field(10, secret=True, **addictional_arguments)

    instance = SomeClass()

    lock = LockTraceWrapper(instance.__locks__['field'])
    instance.__locks__['field'] = lock
    field = SomeClass.field
    field.lock = LockTraceWrapper(field.lock)

    class PseudoDict:
        def get(self, key):
            lock.notify('get')
            field.lock.notify('get')
            return 10

    instance.__values__ = PseudoDict()

    assert not lock.trace
    assert not field.lock.trace

    assert instance.field == 10

    assert lock.trace
    assert field.lock.trace

    assert lock.was_event_locked('get')
    assert not field.lock.was_event_locked('get')


def test_read_lock_off():
    class SomeClass(Storage):
        field: int = Field(10, secret=True, read_lock=False)

    instance = SomeClass()

    lock = LockTraceWrapper(instance.__locks__['field'])
    instance.__locks__['field'] = lock
    field = SomeClass.field
    field.lock = LockTraceWrapper(field.lock)

    class PseudoDict:
        def get(self, key):
            lock.notify('get')
            field.lock.notify('get')
            return 10

    instance.__values__ = PseudoDict()

    assert not lock.trace
    assert not field.lock.trace

    assert instance.field == 10

    assert lock.trace
    assert field.lock.trace

    assert not lock.was_event_locked('get')
    assert not field.lock.was_event_locked('get')


def test_two_storage_instances_by_default_have_not_the_same_locks():
    class SomeClass(Storage):
        field: int = Field(10)
        other_field: int = Field(20)

    instance = SomeClass()
    second_instance = SomeClass()

    assert instance.__locks__ is not second_instance.__locks__

    assert instance.__locks__['field'] is not instance.__locks__['other_field']
    assert second_instance.__locks__['field'] is not second_instance.__locks__['other_field']

    assert second_instance.__locks__['field'] is not instance.__locks__['field']
    assert second_instance.__locks__['other_field'] is not instance.__locks__['other_field']


def test_storage_is_not_singleton():
    class SomeClass(Storage):
        field: int = Field(10)

    instance = SomeClass()
    second_instance = SomeClass()

    assert instance is not second_instance


def test_conflicting_fields_have_the_same_lock():
    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old})
        other_field: int = Field(20)
        second_other_field: int = Field(25)

    instance = SomeClass()

    assert instance.__locks__['field'] is instance.__locks__['other_field']
    assert instance.__locks__['field'] is not instance.__locks__['second_other_field']


def test_conflicts_check_is_under_field_lock():
    locks: List[LockTraceWrapper] = []

    def check_function(old, new, other_old, other_new):
        for lock in locks:
            lock.notify('check')
        return False

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': check_function})
        other_field: int = Field(20)

    instance = SomeClass()

    lock = LockTraceWrapper(instance.__locks__['field'])
    locks.append(lock)
    instance.__locks__['field'] = lock

    instance.field = 20

    assert lock.trace
    assert lock.was_event_locked('check')


def test_reverse_conflicts_check_is_under_field_lock():
    locks: List[LockTraceWrapper] = []

    def check_function(old, new, other_old, other_new):
        for lock in locks:
            lock.notify('check')
        return False

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': check_function})
        other_field: int = Field(20)

    instance = SomeClass()

    assert instance.__locks__['field'] is instance.__locks__['other_field']

    lock = LockTraceWrapper(instance.__locks__['other_field'])
    locks.append(lock)
    instance.__locks__['other_field'] = lock

    instance.other_field = 25

    assert lock.trace
    assert lock.was_event_locked('check')


@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_non_existing_conflicting_field_name(addictional_arguments):
    if not addictional_arguments:
        exception_message = 'You have set a conflict condition for "field" field with field "ather_field", but the field "ather_field" does not exist in the class SomeClass.'
    else:
        exception_message = f'You have set a conflict condition for "field" field ({addictional_arguments["doc"]}) with field "ather_field", but the field "ather_field" does not exist in the class SomeClass.'

    with pytest.raises(NameError, match=match(exception_message)):
        class SomeClass(Storage):
            field: int = Field(10, conflicts={'ather_field': lambda old, new, other: new > other}, **addictional_arguments)
            other_field: int = Field(20)


# Check: reverse check
# Check: exceptions messages for both types of fields on the both sides, direct and reverse

@pytest.mark.parametrize(
    ['main_field_is_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_basic_conflicting_fields(addictional_arguments, main_field_is_secret):
    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'secret_other_field': lambda old, new, other_old, other_new: new < 0}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret)
        other_field: int = Field(20, doc=addictional_arguments.get('doc'))
        secret_other_field: int = Field(20, secret=True, doc=addictional_arguments.get('doc'))

    instance = SomeClass()

    assert instance.field == 10

    instance.field = 15

    assert instance.field == 15

    if 'doc' in addictional_arguments:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field (some doc) conflicts with the 20 (int) value of the "other_field" field (some doc).'
        else:
            exception_message = 'The new 21 (int) value of the "field" field (some doc) conflicts with the 20 (int) value of the "other_field" field (some doc).'
    else:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field conflicts with the 20 (int) value of the "other_field" field.'
        else:
            exception_message = 'The new 21 (int) value of the "field" field conflicts with the 20 (int) value of the "other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        instance.field = 21

    assert instance.field == 15

    if 'doc' in addictional_arguments:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field (some doc) conflicts with the *** (int) value of the "secret_other_field" field (some doc).'
        else:
            exception_message = 'The new -1 (int) value of the "field" field (some doc) conflicts with the *** (int) value of the "secret_other_field" field (some doc).'
    else:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'
        else:
            exception_message = 'The new -1 (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        instance.field = -1

    assert instance.field == 15


@pytest.mark.parametrize(
    ['main_field_is_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_conflicting_fields_when_set_in_init(addictional_arguments, main_field_is_secret):
    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'secret_other_field': lambda old, new, other_old, other_new: new < 0}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret)
        other_field: int = Field(20, doc=addictional_arguments.get('doc'))
        secret_other_field: int = Field(20, secret=True, doc=addictional_arguments.get('doc'))

    instance = SomeClass()

    assert instance.field == 10

    instance = SomeClass(field=15)

    assert instance.field == 15

    if 'doc' in addictional_arguments:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field (some doc) conflicts with the 20 (int) value of the "other_field" field (some doc).'
        else:
            exception_message = 'The new 21 (int) value of the "field" field (some doc) conflicts with the 20 (int) value of the "other_field" field (some doc).'
    else:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field conflicts with the 20 (int) value of the "other_field" field.'
        else:
            exception_message = 'The new 21 (int) value of the "field" field conflicts with the 20 (int) value of the "other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        SomeClass(field=21)

    if 'doc' in addictional_arguments:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field (some doc) conflicts with the *** (int) value of the "secret_other_field" field (some doc).'
        else:
            exception_message = 'The new -1 (int) value of the "field" field (some doc) conflicts with the *** (int) value of the "secret_other_field" field (some doc).'
    else:
        if main_field_is_secret:
            exception_message = 'The new *** (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'
        else:
            exception_message = 'The new -1 (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        SomeClass(field=-1)


@pytest.mark.parametrize(
    ['are_fields_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_conflicting_fields_when_defaults_are_conflicting(addictional_arguments, are_fields_secret):
    if 'doc' in addictional_arguments:
        if are_fields_secret:
            exception_message = 'The *** (int) default value of the "field" field (some doc) conflicts with the *** (int) value of the "other_field" field (some doc).'
        else:
            exception_message = 'The 21 (int) default value of the "field" field (some doc) conflicts with the 20 (int) value of the "other_field" field (some doc).'
    else:
        if are_fields_secret:
            exception_message = 'The *** (int) default value of the "field" field conflicts with the *** (int) value of the "other_field" field.'
        else:
            exception_message = 'The 21 (int) default value of the "field" field conflicts with the 20 (int) value of the "other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        class SomeClass(Storage):
            field: int = Field(21, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'secret_other_field': lambda old, new, other_old, other_new: new > 30}, doc=addictional_arguments.get('doc'), secret=are_fields_secret)
            other_field: int = Field(20, doc=addictional_arguments.get('doc'), secret=are_fields_secret)


@pytest.mark.parametrize(
    ['are_fields_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
        ({'reverse_conflicts': True},),
        ({'reverse_conflicts': True, 'doc': 'some doc'},),
    ],
)
def test_basic_conflicting_fields_reverse_when_its_on(addictional_arguments, are_fields_secret):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments)
        other_field: int = Field(20, doc=doc, secret=are_fields_secret, **addictional_arguments)

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_field == 20

    instance.other_field = 30

    assert instance.other_field == 30

    if doc is not None:
        if are_fields_secret:
            exception_message = 'The new *** (int) value of the "other_field" field (some doc) conflicts with the *** (int) value of the "field" field (some doc).'
        else:
            exception_message = 'The new 5 (int) value of the "other_field" field (some doc) conflicts with the 10 (int) value of the "field" field (some doc).'
    else:
        if are_fields_secret:
            exception_message = 'The new *** (int) value of the "other_field" field conflicts with the *** (int) value of the "field" field.'
        else:
            exception_message = 'The new 5 (int) value of the "other_field" field conflicts with the 10 (int) value of the "field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        instance.other_field = 5

    assert instance.other_field == 30
    assert instance.field == 10


@pytest.mark.parametrize(
    ['are_fields_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
        ({'reverse_conflicts': True},),
        ({'reverse_conflicts': True, 'doc': 'some doc'},),
    ],
)
def test_conflicting_fields_reverse_when_its_on_and_when_set_in_init(addictional_arguments, are_fields_secret):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments)
        other_field: int = Field(20, doc=doc, secret=are_fields_secret, **addictional_arguments)

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_field == 20

    instance = SomeClass(other_field=30)

    assert instance.other_field == 30

    if doc is not None:
        if are_fields_secret:
            exception_message = 'The new *** (int) value of the "other_field" field (some doc) conflicts with the *** (int) value of the "field" field (some doc).'
        else:
            exception_message = 'The new 5 (int) value of the "other_field" field (some doc) conflicts with the 10 (int) value of the "field" field (some doc).'
    else:
        if are_fields_secret:
            exception_message = 'The new *** (int) value of the "other_field" field conflicts with the *** (int) value of the "field" field.'
        else:
            exception_message = 'The new 5 (int) value of the "other_field" field conflicts with the 10 (int) value of the "field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        SomeClass(other_field=5)


@pytest.mark.parametrize(
    ['reverse_check_parameters'],
    [
        ({'class': False, 'field': True},),
        ({'class': True, 'field': False},),
        ({'class': False, 'field': False},),
    ],
)
@pytest.mark.parametrize(
    ['are_fields_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_basic_conflicting_fields_reverse_when_its_off(addictional_arguments, are_fields_secret, reverse_check_parameters):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments, reverse_conflicts=reverse_check_parameters['field'])
        other_field: int = Field(20, doc=doc, secret=are_fields_secret, **addictional_arguments)

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_field == 20

    instance.other_field = 30

    assert instance.other_field == 30

    instance.other_field = 5

    assert instance.other_field == 5
    assert instance.field == 10


@pytest.mark.parametrize(
    ['reverse_check_parameters'],
    [
        ({'class': False, 'field': True},),
        ({'class': True, 'field': False},),
        ({'class': False, 'field': False},),
    ],
)
@pytest.mark.parametrize(
    ['are_fields_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
def test_conflicting_fields_reverse_when_its_off_and_when_set_in_init(addictional_arguments, are_fields_secret, reverse_check_parameters):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments, reverse_conflicts=reverse_check_parameters['field'])
        other_field: int = Field(20, doc=doc, secret=are_fields_secret, **addictional_arguments)

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_field == 20

    instance = SomeClass(other_field=30)

    assert instance.other_field == 30

    instance = SomeClass(other_field=5)

    assert instance.other_field == 5
    assert instance.field == 10


@pytest.mark.parametrize(
    ['main_field_is_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
@pytest.mark.parametrize(
    ['reverse_check_parameters'],
    [
        ({'class': False, 'field': True},),
        ({'class': True, 'field': False},),
        ({'class': False, 'field': False},),
    ],
)
def test_conflicting_fields_when_reverse_check_off(addictional_arguments, main_field_is_secret, reverse_check_parameters):
    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret, reverse_conflicts=reverse_check_parameters['field'])
        other_field: int = Field(20, doc=addictional_arguments.get('doc'))

    instance = SomeClass()

    assert instance.field == 10

    instance.other_field = 5

    assert instance.other_field == 5


@pytest.mark.parametrize(
    ['main_field_is_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
@pytest.mark.parametrize(
    ['reverse_check_parameters'],
    [
        ({'class': False, 'field': True},),
        ({'class': True, 'field': False},),
        ({'class': False, 'field': False},),
    ],
)
def test_conflicting_fields_in_init_when_reverse_check_off(addictional_arguments, main_field_is_secret, reverse_check_parameters):
    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret, reverse_conflicts=reverse_check_parameters['field'])
        other_field: int = Field(20, doc=addictional_arguments.get('doc'))

    instance = SomeClass(other_field=5)

    assert instance.field == 10
    assert instance.other_field == 5


@pytest.mark.parametrize(
    ['main_field_is_secret'],
    [
        (True,),
        (False,),
    ],
)
@pytest.mark.parametrize(
    ['addictional_arguments'],
    [
        ({},),
        ({'doc': 'some doc'},),
    ],
)
@pytest.mark.parametrize(
    ['reverse_check_parameters'],
    [
        ({'class': False, 'field': True},),
        ({'class': True, 'field': False},),
        ({'class': False, 'field': False},),
    ],
)
def test_conflicting_fields_in_defaults_when_reverse_check_off(addictional_arguments, main_field_is_secret, reverse_check_parameters):
    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret, reverse_conflicts=reverse_check_parameters['field'])
        other_field: int = Field(5, doc=addictional_arguments.get('doc'))

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_field == 5


def test_variables_order_when_conflicts_checking():
    breadcrumbs = []

    def check_conflicts(old, new, other_old, other_new):
        breadcrumbs.append((old, new, other_old, other_new))
        return old > other_new

    class SomeClass(Storage):
        field: int = Field(5, conflicts={'other_field': check_conflicts})
        other_field: int = Field(10)

    assert len(breadcrumbs) == 1
    assert breadcrumbs[0] == (5, 5, 10, 10)

    instance = SomeClass()

    assert len(breadcrumbs) == 1

    instance.field = 5

    assert len(breadcrumbs) == 2
    assert breadcrumbs[1] == (5, 5, 10, 10)

    instance.field = 6

    assert len(breadcrumbs) == 3
    assert breadcrumbs[2] == (5, 6, 10, 10)

    instance.other_field = 11

    assert len(breadcrumbs) == 4
    assert breadcrumbs[3] == (6, 6, 10, 11)

    instance.other_field = 11

    assert len(breadcrumbs) == 5
    assert breadcrumbs[4] == (6, 6, 11, 11)


def test_there_is_no_dunder_starting_fields_except_user_ones():
    class EmptyClass(Storage):
        ...

    for field_name in dir(EmptyClass()):
        assert field_name.startswith('_')

    class NotEmptyClass(Storage):
        field = Field(5)
        other_field = Field(10)

    for field_name in dir(NotEmptyClass()):
        if field_name not in ('field', 'other_field'):
            assert field_name.startswith('_')


def test_reverse_fields_container_in_basic_case():
    class SomeClass(Storage):
        field: int = Field(5, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new})
        other_field: int = Field(10)

    assert SomeClass.__reverse_conflicts__ == {'other_field': ['field']}
    assert SomeClass.__field_names__ == ['field', 'other_field']


def test_reverse_fields_container_in_case_of_inheritance_with_new_field():
    class SomeClass(Storage):
        field: int = Field(5, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new})
        other_field: int = Field(10)

    class SomeOtherClass(SomeClass):
        third_field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > 1000})

    assert SomeClass.__reverse_conflicts__ == {'other_field': ['field']}
    assert SomeOtherClass.__reverse_conflicts__ == {'other_field': ['field', 'third_field']}

    assert SomeClass.__field_names__ == ['field', 'other_field']
    assert SomeOtherClass.__field_names__ == ['field', 'other_field', 'third_field']


def test_reverse_fields_container_in_case_of_inheritance_with_same_field():
    class SomeClass(Storage):
        field: int = Field(5, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new})
        other_field: int = Field(10)

    class SomeOtherClass(SomeClass):
        other_field: int = Field(10, conflicts={'field': lambda old, new, other_old, other_new: old > 1000})

    assert SomeClass.__reverse_conflicts__ == {'other_field': ['field']}
    assert SomeOtherClass.__reverse_conflicts__ == {'other_field': ['field'], 'field': ['other_field']}

    assert SomeClass.__field_names__ == ['field', 'other_field']
    assert SomeOtherClass.__field_names__ == ['field', 'other_field']


@pytest.mark.parametrize(
    ['sources'],
    [
        ([],),
        ([MemorySource({})],),
    ],
)
def test_empty_set_of_sources(sources):
    class SomeClass(Storage, sources=sources):
        field: int = Field(5)
        other_field: int = Field(10)

    instance = SomeClass()

    assert instance.field == 5
    assert instance.other_field == 10


def test_reset_value_using_source():
    class SomeClass(Storage, sources=[MemorySource({'field': 15})]):
        field: int = Field(5)
        other_field: int = Field(10)

    instance = SomeClass()

    assert instance.field == 15
    assert instance.other_field == 10

    instance.field = 7

    assert instance.field == 7


def test_order_of_sources():
    class SomeClass(Storage, sources=[MemorySource({'field': 15}), MemorySource({'field': 23})]):
        field: int = Field(5)
        other_field: int = Field(10)

    instance = SomeClass()

    assert instance.field == 15
    assert instance.other_field == 10

    instance.field = 7

    assert instance.field == 7


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 1,
            'other_field': 14,
        },),
    ],
)
def test_load_from_toml(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: int = Field(5)
        other_field: int = Field(10)

    instance = SomeClass()

    assert instance.field == 1
    assert instance.other_field == 14

    instance.field = 7

    assert instance.field == 7
    assert instance.other_field == 14


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 1,
            'other_field': 14,
        },),
    ],
)
def test_load_from_yaml(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: int = Field(5)
        other_field: int = Field(10)

    instance = SomeClass()

    assert instance.field == 1
    assert instance.other_field == 14

    instance.field = 7

    assert instance.field == 7
    assert instance.other_field == 14


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 1,
            'other_field': 14,
        },),
    ],
)
def test_load_from_json(json_config_path):
    class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
        field: int = Field(5)
        other_field: int = Field(10)

    instance = SomeClass()

    assert instance.field == 1
    assert instance.other_field == 14

    instance.field = 7

    assert instance.field == 7
    assert instance.other_field == 14


def test_source_checking_is_under_field_lock_when_its_on():
    locks: List[LockTraceWrapper] = []

    class PseudoDict:
        def __getitem__(self, key: str) -> Any:
            for lock in locks:
                lock.notify('get')
            return 1

    class SomeClass(Storage, sources=[MemorySource(PseudoDict())]):
        field: int = Field(10, read_lock=True)
        other_field: int = Field(20)

    instance = SomeClass()

    lock = LockTraceWrapper(instance.__locks__['field'])
    locks.append(lock)
    instance.__locks__['field'] = lock

    assert instance.field == 1

    assert lock.trace
    assert lock.was_event_locked('get')


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': '1',
        },),
    ],
)
def test_read_bad_typed_value_from_toml_source_for_not_deferred_value(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: int = Field(5)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': '1',
        },),
    ],
)
def test_read_bad_typed_value_from_yaml_source_for_not_deferred_value(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: int = Field(5)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': '1',
        },),
    ],
)
def test_read_bad_typed_value_from_json_source_for_not_deferred_value(json_config_path):
    class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
        field: int = Field(5)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': [14],
        },),
    ],
)
def test_read_bad_typed_value_from_toml_source_for_deferred_value(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: List[str] = Field(default_factory=list)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': [14],
        },),
    ],
)
def test_read_bad_typed_value_from_yaml_source_for_deferred_value(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: List[str] = Field(default_factory=list)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': [14],
        },),
    ],
)
def test_read_bad_typed_value_from_json_source_for_deferred_value(json_config_path):
    class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
        field: List[str] = Field(default_factory=list)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


def test_type_check_with_supertypes():
    class SomeClass(Storage):
        field: NaturalNumber = Field(5)
        other_field: NonNegativeInt = Field(11)

    instance = SomeClass()

    instance.field = 1
    assert instance.field == 1

    instance.field = 1000
    assert instance.field == 1000

    with pytest.raises(TypeError, match=match('The value 0 (int) of the "field" field does not match the type NaturalNumber.')):
        instance.field = 0

    with pytest.raises(TypeError, match=match('The value -1 (int) of the "field" field does not match the type NaturalNumber.')):
        instance.field = -1

    with pytest.raises(TypeError, match=match('The value \'kek\' (str) of the "field" field does not match the type NaturalNumber.')):
        instance.field = 'kek'

    assert instance.field == 1000

    instance.other_field = 1000
    assert instance.other_field == 1000

    instance.other_field = 0
    assert instance.other_field == 0

    with pytest.raises(TypeError, match=match('The value -1 (int) of the "other_field" field does not match the type NonNegativeInt.')):
        instance.other_field = -1

    with pytest.raises(TypeError, match=match('The value \'kek\' (str) of the "other_field" field does not match the type NonNegativeInt.')):
        instance.other_field = 'kek'


def test_wrong_defaults():
    with pytest.raises(ValueError, match=match('You can define a default value or a factory for default values, but not all at the same time.')):
        class SomeClass(Storage):
            field: List[str] = Field([], default_factory=list)


def test_default_value_from_factory():
    class SomeClass(Storage):
        field: List[str] = Field(default_factory=list)

    instance_1 = SomeClass()

    assert instance_1.field == []

    this_field = instance_1.field
    assert instance_1.field is this_field

    instance_2 = SomeClass()

    assert instance_2.field == []

    assert instance_1.field is not instance_2.field

    instance_1.field.append('kek')

    assert instance_1.field == ['kek']
    assert instance_2.field == []

    instance_1.field.append('lol')

    assert instance_1.field == ['kek', 'lol']
    assert instance_2.field == []


def test_type_check_for_default_factory():
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 'kek')

    with pytest.raises(TypeError, match=match('The value \'kek\' (str) of the "field" field does not match the type int.')):
        SomeClass()


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'validate_default': True},),
    ],
)
def test_validate_default_factory_value_fith_function_when_its_on_and_validation_not_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation=lambda x: x != 'kek', **addictional_parameters)

    with pytest.raises(ValueError, match=match('The value \'kek\' (str) of the "field" field does not match the validation.')):
        SomeClass()


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'validate_default': True},),
    ],
)
def test_validate_default_factory_value_fith_function_when_its_on_and_validation_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation=lambda x: x == 'kek', **addictional_parameters)

    instance = SomeClass()

    assert instance.field == 'kek'


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'validate_default': True},),
    ],
)
def test_validate_default_factory_value_fith_dict_when_its_on_and_validation_not_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation={'some message': lambda x: x != 'kek'}, **addictional_parameters)

    with pytest.raises(ValueError, match=match('some message')):
        SomeClass()


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'validate_default': True},),
    ],
)
def test_validate_default_factory_value_fith_dict_when_its_on_and_validation_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation={'some message': lambda x: x == 'kek'}, **addictional_parameters)

    instance = SomeClass()

    assert instance.field == 'kek'


def test_validate_default_factory_value_fith_function_when_its_off_and_validation_not_passed():
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation=lambda x: x != 'kek', validate_default=False)

    instance = SomeClass()

    assert instance.field == 'kek'


def test_validate_default_factory_value_fith_function_when_its_off_and_validation_passed():
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation=lambda x: x == 'kek', validate_default=False)

    instance = SomeClass()

    assert instance.field == 'kek'


def test_validate_default_factory_value_fith_dict_when_its_off_and_validation_not_passed():
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation={'some message': lambda x: x != 'kek'}, validate_default=False)

    instance = SomeClass()

    assert instance.field == 'kek'


def test_validate_default_factory_value_fith_dict_when_its_off_and_validation_passed():
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation={'some message': lambda x: x == 'kek'}, validate_default=False)

    instance = SomeClass()

    assert instance.field == 'kek'


def test_conflicts_for_default_factory():
    field_value = 10
    other_lazy_field_value = 5
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: field_value, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'other_lazy_field': lambda old, new, other_old, other_new: new > other_old})
        other_field: int = Field(20)
        other_lazy_field: int = Field(default_factory=lambda: other_lazy_field_value)

    with pytest.raises(ValueError, match=match('The 10 (int) deferred default value of the "field" field conflicts with the 5 (int) value of the "other_lazy_field" field.')):
        SomeClass()

    field_value = 25

    with pytest.raises(ValueError, match=match('The 25 (int) deferred default value of the "field" field conflicts with the 20 (int) value of the "other_field" field.')):
        SomeClass()

    field_value = 5
    other_lazy_field_value = 30

    instance = SomeClass()

    assert instance.field == 5
    assert instance.other_field == 20
    assert instance.other_lazy_field == 30


def test_reverse_conflicts_for_default_factory():
    other_lazy_field_value = 5

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_lazy_field': lambda old, new, other_old, other_new: new > other_old})
        other_lazy_field: int = Field(default_factory=lambda: other_lazy_field_value)

    with pytest.raises(ValueError, match=match('The 10 (int) deferred default value of the "field" field conflicts with the 5 (int) value of the "other_lazy_field" field.')):
        SomeClass()

    other_lazy_field_value = 15

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_lazy_field == 15


@pytest.mark.parametrize(
    ['class_flag', 'field_flag'],
    [
        (True, False),
        (False, True),
        (False, False),
    ],
)
def test_reverse_conflicts_off_for_default_factory(class_flag, field_flag):
    other_lazy_field_value = 5

    class SomeClass(Storage, reverse_conflicts=class_flag):
        field: int = Field(10, conflicts={'other_lazy_field': lambda old, new, other_old, other_new: new > other_old}, reverse_conflicts=field_flag)
        other_lazy_field: int = Field(default_factory=lambda: other_lazy_field_value)

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_lazy_field == 5

    other_lazy_field_value = 15

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_lazy_field == 15


def test_conversion_is_not_under_field_lock():
    locks = []

    def conversion(value: int) -> int:
        for lock in locks:
            lock.notify('conversion')
        return value * 2

    class SomeClass(Storage):
        field = Field(42, conversion=conversion)

    storage = SomeClass()

    lock = LockTraceWrapper(storage.__locks__['field'])
    storage.__locks__['field'] = lock
    locks.append(lock)

    storage.field = 5

    assert storage.field == 10

    assert not lock.was_event_locked('conversion') and lock.trace


def test_conflicts_check_on_set_is_after_conversion():
    class SomeClass(Storage):
        field: int = Field(5, conversion=lambda x: x * 2, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new})
        other_field: int = Field(10)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match('The new 20 (int) value of the "field" field conflicts with the 10 (int) value of the "other_field" field.')):
        instance.field = 10


def test_conflicts_check_on_defaults_is_after_conversion():
    with pytest.raises(ValueError, match=match('The 20 (int) default value of the "field" field conflicts with the 10 (int) value of the "other_field" field.')):
        class SomeClass(Storage):
            field: int = Field(10, conversion=lambda x: x * 2, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new})
            other_field: int = Field(10)


def test_value_check_for_defaults_is_after_conversion():
    with pytest.raises(ValueError, match=match('The value 20 (int) of the "field" field does not match the validation.')):
        class SomeClass(Storage):
            field: int = Field(10, conversion=lambda x: x * 2, validation=lambda x: x == 10)
            other_field: int = Field(10)


def test_value_check_for_set_is_after_conversion():
    class SomeClass(Storage):
        field: int = Field(5, conversion=lambda x: x * 2, validation=lambda x: x == 10)
        other_field: int = Field(10)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match('The value 20 (int) of the "field" field does not match the validation.')):
        instance.field = 10


def test_type_check_for_defaults_is_before_conversion():
    with pytest.raises(TypeError, match=match('The value 5 (int) of the "field" field does not match the type str.')):
        class SomeClass(Storage):
            field: str = Field(5, conversion=lambda x: str(x))


def test_type_check_for_defaults_is_after_conversion():
    with pytest.raises(TypeError, match=match('The value \'5\' (str) of the "field" field does not match the type int.')):
        class SomeClass(Storage):
            field: int = Field(5, conversion=lambda x: str(x))


def test_type_check_for_set_is_before_conversion():
    class SomeClass(Storage):
        field: Union[int, str] = Field(5, conversion=lambda x: str(x))

    instance = SomeClass()

    assert instance.field == '5'

    if sys.version_info < (3, 10):
        type_representation = 'typing.Union'
    else:
        type_representation = 'Union'

    with pytest.raises(TypeError, match=match(f'The value 5.5 (float) of the "field" field does not match the type {type_representation}.')):
        instance.field = 5.5


def test_type_check_for_set_is_after_conversion():
    class SomeClass(Storage):
        field: int = Field(5, conversion=lambda x: x if x == 5 else str(x))

    instance = SomeClass()

    assert instance.field == 5

    with pytest.raises(TypeError, match=match('The value \'6\' (str) of the "field" field does not match the type int.')):
        instance.field = 6


def test_basic_conversion_when_set_and_init_with_passed_type_check_for_new_and_old_results():
    class SomeClass(Storage):
        field: int = Field(10, conversion=lambda x: x * 2)

    instance = SomeClass()

    assert instance.field == 20

    instance.field = 3

    assert instance.field == 6


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 15,
        },),
    ],
)
def test_conversion_for_source(toml_config_path, json_config_path, yaml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: int = Field(10, conversion=lambda x: x * 2)

    assert SomeClass().field == 30

    class SecondClass(Storage, sources=[JSONSource(json_config_path)]):
        field: int = Field(10, conversion=lambda x: x * 2)

    assert SecondClass().field == 30

    class SecondClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: int = Field(10, conversion=lambda x: x * 2)

    assert SecondClass().field == 30


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 15,
        },),
    ],
)
def test_type_check_before_conversion_for_toml_source(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: str = Field('kek', conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 15,
        },),
    ],
)
def test_type_check_before_conversion_for_yaml_source(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: str = Field('kek', conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 15,
        },),
    ],
)
def test_type_check_before_conversion_for_json_source(json_config_path):
    class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
        field: str = Field('kek', conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'field': 15,
        },),
    ],
)
def test_type_check_after_conversion_for_source(toml_config_path, json_config_path, yaml_config_path):
    with pytest.raises(TypeError, match=match('The value \'10\' (str) of the "field" field does not match the type int.')):
        class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
            field: int = Field(10, conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value \'10\' (str) of the "field" field does not match the type int.')):
        class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
            field: int = Field(10, conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value \'10\' (str) of the "field" field does not match the type int.')):
        class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
            field: int = Field(10, conversion=lambda x: str(x))


def test_conversion_for_default_factory():
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 10, conversion=lambda x: x * 2)

    assert SomeClass().field == 20


def test_type_check_is_before_conversion_for_default_factory():
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 10, conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value 10 (int) of the "field" field does not match the type str.')):
        SomeClass()


def test_type_check_is_after_conversion_for_default_factory():
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 10, conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value \'10\' (str) of the "field" field does not match the type int.')):
        SomeClass()


def test_validation_is_after_conversion_for_default_factory():
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 5, conversion=lambda x: 10, validation=lambda x: x != 10)

    with pytest.raises(ValueError, match=match('The value 10 (int) of the "field" field does not match the validation.')):
        SomeClass()


def test_validation_is_after_conversion_for_default_factory_when_its_off():
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 5, conversion=lambda x: 10, validation=lambda x: x != 10, validate_default=False)

    instance = SomeClass()

    assert instance.field == 10

    with pytest.raises(ValueError, match=match('The value 10 (int) of the "field" field does not match the validation.')):
        instance.field = 5


def test_share_locks():
    class SomeClass(Storage):
        first_field: int = Field(1, share_mutex_with=['second_field'])
        second_field: int = Field(2)
        third_field: int = Field(3)
        forth_field: int = Field(4, conflicts={'fifth_field': lambda x, y, z, m: False})
        fifth_field: int = Field(5)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is instance.__locks__['second_field']

    assert instance.__locks__['first_field'] is not instance.__locks__['third_field']
    assert instance.__locks__['first_field'] is not instance.__locks__['forth_field']
    assert instance.__locks__['first_field'] is not instance.__locks__['fifth_field']

    assert instance.__locks__['second_field'] is not instance.__locks__['third_field']
    assert instance.__locks__['second_field'] is not instance.__locks__['forth_field']
    assert instance.__locks__['second_field'] is not instance.__locks__['fifth_field']

    assert instance.__locks__['third_field'] is not instance.__locks__['forth_field']
    assert instance.__locks__['third_field'] is not instance.__locks__['fifth_field']

    assert instance.__locks__['forth_field'] is instance.__locks__['fifth_field']


def test_non_existing_field_to_share_mutex():
    with pytest.raises(NameError, match=match('You indicated that you need to share the mutex of "first_field" field with field "sacond_field", but field "sacond_field" does not exist.')):
        class SomeClass(Storage):
            first_field: int = Field(1, share_mutex_with=['sacond_field'])
            second_field: int = Field(2)


def test_share_mutex_with_twice():
    class SomeClass(Storage):
        first_field: int = Field(1, share_mutex_with=['second_field'])
        second_field: int = Field(2, share_mutex_with=['third_field'])
        third_field: int = Field(3)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is instance.__locks__['second_field']
    assert instance.__locks__['third_field'] is instance.__locks__['third_field']


def test_share_mutex_with_conflicting_field():
    class SomeClass(Storage):
        first_field: int = Field(1, share_mutex_with=['second_field'], conflicts={'third_field': lambda x, y, z, m: False})
        second_field: int = Field(2)
        third_field: int = Field(3)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is instance.__locks__['second_field']
    assert instance.__locks__['third_field'] is instance.__locks__['third_field']


def test_get_something_from_env(monkeypatch):
    monkeypatch.setenv("SKELET_FIELD", "1")
    monkeypatch.setenv("SKELET_ANOTHER_FIELD", "kek")

    class SomeClass(Storage, sources=EnvSource.for_library('skelet')):
        field: int = Field(10)
        another_field: str = Field('lol')
        third_field: List[int] = Field(default_factory=lambda: [1, 2, 3])

    instance = SomeClass()

    assert instance.field == 1
    assert instance.another_field == 'kek'
    assert instance.third_field == [1, 2, 3]


def test_get_value_from_sources_by_aliases():
    class SomeClass(Storage, sources=[MemorySource({'field': 1, 'a-b-c': 2})]):
        first_field: int = Field(123, alias='field')
        second_field: int = Field(456, alias='a-b-c')

    instance = SomeClass()

    assert instance.first_field == 1
    assert instance.second_field == 2


def test_get_value_from_sources_by_aliases_when_there_are_original_field_names_available():
    class SomeClass(Storage, sources=[MemorySource({'field': 1, 'a-b-c': 2, 'first_field': 3, 'second_field': 4})]):
        first_field: int = Field(123, alias='field')
        second_field: int = Field(456, alias='a-b-c')

    instance = SomeClass()

    assert instance.first_field == 1
    assert instance.second_field == 2


def test_per_field_sources():
    class SomeClass(Storage):
        first_field: int = Field(123, sources=[MemorySource({'first_field': 1, 'second_field': 2})])
        second_field: int = Field(456, sources=[MemorySource({'first_field': 1, 'second_field': 2})])

    instance = SomeClass()

    assert instance.first_field == 1
    assert instance.second_field == 2


def test_per_field_sources_in_conflict_with_class_source():
    class SomeClass(Storage, sources=[MemorySource({'first_field': 4, 'second_field': 5})]):
        first_field: int = Field(123, sources=[MemorySource({'first_field': 1, 'second_field': 2})])
        second_field: int = Field(456, sources=[MemorySource({'first_field': 1})])

    instance = SomeClass()

    assert instance.first_field == 1
    assert instance.second_field == 456


def test_per_field_sources_with_ellipsis_in_conflict_with_class_source():
    class SomeClass(Storage, sources=[MemorySource({'first_field': 4, 'second_field': 5})]):
        first_field: int = Field(123, sources=[MemorySource({'first_field': 1, 'second_field': 2}), ...])
        second_field: int = Field(456, sources=[MemorySource({'first_field': 1}), ...])

    instance = SomeClass()

    assert instance.first_field == 1
    assert instance.second_field == 5


def test_default_value_is_not_set():
    class SomeClass(Storage):
        first_field: int = Field()
        second_field: int = Field()

    with pytest.raises(ValueError, match=match('The value for the "first_field" field is undefined. Set the default value, or specify the value when creating the instance.')):
        SomeClass()

    with pytest.raises(ValueError, match=match('The value for the "second_field" field is undefined. Set the default value, or specify the value when creating the instance.')):
        SomeClass(first_field=5)

    instance = SomeClass(first_field=5, second_field=10)

    assert instance.first_field == 5
    assert instance.second_field == 10



def test_default_value_is_not_set_but_there_is_source():
    class SomeClass(Storage, sources=[MemorySource({'first_field': 4, 'second_field': 5})]):
        first_field: int = Field()
        second_field: int = Field()

    instance = SomeClass()

    assert instance.first_field == 4
    assert instance.second_field == 5


def test_default_value_is_not_set_but_there_are_per_field_sources():
    class SomeClass(Storage):
        first_field: int = Field(sources=[MemorySource({'first_field': 4, 'second_field': 5})])
        second_field: int = Field(sources=[MemorySource({'first_field': 4, 'second_field': 5})])

    instance = SomeClass()

    assert instance.first_field == 4
    assert instance.second_field == 5
