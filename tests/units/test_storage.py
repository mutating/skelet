import sys
from functools import partial
from types import FunctionType
from typing import Any, List, Optional, Union

import pytest
from full_match import match
from locklib import LockTraceWrapper
from sigmatch import PossibleCallMatcher, SignatureMismatchError

from skelet import (
    EnvSource,
    Field,
    FieldDescriptor,
    JSONSource,
    MemorySource,
    NaturalNumber,
    NonNegativeInt,
    Storage,
    TOMLSource,
    YAMLSource,
)


def test_try_to_get_descriptor_object_from_class_inherited_from_storage():
    class SomeClass(Storage):
        field = Field(42)

    assert isinstance(SomeClass.field, FieldDescriptor)


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

    instance = SomeClass()

    for index in range(10):
        assert instance.field == index
        instance.field += 1


def test_changing_value_is_not_changing_the_default_value():
    class SomeClass(Storage):
        field = Field(42)

    instance = SomeClass()

    assert instance.field == 42

    instance.field += 1

    assert instance.field == 43

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

    instance = SomeClass()

    with pytest.raises(AttributeError, match=match('"field" field is read-only.')):
        instance.field = 43

    assert instance.field == 42


def test_try_to_set_new_value_to_read_only_attribute_with_doc():
    class SomeClass(Storage):
        field = Field(42, read_only=True, doc='some doc')

    instance = SomeClass()

    with pytest.raises(AttributeError, match=match('"field" field (some doc) is read-only.')):
        instance.field = 43

    assert instance.field == 42


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
    assert SecondClass.__field_names__ ==  [*FirstClass.__field_names__, 'field_4']

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
    assert SecondClass.__field_names__ ==  [*FirstClass.__field_names__, 'field_4']
    assert ThirdClass.__field_names__ == [*SecondClass.__field_names__, 'field_5']

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

    assert StorageChild.__field_names__ == ()


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
        field = Field(42, read_lock=True)

    storage = SomeClass()
    field = SomeClass.field

    field.lock = LockTraceWrapper(field.lock)
    storage.__locks__['field'] = LockTraceWrapper(storage.__locks__['field'])

    class PseudoDict:
        def get(self, key):  # noqa: ARG002
            storage.__locks__['field'].notify('get')
            field.lock.notify('get')
            return 43

    storage.__values__ = PseudoDict()

    assert storage.field == 43
    assert storage.__locks__['field'].was_event_locked('get')

    assert not field.lock.was_event_locked('get')
    assert field.lock.trace


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

        def get(self, key):  # noqa: ARG002
            storage.__locks__['field'].notify('get')
            field.lock.notify('get')
            return 42

    storage.__values__ = PseudoDict()

    storage.field = 44

    assert storage.__locks__['field'].was_event_locked('set')
    assert storage.__locks__['field'].was_event_locked('get')

    assert not field.lock.was_event_locked('set')
    assert field.lock.trace
    assert not field.lock.was_event_locked('get')


def test_set_name_uses_per_field_object_lock():
    class SomeClass(Storage):
        ...

    field = Field(42)
    field.lock = LockTraceWrapper(field.lock)
    field.set_field_names = lambda x, y: field.lock.notify('get')  # noqa: ARG005

    field.__set_name__(SomeClass, 'field')

    assert field.lock.was_event_locked('get')
    assert field.lock.trace


def test_simple_type_check_failed_when_set_bool_if_expected_int():
    class SomeClass(Storage):
        field: int = Field(15)

    instance = SomeClass()

    instance.field = True

    assert instance.field is True


@pytest.mark.parametrize(
    ('int_value', 'float_value', 'secret'),
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
    ('int_value', 'float_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    'addictional_parameters',
    [
        {},
        {'doc': 'some doc'},
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
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
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
    'addictional_parameters',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_validation_functions_dict_failed_when_init(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation={'some message': lambda value: value > 0}, **addictional_parameters)

    with pytest.raises(ValueError, match=match('some message')):
        SomeClass(field=-1)


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_validation_function_not_failed_when_init(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation=lambda value: value > 0, **addictional_parameters)

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_validation_functions_dict_not_failed_when_init(addictional_parameters):
    class SomeClass(Storage):
        field: int = Field(15, validation={'some message': lambda value: value > 0}, **addictional_parameters)

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1


@pytest.mark.parametrize(
    ('wrong_value', 'secret'),
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
    ('wrong_value', 'secret'),
    [
        ('***', True),
        ('-15', False),
    ],
)
def test_validation_function_failed_when_default_with_doc(wrong_value, secret):
    with pytest.raises(ValueError, match=match(f'The value {wrong_value} (int) of the "field" field (some doc) does not match the validation.')):
        class SomeClass(Storage):
            field: int = Field(-15, validation=lambda value: value > 0, doc='some doc', secret=secret)


def test_validation_functions_dict_failed_when_default():
    with pytest.raises(ValueError, match=match('some message')):
        class SomeClass(Storage):
            field: int = Field(-15, validation={'some message': lambda value: value > 0})


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'doc': 'some doc'},
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
    SomeClass.field.validation = lambda x: instance.__locks__['field'].notify('kek') is None  # noqa: ARG005
    instance.field = 5

    assert instance.field == 5

    assert not instance.__locks__['field'].was_event_locked('kek')


def test_type_check_when_set_is_not_under_lock():
    class SomeClass(Storage):
        field: int = Field(10, validation=lambda value: value > 0)

    instance = SomeClass()

    instance.__locks__['field'] = LockTraceWrapper(instance.__locks__['field'])
    SomeClass.field.check_type_hints = lambda x, raise_all: instance.__locks__['field'].notify('kek')  # noqa: ARG005
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
    SomeClass.field.check_type_hints = lambda z, raise_all: flags.append('type_check') is old_check_type_hints(z, raise_all=raise_all)
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
        field: int = Field(10, secret=True, action=lambda old, new, storage: flags.append(True))  # noqa: ARG005

    instance = SomeClass()

    assert not flags

    instance.field = 13

    assert flags == [True]

    instance.field = 14

    assert flags == [True, True]


def test_action_doesnt_work_when_new_value_is_same():
    flags = []

    class SomeClass(Storage):
        field: int = Field(10, secret=True, action=lambda old, new, storage: flags.append(True))  # noqa: ARG005

    instance = SomeClass()

    assert not flags

    instance.field = 10

    assert not flags
    assert instance.field == 10


@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {'read_lock': True},
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
        def get(self, key):  # noqa: ARG002
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
        def get(self, key):  # noqa: ARG002
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
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old})  # noqa: ARG005
        other_field: int = Field(20)
        second_other_field: int = Field(25)

    instance = SomeClass()

    assert instance.__locks__['field'] is instance.__locks__['other_field']
    assert instance.__locks__['field'] is not instance.__locks__['second_other_field']


def test_conflicts_check_is_under_field_lock():
    locks: List[LockTraceWrapper] = []

    def check_function(old, new, other_old, other_new):  # noqa: ARG001
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

    def check_function(old, new, other_old, other_new):  # noqa: ARG001
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
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_non_existing_conflicting_field_name(addictional_arguments):
    if not addictional_arguments:
        exception_message = 'You have set a conflict condition for "field" field with field "ather_field", but the field "ather_field" does not exist in the class SomeClass.'
    else:
        exception_message = f'You have set a conflict condition for "field" field ({addictional_arguments["doc"]}) with field "ather_field", but the field "ather_field" does not exist in the class SomeClass.'

    with pytest.raises(NameError, match=match(exception_message)):
        class SomeClass(Storage):
            field: int = Field(10, conflicts={'ather_field': lambda old, new, other_old, other_new: new > other_old}, **addictional_arguments)  # noqa: ARG005
            other_field: int = Field(20)


