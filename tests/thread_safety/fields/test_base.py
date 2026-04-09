from queue import Queue
from threading import Event, Lock
from typing import List

import pytest
from locklib import DeadLockError

from skelet import Field, Storage
from tests.thread_safety.conftest import (
    DEFAULT_THREAD_TIMEOUT,
    STRESS_THREAD_TIMEOUT,
    collect_thread_outcome,
    make_gate_callback,
    replace_field_lock_with_locklib_lock,
    run_in_thread,
    start_barrier,
)

pytestmark = pytest.mark.thread_safety


def test_writes_to_same_field_are_serialized(event_log):
    first_entered = Event()
    second_entered = Event()
    release_first = Event()
    release_second = Event()

    def action(old_value: int, new_value: int, storage: Storage) -> None:
        callback = make_gate_callback(
            event_log,
            first_entered if new_value == 1 else second_entered,
            release_first if new_value == 1 else release_second,
            f'writer-{new_value}',
        )
        callback(old_value, new_value, storage)

    class SomeClass(Storage):
        field = Field(0, action=action)

    instance = SomeClass()

    first_thread, first_outcome = run_in_thread(lambda: setattr(instance, 'field', 1))
    assert first_entered.wait(DEFAULT_THREAD_TIMEOUT)

    second_thread, second_outcome = run_in_thread(lambda: setattr(instance, 'field', 2))
    assert not second_entered.is_set()
    assert second_outcome.queue.empty()

    release_first.set()
    assert second_entered.wait(DEFAULT_THREAD_TIMEOUT)
    assert event_log.snapshot() == ['writer-1:enter', 'writer-1:exit', 'writer-2:enter']

    release_second.set()

    collect_thread_outcome(first_thread, first_outcome)
    collect_thread_outcome(second_thread, second_outcome)

    assert instance.field == 2
    assert event_log.snapshot() == [
        'writer-1:enter',
        'writer-1:exit',
        'writer-2:enter',
        'writer-2:exit',
    ]


def test_read_with_read_lock_waits_for_writer(event_log):
    writer_entered = Event()
    release_writer = Event()

    class SomeClass(Storage):
        field = Field(
            0,
            read_lock=True,
            action=make_gate_callback(event_log, writer_entered, release_writer, 'writer'),
        )

    instance = SomeClass()

    writer_thread, writer_outcome = run_in_thread(lambda: setattr(instance, 'field', 1))
    assert writer_entered.wait(DEFAULT_THREAD_TIMEOUT)

    reader_thread, reader_outcome = run_in_thread(lambda: instance.field)
    assert reader_outcome.queue.empty()
    assert writer_outcome.queue.empty()

    release_writer.set()

    collect_thread_outcome(writer_thread, writer_outcome)
    assert collect_thread_outcome(reader_thread, reader_outcome) == 1
    assert event_log.snapshot() == ['writer:enter', 'writer:exit']


def test_write_visibility_across_threads():
    write_done = Event()

    class SomeClass(Storage):
        field = Field(0)

    instance = SomeClass()

    def writer() -> None:
        instance.field = 1
        write_done.set()

    def reader() -> int:
        write_done.wait()
        return instance.field

    reader_thread, reader_outcome = run_in_thread(reader)
    writer_thread, writer_outcome = run_in_thread(writer)

    collect_thread_outcome(writer_thread, writer_outcome)
    assert collect_thread_outcome(reader_thread, reader_outcome) == 1


