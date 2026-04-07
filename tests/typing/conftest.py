"""Skip runtime execution of negative typing tests.

Tests in test_negative_types.py contain intentional type errors that crash
at runtime. The [mypy] test items should still run; only the normal pytest
function items should be skipped.
"""
import pytest


def pytest_collection_modifyitems(items: list) -> None:  # type: ignore[type-arg]
    for item in items:
        if 'test_negative_types' in item.nodeid and '[mypy]' not in item.nodeid:
            item.add_marker(pytest.mark.skip(reason='negative typing test, runtime execution not expected'))