# Check: reverse check
# Check: exceptions messages for both types of fields on the both sides, direct and reverse

@pytest.mark.parametrize(
    'main_field_is_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_basic_conflicting_fields(addictional_arguments, main_field_is_secret):
    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'secret_other_field': lambda old, new, other_old, other_new: new < 0}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret)  # noqa: ARG005
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
    elif main_field_is_secret:
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
    elif main_field_is_secret:
        exception_message = 'The new *** (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'
    else:
        exception_message = 'The new -1 (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        instance.field = -1

    assert instance.field == 15


@pytest.mark.parametrize(
    'main_field_is_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_conflicting_fields_when_set_in_init(addictional_arguments, main_field_is_secret):
    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'secret_other_field': lambda old, new, other_old, other_new: new < 0}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret)  # noqa: ARG005
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
    elif main_field_is_secret:
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
    elif main_field_is_secret:
        exception_message = 'The new *** (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'
    else:
        exception_message = 'The new -1 (int) value of the "field" field conflicts with the *** (int) value of the "secret_other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        SomeClass(field=-1)


@pytest.mark.parametrize(
    'are_fields_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_conflicting_fields_when_defaults_are_conflicting(addictional_arguments, are_fields_secret):
    if 'doc' in addictional_arguments:
        if are_fields_secret:
            exception_message = 'The *** (int) default value of the "field" field (some doc) conflicts with the *** (int) value of the "other_field" field (some doc).'
        else:
            exception_message = 'The 21 (int) default value of the "field" field (some doc) conflicts with the 20 (int) value of the "other_field" field (some doc).'
    elif are_fields_secret:
        exception_message = 'The *** (int) default value of the "field" field conflicts with the *** (int) value of the "other_field" field.'
    else:
        exception_message = 'The 21 (int) default value of the "field" field conflicts with the 20 (int) value of the "other_field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        class SomeClass(Storage):
            field: int = Field(21, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'secret_other_field': lambda old, new, other_old, other_new: new > 30}, doc=addictional_arguments.get('doc'), secret=are_fields_secret)  # noqa: ARG005
            other_field: int = Field(20, doc=addictional_arguments.get('doc'), secret=are_fields_secret)


@pytest.mark.parametrize(
    'are_fields_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
        {'reverse_conflicts': True},
        {'reverse_conflicts': True, 'doc': 'some doc'},
    ],
)
def test_basic_conflicting_fields_reverse_when_its_on(addictional_arguments, are_fields_secret):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments)  # noqa: ARG005
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
    elif are_fields_secret:
        exception_message = 'The new *** (int) value of the "other_field" field conflicts with the *** (int) value of the "field" field.'
    else:
        exception_message = 'The new 5 (int) value of the "other_field" field conflicts with the 10 (int) value of the "field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        instance.other_field = 5

    assert instance.other_field == 30
    assert instance.field == 10


@pytest.mark.parametrize(
    'are_fields_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
        {'reverse_conflicts': True},
        {'reverse_conflicts': True, 'doc': 'some doc'},
    ],
)
def test_conflicting_fields_reverse_when_its_on_and_when_set_in_init(addictional_arguments, are_fields_secret):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments)  # noqa: ARG005
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
    elif are_fields_secret:
        exception_message = 'The new *** (int) value of the "other_field" field conflicts with the *** (int) value of the "field" field.'
    else:
        exception_message = 'The new 5 (int) value of the "other_field" field conflicts with the 10 (int) value of the "field" field.'

    with pytest.raises(ValueError, match=match(exception_message)):
        SomeClass(other_field=5)


@pytest.mark.parametrize(
    'reverse_check_parameters',
    [
        {'class': False, 'field': True},
        {'class': True, 'field': False},
        {'class': False, 'field': False},
    ],
)
@pytest.mark.parametrize(
    'are_fields_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_basic_conflicting_fields_reverse_when_its_off(addictional_arguments, are_fields_secret, reverse_check_parameters):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments, reverse_conflicts=reverse_check_parameters['field'])  # noqa: ARG005
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
    'reverse_check_parameters',
    [
        {'class': False, 'field': True},
        {'class': True, 'field': False},
        {'class': False, 'field': False},
    ],
)
@pytest.mark.parametrize(
    'are_fields_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
def test_conflicting_fields_reverse_when_its_off_and_when_set_in_init(addictional_arguments, are_fields_secret, reverse_check_parameters):
    doc = addictional_arguments.pop('doc', None)

    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new}, doc=doc, secret=are_fields_secret, **addictional_arguments, reverse_conflicts=reverse_check_parameters['field'])  # noqa: ARG005
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
    'main_field_is_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
@pytest.mark.parametrize(
    'reverse_check_parameters',
    [
        {'class': False, 'field': True},
        {'class': True, 'field': False},
        {'class': False, 'field': False},
    ],
)
def test_conflicting_fields_when_reverse_check_off(addictional_arguments, main_field_is_secret, reverse_check_parameters):
    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret, reverse_conflicts=reverse_check_parameters['field'])  # noqa: ARG005
        other_field: int = Field(20, doc=addictional_arguments.get('doc'))

    instance = SomeClass()

    assert instance.field == 10

    instance.other_field = 5

    assert instance.other_field == 5


@pytest.mark.parametrize(
    'main_field_is_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
@pytest.mark.parametrize(
    'reverse_check_parameters',
    [
        {'class': False, 'field': True},
        {'class': True, 'field': False},
        {'class': False, 'field': False},
    ],
)
def test_conflicting_fields_in_init_when_reverse_check_off(addictional_arguments, main_field_is_secret, reverse_check_parameters):
    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret, reverse_conflicts=reverse_check_parameters['field'])  # noqa: ARG005
        other_field: int = Field(20, doc=addictional_arguments.get('doc'))

    instance = SomeClass(other_field=5)

    assert instance.field == 10
    assert instance.other_field == 5


@pytest.mark.parametrize(
    'main_field_is_secret',
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    'addictional_arguments',
    [
        {},
        {'doc': 'some doc'},
    ],
)
@pytest.mark.parametrize(
    'reverse_check_parameters',
    [
        {'class': False, 'field': True},
        {'class': True, 'field': False},
        {'class': False, 'field': False},
    ],
)
def test_conflicting_fields_in_defaults_when_reverse_check_off(addictional_arguments, main_field_is_secret, reverse_check_parameters):
    class SomeClass(Storage, reverse_conflicts=reverse_check_parameters['class']):
        field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new}, doc=addictional_arguments.get('doc'), secret=main_field_is_secret, reverse_conflicts=reverse_check_parameters['field'])  # noqa: ARG005
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
        field: int = Field(5, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new})  # noqa: ARG005
        other_field: int = Field(10)

    assert SomeClass.__reverse_conflicts__ == {'other_field': ['field']}
    assert SomeClass.__field_names__ == ['field', 'other_field']


def test_reverse_fields_container_in_case_of_inheritance_with_new_field():
    class SomeClass(Storage):
        field: int = Field(5, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new})  # noqa: ARG005
        other_field: int = Field(10)

    class SomeOtherClass(SomeClass):
        third_field: int = Field(10, conflicts={'other_field': lambda old, new, other_old, other_new: old > 1000})  # noqa: ARG005

    assert SomeClass.__reverse_conflicts__ == {'other_field': ['field']}
    assert SomeOtherClass.__reverse_conflicts__ == {'other_field': ['field', 'third_field']}

    assert SomeClass.__field_names__ == ['field', 'other_field']
    assert SomeOtherClass.__field_names__ == ['field', 'other_field', 'third_field']


