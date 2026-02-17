from typing import List

import pytest
from full_match import match

from skelet import TOMLSource


@pytest.mark.parametrize(
    'data',
    [
        {'int_top_value': 1, 'str_top_value': 'lol', 'list_top_value': ['lol', 'kek'], 'float_top_value': 1.5, 'bool_top_value': True, 'dict_top_value': {'another_bool_top_value': True}},
    ],
)
def test_read_simple_values_from_top_level_table(toml_config_path):
    source = TOMLSource(toml_config_path)

    assert source['int_top_value'] == 1
    assert source['str_top_value'] == 'lol'
    assert source['list_top_value'] == ['lol', 'kek']
    assert source['float_top_value'] == 1.5
    assert source['bool_top_value'] == True
    assert source['dict_top_value']['another_bool_top_value'] == True


@pytest.mark.parametrize(
    'data',
    [
        {},
    ],
)
def test_read_empty_value_from_top_level_table(toml_config_path):
    source = TOMLSource(toml_config_path)

    with pytest.raises(KeyError):
        source['some_top_value']


@pytest.mark.parametrize(
    'data',
    [
        {'table': {'value': 1}},
    ],
)
@pytest.mark.parametrize(
    'table_name',
    [
        [],
        ['table'],
        'table',
        'kek',
    ],
)
def test_read_empty_value_from_nested_level_table(toml_config_path, table_name):
    source = TOMLSource(toml_config_path, table=table_name)

    with pytest.raises(KeyError):
        source['non_existent_value']


@pytest.mark.parametrize(
    'data',
    [
        {'int_top_value': 1, 'str_top_value': 'lol', 'table': {'int_value': 3, 'str_value': 'kek', 'another_table': {'int_value': 15, 'str_value': 'cheburek'}}},
    ],
)
def test_read_simple_values_from_users_table_written_as_string(toml_config_path):
    source = TOMLSource(toml_config_path, table='table')

    assert source['int_value'] == 3
    assert source['str_value'] == 'kek'

    source = TOMLSource(toml_config_path, table='table.another_table')

    assert source['int_value'] == 15
    assert source['str_value'] == 'cheburek'


@pytest.mark.parametrize(
    'data',
    [
        {'int_top_value': 1, 'str_top_value': 'lol', 'table': {'int_value': 3, 'str_value': 'kek', 'another_table': {'int_value': 15, 'str_value': 'cheburek', 'third_table': {'int_value': 25, 'str_value': 'super_cheburek'}}}},
    ],
)
def test_read_simple_values_from_users_table_written_as_list(toml_config_path):
    source = TOMLSource(toml_config_path, table=['table'])

    assert source['int_value'] == 3
    assert source['str_value'] == 'kek'

    source = TOMLSource(toml_config_path, table=['table', 'another_table'])

    assert source['int_value'] == 15
    assert source['str_value'] == 'cheburek'

    source = TOMLSource(toml_config_path, table=['table.another_table'])

    assert source['int_value'] == 15
    assert source['str_value'] == 'cheburek'

    source = TOMLSource(toml_config_path, table=['table', 'another_table.third_table'])

    assert source['int_value'] == 25
    assert source['str_value'] == 'super_cheburek'

    source = TOMLSource(toml_config_path, table=['table.another_table', 'third_table'])

    assert source['int_value'] == 25
    assert source['str_value'] == 'super_cheburek'


@pytest.mark.parametrize(
    'data',
    [
        {},
    ],
)
@pytest.mark.parametrize(
    'wrong_table',
    [
        ':kek',
        [':kek'],
        [':kek', 'lol'],
        ['lol', ':kek'],
        ['lol.:kek'],
    ],
)
def test_non_python_identifier_as_string(toml_config_path, wrong_table):
    with pytest.raises(ValueError, match=match('You can only use a subset of all valid TOML format identifiers that can be used as a Python identifier. You used ":kek".')):
        TOMLSource(toml_config_path, table=wrong_table)


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'allow_non_existent_files': True},
    ],
)
def test_non_existing_files_are_allowed(addictional_parameters):
    source = TOMLSource('non_existing_path.toml', **addictional_parameters)

    with pytest.raises(KeyError):
        source['some_top_value']


def test_non_existing_files_are_not_allowed():
    source = TOMLSource('non_existing_path.toml', allow_non_existent_files=False)

    with pytest.raises(FileNotFoundError):
        source['some_top_value']


def test_defaults_for_libraries():
    sources = TOMLSource.for_library('library')

    assert len(sources) == 3

    assert sources[0].path == 'library.toml'
    assert sources[0].table == []
    assert sources[0].allow_non_existent_files == True

    assert sources[1].path == '.library.toml'
    assert sources[1].table == []
    assert sources[1].allow_non_existent_files == True

    assert sources[2].path == 'pyproject.toml'
    assert sources[2].table == ['tool', 'library']
    assert sources[2].allow_non_existent_files == True


def test_defaults_for_not_allowed_library_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        TOMLSource.for_library(':library')


def test_repr():
    assert repr(TOMLSource('file.toml')) == "TOMLSource('file.toml')"
    assert repr(TOMLSource('file.toml', allow_non_existent_files=False)) == "TOMLSource('file.toml', allow_non_existent_files=False)"
    assert repr(TOMLSource('file.toml', allow_non_existent_files=True)) == "TOMLSource('file.toml')"
    assert repr(TOMLSource('file.toml', table='lol.kek')) == "TOMLSource('file.toml', table=['lol', 'kek'])"
    assert repr(TOMLSource('file.toml', table=['lol', 'kek'])) == "TOMLSource('file.toml', table=['lol', 'kek'])"
    assert repr(TOMLSource('file.toml', table=['lol', 'kek'], allow_non_existent_files=False)) == "TOMLSource('file.toml', table=['lol', 'kek'], allow_non_existent_files=False)"


@pytest.mark.parametrize(
    'data',
    [
        {'string': 'kek', 'number': 123, 'list_with_numbers': [123, 456], 'list_with_strings': ['123', '456']},
    ],
)
def test_type_awared_get(toml_config_path):
    assert TOMLSource(toml_config_path).type_awared_get('string', str) == 'kek'
    assert TOMLSource(toml_config_path).type_awared_get('number', int) == 123
    assert TOMLSource(toml_config_path).type_awared_get('list_with_numbers', List[int]) == [123, 456]
    assert TOMLSource(toml_config_path).type_awared_get('list_with_numbers', List) == [123, 456]
    assert TOMLSource(toml_config_path).type_awared_get('list_with_numbers', list) == [123, 456]

    with pytest.raises(TypeError, match=match('The value of the "number" field did not pass the type check.')):
        TOMLSource(toml_config_path).type_awared_get('number', str)

    with pytest.raises(TypeError, match=match('The value of the "string" field did not pass the type check.')):
        TOMLSource(toml_config_path).type_awared_get('string', int)

    with pytest.raises(TypeError, match=match('The value of the "list_with_numbers" field did not pass the type check.')):
        TOMLSource(toml_config_path).type_awared_get('list_with_numbers', List[str])

    with pytest.raises(TypeError, match=match('The value of the "list_with_strings" field did not pass the type check.')):
        TOMLSource(toml_config_path).type_awared_get('list_with_strings', List[int])

    assert TOMLSource(toml_config_path).type_awared_get('key2', str) is None
    assert TOMLSource(toml_config_path).type_awared_get('key2', str, default='kek') == 'kek'
