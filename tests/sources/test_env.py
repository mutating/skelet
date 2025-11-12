import os
from typing import List, Dict
import platform

import pytest
from full_match import match

from skelet import EnvSource
from skelet.errors import CaseError


@pytest.mark.parametrize(
    ['addictional_parameters'],
    [
        ({},),
        ({'case_sensitive': True},),
        ({'case_sensitive': False},),
    ],
)
def test_data_is_not_caching_between_instances(addictional_parameters):
    if addictional_parameters.get('case_sensitive', False) and platform.system() == 'Windows':
        return

    first_source = EnvSource(**addictional_parameters)
    second_source = EnvSource(**addictional_parameters)

    assert first_source.data is not second_source.data
    assert first_source.data == second_source.data
    assert first_source.data is not os.environ


def test_cases_conflict(monkeypatch):
    monkeypatch.setenv("lol", "1")
    monkeypatch.setenv("LoL", "2")

    if platform.system() != 'Windows':
        with pytest.raises(CaseError, match=match('There are 2 environment variables that are written the same way when capitalized: "LoL" and "lol".')):
            EnvSource(case_sensitive=False).data

    monkeypatch.setenv("lol", "1")
    monkeypatch.setenv("LoL", "1")

    assert EnvSource(case_sensitive=False)['lol'] == '1'
    assert EnvSource(case_sensitive=False).data['LOL'] == '1'
    assert 'lol' not in EnvSource(case_sensitive=False).data
    assert 'LoL' not in EnvSource(case_sensitive=False).data

    if platform.system() != 'Windows':
        assert EnvSource(case_sensitive=True)['lol'] == '1'
        assert EnvSource(case_sensitive=True)['LoL'] == '1'

        with pytest.raises(KeyError):
            EnvSource(case_sensitive=True)['LOL']
    else:
        assert EnvSource()['LOL'] == '1'
        assert EnvSource()['lol'] == '1'
        assert EnvSource()['lOl'] == '1'
        assert EnvSource()['LoL'] == '1'


def test_repr():
    assert repr(EnvSource()) == "EnvSource()"
    assert repr(EnvSource(prefix='lol')) == "EnvSource(prefix='lol')"
    assert repr(EnvSource(postfix='kek')) == "EnvSource(postfix='kek')"
    assert repr(EnvSource(prefix='lol', postfix='kek')) == "EnvSource(prefix='lol', postfix='kek')"

    if platform.system() != 'Windows':
        assert repr(EnvSource(case_sensitive=True)) == "EnvSource(case_sensitive=True)"
        assert repr(EnvSource(prefix='lol', postfix='kek', case_sensitive=True)) == "EnvSource(prefix='lol', postfix='kek', case_sensitive=True)"


def test_defaults_for_not_allowed_library_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        EnvSource.for_library(':library')


def test_defaults_for_libraries(monkeypatch):
    sources = EnvSource.for_library('library')

    assert len(sources) == 1

    assert sources[0].prefix == 'LIBRARY_'
    assert sources[0].postfix == ''
    assert sources[0].case_sensitive == False

    monkeypatch.setenv("LIBRARY_KEY", "kek")

    assert sources[0]['key'] == 'kek'


def test_there_is_no_that_key(monkeypatch):
    monkeypatch.delenv('lol', raising=False)

    with pytest.raises(KeyError):
        EnvSource()['lol']

    assert EnvSource().type_awared_get('lol', str) is None
    assert EnvSource().type_awared_get('lol', str, default='kek') == 'kek'
    assert EnvSource().type_awared_get('lol', str, default=123) == 123


def test_read_existing_key(monkeypatch):
    monkeypatch.setenv("lol", "1")

    assert EnvSource()['lol'] == '1'
    assert EnvSource().type_awared_get('lol', str) == '1'
    assert EnvSource().type_awared_get('lol', int) == 1

    assert EnvSource()['LOL'] == '1'
    assert EnvSource().type_awared_get('LOL', str) == '1'
    assert EnvSource().type_awared_get('LOL', int) == 1



    if platform.system() != 'Windows':
        assert EnvSource(case_sensitive=True)['lol'] == '1'
        assert EnvSource(case_sensitive=True).type_awared_get('lol', str) == '1'
        assert EnvSource(case_sensitive=True).type_awared_get('lol', int) == 1
        assert EnvSource(case_sensitive=True).type_awared_get('LOL', str) is None
        assert EnvSource(case_sensitive=True).type_awared_get('LOL', int) is None
        assert EnvSource(case_sensitive=True).type_awared_get('LOL', str, default=1) == 1
        assert EnvSource(case_sensitive=True).type_awared_get('LOL', str, default='kek') == 'kek'

        with pytest.raises(KeyError):
            EnvSource(case_sensitive=True)['LOL']
    else:
        assert EnvSource()['lol'] == '1'
        assert EnvSource().type_awared_get('lol', str) == '1'
        assert EnvSource().type_awared_get('lol', int) == 1
        assert EnvSource().type_awared_get('LOL', str) == '1'
        assert EnvSource()['LOL'] == '1'