def test_reverse_fields_container_in_case_of_inheritance_with_same_field():
    class SomeClass(Storage):
        field: int = Field(5, conflicts={'other_field': lambda old, new, other_old, other_new: old > other_new})  # noqa: ARG005
        other_field: int = Field(10)

    class SomeOtherClass(SomeClass):
        other_field: int = Field(10, conflicts={'field': lambda old, new, other_old, other_new: old > 1000})  # noqa: ARG005

    assert SomeClass.__reverse_conflicts__ == {'other_field': ['field']}
    assert SomeOtherClass.__reverse_conflicts__ == {'other_field': ['field'], 'field': ['other_field']}

    assert SomeClass.__field_names__ == ['field', 'other_field']
    assert SomeOtherClass.__field_names__ == ['field', 'other_field']


@pytest.mark.parametrize(
    'sources',
    [
        [],
        [MemorySource({})],
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
    'data',
    [
        {'field': 1, 'other_field': 14},
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
    'data',
    [
        {'field': 1, 'other_field': 14},
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
    'data',
    [
        {'field': 1, 'other_field': 14},
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


def test_source_check_is_in_init():
    keys = []

    class PseudoDict:
        def __getitem__(self, key: str) -> Any:
            keys.append(key)
            return 1

    class SomeClass(Storage, sources=[MemorySource(PseudoDict())]):
        field: int = Field(10, read_lock=True)
        other_field: int = Field(20)

    assert not keys

    instance = SomeClass()

    assert keys == ['field', 'other_field']

    assert instance.field == 1
    assert instance.other_field == 1

    assert keys == ['field', 'other_field']


def test_velue_reading_is_under_field_lock_when_its_on():
    locks: List[LockTraceWrapper] = []

    class PseudoDict:
        def get(self, key: str) -> Any:  # noqa: ARG002
            for lock in locks:
                lock.notify('get')
            return 1

    class SomeClass(Storage):
        field: int = Field(10, read_lock=True)
        other_field: int = Field(20)

    instance = SomeClass()

    lock = LockTraceWrapper(instance.__locks__['field'])
    locks.append(lock)
    instance.__locks__['field'] = lock
    instance.__values__ = PseudoDict()

    assert instance.field == 1

    assert lock.was_event_locked('get')


@pytest.mark.parametrize(
    'data',
    [
        {'field': '1'},
    ],
)
def test_read_bad_typed_value_from_toml_source_for_not_deferred_value(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: int = Field(5)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': '1'},
    ],
)
def test_read_bad_typed_value_from_yaml_source_for_not_deferred_value(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: int = Field(5)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': '1'},
    ],
)
def test_read_bad_typed_value_from_json_source_for_not_deferred_value(json_config_path):
    class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
        field: int = Field(5)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': [14]},
    ],
)
def test_read_bad_typed_value_from_toml_source_for_deferred_value(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: List[str] = Field(default_factory=list)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': [14]},
    ],
)
def test_read_bad_typed_value_from_yaml_source_for_deferred_value(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: List[str] = Field(default_factory=list)

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': [14]},
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
    'addictional_parameters',
    [
        {},
        {'validate_default': True},
    ],
)
def test_validate_default_factory_value_fith_function_when_its_on_and_validation_not_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation=lambda x: x != 'kek', **addictional_parameters)

    with pytest.raises(ValueError, match=match('The value \'kek\' (str) of the "field" field does not match the validation.')):
        SomeClass()


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'validate_default': True},
    ],
)
def test_validate_default_factory_value_fith_function_when_its_on_and_validation_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation=lambda x: x == 'kek', **addictional_parameters)

    instance = SomeClass()

    assert instance.field == 'kek'


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'validate_default': True},
    ],
)
def test_validate_default_factory_value_fith_dict_when_its_on_and_validation_not_passed(addictional_parameters):
    class SomeClass(Storage):
        field: str = Field(default_factory=lambda: 'kek', validation={'some message': lambda x: x != 'kek'}, **addictional_parameters)

    with pytest.raises(ValueError, match=match('some message')):
        SomeClass()


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'validate_default': True},
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
        field: int = Field(default_factory=lambda: field_value, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_old, 'other_lazy_field': lambda old, new, other_old, other_new: new > other_old})  # noqa: ARG005
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
        field: int = Field(10, conflicts={'other_lazy_field': lambda old, new, other_old, other_new: new > other_old})  # noqa: ARG005
        other_lazy_field: int = Field(default_factory=lambda: other_lazy_field_value)

    with pytest.raises(ValueError, match=match('The 10 (int) deferred default value of the "field" field conflicts with the 5 (int) value of the "other_lazy_field" field.')):
        SomeClass()

    other_lazy_field_value = 15

    instance = SomeClass()

    assert instance.field == 10
    assert instance.other_lazy_field == 15


@pytest.mark.parametrize(
    ('class_flag', 'field_flag'),
    [
        (True, False),
        (False, True),
        (False, False),
    ],
)
def test_reverse_conflicts_off_for_default_factory(class_flag, field_flag):
    other_lazy_field_value = 5

    class SomeClass(Storage, reverse_conflicts=class_flag):
        field: int = Field(10, conflicts={'other_lazy_field': lambda old, new, other_old, other_new: new > other_old}, reverse_conflicts=field_flag)  # noqa: ARG005
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

    assert not lock.was_event_locked('conversion')
    assert lock.trace


def test_validation_runs_before_and_after_conversion_for_assignment():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(0, conversion=conversion, validation=validation, validate_default=False)

    instance = SomeClass()
    events.clear()

    instance.field = 1

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


def test_validation_runs_before_and_after_conversion_for_init_kwargs():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(0, conversion=conversion, validation=validation, validate_default=False)

    events.clear()

    instance = SomeClass(field=1)

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


def test_validation_runs_before_and_after_conversion_for_literal_default():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation)

    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]
    assert SomeClass().field == 2


def test_validation_runs_before_and_after_conversion_for_default_factory():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 1, conversion=conversion, validation=validation)

    instance = SomeClass()

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


def test_validation_runs_before_and_after_conversion_for_class_source():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage, sources=[MemorySource({'field': 1})]):
        field: int = Field(conversion=conversion, validation=validation)

    instance = SomeClass()

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_validation_runs_before_and_after_conversion_for_instance_source(collection_type):
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(conversion=conversion, validation=validation)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 1})]))

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


def test_validation_without_conversion_runs_once_when_set():
    events = []

    def validation(value):
        events.append(value)
        return True

    class SomeClass(Storage):
        field: int = Field(0, validation=validation, validate_default=False)

    instance = SomeClass()

    instance.field = 1

    assert instance.field == 1
    assert events == [1]


def test_identity_conversion_still_validates_before_and_after_conversion():
    events = []

    def validation(value):
        events.append(('validation', value))
        return True

    def conversion(value):
        events.append(('conversion', value))
        return value

    class SomeClass(Storage):
        field: int = Field(0, conversion=conversion, validation=validation, validate_default=False)

    instance = SomeClass()
    events.clear()

    instance.field = 1

    assert instance.field == 1
    assert events == [('validation', 1), ('conversion', 1), ('validation', 1)]


