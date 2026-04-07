from typing import List

import pytest
from full_match import match

from skelet import YAMLSource


@pytest.mark.parametrize(
    'data',
    [
        {'int_top_value': 1, 'str_top_value': 'lol', 'list_top_value': ['lol', 'kek'], 'float_top_value': 1.5, 'bool_top_value': True, 'dict_top_value': {'another_bool_top_value': True}},
    ],
)
def test_read_simple_values_from_top_level(yaml_config_path):
    source = YAMLSource(yaml_config_path)

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
def test_read_empty_value_from_top_level_table(yaml_config_path):
    source = YAMLSource(yaml_config_path)

    with pytest.raises(KeyError):
        source['some_top_value']


@pytest.mark.parametrize(
    'addictional_parameters',
    [
        {},
        {'allow_non_existent_files': True},
    ],
)
def test_non_existing_files_are_allowed(addictional_parameters):
    source = YAMLSource('non_existing_path.json', **addictional_parameters)

    with pytest.raises(KeyError):
        source['some_top_value']


def test_non_existing_files_are_not_allowed():
    source = YAMLSource('non_existing_path.json', allow_non_existent_files=False)

    with pytest.raises(FileNotFoundError):
        source['some_top_value']


def test_defaults_for_libraries():
    sources = YAMLSource.for_library('library')

    assert len(sources) == 2

    assert sources[0].path == 'library.yaml'
    assert sources[0].allow_non_existent_files == True

    assert sources[1].path == '.library.yaml'
    assert sources[1].allow_non_existent_files == True


def test_defaults_for_not_allowed_library_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        YAMLSource.for_library(':library')


def test_repr():
    assert repr(YAMLSource('file.yaml')) == "YAMLSource('file.yaml')"
    assert repr(YAMLSource('file.yaml', allow_non_existent_files=False)) == "YAMLSource('file.yaml', allow_non_existent_files=False)"
    assert repr(YAMLSource('file.yaml', allow_non_existent_files=True)) == "YAMLSource('file.yaml')"


@pytest.mark.parametrize(
    'data',
    [
        {'string': 'kek', 'number': 123, 'list_with_numbers': [123, 456], 'list_with_strings': ['123', '456']},
    ],
)
def test_type_awared_get(yaml_config_path):
    assert YAMLSource(yaml_config_path).type_awared_get('string', str) == 'kek'
    assert YAMLSource(yaml_config_path).type_awared_get('number', int) == 123
    assert YAMLSource(yaml_config_path).type_awared_get('list_with_numbers', List[int]) == [123, 456]
    assert YAMLSource(yaml_config_path).type_awared_get('list_with_numbers', List) == [123, 456]
    assert YAMLSource(yaml_config_path).type_awared_get('list_with_numbers', list) == [123, 456]

    with pytest.raises(TypeError, match=match('The value of the "number" field did not pass the type check.')):
        YAMLSource(yaml_config_path).type_awared_get('number', str)

    with pytest.raises(TypeError, match=match('The value of the "string" field did not pass the type check.')):
        YAMLSource(yaml_config_path).type_awared_get('string', int)

    with pytest.raises(TypeError, match=match('The value of the "list_with_numbers" field did not pass the type check.')):
        YAMLSource(yaml_config_path).type_awared_get('list_with_numbers', List[str])

    with pytest.raises(TypeError, match=match('The value of the "list_with_strings" field did not pass the type check.')):
        YAMLSource(yaml_config_path).type_awared_get('list_with_strings', List[int])

    assert YAMLSource(yaml_config_path).type_awared_get('key2', str) is None
    assert YAMLSource(yaml_config_path).type_awared_get('key2', str, default='kek') == 'kek'