def test_type_awared_get(monkeypatch):
    monkeypatch.setenv("string", "kek")
    monkeypatch.setenv("number", "1")
    monkeypatch.setenv("float_number", "1.0")
    monkeypatch.setenv("numbers_list", "[1, 2, 3]")
    monkeypatch.setenv("boolean_yes", "yes")
    monkeypatch.setenv("boolean_no", "no")
    monkeypatch.setenv("strings_list", '["1", "2", "3"]')
    monkeypatch.setenv("strings_dict", '{"lol": "kek"}')

    assert EnvSource().type_awared_get("string", str) == 'kek'
    assert EnvSource().type_awared_get("number", str) == '1'
    assert EnvSource().type_awared_get("number", int) == 1
    assert EnvSource().type_awared_get("number", float) == 1.0
    assert EnvSource().type_awared_get("float_number", float) == 1.0
    assert EnvSource().type_awared_get("boolean_yes", bool) == True
    assert EnvSource().type_awared_get("boolean_no", bool) == False
    assert EnvSource().type_awared_get("numbers_list", List[int]) == [1, 2, 3]
    assert EnvSource().type_awared_get("numbers_list", List) == [1, 2, 3]
    assert EnvSource().type_awared_get("numbers_list", list) == [1, 2, 3]
    assert EnvSource().type_awared_get("strings_list", List[str]) == ['1', '2', '3']
    assert EnvSource().type_awared_get("strings_list", List) == ['1', '2', '3']
    assert EnvSource().type_awared_get("strings_list", list) == ['1', '2', '3']
    assert EnvSource().type_awared_get("strings_dict", Dict[str, str]) == {'lol': 'kek'}
    assert EnvSource().type_awared_get("strings_dict", Dict) == {'lol': 'kek'}
    assert EnvSource().type_awared_get("strings_dict", dict) == {'lol': 'kek'}

    with pytest.raises(TypeError, match=match('The string "[1, 2, 3]" cannot be interpreted as a list of the specified format.')):
        EnvSource().type_awared_get("numbers_list", List[str])

    with pytest.raises(TypeError, match=match('The string "["1", "2", "3"]" cannot be interpreted as a list of the specified format.')):
        EnvSource().type_awared_get("strings_list", List[int])

    with pytest.raises(TypeError, match=match('The string "kek" cannot be interpreted as an integer.')):
        EnvSource().type_awared_get("string", int)


def test_read_with_prefix(monkeypatch):
    monkeypatch.setenv("LIBRARY_KEY", "kek")

    assert EnvSource(prefix='library_')['key'] == 'kek'

    if platform.system() != 'Windows':
        with pytest.raises(KeyError):
            EnvSource(prefix='library_', case_sensitive=True)['key']
        assert EnvSource(prefix='LIBRARY_', case_sensitive=True)['KEY'] == 'kek'
    else:
        assert EnvSource(prefix='library_')['key'] == 'kek'
        assert EnvSource(prefix='LIBRARY_')['KEY'] == 'kek'

    assert EnvSource(prefix='LIBRARY_')['KEY'] == 'kek'


def test_read_with_postfix(monkeypatch):
    monkeypatch.setenv("LIBRARY_KEY", "kek")

    assert EnvSource(postfix='_key')['library'] == 'kek'

    if platform.system() != 'Windows':
        with pytest.raises(KeyError):
            EnvSource(postfix='_key', case_sensitive=True)['library']
        assert EnvSource(postfix='_KEY', case_sensitive=True)['LIBRARY'] == 'kek'
    else:
        assert EnvSource(postfix='_key')['library'] == 'kek'
        assert EnvSource(postfix='_KEY')['LIBRARY'] == 'kek'

    assert EnvSource(postfix='_KEY')['LIBRARY'] == 'kek'


def test_read_with_prefix_and_postfix(monkeypatch):
    monkeypatch.setenv("LIBRARY_KEY_POSTFIX", "kek")

    assert EnvSource(prefix='library_', postfix='_postfix')['key'] == 'kek'

    if platform.system() != 'Windows':
        with pytest.raises(KeyError):
            EnvSource(prefix='library_', postfix='_postfix', case_sensitive=True)['key']
        assert EnvSource(prefix='LIBRARY_', postfix='_POSTFIX', case_sensitive=True)['KEY'] == 'kek'
    else:
        assert EnvSource(prefix='library_', postfix='_postfix')['key'] == 'kek'

    assert EnvSource(prefix='LIBRARY_', postfix='_POSTFIX')['KEY'] == 'kek'


@pytest.mark.skipif(platform.system() != 'Windows', reason='On Windows, the environment variables are case-independent.')
def test_try_to_use_case_sensitive_mod_on_windows():
    with pytest.raises(OSError, match=match('On Windows, the environment variables are case-independent.')):
        EnvSource(case_sensitive=True)