def test_writes_to_conflicting_fields_are_serialized_by_shared_mutex(event_log):
    writer_entered = Event()
    release_writer = Event()

    def conflicts_with_b(
        _old_a: int,
        new_a: int,
        _old_b: int,
        new_b: int,
    ) -> bool:
        return new_a > 0 and new_b > 0

    class SomeClass(Storage):
        a = Field(
            0,
            conflicts={'b': conflicts_with_b},
            action=make_gate_callback(event_log, writer_entered, release_writer, 'writer-a'),
        )
        b = Field(0)

    instance = SomeClass()

    first_thread, first_outcome = run_in_thread(lambda: setattr(instance, 'a', 1))
    assert writer_entered.wait(DEFAULT_THREAD_TIMEOUT)

    def write_conflicting_value() -> None:
        writer_entered.wait()
        instance.b = 1

    second_thread, second_outcome = run_in_thread(write_conflicting_value)
    assert first_outcome.queue.empty()
    assert second_outcome.queue.empty()

    release_writer.set()

    collect_thread_outcome(first_thread, first_outcome)
    with pytest.raises(ValueError, match='conflicts with'):
        collect_thread_outcome(second_thread, second_outcome)

    assert instance.a == 1
    assert instance.b == 0
    assert not (instance.a > 0 and instance.b > 0)
    assert event_log.snapshot() == ['writer-a:enter', 'writer-a:exit']


def test_writes_to_non_conflicting_fields_do_not_block_each_other_on_field_lock(event_log):
    first_entered = Event()
    second_entered = Event()
    release_all = Event()

    class SomeClass(Storage):
        a = Field(0, action=make_gate_callback(event_log, first_entered, release_all, 'writer-a'))
        b = Field(0, action=make_gate_callback(event_log, second_entered, release_all, 'writer-b'))

    instance = SomeClass()

    first_thread, first_outcome = run_in_thread(lambda: setattr(instance, 'a', 1))
    assert first_entered.wait(DEFAULT_THREAD_TIMEOUT)

    second_thread, second_outcome = run_in_thread(lambda: setattr(instance, 'b', 2))
    assert second_entered.wait(DEFAULT_THREAD_TIMEOUT)
    assert event_log.snapshot() == ['writer-a:enter', 'writer-b:enter']

    release_all.set()

    collect_thread_outcome(first_thread, first_outcome)
    collect_thread_outcome(second_thread, second_outcome)

    assert instance.a == 1
    assert instance.b == 2


def test_callback_exception_releases_lock(event_log):
    writer_entered = Event()
    release_successful_callback = Event()

    def action(old_value: int, new_value: int, storage: Storage) -> None:
        callback = make_gate_callback(
            event_log,
            writer_entered,
            release_successful_callback,
            'writer',
            exception=RuntimeError('boom') if new_value == 1 else None,
        )
        callback(old_value, new_value, storage)

    class SomeClass(Storage):
        field = Field(0, action=action)

    instance = SomeClass()

    failing_thread, failing_outcome = run_in_thread(lambda: setattr(instance, 'field', 1))
    assert writer_entered.wait(DEFAULT_THREAD_TIMEOUT)

    with pytest.raises(RuntimeError, match='boom'):
        collect_thread_outcome(failing_thread, failing_outcome)

    successful_thread, successful_outcome = run_in_thread(
        lambda: setattr(instance, 'field', 2),
    )
    assert writer_entered.wait(DEFAULT_THREAD_TIMEOUT)
    release_successful_callback.set()
    collect_thread_outcome(successful_thread, successful_outcome)

    assert instance.field == 2
    assert event_log.snapshot() == ['writer:enter', 'writer:enter', 'writer:exit']


def test_callback_reading_same_field_with_read_lock_raises_locklib_error():
    def read_same_field(_old_value: int, _new_value: int, storage: Storage) -> int:
        return storage.field

    class SomeClass(Storage):
        field = Field(0, read_lock=True, action=read_same_field)

    instance = SomeClass()
    replace_field_lock_with_locklib_lock(instance, 'field', ['field'])

    with pytest.raises(DeadLockError, match='repeated acquire attempt'):
        instance.field = 1


def test_callback_writing_same_field_raises_locklib_error():
    def write_same_field(_old_value: int, new_value: int, storage: Storage) -> None:
        if new_value == 1:
            storage.field = 2

    class SomeClass(Storage):
        field = Field(0, action=write_same_field)

    instance = SomeClass()
    replace_field_lock_with_locklib_lock(instance, 'field', ['field'])

    with pytest.raises(DeadLockError, match='repeated acquire attempt'):
        instance.field = 1


