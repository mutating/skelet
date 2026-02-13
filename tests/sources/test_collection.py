from typing import List

import pytest
from full_match import match

from skelet import JSONSource, MemorySource, TOMLSource
from skelet.sources.collection import SourcesCollection


def test_there_is_no_that_key():
    with pytest.raises(KeyError):
        SourcesCollection([MemorySource({}), MemorySource({}), MemorySource({})])['key']


def test_there_is_no_that_key_and_use_get_method():
    assert SourcesCollection([MemorySource({}), MemorySource({}), MemorySource({})]).get('key') is None
    assert SourcesCollection([MemorySource({}), MemorySource({}), MemorySource({})]).get('key', 'value') == 'value'


@pytest.mark.parametrize(
    'sources',
    [
        [{'key': 'value'}, {}, {}],
        [{}, {'key': 'value'}, {}],
        [{}, {}, {'key': 'value'}],
    ],
)
def test_there_is_key_in_one_source(sources):
    assert SourcesCollection(sources)['key'] == 'value'
    assert SourcesCollection(sources).get('key') == 'value'
    assert SourcesCollection(sources).get('key', 'another_value') == 'value'


@pytest.mark.parametrize(
    'sources',
    [
        [{'key': 'value'}, {}, {}, {'key': 'second_value'}],
        [{}, {'key': 'value'}, {}, {'key': 'second_value'}],
        [{}, {}, {'key': 'value'}, {'key': 'second_value'}],
    ],
)
def test_shading_sources(sources):
    assert SourcesCollection(sources)['key'] == 'value'
    assert SourcesCollection(sources).get('key') == 'value'
    assert SourcesCollection(sources).get('key', 'another_value') == 'value'


def test_simple_proxy():
    assert SourcesCollection([{'lol': 'kek'}])['lol'] == 'kek'

    with pytest.raises(KeyError):
        SourcesCollection([{'lol': 'kek'}])['kek']


def test_repr():
    assert repr(SourcesCollection([TOMLSource('kek.toml')])) == "SourcesCollection([TOMLSource('kek.toml')])"
    assert repr(SourcesCollection([TOMLSource('kek.toml'), JSONSource('lol.json')])) == "SourcesCollection([TOMLSource('kek.toml'), JSONSource('lol.json')])"


def test_type_awared_get():
    assert SourcesCollection([MemorySource({'key': 'kek'})]).type_awared_get('key', str) == 'kek'
    assert SourcesCollection([MemorySource({}), MemorySource({'key': 'kek'})]).type_awared_get('key', str) == 'kek'
    assert SourcesCollection([MemorySource({}), MemorySource({'key': 'kek'}), MemorySource({})]).type_awared_get('key', str) == 'kek'
    assert SourcesCollection([MemorySource({'key': 123})]).type_awared_get('key', int) == 123
    assert SourcesCollection([MemorySource({'key': [123, 456]})]).type_awared_get('key', List[int]) == [123, 456]
    assert SourcesCollection([MemorySource({'key': [123, 456]})]).type_awared_get('key', List) == [123, 456]
    assert SourcesCollection([MemorySource({'key': [123, 456]})]).type_awared_get('key', list) == [123, 456]

    assert SourcesCollection([MemorySource({}), MemorySource({'key': 'kek'}), MemorySource({})]).type_awared_get('key2', str, default='lol') == 'lol'

    with pytest.raises(TypeError, match=match('The value of the "key" field did not pass the type check.')):
        SourcesCollection([MemorySource({'key': 123})]).type_awared_get('key', str)

    with pytest.raises(TypeError, match=match('The value of the "key" field did not pass the type check.')):
        SourcesCollection([MemorySource({'key': '123'})]).type_awared_get('key', int)

    with pytest.raises(TypeError, match=match('The value of the "key" field did not pass the type check.')):
        SourcesCollection([MemorySource({'key': [123, 456]})]).type_awared_get('key', List[str])

    with pytest.raises(TypeError, match=match('The value of the "key" field did not pass the type check.')):
        SourcesCollection([MemorySource({'key': ['123', '456']})]).type_awared_get('key', List[int])

    assert SourcesCollection([MemorySource({'key': 'kek'})]).type_awared_get('key2', str) is None
    assert SourcesCollection([MemorySource({'key': 'kek'}), MemorySource({})]).type_awared_get('key2', str) is None
    assert SourcesCollection([MemorySource({}), MemorySource({'key': 'kek'}), MemorySource({})]).type_awared_get('key2', str) is None
    assert SourcesCollection([MemorySource({}), MemorySource({'key': 'kek'}), MemorySource({})]).type_awared_get('key2', str, default='kek') == 'kek'
    assert SourcesCollection([MemorySource({}), MemorySource({'key': 'kek'}), MemorySource({})]).type_awared_get('key2', str, default=1) == 1
