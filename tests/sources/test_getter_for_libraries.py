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