def test_callback_accessing_shared_mutex_field_raises_locklib_error():
    def read_shared_field(_old_value: int, _new_value: int, storage: Storage) -> int:
        return storage.b

    class SomeClass(Storage):
        a = Field(0, share_mutex_with=['b'], action=read_shared_field)
        b = Field(0, read_lock=True)

    instance = SomeClass()
    replace_field_lock_with_locklib_lock(instance, 'a', ['a', 'b'])

    with pytest.raises(DeadLockError, match='repeated acquire attempt'):
        instance.a = 1


def test_callback_accessing_conflicting_field_raises_locklib_error():
    def read_conflicting_field(_old_value: int, _new_value: int, storage: Storage) -> int:
        return storage.b

    class SomeClass(Storage):
        a = Field(0, conflicts={'b': lambda *_: False}, action=read_conflicting_field)
        b = Field(0, read_lock=True)

    instance = SomeClass()
    replace_field_lock_with_locklib_lock(instance, 'a', ['a', 'b'])

    with pytest.raises(DeadLockError, match='repeated acquire attempt'):
        instance.a = 1


def test_conflict_checker_accessing_locked_field_raises_locklib_error():
    holder = {}

    def checker(old_a: int, new_a: int, old_b: int, new_b: int) -> bool:  # noqa: ARG001
        if 'instance' not in holder:
            return False
        return bool(holder['instance'].b)

    class SomeClass(Storage):
        a = Field(0, conflicts={'b': checker})
        b = Field(0, read_lock=True)

    instance = SomeClass()
    holder['instance'] = instance
    replace_field_lock_with_locklib_lock(instance, 'a', ['a', 'b'])

    with pytest.raises(DeadLockError, match='repeated acquire attempt'):
        instance.a = 1


def test_stress_many_threads_read_and_write_field_with_read_lock():
    num_writers = 5
    num_readers = 5
    iterations = 100
    barrier = start_barrier(num_writers + num_readers)
    read_values: 'Queue[int]' = Queue()

    class SomeClass(Storage):
        field = Field(0, read_lock=True)

    instance = SomeClass()

    def writer(value: int) -> None:
        barrier.wait()
        for _ in range(iterations):
            instance.field = value

    def reader() -> None:
        barrier.wait()
        for _ in range(iterations):
            read_values.put(instance.field)

    threads_and_outcomes = []
    for value in range(1, num_writers + 1):
        threads_and_outcomes.append(run_in_thread(lambda value=value: writer(value)))
    for _ in range(num_readers):
        threads_and_outcomes.append(run_in_thread(reader))

    for thread, outcome in threads_and_outcomes:
        collect_thread_outcome(thread, outcome, timeout=STRESS_THREAD_TIMEOUT)

    collected_reads = []
    while not read_values.empty():
        collected_reads.append(read_values.get_nowait())

    assert len(collected_reads) == num_readers * iterations
    assert set(collected_reads).issubset({0, 1, 2, 3, 4, 5})


def test_stress_many_threads_write_conflicting_fields():
    num_threads = 10
    iterations = 100
    barrier = start_barrier(num_threads)
    errors: List[BaseException] = []
    errors_lock = Lock()

    def conflicts_with_b(
        _old_a: int,
        new_a: int,
        _old_b: int,
        new_b: int,
    ) -> bool:
        return new_a > 0 and new_b > 0

    class SomeClass(Storage):
        a = Field(0, conflicts={'b': conflicts_with_b})
        b = Field(0)

    instance = SomeClass()

    def worker(index: int) -> None:
        barrier.wait()
        for _ in range(iterations):
            try:
                if index % 2 == 0:
                    instance.a = 1
                    instance.a = 0
                else:
                    instance.b = 1
                    instance.b = 0
            except ValueError as error:
                with errors_lock:
                    errors.append(error)

    threads_and_outcomes = [
        run_in_thread(lambda index=index: worker(index)) for index in range(num_threads)
    ]

    for thread, outcome in threads_and_outcomes:
        collect_thread_outcome(thread, outcome, timeout=STRESS_THREAD_TIMEOUT)

    assert all(isinstance(error, ValueError) for error in errors)
    assert not (instance.a > 0 and instance.b > 0)
