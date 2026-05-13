import pytest
from full_match import match

from skelet import EnvSource, JSONSource, TOMLSource, YAMLSource, for_tool


def test_all_sources():
    sources = for_tool('kek')

    assert len(sources) == 8

    assert isinstance(sources[0], EnvSource)
    assert sources[0].prefix == 'KEK_'
    assert sources[0].postfix == ''
    assert sources[0].case_sensitive == False

    assert isinstance(sources[1], TOMLSource)
    assert sources[1].path == 'kek.toml'
    assert sources[1].allow_non_existent_files == True
    assert sources[1].table == []

    assert isinstance(sources[2], TOMLSource)
    assert sources[2].path == '.kek.toml'
    assert sources[2].allow_non_existent_files == True
    assert sources[2].table == []

    assert isinstance(sources[3], TOMLSource)
    assert sources[3].path == 'pyproject.toml'
    assert sources[3].allow_non_existent_files == True
    assert sources[3].table == ['tool', 'kek']

    assert isinstance(sources[4], YAMLSource)
    assert sources[4].path == 'kek.yaml'
    assert sources[4].allow_non_existent_files == True

    assert isinstance(sources[5], YAMLSource)
    assert sources[5].path == '.kek.yaml'
    assert sources[5].allow_non_existent_files == True

    assert isinstance(sources[6], JSONSource)
    assert sources[6].path == 'kek.json'
    assert sources[6].allow_non_existent_files == True

    assert isinstance(sources[7], JSONSource)
    assert sources[7].path == '.kek.json'
    assert sources[7].allow_non_existent_files == True


def test_invalid_tool_name():
    with pytest.raises(ValueError, match=match('The library name can only be a valid Python identifier.')):
        for_tool(':kek')


def test_builtin_plugins_order():
    assert for_tool.keys() == (
        'env',
        'toml',
        'hidden_toml',
        'pyproject_toml',
        'yaml',
        'hidden_yaml',
        'json',
        'hidden_json',
    )


def test_dynamic_plugin_can_be_added_and_removed():
    @for_tool.plugin
    def temporary_plugin(tool_name: str) -> JSONSource:
        return JSONSource(f'{tool_name}.plugin.json')

    try:
        assert 'temporary_plugin' in for_tool

        sources_before_removal = for_tool('kek')

        assert len(sources_before_removal) == 9
        assert isinstance(sources_before_removal[-1], JSONSource)
        assert sources_before_removal[-1].path == 'kek.plugin.json'

        removed_plugins = for_tool.pop('temporary_plugin')

        assert len(removed_plugins) == 1
        assert 'temporary_plugin' not in for_tool

        sources_after_removal = for_tool('kek')

        assert len(sources_after_removal) == 8
        assert all(not (isinstance(source, JSONSource) and source.path == 'kek.plugin.json') for source in sources_after_removal)
    finally:
        for_tool.pop('temporary_plugin', None)
