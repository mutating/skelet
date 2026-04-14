import pytest


def pytest_collection_modifyitems(items: list) -> None:  # type: ignore[type-arg]
    for item in items:
        if 'test_negative_types' in item.nodeid and '[mypy]' not in item.nodeid:
            item.add_marker(pytest.mark.skip(reason='negative typing test, runtime execution not expected'))
