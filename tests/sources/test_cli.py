from typing import List, Dict

import pytest
from full_match import match

from skelet import FixedCLISource
from skelet.errors import CLIFormatError


def test_repr():
    assert repr(FixedCLISource(named_arguments=['a', 'b', 'c'])) == "FixedCLISource(named_arguments=['a', 'b', 'c'])"
    assert repr(FixedCLISource(position_arguments=['a', 'b', 'c'])) == "FixedCLISource(position_arguments=['a', 'b', 'c'])"
    assert repr(FixedCLISource(position_arguments=['a', 'b', 'c'], named_arguments=['d', 'f', 'g'])) == "FixedCLISource(position_arguments=['a', 'b', 'c'], named_arguments=['d', 'f', 'g'])"


def test_defaults_for_not_allowed_library_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        FixedCLISource.for_library(':library')


def test_defaults_for_libraries():
    assert FixedCLISource.for_library('library') == []


@pytest.mark.parametrize(
    ['argv'],
    [
        ([],),
        (['--kek'],),
        (['--kek', 'kek'],),
    ],
)
def test_there_is_no_that_key(temp_argv):
    with pytest.raises(KeyError):
        FixedCLISource(named_arguments=['kek'])['lol']

    assert FixedCLISource(named_arguments=['kek']).type_awared_get('lol', str) is None
    assert FixedCLISource(named_arguments=['kek']).type_awared_get('lol', str, default='kek') == 'kek'
    assert FixedCLISource(named_arguments=['kek']).type_awared_get('lol', str, default=123) == 123

    assert FixedCLISource(named_arguments=['kek']).get('lol') is None
    assert FixedCLISource(named_arguments=['kek']).get('lol', 'kek') == 'kek'


@pytest.mark.parametrize(
    ['argv'],
    [
        (['--lol', '123'],),
    ],
)
def test_read_existing_key(temp_argv):
    assert FixedCLISource(named_arguments=['lol'])['lol'] == '123'
    assert FixedCLISource(named_arguments=['lol']).get('lol') == '123'
    assert FixedCLISource(named_arguments=['lol']).type_awared_get('lol', str) == '123'
    assert FixedCLISource(named_arguments=['lol']).type_awared_get('lol', int) == 123


@pytest.mark.parametrize(
    ['argv'],
    [
        (['--lol-kek', '123'],),
    ],
)
def test_read_existing_key_with_dash(temp_argv):
    assert FixedCLISource(named_arguments=['lol_kek'])['lol_kek'] == '123'
    assert FixedCLISource(named_arguments=['lol_kek']).get('lol_kek') == '123'
    assert FixedCLISource(named_arguments=['lol_kek']).type_awared_get('lol_kek', str) == '123'
    assert FixedCLISource(named_arguments=['lol_kek']).type_awared_get('lol_kek', int) == 123


@pytest.mark.parametrize(
    ['argv'],
    [
        ([
            '--string', 'kek',
            '--number', '1',
            '--float-number', '1.0',
            '--numbers-list', '[1, 2, 3]',
            '--boolean-yes',
            '--strings-list', '["1", "2", "3"]',
            '--strings-dict', '{"lol": "kek"}',
        ],),
    ],
)
def test_type_awared_get(temp_argv):
    field_names = [
        'string',
        'number',
        'float_number',
        'numbers_list',
        'boolean_yes',
        'boolean_no',
        'strings_list',
        'strings_dict',
    ]

    assert FixedCLISource(named_arguments=field_names).type_awared_get("string", str) == 'kek'
    assert FixedCLISource(named_arguments=field_names).type_awared_get("number", str) == '1'
    assert FixedCLISource(named_arguments=field_names).type_awared_get("number", int) == 1
    assert FixedCLISource(named_arguments=field_names).type_awared_get("number", float) == 1.0
    assert FixedCLISource(named_arguments=field_names).type_awared_get("float_number", float) == 1.0
    assert FixedCLISource(named_arguments=field_names).type_awared_get("boolean_yes", bool) == True
    assert FixedCLISource(named_arguments=field_names).type_awared_get("boolean_no", bool) == False
    assert FixedCLISource(named_arguments=field_names).type_awared_get("numbers_list", List[int]) == [1, 2, 3]
    assert FixedCLISource(named_arguments=field_names).type_awared_get("numbers_list", List) == [1, 2, 3]
    assert FixedCLISource(named_arguments=field_names).type_awared_get("numbers_list", list) == [1, 2, 3]
    assert FixedCLISource(named_arguments=field_names).type_awared_get("strings_list", List[str]) == ['1', '2', '3']
    assert FixedCLISource(named_arguments=field_names).type_awared_get("strings_list", List) == ['1', '2', '3']
    assert FixedCLISource(named_arguments=field_names).type_awared_get("strings_list", list) == ['1', '2', '3']
    assert FixedCLISource(named_arguments=field_names).type_awared_get("strings_dict", Dict[str, str]) == {'lol': 'kek'}
    assert FixedCLISource(named_arguments=field_names).type_awared_get("strings_dict", Dict) == {'lol': 'kek'}
    assert FixedCLISource(named_arguments=field_names).type_awared_get("strings_dict", dict) == {'lol': 'kek'}

    with pytest.raises(TypeError, match=match('The string "[1, 2, 3]" cannot be interpreted as a list of the specified format.')):
        FixedCLISource(named_arguments=field_names).type_awared_get("numbers_list", List[str])

    with pytest.raises(TypeError, match=match('The string "["1", "2", "3"]" cannot be interpreted as a list of the specified format.')):
        FixedCLISource(named_arguments=field_names).type_awared_get("strings_list", List[int])

    with pytest.raises(TypeError, match=match('The string "kek" cannot be interpreted as an integer.')):
        FixedCLISource(named_arguments=field_names).type_awared_get("string", int)


def test_pass_not_valid_variable_names():
    with pytest.raises(ValueError, match=match('The "_" parameter is not valid for use on the command line (most likely, it is also not a valid Python name).')):
        FixedCLISource(named_arguments=['_'])

    with pytest.raises(ValueError, match=match('The "lol__kek" parameter is not valid for use on the command line (most likely, it is also not a valid Python name).')):
        FixedCLISource(named_arguments=['lol__kek'])

    with pytest.raises(ValueError, match=match('The "+lol_kek" parameter is not valid for use on the command line (most likely, it is also not a valid Python name).')):
        FixedCLISource(named_arguments=['+lol_kek'])


@pytest.mark.parametrize(
    ['argv'],
    [
        ([
            '-o', 'kek',
        ],),
    ],
)
def test_one_letter_field_name(temp_argv):
    assert FixedCLISource(named_arguments=['o']).get('o') == 'kek'

@pytest.mark.parametrize(
    ['argv'],
    [
        ([
            '--lol', 'kek',
        ],),
    ],
)
def test_bool_variable_with_value(temp_argv):
    with pytest.raises(CLIFormatError, match=match("You can't pass values for boolean fields to the CLI.")):
        FixedCLISource(named_arguments=['lol']).type_awared_get('lol', bool)
