import pytest

from skelet import Field, Storage

pytestmark = [
    pytest.mark.thread_safety,
    pytest.mark.xfail(strict=False, reason='Known lock-group topology limitation.'),
]


def test_lock_group_topology_is_order_dependent_for_connected_graph():
    class SomeClass(Storage):
        second_field = Field(2, conflicts={'third_field': lambda *_: False})
        first_field = Field(1, share_mutex_with=['second_field'])
        third_field = Field(3)

    instance = SomeClass()

    assert instance.__locks__['first_field'] is instance.__locks__['second_field']
    assert instance.__locks__['second_field'] is instance.__locks__['third_field']