def test_failed_raw_type_check_is_transactional_before_conversion():
    events = []

    def validation(value):
        events.append(('validation', value))
        return True

    def conversion(value):
        events.append(('conversion', value))
        return 100

    def conflict(*args):
        events.append(('conflict', args))
        return False

    def action(old, new, storage):
        events.append(('action', old, new, storage))

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation, action=action, conflicts={'other_field': conflict})
        other_field: int = Field(1000)

    instance = SomeClass()
    assert instance.field == 100
    events.clear()

    with pytest.raises(TypeError, match=match('The value \'bad\' (str) of the "field" field does not match the type int.')):
        instance.field = 'bad'

    assert instance.field == 100
    assert events == []


def test_failed_raw_validation_is_transactional_before_conversion():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value >= 0

    def conversion(value):
        events.append(('conversion', value))
        return abs(value)

    def conflict(*args):
        events.append(('conflict', args))
        return False

    def action(old, new, storage):
        events.append(('action', old, new, storage))

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation, action=action, conflicts={'other_field': conflict})
        other_field: int = Field(1000)

    instance = SomeClass()
    assert instance.field == 1
    events.clear()

    with pytest.raises(ValueError, match=match('The value -5 (int) of the "field" field does not match the validation.')):
        instance.field = -5

    assert instance.field == 1
    assert events == [('validation', -5)]


def test_conversion_exception_is_transactional():
    events = []

    def validation(value):
        events.append(('validation', value))
        return True

    def conversion(value):
        events.append(('conversion', value))
        if value == 5:
            raise RuntimeError('conversion failed')
        return value

    def conflict(*args):
        events.append(('conflict', args))
        return False

    def action(old, new, storage):
        events.append(('action', old, new, storage))

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation, action=action, conflicts={'other_field': conflict})
        other_field: int = Field(1000)

    instance = SomeClass()
    events.clear()

    with pytest.raises(RuntimeError, match=match('conversion failed')):
        instance.field = 5

    assert instance.field == 1
    assert events == [('validation', 5), ('conversion', 5)]


def test_literal_default_conversion_exception_is_raised_from_storage_subclass():
    def conversion(_value):
        raise RuntimeError('conversion failed')

    with pytest.raises(RuntimeError, match=match('conversion failed')):
        class SomeClass(Storage):
            field: int = Field(1, conversion=conversion)


def test_failed_converted_type_check_is_transactional_before_post_validation():
    events = []

    def validation(value):
        events.append(('validation', value))
        return True

    def conversion(value):
        events.append(('conversion', value))
        if value == 5:
            return 'bad'
        return value

    def conflict(*args):
        events.append(('conflict', args))
        return False

    def action(old, new, storage):
        events.append(('action', old, new, storage))

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation, action=action, conflicts={'other_field': conflict})
        other_field: int = Field(1000)

    instance = SomeClass()
    events.clear()

    with pytest.raises(TypeError, match=match('The value \'bad\' (str) of the "field" field does not match the type int.')):
        instance.field = 5

    assert instance.field == 1
    assert events == [('validation', 5), ('conversion', 5)]


def test_failed_converted_validation_is_transactional():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value < 5

    def conversion(value):
        events.append(('conversion', value))
        return value * 2

    def conflict(*args):
        events.append(('conflict', args))
        return False

    def action(old, new, storage):
        events.append(('action', old, new, storage))

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation, action=action, conflicts={'other_field': conflict})
        other_field: int = Field(1000)

    instance = SomeClass()
    assert instance.field == 2
    events.clear()

    with pytest.raises(ValueError, match=match('The value 8 (int) of the "field" field does not match the validation.')):
        instance.field = 4

    assert instance.field == 2
    assert events == [('validation', 4), ('conversion', 4), ('validation', 8)]


def test_failed_conflict_check_is_transactional_after_conversion():
    events = []

    def conversion(value):
        events.append(('conversion', value))
        return value * 2

    def conflict(old, new, other_old, other_new):
        events.append(('conflict', old, new, other_old, other_new))
        return new == 10

    def action(old, new, storage):
        events.append(('action', old, new, storage))

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=lambda _value: True, action=action, conflicts={'other_field': conflict})
        other_field: int = Field(1000)

    instance = SomeClass()
    assert instance.field == 2
    events.clear()

    with pytest.raises(ValueError, match='conflicts with'):
        instance.field = 5

    assert instance.field == 2
    assert events == [('conversion', 5), ('conflict', 2, 10, 1000, 1000)]


def test_validate_default_false_skips_both_validation_phases_for_literal_default():
    events = []

    def validation(value):
        events.append(('validation', value))
        return False

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation, validate_default=False)

    assert SomeClass().field == 2
    assert events == [('conversion', 1)]


def test_validate_default_false_skips_both_validation_phases_for_default_factory():
    events = []

    def validation(value):
        events.append(('validation', value))
        return False

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 1, conversion=conversion, validation=validation, validate_default=False)

    assert SomeClass().field == 2
    assert events == [('conversion', 1)]


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_sources_validate_before_and_after_conversion_even_when_validate_default_false(collection_type):
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(0, conversion=conversion, validation=validation, validate_default=False)

    events.clear()

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 1})]))

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


def test_init_kwargs_validate_before_and_after_conversion_when_validate_default_false():
    events = []

    def validation(value):
        events.append(('validation', value))
        return value in (1, 2)

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(0, conversion=conversion, validation=validation, validate_default=False)

    events.clear()

    instance = SomeClass(field=1)

    assert instance.field == 2
    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]


def test_secret_value_is_masked_for_all_conversion_failure_phases():
    class RawTypeFailure(Storage):
        field: int = Field(1, conversion=lambda value: value, validation=lambda _value: True, secret=True)

    with pytest.raises(TypeError, match=match('The value *** (str) of the "field" field does not match the type int.')):
        RawTypeFailure().field = 'bad'

    class RawValidationFailure(Storage):
        field: int = Field(1, conversion=abs, validation=lambda value: value >= 0, secret=True)

    with pytest.raises(ValueError, match=match('The value *** (int) of the "field" field does not match the validation.')):
        RawValidationFailure().field = -1

    class ConvertedTypeFailure(Storage):
        field: int = Field(0, conversion=lambda value: 'bad' if value == 1 else value, validation=lambda _value: True, secret=True)

    with pytest.raises(TypeError, match=match('The value *** (str) of the "field" field does not match the type int.')):
        ConvertedTypeFailure().field = 1

    class ConvertedValidationFailure(Storage):
        field: int = Field(0, conversion=lambda value: -value, validation=lambda value: value >= 0, secret=True)

    with pytest.raises(ValueError, match=match('The value *** (int) of the "field" field does not match the validation.')):
        ConvertedValidationFailure().field = 1


def test_dict_validation_messages_and_order_before_and_after_conversion():
    events = []

    def first(value):
        events.append(('first', value))
        return value != -1

    def second(value):
        events.append(('second', value))
        return value != 2

    class SomeClass(Storage):
        field: int = Field(0, conversion=lambda value: value + 1, validation={'first message': first, 'second message': second}, validate_default=False)

    instance = SomeClass()
    events.clear()

    with pytest.raises(ValueError, match=match('first message')):
        instance.field = -1

    assert instance.field == 1
    assert events == [('first', -1)]

    events.clear()

    with pytest.raises(ValueError, match=match('second message')):
        instance.field = 1

    assert instance.field == 1
    assert events == [('first', 1), ('second', 1), ('first', 2), ('second', 2)]


