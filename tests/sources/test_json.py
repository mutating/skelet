import pytest
from full_match import match

from skelet import JSONSource


@pytest.mark.parametrize(
    ['data'],
    [
        ({
            'int_top_value': 1,
            'str_top_value': 'lol',
            'list_top_value': ['lol', 'kek'],
            'float_top_value': 1.5,
            'bool_top_value': True,
            'dict_top_value': {'another_bool_top_value': True},
        },),
    ],
)
def test_read_simple_values_from_top_level(json_config_path):
    source = JSONSource(json_config_path)

    assert source['int_top_value'] == 1
    assert source['str_top_value'] == 'lol'
    assert source['list_top_value'] == ['lol', 'kek']
    assert source['float_top_value'] == 1.5
    assert source['bool_top_value'] == True
    assert source['dict_top_value']['another_bool_top_value'] == True


@pytest.mark.parametrize(
    ['data'],
    [
        ({},),
    ],
)
def test_read_empty_value_from_top_level_table(json_config_path):
    source = JSONSource(json_config_path)

    with pytest.raises(KeyError):
        source['some_top_value']


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'allow_non_existent_files': True},),
    ],
)
def test_non_existing_files_are_allowed(addictional_parameters):
    source = JSONSource('non_existing_path.json', **addictional_parameters)

    with pytest.raises(KeyError):
        source['some_top_value']


def test_non_existing_files_are_not_allowed():
    source = JSONSource('non_existing_path.json', allow_non_existent_files=False)

    with pytest.raises(FileNotFoundError):
        source['some_top_value']


def test_defaults_for_libraries():
    sources = JSONSource.for_library('library')

    assert len(sources) == 2

    assert sources[0].path == 'library.json'
    assert sources[0].allow_non_existent_files == True

    assert sources[1].path == '.library.json'
    assert sources[1].allow_non_existent_files == True


def test_defaults_for_not_allowed_library_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        JSONSource.for_library(':library')


def test_repr():
    assert repr(JSONSource('file.json')) == "JSONSource('file.json')"
    assert repr(JSONSource('file.json', allow_non_existent_files=False)) == "JSONSource('file.json', allow_non_existent_files=False)"
    assert repr(JSONSource('file.json', allow_non_existent_files=True)) == "JSONSource('file.json')"
