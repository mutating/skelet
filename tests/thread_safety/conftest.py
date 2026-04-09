from collections import deque
from queue import Empty, Queue
from threading import Barrier, Event, Lock, Thread, get_ident
from typing import Any, Callable, Deque, Generic, List, Optional, Tuple, TypeVar

import pytest
from locklib import DeadLockError, SmartLock

DEFAULT_THREAD_TIMEOUT = 5
STRESS_THREAD_TIMEOUT = 30

ResultType = TypeVar('ResultType')


class ThreadSafeEventLog:
    def __init__(self) -> None:
        self._lock = Lock()
        self._events: Deque[str] = deque()

    def append(self, event: str) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> List[str]:
        with self._lock:
            return list(self._events)


class ThreadOutcome(Generic[ResultType]):
    def __init__(self) -> None:
        self.queue: 'Queue[Tuple[str, Any]]' = Queue()


class LocklibDeadlockDetectingLock:
    def __init__(self) -> None:
        self._lock = SmartLock()
        self._owner_thread_id: Optional[int] = None
        self._state_lock = Lock()

    def __enter__(self) -> None:
        self.acquire()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()

    def acquire(self) -> None:
        thread_id = get_ident()
        with self._state_lock:
            if self._owner_thread_id == thread_id:
                raise DeadLockError(
                    f'A repeated acquire attempt by thread {thread_id} was detected.',
                )
        self._lock.acquire()
        with self._state_lock:
            self._owner_thread_id = thread_id

    def release(self) -> None:
        thread_id = get_ident()
        with self._state_lock:
            if self._owner_thread_id != thread_id:
                raise RuntimeError('Release from a non-owner thread was detected.')
            self._owner_thread_id = None
        self._lock.release()


def run_in_thread(
    target: Callable[[], ResultType],
) -> Tuple[Thread, ThreadOutcome[ResultType]]:
    outcome: ThreadOutcome[ResultType] = ThreadOutcome()

    def wrapped_target() -> None:
        try:
            outcome.queue.put(('result', target()))
        except BaseException as error:  # noqa: BLE001
            outcome.queue.put(('error', error))

    thread = Thread(target=wrapped_target)
    thread.start()
    return thread, outcome


def collect_thread_outcome(
    thread: Thread,
    outcome: ThreadOutcome[ResultType],
    timeout: int = DEFAULT_THREAD_TIMEOUT,
) -> ResultType:
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(
            f'Thread did not complete within {timeout} seconds; possible deadlock.',
        )

    try:
        state, payload = outcome.queue.get_nowait()
    except Empty as error:
        raise RuntimeError('Thread completed without publishing an outcome.') from error

    if state == 'error':
        raise payload

    return payload


def make_gate_callback(
    event_log: ThreadSafeEventLog,
    entered_event: Event,
    release_event: Event,
    label: str,
    exception: Optional[BaseException] = None,
) -> Callable[[Any, Any, Any], None]:
    def callback(old_value: Any, new_value: Any, storage: Any) -> None:  # noqa: ARG001
        event_log.append(f'{label}:enter')
        entered_event.set()
        if exception is not None:
            raise exception
        if not release_event.wait(DEFAULT_THREAD_TIMEOUT):
            raise TimeoutError(
                f'Gate callback "{label}" was not released within {DEFAULT_THREAD_TIMEOUT} seconds.',
            )
        event_log.append(f'{label}:exit')

    return callback


def replace_field_lock_with_locklib_lock(
    instance: Any,
    field_name: str,
    expected_group_fields: List[str],
) -> LocklibDeadlockDetectingLock:
    if field_name not in instance.__locks__:
        raise RuntimeError(f'The "{field_name}" field is missing from instance.__locks__.')

    old_lock = instance.__locks__[field_name]
    new_lock = LocklibDeadlockDetectingLock()
    replaced_fields = []

    for current_field_name, current_lock in list(instance.__locks__.items()):
        if current_lock is old_lock:
            instance.__locks__[current_field_name] = new_lock
            replaced_fields.append(current_field_name)

    if not replaced_fields:
        raise RuntimeError(f'No fields were rebound for the "{field_name}" lock group.')

    for expected_field_name in expected_group_fields:
        if expected_field_name not in instance.__locks__:
            raise RuntimeError(
                f'The expected field "{expected_field_name}" is missing from instance.__locks__.',
            )
        if instance.__locks__[expected_field_name] is not new_lock:
            raise RuntimeError(
                f'The "{expected_field_name}" field was not rebound to the expected lock group.',
            )

    return new_lock


def start_barrier(participants: int) -> Barrier:
    return Barrier(participants)


@pytest.fixture
def event_log() -> ThreadSafeEventLog:
    return ThreadSafeEventLog()