def test_literal_default_is_converted_once_for_all_instances_and_accesses():
    events = []

    def conversion(value):
        events.append(value)
        return value + 1

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=lambda _value: True)

    assert events == [1]

    first = SomeClass()
    second = SomeClass()

    assert first.field == 2
    assert first.field == 2
    assert second.field == 2
    assert events == [1]


def test_conflicts_check_on_set_is_after_conversion():
    class SomeClass(Storage):
        field: int = Field(5, conversion=lambda x: x * 2, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new})  # noqa: ARG005
        other_field: int = Field(10)

    instance = SomeClass()

    with pytest.raises(ValueError, match=match('The new 20 (int) value of the "field" field conflicts with the 10 (int) value of the "other_field" field.')):
        instance.field = 10


def test_conflicts_check_on_defaults_is_after_conversion():
    with pytest.raises(ValueError, match=match('The 20 (int) default value of the "field" field conflicts with the 10 (int) value of the "other_field" field.')):
        class SomeClass(Storage):
            field: int = Field(10, conversion=lambda x: x * 2, conflicts={'other_field': lambda old, new, other_old, other_new: new > other_new})  # noqa: ARG005
            other_field: int = Field(10)


def test_value_check_for_defaults_is_after_conversion():
    with pytest.raises(ValueError, match=match('The value 20 (int) of the "field" field does not match the validation.')):
        class SomeClass(Storage):
            field: int = Field(10, conversion=lambda x: x * 2, validation=lambda x: x == 10)
            other_field: int = Field(10)


def test_value_check_for_set_is_after_conversion():
    class SomeClass(Storage):
        field: int = Field(10, conversion=lambda x: x * 2, validation=lambda x: x == 10, validate_default=False)
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
    'data',
    [
        {'field': 15},
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
    'data',
    [
        {'field': 15},
    ],
)
def test_type_check_before_conversion_for_toml_source(toml_config_path):
    class SomeClass(Storage, sources=[TOMLSource(toml_config_path)]):
        field: str = Field('kek', conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': 15},
    ],
)
def test_type_check_before_conversion_for_yaml_source(yaml_config_path):
    class SomeClass(Storage, sources=[YAMLSource(yaml_config_path)]):
        field: str = Field('kek', conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': 15},
    ],
)
def test_type_check_before_conversion_for_json_source(json_config_path):
    class SomeClass(Storage, sources=[JSONSource(json_config_path)]):
        field: str = Field('kek', conversion=lambda x: str(x))

    with pytest.raises(TypeError, match=match('The value of the "field" field did not pass the type check.')):
        SomeClass()


@pytest.mark.parametrize(
    'data',
    [
        {'field': 15},
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
        field: int = Field(default_factory=lambda: 5, conversion=lambda x: 10, validation=lambda x: x != 10)  # noqa: ARG005

    with pytest.raises(ValueError, match=match('The value 10 (int) of the "field" field does not match the validation.')):
        SomeClass()


def test_validation_is_after_conversion_for_default_factory_when_its_off():
    class SomeClass(Storage):
        field: int = Field(default_factory=lambda: 5, conversion=lambda x: 10, validation=lambda x: x != 10, validate_default=False)  # noqa: ARG005

    instance = SomeClass()

    assert instance.field == 10

    with pytest.raises(ValueError, match=match('The value 10 (int) of the "field" field does not match the validation.')):
        instance.field = 5


def test_share_locks():
    class SomeClass(Storage):
        first_field: int = Field(1, share_mutex_with=['second_field'])
        second_field: int = Field(2)
        third_field: int = Field(3)
        forth_field: int = Field(4, conflicts={'fifth_field': lambda x, y, z, m: False})  # noqa: ARG005
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
        first_field: int = Field(1, share_mutex_with=['second_field'], conflicts={'third_field': lambda x, y, z, m: False})  # noqa: ARG005
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


def _required_keyword_only(*, value):
    return bool(value)


def _pure_kwargs(**kwargs):
    return bool(kwargs)


def _bad_partial_base(value):
    return bool(value)


def _callback_signature_message(parameter_path, call_description, callback_representation):
    return f'Callback parameter {parameter_path} is invalid: skelet calls it {call_description}, but {callback_representation} cannot be called in that form.'


DEFAULT_FACTORY_CALL_DESCRIPTION = 'with no arguments'
VALIDATION_CALL_DESCRIPTION = 'with one positional argument: value is the field value being validated'
CONVERSION_CALL_DESCRIPTION = 'with one positional argument: value is the raw field value before conversion'
ACTION_CALL_DESCRIPTION = 'with three positional arguments: old_value is the previous field value, new_value is the assigned field value, and storage is the Storage instance'
CONFLICT_CALL_DESCRIPTION = "with four positional arguments: old is this field's previous value, new is this field's candidate value, other_old is the conflicting field's previous value, and other_new is the conflicting field's candidate value"


def _one_arg(value):
    return bool(value)


def _zero_arg_callback():
    return True


def _two_arg_callback(value, extra):
    return bool(value) or bool(extra)


def _three_arg_callback(old_value, new_value, storage):
    return old_value != new_value and storage is not None


def _four_arg_callback(old_value, new_value, other_old, other_new):
    return old_value != new_value and other_old != other_new


def _five_arg_callback(old_value, new_value, other_old, other_new, extra):
    return old_value != new_value and other_old != other_new and bool(extra)


def _bad_named_validator(value, extra):
    return bool(value) or bool(extra)


def _bad_generator_validator(value, extra):
    yield bool(value) or bool(extra)


async def _bad_async_validator(value, extra):
    return bool(value) or bool(extra)


class BadClassValidator:
    def __init__(self, value, extra):
        self.value = value
        self.extra = extra


class BadClassNameMeta(type):
    def __getattribute__(cls, name):
        if name == '__name__':
            raise RuntimeError('broken class name')
        return super().__getattribute__(name)


class BadClassNameValidator(metaclass=BadClassNameMeta):
    def __init__(self, value, extra):
        self.value = value
        self.extra = extra


class BadCallableRepr:
    def __call__(self):
        return True

    def __repr__(self):
        raise ValueError('broken callback repr')


class BadCallableMetadata:
    def __call__(self):
        return True

    def __repr__(self):
        return '<bad callable metadata>'

    def __getattribute__(self, name):
        if name in {'__name__', '__qualname__'}:
            raise RuntimeError('broken callback metadata')
        return super().__getattribute__(name)


class CallableNoneMetadata:
    def __call__(self):
        return True

    def __repr__(self):
        return '<callable none metadata>'

    def __getattribute__(self, name):
        if name in {'__name__', '__qualname__'}:
            return None
        return super().__getattribute__(name)


class BadKeyRepr:
    def __repr__(self):
        raise ValueError('broken key repr')


class LongBadCallableRepr:
    def __call__(self):
        return True

    def __repr__(self):
        return f'<{"x" * 300}>'


def _class_with_field(**field_kwargs):
    class SomeClass(Storage):
        field: int = Field(123, **field_kwargs)
        another_field: int = Field(456)

    return SomeClass


def _field_for_signature_check(**field_kwargs):
    if 'default_factory' in field_kwargs:
        return Field(**field_kwargs)
    return Field(123, **field_kwargs)


_overfilled_partial = partial(_bad_partial_base, 1)


@pytest.mark.parametrize(
    ('field_kwargs', 'expected_message'),
    [
        pytest.param({'default_factory': _one_arg}, _callback_signature_message('default_factory', DEFAULT_FACTORY_CALL_DESCRIPTION, '_one_arg'), id='default_factory-one-required-arg'),
        pytest.param({'default_factory': 123}, _callback_signature_message('default_factory', DEFAULT_FACTORY_CALL_DESCRIPTION, '123'), id='default_factory-non-callable'),
        pytest.param({'default_factory': dict}, _callback_signature_message('default_factory', DEFAULT_FACTORY_CALL_DESCRIPTION, 'dict'), id='default_factory-uninspectable-dict'),
        pytest.param({'validation': _zero_arg_callback}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_zero_arg_callback'), id='validation-no-args'),
        pytest.param({'validation': _two_arg_callback}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_two_arg_callback'), id='validation-two-required-args'),
        pytest.param({'validation': 123}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '123'), id='validation-non-callable'),
        pytest.param({'validation': _required_keyword_only}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_required_keyword_only'), id='validation-required-keyword-only'),
        pytest.param({'validation': _pure_kwargs}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_pure_kwargs'), id='validation-pure-kwargs'),
        pytest.param({'validation': _overfilled_partial}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, 'functools.partial(_bad_partial_base, 1)'), id='validation-overfilled-partial'),
        pytest.param({'validation': next}, _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '<built-in function next>'), id='validation-rejected-builtin'),
        pytest.param({'validation': {'some message': _zero_arg_callback}}, _callback_signature_message("validation['some message']", VALIDATION_CALL_DESCRIPTION, '_zero_arg_callback'), id='dict-validation-first-bad'),
        pytest.param({'validation': {'some message': _one_arg, 'some another message': _zero_arg_callback}}, _callback_signature_message("validation['some another message']", VALIDATION_CALL_DESCRIPTION, '_zero_arg_callback'), id='dict-validation-second-bad'),
        pytest.param({'conflicts': {'another_field': _zero_arg_callback}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '_zero_arg_callback'), id='conflict-no-args'),
        pytest.param({'conflicts': {'another_field': _one_arg}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '_one_arg'), id='conflict-one-required-arg'),
        pytest.param({'conflicts': {'another_field': _two_arg_callback}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '_two_arg_callback'), id='conflict-two-required-args'),
        pytest.param({'conflicts': {'another_field': _three_arg_callback}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '_three_arg_callback'), id='conflict-three-required-args'),
        pytest.param({'conflicts': {'another_field': _five_arg_callback}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '_five_arg_callback'), id='conflict-five-required-args'),
        pytest.param({'conflicts': {'another_field': _pure_kwargs}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '_pure_kwargs'), id='conflict-pure-kwargs'),
        pytest.param({'conflicts': {'another_field': 123}}, _callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, '123'), id='conflict-non-callable'),
        pytest.param({'conversion': _zero_arg_callback}, _callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, '_zero_arg_callback'), id='conversion-no-args'),
        pytest.param({'conversion': _two_arg_callback}, _callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, '_two_arg_callback'), id='conversion-two-required-args'),
        pytest.param({'conversion': _three_arg_callback}, _callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, '_three_arg_callback'), id='conversion-three-required-args'),
        pytest.param({'conversion': _pure_kwargs}, _callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, '_pure_kwargs'), id='conversion-pure-kwargs'),
        pytest.param({'conversion': 123}, _callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, '123'), id='conversion-non-callable'),
        pytest.param({'conversion': int}, _callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, 'int'), id='conversion-uninspectable-int'),
        pytest.param({'action': _zero_arg_callback}, _callback_signature_message('action', ACTION_CALL_DESCRIPTION, '_zero_arg_callback'), id='action-no-args'),
        pytest.param({'action': _one_arg}, _callback_signature_message('action', ACTION_CALL_DESCRIPTION, '_one_arg'), id='action-one-required-arg'),
        pytest.param({'action': _two_arg_callback}, _callback_signature_message('action', ACTION_CALL_DESCRIPTION, '_two_arg_callback'), id='action-two-required-args'),
        pytest.param({'action': _four_arg_callback}, _callback_signature_message('action', ACTION_CALL_DESCRIPTION, '_four_arg_callback'), id='action-four-required-args'),
        pytest.param({'action': _pure_kwargs}, _callback_signature_message('action', ACTION_CALL_DESCRIPTION, '_pure_kwargs'), id='action-pure-kwargs'),
        pytest.param({'action': 123}, _callback_signature_message('action', ACTION_CALL_DESCRIPTION, '123'), id='action-non-callable'),
    ],
)
def test_wrong_callback_signatures(field_kwargs, expected_message):
    with pytest.raises(SignatureMismatchError, match=match(expected_message)):
        _field_for_signature_check(**field_kwargs)


