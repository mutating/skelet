from threading import Event

import pytest

from skelet import Field, Storage, asdict
from tests.thread_safety.conftest import collect_thread_outcome, run_in_thread

pytestmark = pytest.mark.thread_safety


def test_asdict_can_return_inconsistent_snapshot():
    first_write_done = Event()
    snapshot_done = Event()

    class SomeClass(Storage):
        first_field = Field(0)
        second_field = Field(0)

    instance = SomeClass()

    def writer() -> None:
        instance.first_field = 1
        first_write_done.set()
        snapshot_done.wait()
        instance.second_field = 2

    def snapshotter():
        first_write_done.wait()
        result = asdict(instance)
        snapshot_done.set()
        return result

    writer_thread, writer_outcome = run_in_thread(writer)
    snapshot_thread, snapshot_outcome = run_in_thread(snapshotter)

    snapshot = collect_thread_outcome(snapshot_thread, snapshot_outcome)
    collect_thread_outcome(writer_thread, writer_outcome)

    assert snapshot == {'first_field': 1, 'second_field': 0}
