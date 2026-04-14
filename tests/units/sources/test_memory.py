from typing import List

import pytest
from full_match import match

from skelet import MemorySource


def test_read_simple_values():
    source = MemorySource(
        {
            'int_top_value': 1,
            'str_top_value': 'lol',
            'list_top_value': ['lol', 'kek'],
            'float_top_value': 1.5,
            'bool_top_value': True,
            'dict_top_value': {'another_bool_top_value': True},
        },
    )

    assert source['int_top_value'] == 1
    assert source['str_top_value'] == 'lol'
    assert source['list_top_value'] == ['lol', 'kek']
    assert source['float_top_value'] == 1.5
    assert source['bool_top_value'] == True
    assert source['dict_top_value']['another_bool_top_value'] == True


def test_read_empty_value():
    source = MemorySource({})

    with pytest.raises(KeyError):
        source['some_top_value']


def test_defaults_for_libraries():
    assert MemorySource.for_library('library') == []


def test_defaults_for_not_allowed_library_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        MemorySource.for_library(':library')


def test_repr():
    assert repr(MemorySource({})) == "MemorySource({})"
    assert repr(MemorySource({'lol': 'kek'})) == "MemorySource({'lol': 'kek'})"


def test_type_awared_get():
    source = MemorySource(
        {
            'string': 'kek',
            'number': 123,
            'list_with_numbers': [123, 456],
            'list_with_strings': ['123', '456'],
        },
    )

    assert source.type_awared_get('string', str) == 'kek'
    assert source.type_awared_get('number', int) == 123
    assert source.type_awared_get('list_with_numbers', List[int]) == [123, 456]
    assert source.type_awared_get('list_with_numbers', List) == [123, 456]
    assert source.type_awared_get('list_with_numbers', list) == [123, 456]

    with pytest.raises(TypeError, match=match('The value of the "number" field did not pass the type check.')):
        source.type_awared_get('number', str)

    with pytest.raises(TypeError, match=match('The value of the "string" field did not pass the type check.')):
        source.type_awared_get('string', int)

    with pytest.raises(TypeError, match=match('The value of the "list_with_numbers" field did not pass the type check.')):
        source.type_awared_get('list_with_numbers', List[str])

    with pytest.raises(TypeError, match=match('The value of the "list_with_strings" field did not pass the type check.')):
        source.type_awared_get('list_with_strings', List[int])

    assert source.type_awared_get('key2', str) is None
    assert source.type_awared_get('key2', str, default='kek') == 'kek'