def test_callback_signature_error_preserves_sigmatch_exception_cause():
    with pytest.raises(SignatureMismatchError) as exc_info:
        Field(validation=_two_arg_callback)

    assert isinstance(exc_info.value.__cause__, SignatureMismatchError)
    assert str(exc_info.value.__cause__)


def test_callback_signature_error_handles_broken_callback_repr():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, "<BadCallableRepr's object>"))):
        Field(validation=BadCallableRepr())


def test_callback_signature_error_handles_broken_action_callback_repr():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('action', ACTION_CALL_DESCRIPTION, "<BadCallableRepr's object>"))):
        Field(123, action=BadCallableRepr())


def test_callback_signature_error_handles_broken_conflict_callback_repr():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message("conflicts['another_field']", CONFLICT_CALL_DESCRIPTION, "<BadCallableRepr's object>"))):
        Field(123, conflicts={'another_field': BadCallableRepr()})


def test_callback_signature_error_handles_broken_conversion_callback_repr():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('conversion', CONVERSION_CALL_DESCRIPTION, "<BadCallableRepr's object>"))):
        Field(123, conversion=BadCallableRepr())


def test_callback_signature_error_uses_named_function_representation():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_bad_named_validator'))):
        Field(validation=_bad_named_validator)


def test_callback_signature_error_uses_generator_function_name():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_bad_generator_validator'))):
        Field(validation=_bad_generator_validator)


def test_callback_signature_error_uses_async_function_name():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_bad_async_validator'))):
        Field(validation=_bad_async_validator)


def test_callback_signature_error_uses_class_name():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, 'BadClassValidator'))):
        Field(validation=BadClassValidator)


def test_callback_signature_error_handles_broken_class_name():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, "<class 'tests.units.test_storage.BadClassNameValidator'>"))):
        Field(validation=BadClassNameValidator)


def test_callback_signature_error_uses_lambda_source():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, 'lambda value, extra: False'))):
        Field(validation=lambda value, extra: False)  # noqa: ARG005


def test_callback_signature_error_uses_lambda_symbol_when_source_is_unavailable():
    callback = FunctionType((lambda value, extra: False).__code__.replace(co_filename='<unavailable callback source>'), {})  # noqa: ARG005

    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, 'λ'))):
        Field(validation=callback)


def test_callback_signature_error_handles_broken_callable_metadata():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '<bad callable metadata>'))):
        Field(validation=BadCallableMetadata())


def test_callback_signature_error_handles_none_callable_metadata():
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '<callable none metadata>'))):
        Field(validation=CallableNoneMetadata())


@pytest.mark.parametrize(
    ('field_kwargs', 'expected_message'),
    [
        ({'validation': {BadKeyRepr(): _zero_arg_callback}}, _callback_signature_message('validation[<unrepresentable BadKeyRepr: ValueError>]', VALIDATION_CALL_DESCRIPTION, '_zero_arg_callback')),
        ({'conflicts': {BadKeyRepr(): _zero_arg_callback}}, _callback_signature_message('conflicts[<unrepresentable BadKeyRepr: ValueError>]', CONFLICT_CALL_DESCRIPTION, '_zero_arg_callback')),
    ],
)
def test_callback_signature_error_does_not_call_dict_key_repr(field_kwargs, expected_message):
    with pytest.raises(SignatureMismatchError, match=match(expected_message)):
        _field_for_signature_check(**field_kwargs)


def test_callback_signature_error_truncates_long_dict_key_repr():
    expected_key = f'<{"x" * 196}...'
    expected_message = _callback_signature_message(f'validation[{expected_key}]', VALIDATION_CALL_DESCRIPTION, '_zero_arg_callback')

    with pytest.raises(SignatureMismatchError, match=match(expected_message)):
        Field(123, validation={LongBadCallableRepr(): _zero_arg_callback})


def test_callback_signature_error_keeps_long_callback_repr_from_superrepr():
    expected_representation = f'<{"x" * 300}>'
    with pytest.raises(SignatureMismatchError, match=match(_callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, expected_representation))):
        Field(validation=LongBadCallableRepr())


def test_callback_signature_error_handles_false_matcher_result(monkeypatch):
    callback = _one_arg
    original_match = PossibleCallMatcher.match

    def fake_match(self, checked_callback, raise_exception=False):
        if checked_callback is callback:
            return False
        return original_match(self, checked_callback, raise_exception=raise_exception)

    monkeypatch.setattr(PossibleCallMatcher, 'match', fake_match)

    with pytest.raises(SignatureMismatchError) as exc_info:
        Field(validation=callback)

    assert str(exc_info.value) == _callback_signature_message('validation', VALIDATION_CALL_DESCRIPTION, '_one_arg')


def _one_arg_with_default(value, extra=False):
    return bool(value) or extra


def _one_arg_with_optional_keyword(value, *, extra=False):
    return bool(value) or extra


def _one_positional_only(value, /):
    return bool(value)


def _three_args(old_value, new_value, storage):
    return old_value != new_value and storage is not None


def _four_args(old_value, new_value, other_old, other_new):
    return old_value != new_value and other_old != other_new


def _variadic(*args):
    return bool(args)


def _variadic_with_kwargs(*args, **kwargs):
    return bool(args) or bool(kwargs)


class OneArgCallable:
    def __call__(self, value):
        return bool(value)


class CallbackMethods:
    def one(self, value):
        return bool(value)

    def three(self, old_value, new_value, storage):
        return old_value != new_value and storage is not None

    def four(self, old_value, new_value, other_old, other_new):
        return old_value != new_value and other_old != other_new


@pytest.mark.parametrize(
    'field_kwargs',
    [
        pytest.param({'default_factory': lambda: 1}, id='default_factory-no-args'),
        pytest.param({'default_factory': list}, id='default_factory-accepted-builtin-list'),
        pytest.param({'validation': _one_arg}, id='validation-one-arg'),
        pytest.param({'validation': {'some message': _one_arg}}, id='dict-validation-one-arg'),
        pytest.param({'validation': _one_arg_with_default}, id='validation-extra-default'),
        pytest.param({'validation': _one_arg_with_optional_keyword}, id='validation-optional-keyword-only'),
        pytest.param({'validation': _one_positional_only}, id='validation-positional-only'),
        pytest.param({'validation': _variadic}, id='validation-variadic'),
        pytest.param({'validation': _variadic_with_kwargs}, id='validation-variadic-with-kwargs'),
        pytest.param({'validation': OneArgCallable()}, id='validation-callable-instance'),
        pytest.param({'validation': CallbackMethods().one}, id='validation-bound-method'),
        pytest.param({'validation': partial(lambda expected, value: value == expected, 123)}, id='validation-partial-one-open-arg'),
        pytest.param({'validation': len}, id='validation-accepted-builtin-len'),
        pytest.param({'conversion': _one_arg}, id='conversion-one-arg'),
        pytest.param({'conversion': list}, id='conversion-accepted-builtin-list'),
        pytest.param({'action': _three_args}, id='action-three-args'),
        pytest.param({'action': _variadic}, id='action-variadic'),
        pytest.param({'action': CallbackMethods().three}, id='action-bound-method'),
        pytest.param({'conflicts': {'another_field': _four_args}}, id='conflict-four-args'),
        pytest.param({'conflicts': {'another_field': _variadic}}, id='conflict-variadic'),
        pytest.param({'conflicts': {'another_field': CallbackMethods().four}}, id='conflict-bound-method'),
    ],
)
def test_valid_callback_signatures_are_accepted(field_kwargs):
    _field_for_signature_check(**field_kwargs)


def test_standalone_field_signature_checks_do_not_call_callback_bodies():
    def fail(*args, **kwargs):
        raise AssertionError((args, kwargs))

    Field(1, validation=fail)
    Field(1, conversion=fail)
    Field(1, action=fail)
    Field(1, conflicts={'other': fail})


def test_literal_default_validation_and_conversion_timing():
    events = []

    def validation(value):
        events.append(('validation', value))
        return True

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(1, conversion=conversion, validation=validation)

    assert events == [('validation', 1), ('conversion', 1), ('validation', 2)]
    assert SomeClass().field == 2


def test_default_factory_validation_and_conversion_timing():
    events = []

    def factory():
        events.append(('factory', None))
        return 1

    def validation(value):
        events.append(('validation', value))
        return True

    def conversion(value):
        events.append(('conversion', value))
        return value + 1

    class SomeClass(Storage):
        field: int = Field(default_factory=factory, conversion=conversion, validation=validation)

    assert events == []
    assert SomeClass().field == 2
    assert events == [('factory', None), ('validation', 1), ('conversion', 1), ('validation', 2)]


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_basic(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))

    assert instance.field == 42


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_override_class_sources(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1})]):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 2})]))

    assert instance.field == 2


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_override_field_sources(collection_type):
    class SomeClass(Storage):
        field: int = Field(100, sources=[MemorySource({'field': 1})])

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 2})]))

    assert instance.field == 2


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_override_both_class_and_field_sources(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1, 'other': 10})]):
        field: int = Field(100, sources=[MemorySource({'field': 3})])
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 5, 'other': 50})]))

    assert instance.field == 5
    assert instance.other == 50


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_without_ellipsis_ignores_class_and_field(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1, 'other': 10})]):
        field: int = Field(100, sources=[MemorySource({'field': 3})])
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 5})]))

    assert instance.field == 5
    assert instance.other == 200


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_fallback_to_default(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))

    assert instance.field == 42
    assert instance.other == 200


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_ellipsis_only(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1})]):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([...]))

    assert instance.field == 1


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_ellipsis_only_with_field_sources(collection_type):
    class SomeClass(Storage):
        field: int = Field(100, sources=[MemorySource({'field': 7})])

    instance = SomeClass(_sources=collection_type([...]))

    assert instance.field == 7


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_ellipsis_priority_over_class(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1, 'other': 10})]):
        field: int = Field(100)
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 2}), ...]))

    assert instance.field == 2
    assert instance.other == 10


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_ellipsis_priority_over_field(collection_type):
    class SomeClass(Storage):
        field: int = Field(100, sources=[MemorySource({'field': 7})])

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 2}), ...]))

    assert instance.field == 2


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_ellipsis_falls_through_to_field(collection_type):
    class SomeClass(Storage):
        field: int = Field(100, sources=[MemorySource({'field': 7})])
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([MemorySource({'other': 50}), ...]))

    assert instance.field == 7
    assert instance.other == 50


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_full_three_tier_chain(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'class_field': 30})]):
        instance_field: int = Field(100)
        field_field: int = Field(200, sources=[MemorySource({'field_field': 20}), ...])
        class_field: int = Field(300)

    instance = SomeClass(_sources=collection_type([MemorySource({'instance_field': 10}), ...]))

    assert instance.instance_field == 10
    assert instance.field_field == 20
    assert instance.class_field == 30


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_ellipsis_field_without_ellipsis(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1, 'other': 10})]):
        field: int = Field(100, sources=[MemorySource({'field': 7})])
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([MemorySource({'other': 50}), ...]))

    assert instance.field == 7
    assert instance.other == 50


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_multiple_sources_ordering(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 1}), MemorySource({'field': 2})]))

    assert instance.field == 1


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_kwargs_override(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]), field=99)

    assert instance.field == 99


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_runtime_assignment_overrides(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))
    instance.field = 99

    assert instance.field == 99


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_value_resolution_order(collection_type):
    class SomeClass(Storage):
        from_source: int = Field(100)
        from_factory: int = Field(default_factory=lambda: 200)
        from_default: int = Field(300)

    instance = SomeClass(_sources=collection_type([MemorySource({'from_source': 1})]))

    assert instance.from_source == 1
    assert instance.from_factory == 200
    assert instance.from_default == 300


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_empty_collection(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 1})]):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([]))

    assert instance.field == 100


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_type_check(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError):
        SomeClass(_sources=collection_type([MemorySource({'field': 'not_an_int'})]))


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_validation(collection_type):
    class SomeClass(Storage):
        field: int = Field(100, validation=lambda x: x > 0)

    with pytest.raises(ValueError, match='does not match the validation'):
        SomeClass(_sources=collection_type([MemorySource({'field': -5})]))


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_conflicts(collection_type):
    class SomeClass(Storage):
        a: int = Field(default_factory=lambda: 100, conflicts={'b': lambda old, new, other_old, other_new: new > other_old})  # noqa: ARG005
        b: int = Field(10)

    with pytest.raises(ValueError, match='conflicts with'):
        SomeClass(_sources=collection_type([MemorySource({'a': 100})]))


def test_instance_sources_invalid_type_dict():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('_sources must be a list or a tuple.')):
        SomeClass(_sources={'field': 1})


def test_instance_sources_invalid_type_int():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('_sources must be a list or a tuple.')):
        SomeClass(_sources=42)


def test_instance_sources_invalid_type_string():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('_sources must be a list or a tuple.')):
        SomeClass(_sources='bad')


def test_instance_sources_invalid_element():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('Each element of _sources must be a source or Ellipsis, got int.')):
        SomeClass(_sources=[42])


def test_instance_sources_invalid_element_string():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('Each element of _sources must be a source or Ellipsis, got str.')):
        SomeClass(_sources=['bad'])


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_alias(collection_type):
    class SomeClass(Storage):
        my_field: int = Field(100, alias='custom_key')

    instance = SomeClass(_sources=collection_type([MemorySource({'custom_key': 42})]))

    assert instance.my_field == 42


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_alias_and_ellipsis(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'other_key': 10})]):
        my_field: int = Field(100, alias='custom_key')
        other_field: int = Field(200, alias='other_key')

    instance = SomeClass(_sources=collection_type([MemorySource({'custom_key': 42}), ...]))

    assert instance.my_field == 42
    assert instance.other_field == 10


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_conversion(collection_type):
    class SomeClass(Storage):
        field: int = Field(10, conversion=lambda x: x * 2)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 15})]))

    assert instance.field == 30


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_inheritance(collection_type):
    class ParentClass(Storage):
        parent_field: int = Field(100)

    class ChildClass(ParentClass):
        child_field: int = Field(200)

    instance = ChildClass(_sources=collection_type([MemorySource({'parent_field': 1, 'child_field': 2})]))

    assert instance.parent_field == 1
    assert instance.child_field == 2


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_inheritance_and_ellipsis(collection_type):
    class ParentClass(Storage):
        parent_field: int = Field(100)

    class ChildClass(ParentClass, sources=[MemorySource({'parent_field': 10})]):
        child_field: int = Field(200)

    instance = ChildClass(_sources=collection_type([MemorySource({'child_field': 2}), ...]))

    assert instance.parent_field == 10
    assert instance.child_field == 2


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_no_default_and_missing_key(collection_type):
    class SomeClass(Storage):
        field: int = Field()

    with pytest.raises(ValueError, match=match('The value for the "field" field is undefined. Set the default value, or specify the value when creating the instance.')):
        SomeClass(_sources=collection_type([MemorySource({'other': 1})]))


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_no_default_but_key_present(collection_type):
    class SomeClass(Storage):
        field: int = Field()

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))

    assert instance.field == 42


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_repr(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)
        secret_field: int = Field(200, secret=True)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42, 'secret_field': 99})]))

    assert repr(instance) == 'SomeClass(field=42, secret_field=***)'


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_read_only(collection_type):
    class SomeClass(Storage):
        field: int = Field(100, read_only=True)

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))

    assert instance.field == 42

    with pytest.raises(AttributeError, match=match('"field" field is read-only.')):
        instance.field = 99


def test_instance_sources_explicit_none():
    """Passing _sources=None explicitly is equivalent to not passing it at all."""
    class SomeClass(Storage):
        field: int = Field(100)

    instance = SomeClass(_sources=None)
    assert instance.field == 100


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_ellipsis_does_not_reach_class_when_field_has_no_ellipsis(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 99})]):
        field: int = Field(100, sources=[MemorySource({'other': 1})])

    instance = SomeClass(_sources=collection_type([MemorySource({'other': 2}), ...]))

    assert instance.field == 100


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_multiple_ellipses(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 10})]):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([..., ...]))

    assert instance.field == 10


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_ellipsis_not_at_end(collection_type):
    class SomeClass(Storage, sources=[MemorySource({'field': 10, 'other': 20})]):
        field: int = Field(100)
        other: int = Field(200)

    instance = SomeClass(_sources=collection_type([..., MemorySource({'field': 42})]))

    assert instance.field == 42
    assert instance.other == 20


@pytest.mark.parametrize(
    'data',
    [
        {'field': 77},
    ],
)
@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_with_json_source(collection_type, json_config_path):
    class SomeClass(Storage):
        field: int = Field(100)

    instance = SomeClass(_sources=collection_type([JSONSource(json_config_path)]))

    assert instance.field == 77


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_isolation_between_instances(collection_type):
    class SomeClass(Storage):
        field: int = Field(100)

    first = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))
    second = SomeClass()

    assert first.field == 42
    assert second.field == 100


def test_instance_sources_invalid_type_set():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('_sources must be a list or a tuple.')):
        SomeClass(_sources={MemorySource({'field': 1})})


def test_instance_sources_invalid_type_frozenset():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('_sources must be a list or a tuple.')):
        SomeClass(_sources=frozenset([]))


def test_instance_sources_invalid_type_generator():
    class SomeClass(Storage):
        field: int = Field(100)

    with pytest.raises(TypeError, match=match('_sources must be a list or a tuple.')):
        SomeClass(_sources=(x for x in [MemorySource({'field': 1})]))


@pytest.mark.parametrize('collection_type', [list, tuple])
def test_instance_sources_change_action_not_called(collection_type):
    calls = []

    class SomeClass(Storage):
        field: int = Field(100, action=lambda old, new, storage: calls.append((old, new)))  # noqa: ARG005

    instance = SomeClass(_sources=collection_type([MemorySource({'field': 42})]))

    assert instance.field == 42
    assert calls == []
