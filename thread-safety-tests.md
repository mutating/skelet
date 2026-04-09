# План тестирования потокобезопасности `skelet`

## Цель

Собрать отдельный, устойчивый слой тестов для проверки потокобезопасности библиотеки без `sleep()` и без таймаутов как механизма проверки корректности.

План должен опираться на фактический контракт текущей реализации, а не на гипотетическое "идеальное" поведение. Главные цели:

- проверять реальные гарантии `Field.__set__` и `Field.__get__`;
- не писать флаки-тесты на тонкий interleaving, который нельзя зафиксировать событиями;
- честно отделять production-контракты от dev-mode тестов на детекцию опасных сценариев через `locklib`;
- дополнить детерминированные тесты небольшим набором стресс-тестов для самых частых сценариев.


## Что из критики справедливо

Справедливые замечания:

- Тест `test_read_without_read_lock_does_not_wait_for_writer_callback` в изначальной формулировке был недетерминированным. Без дополнительного hook между записью в `__values__` и входом в callback нельзя гарантировать, что reader увидит именно новое значение.
- `locklib`-слой нужно называть честно. Такие тесты не доказывают production-behavior `threading.Lock`; они нужны как dev-mode canary, чтобы безопасно фиксировать reentrant-сценарии без подвешивания suite.
- Для конфликтующих полей нужно заранее зафиксировать конкретную конфликтную функцию и конкретные значения, иначе тест может оказаться логически пустым.
- В плане действительно не хватало отдельного теста на visibility записи между потоками.
- Для `asdict()` не хватало теста именно на последствие, а не только на механизм. Главный риск там не "чтение без lock", а возможность получить несогласованный снимок.
- Отдельный тест `test_callbacks_for_same_field_do_not_run_simultaneously` дублировал `test_writes_to_same_field_are_serialized`.
- Условный статус у `test_conflict_checker_accessing_locked_field_raises_locklib_error` был размыт.
- Формулировку про "independent progress" для независимых полей надо было сузить до того, что реально можно доказать: второй writer не блокируется на mutex первого поля.
- Для stress-тестов нужны фиксированные параметры.
- `collect_thread_outcome` должен иметь safeguard timeout, иначе неожиданный deadlock может повесить CI навсегда.
- `event_log` должен быть явно потокобезопасным и не полагаться на детали GIL.
- Стоит хотя бы минимально покрыть конкурентный `__init__` для сценария с общим `default_factory`.

Частично справедливые замечания:

- Замечание про "тестирование `locklib`, а не `skelet`" верно только наполовину. Если такие тесты подать как production-гарантию, это ошибка. Но если подать их как dev-mode детекцию того, что код `skelet` действительно повторно входит в тот же mutex, то они полезны и уместны.
- Замечание про отсутствие теста на `reverse_conflicts=False` справедливо, если считать текущую асимметрию частью важной наблюдаемой семантики. Такой тест стоит добавить, но как фиксацию ограничения/поведения, а не как "ожидаемую защиту".

Замечания, которые я не считаю обязательными для первой волны:

- Доказательство реального deadlock на `threading.Lock` через отдельный test/demo с таймаутом. Это можно сделать как отдельный диагностический сценарий, но в основной suite я бы такое не включал: даже `xfail`-тесты на зависание плохо масштабируются и ухудшают надежность CI.
- Полноценное покрытие `__init__` как источника всех возможных гонок. Для первой волны достаточно узкого smoke-теста на concurrent-init с общим `default_factory`; более глубокие проверки публикации partially initialized object сюда не входят.


## Структура тестов

Новая директория:

- `tests/thread_safety/`

Структура повторяет подход `tests/units`: один исходный модуль библиотеки -> один тестовый файл с относящимися к нему thread-safety тестами.

Замечание по структуре:

- в текущем репозитории `units`-тесты в основном лежат плоско;
- для `thread_safety` сознательно выбирается более структурированная раскладка с подпапками (`fields/`, `functions/`), и это нужно считать целевым форматом.

Планируемые файлы:

- `tests/thread_safety/conftest.py`
- `tests/thread_safety/test_storage.py`
- `tests/thread_safety/test_known_limitations.py`
- `tests/thread_safety/fields/test_base.py`
- `tests/thread_safety/functions/test_asdict.py`


## Общие правила

### Что обязательно

- Использовать реальные `threading.Thread`.
- Координировать сценарии через `threading.Event`, `threading.Barrier`, `queue.Queue`.
- Строить тесты вокруг контролируемых фаз исполнения.
- Проверять только сильные и стабильные инварианты.
- Для reentrant/deadlock-сценариев использовать `locklib` только как dev-mode детектор повторного захвата lock.
- Иметь небольшой safeguard timeout в helper-ах, чтобы неожиданная блокировка не вешала CI навсегда.
- Проектировать oracle-ы тестов так, чтобы они не зависели от GIL.

### Чего избегать

- `time.sleep()`
- таймаутов как критерия правильности теста
- stress/fuzz в стиле "погоняем подольше и вдруг поймаем"
- проверок, завязанных на случайный порядок планировщика
- утверждений о поведении, которое невозможно детерминированно зафиксировать текущими hook-ами

### Допустимые виды проверок

- поток дошел до определенной фазы;
- второй поток еще не дошел до своей фазы до `release_event`;
- callback 2 не может начаться до завершения callback 1;
- reader блокируется при `read_lock=True`;
- запись из одного потока становится видимой в другом;
- операция завершается ожидаемым исключением;
- финальное значение принадлежит допустимому множеству;
- итоговый инвариант между полями сохраняется.


## Слои покрытия

### 1. Контрактные детерминированные тесты

Это основной слой. Именно он должен доказывать наблюдаемые гарантии библиотеки.

Сюда входят:

- topology lock-групп;
- serialization writes;
- read/write visibility;
- conflict-handling под общей блокировкой;
- отсутствие ложной блокировки между независимыми полями;
- минимальный слой действительно сигнальных stress-тестов.

### 2. Reentrant/deadlock detection через `locklib`

Это отдельный dev-mode слой для неподдерживаемых, но опасных сценариев:

- callback повторно входит в тот же lock;
- callback трогает поле той же lock-группы;
- conflict checker провоцирует повторный вход в lock.

Эти тесты не доказывают, что библиотека "обрабатывает дедлок" в production. Они нужны, чтобы:

- подтвердить сам факт повторного захвата lock в коде `skelet`;
- не повесить suite;
- зафиксировать ограничение библиотеки в проверяемой форме.

### 3. Небольшой слой stress-тестов

Это дополнительная страховка для самых частых сценариев:

- много concurrent writes в одно поле;
- concurrent readers/writers для `read_lock=True`;
- concurrent writes в независимые поля;
- concurrent writes в конфликтующие поля.

Stress-тесты не должны подменять основной слой и не должны проверять тонкий interleaving.


## Общие helper-ы

Файл:

- `tests/thread_safety/conftest.py`

Нужные helper-ы/фикстуры:

1. `run_in_thread`

Назначение:

- запускает функцию в отдельном потоке;
- складывает результат или исключение в `queue.Queue`;
- возвращает `Thread` и очередь результата.

2. `collect_thread_outcome`

Назначение:

- достает из очереди результат выполнения потока;
- если в очереди лежит исключение, пробрасывает или возвращает его для явной проверки;
- по умолчанию использует safeguard timeout `5` секунд, чтобы не повесить CI при неожиданной блокировке;
- для stress-тестов использует `timeout=30` секунд;
- допускает переопределение timeout при необходимости.

Если timeout сработал:

- helper поднимает `TimeoutError` с явным сообщением вида `Thread did not complete within 5 seconds; possible deadlock`.

Практическое правило:

- для контрактных и dev-mode тестов использовать дефолтный timeout;
- для stress-тестов явно передавать `timeout=30`.

3. `event_log`

Назначение:

- явно потокобезопасная структура для записи событий;
- позволяет проверять порядок фаз без привязки ко времени.

Реализация:

- небольшой wrapper над `list` или `deque` с внутренним `threading.Lock`;
- должен поддерживать как минимум `append()` и `snapshot()`;
- не опираться на атомарность `list.append()` как побочный эффект GIL.

4. `make_gate_callback`

Назначение:

- возвращает callback, который:
  - пишет событие о входе;
  - выставляет `entered_event`;
  - ждет `release_event`;
  - пишет событие о выходе.

Это основной инструмент для детерминированной фиксации фазы "поток уже внутри callback под mutex".

Рекомендуемая сигнатура:

- `make_gate_callback(event_log, entered_event, release_event, label)`

Возвращаемый callback должен:

- принимать `(old_value, new_value, storage)`;
- писать в лог событие с `label`;
- выставлять `entered_event`;
- ждать `release_event`;
- затем писать событие выхода.

Вариант для exception-сценариев:

- helper должен поддерживать режим, в котором после `entered_event.set()` callback выбрасывает переданное исключение вместо ожидания `release_event`;
- это нужно для `test_callback_exception_releases_lock`, чтобы детерминированно зафиксировать вход в critical section и затем проверить освобождение mutex после исключения.

5. `replace_field_lock_with_locklib_lock`

Назначение:

- подменяет всю lock-группу поля на один lock из `locklib`, который бросает исключение при повторном захвате;
- helper должен перепривязывать все ключи `instance.__locks__`, которые указывают на тот же lock-объект, что и исходное поле.
- helper должен принимать `expected_group_fields`, чтобы тест явно задавал ожидаемый состав lock-группы.

Ограничение helper-а:

- helper полагается на identity-сравнение текущих lock-объектов (`is`);
- если алгоритм сборки lock-групп изменится и перестанет выражаться через общий объект lock на все поля группы, helper нужно будет адаптировать.

Fail-fast требование:

- после перепривязки helper должен проверять, что все ожидаемые поля группы действительно смотрят на один и тот же новый `locklib`-lock;
- если хотя бы один ключ остался привязан к старому lock-объекту, helper должен бросать `RuntimeError` с понятным сообщением, а не позволять тесту стать no-op.

Нужен только для dev-mode anti-deadlock тестов.

6. `start_barrier`

Назначение:

- helper-функция, создающая `Barrier(n)` для нужного числа участников;
- используется там, где нужен одновременный старт worker-потоков.

7. `thread_safety` marker

Назначение:

- отдельный pytest marker для всего раздела `tests/thread_safety/`;
- позволяет запускать эти тесты выборочно и позже использовать их как отдельный набор в CI.


## План по файлам

## `tests/thread_safety/test_storage.py`

Этот файл отвечает за lock topology и композицию mutex-групп на уровне `Storage`.

### Контрактные тесты

1. `test_share_mutex_with_is_transitive`

Проверяет:

- `A share_mutex_with B`, `B share_mutex_with C` приводят к единой группе mutex-ов.

2. `test_share_mutex_with_and_conflicts_merge_into_one_group`

Проверяет:

- если поле делит mutex с одним полем и конфликтует с другим, все три поля используют один mutex.

3. `test_independent_fields_use_different_mutexes`

Проверяет:

- поля без `share_mutex_with` и `conflicts` не попадают в одну группу.

4. `test_two_instances_do_not_share_mutex_groups`

Статус:

- опциональный тест;
- включать только если он будет усиливать существующий unit-тест, а не просто дублировать его.

### Stress-тесты

Не нужны.


## `tests/thread_safety/test_known_limitations.py`

Этот файл отвечает за известные ограничения текущей реализации, которые важно не потерять из виду, но не стоит смешивать с основным контрактным слоем.

### Known limitation tests

1. `test_lock_group_topology_is_order_dependent_for_connected_graph`

Проверяет:

- order-sensitive конфигурации связного графа полей;
- пример вида:
  - `b = Field(..., conflicts={'c': ...})`
  - `a = Field(..., share_mutex_with=['b'])`
  - `c = Field(...)`
- фиксирует known limitation текущего алгоритма: связный граф может распасться на несколько lock-групп из-за порядка объявления полей.

Статус:

- тест должен быть помечен как `xfail(strict=False)` или эквивалентный known-limitation marker;
- если алгоритм позже будет исправлен, этот тест нужно заменить на обычный контрактный `test_lock_group_topology_is_not_order_dependent_for_connected_graph` в `test_storage.py`.

2. `test_cross_lock_group_abba_deadlock_is_known_limitation`

Проверяет:

- сценарий ABBA deadlock между callback-ами двух независимых lock-групп рассматривается как известное ограничение и не входит в обязательный основной suite.

Статус:

- это не обязательный исполняемый тест первой волны;
- достаточно документировать его в коде/плане как known limitation или отдельный demo/xfail-набор.


## `tests/thread_safety/fields/test_base.py`

Это главный файл всего плана. Здесь сосредоточена фактическая модель многопоточного поведения библиотеки.

### Блок A. Контрактные детерминированные тесты

1. `test_writes_to_same_field_are_serialized`

Сценарий:

- поток 1 пишет значение и застревает в callback;
- поток 2 пытается писать в то же поле.

Проверки:

- второй callback не начинается до `release_event`;
- порядок событий сериализован;
- финальное значение соответствует второй записи после завершения обеих операций.

2. `test_read_with_read_lock_waits_for_writer`

Сценарий:

- writer записывает новое значение;
- callback writer-а удерживает field mutex;
- reader ждёт `writer_entered_event` и только после этого читает поле с `read_lock=True`.

Проверки:

- reader не завершился до `release_event`;
- после release reader вернул уже новое значение.

3. `test_write_visibility_across_threads`

Сценарий:

- writer записывает новое значение и после этого подает явный сигнал читателю;
- reader запускается заранее, сразу делает `signal_event.wait()`, и только после разблокировки начинает чтение.

Проверки:

- reader видит новое значение;
- тест фиксирует visibility обычной записи между потоками.

Замечание:

- тест на `read_lock=False` в формулировке "reader не ждет callback и получает новое значение" исключен из плана как недетерминированный.

4. `test_writes_to_conflicting_fields_are_serialized_by_shared_mutex`

Сценарий:

- `a: int = Field(0, conflicts={'b': lambda old_a, new_a, old_b, new_b: new_a > 0 and new_b > 0})`
- `b: int = Field(0)`
- поток 1 пишет `a = 1` и удерживает callback;
- поток 2 ждёт `writer_1_entered_event` и только после этого пытается написать `b = 1`.

Проверки:

- пока первый поток удерживает mutex, второй не завершает операцию;
- после release второй поток получает `ValueError`;
- финальное состояние удовлетворяет конфликтному инварианту.

Замечание:

- `writer_1_entered_event` должен выставляться после фактической записи нового значения и при входе в callback;
- это важно, чтобы второй поток проверял конфликт уже против закоммиченного значения первого поля.

5. `test_writes_to_non_conflicting_fields_do_not_block_each_other_on_field_lock`

Сценарий:

- два поля не делят mutex;
- оба callback-а блокируются на общем `release_event`.
- поток 2 ждёт `writer_1_entered_event` перед своей записью.

Проверки:

- при управляемом interleaving второй writer может войти в свой callback до `release_event`, пока первый writer еще удерживает свой mutex;
- это показывает отсутствие обязательной блокировки writer 2 на field lock writer-а 1 в данном сценарии;
- тест не трактуется как доказательство общего параллелизма или fairness планировщика.

6. `test_callback_exception_releases_lock`

Сценарий:

- поток 1 пишет в поле;
- callback этого поля выбрасывает исключение внутри `with self.get_field_lock(instance)`;
- поток 2 после этого пытается записать в то же поле.

Проверки:

- исключение из callback не оставляет lock захваченным;
- поток 2 успешно завершает запись и не зависает на освобожденном mutex.

### Блок B. Reentrant/deadlock detection через `locklib`

Все тесты этого блока нужно явно называть как `locklib`/`dev_mode`, чтобы не смешивать их с production-гарантиями.

1. `test_callback_reading_same_field_with_read_lock_raises_locklib_error`

Сценарий:

- конфигурация вида:
  - `field = Field(0, read_lock=True, action=lambda old, new, storage: storage.field)`
- lock поля подменен через `replace_field_lock_with_locklib_lock`.

Проверка:

- вместо silent hang в dev-режиме получаем исключение от `locklib`.

2. `test_callback_writing_same_field_raises_locklib_error`

Сценарий:

- конфигурация вида:
  - `field = Field(0, action=lambda old, new, storage: setattr(storage, 'field', 2))`
- lock поля подменен через `replace_field_lock_with_locklib_lock`.

Проверка:

- повторный захват того же lock детектируется исключением.

3. `test_callback_accessing_shared_mutex_field_raises_locklib_error`

Сценарий:

- конфигурация вида:
  - `a = Field(0, share_mutex_with=['b'], action=lambda old, new, storage: storage.b)`
  - `b = Field(0, read_lock=True)`
- вся lock-группа `a`/`b` перепривязана на один и тот же `locklib`-lock.

Проверка:

- повторный вход в ту же lock-группу детектируется.

4. `test_callback_accessing_conflicting_field_raises_locklib_error`

Сценарий:

- конфигурация вида:
  - `a = Field(0, conflicts={'b': lambda *_: False}, action=lambda old, new, storage: storage.b)`
  - `b = Field(0, read_lock=True)`
- вся lock-группа `a`/`b` перепривязана на один и тот же `locklib`-lock.

Проверка:

- повторный вход в общую lock-группу детектируется.

5. `test_conflict_checker_accessing_locked_field_raises_locklib_error`

Сценарий:

- конфигурация вида:
  - `a = Field(0, conflicts={'b': checker})`
  - `b = Field(0, read_lock=True)`
- `checker` замыкает `instance` и делает `instance.b`;
- checker вызывается под mutex поля `a`;
- вся lock-группа перепривязана на один и тот же `locklib`-lock.

Проверка:

- вместо silent hang в dev-режиме получаем исключение.

Уточнение:

- этот тест не опирается на внутренний `other_field.unlocked_get(...)` внутри `Field.__set__`;
- reentrant происходит именно потому, что пользовательский `checker` сам делает `instance.b`, а у `b` включен `read_lock=True`.

Статус:

- это полноценный тест плана, не "может быть".

### Блок C. Stress-тесты

Stress-тесты должны быть короткими и проверять только сильные инварианты.

Фиксированные параметры:

- `NUM_THREADS = 10`
- `ITERATIONS = 100`
- для mixed reader/writer сценария: `NUM_WRITERS = 5`, `NUM_READERS = 5`

1. `test_stress_many_threads_read_and_write_field_with_read_lock`

Проверки:

- нет неожиданных исключений;
- все прочитанные значения принадлежат допустимому множеству;
- читатели видят только целые допустимые значения, а не какое-либо "промежуточное состояние".

2. `test_stress_many_threads_write_conflicting_fields`

Проверки:

- допускаются только ожидаемые `ValueError`;
- финальное состояние не нарушает конфликтный инвариант.

Статус остальных stress-идей:

- `many_threads_overwrite_same_field` — слишком слабый oracle, не входит в обязательный слой;
- `many_threads_write_independent_fields` — в текущем виде тоже низкосигнальный, не входит в обязательный слой, пока не появится oracle против нежелательной глобальной сериализации.

### Что в этот файл сознательно не включать

- тесты на "настоящий дедлок" через зависание потока;
- тесты на `validation`/`conversion` в реальных потоках, если ради этого придется делать хрупкие сценарии;
- стресс-тесты с большими объемами итераций "на удачу";
- тесты на недетерминированное поведение `read_lock=False` без специального hook-а в internals.


## `tests/thread_safety/functions/test_asdict.py`

Этот файл стоит включить в план, потому что у `asdict()` есть не только особый механизм чтения, но и важное конкурентное последствие: он не является консистентным snapshot API.

### Контрактные тесты

1. `test_asdict_can_return_inconsistent_snapshot`

Сценарий:

- один поток последовательно обновляет несколько полей;
- после первой записи writer выставляет `first_write_done_event`;
- затем writer ждёт `snapshot_done_event` и только потом делает вторую запись;
- другой поток ждёт `first_write_done_event`, вызывает `asdict()`, затем выставляет `snapshot_done_event`.

Проверяет:

- `asdict()` может вернуть частично обновленный multi-field snapshot;
- это тест именно на наблюдаемое последствие, а не только на механизм.

Сильный oracle:

- writer делает, например, `a = 1`, затем ждет snapshotter-а, затем делает `b = 2`;
- snapshotter должен получить состояние вида `{'a': 1, 'b': old_b}`;
- тест проверяет именно конкретное промежуточное состояние, а не абстрактную "частичную обновленность".

### Stress-тесты

Не нужны.


## Что сознательно не входит в этот план

- `__repr__()` как консистентный snapshot;
- in-place mutation mutable значений (`list.append`, `dict.__setitem__` и т.п.);
- `cached_property` в sources;
- динамическое создание `Storage`-классов из нескольких потоков;
- сценарии с partially initialized object из `__init__`;
- доказательство реального deadlock через зависание или time-based ожидание.
- семантический тест `reverse_conflicts=False`, если он не проверяет собственно многопоточное поведение.
- concurrent-init smoke как обязательный контрактный тест.
- отдельное покрытие free-threading режима как обязательная часть первой волны.
- ABBA deadlock между callback-ами разных lock-групп как обязательный тест первой волны.

Причина:

- либо это не часть основного наблюдаемого контракта библиотеки;
- либо такие тесты будут низкосигнальными и хрупкими;
- либо тема лучше решается документацией, а не основным regression suite.

### Future work

- Запуск `tests/thread_safety` в free-threading окружении Python 3.13t+ после стабилизации базового suite.
- Отдельная оценка сценариев, где `unlocked_get` читает значение поля, защищенного другим lock, в условиях free-threading.
- При необходимости добавить или перенести в `tests/units` тест `reverse_conflicts=False` как отдельную проверку семантики API.
- При необходимости вернуть concurrent-init smoke как optional/non-blocking набор.
- Cross-lock-group ABBA deadlock сценарии через callback-и двух независимых lock-групп как отдельный known-limitation/demo-набор.
- При необходимости добавить optional smoke-тест на concurrent init с общим `default_factory`, если появится практический сигнал, что этот сценарий важен.
- При необходимости задокументировать как design decision, что `read_only` проверяется до захвата field lock.

Оговорка про free-threading:

- тесты первой волны должны проектироваться так, чтобы их oracle-ы не зависели от GIL;
- если какой-то тест окажется нестабильным под free-threading интерпретатором, это будет считаться дефектом теста или скрытой зависимостью от текущей модели выполнения.


## Прикладная матрица

### `tests/thread_safety/conftest.py`

Назначение:

- общие helper-ы и фикстуры для всего раздела.

| Helper / fixture | Для чего нужен | Где будет использоваться |
|---|---|---|
| `run_in_thread` | запуск target в потоке с возвратом результата/ошибки | почти все тесты в `fields/test_base.py`, часть тестов в `functions/test_asdict.py` |
| `collect_thread_outcome` | извлечение результата или исключения из очереди с дефолтным timeout `5` секунд и возможностью увеличить его для stress | почти все поточные тесты |
| `event_log` | фиксация порядка событий | детерминированные tests и dev-mode tests |
| `make_gate_callback` | удержание callback внутри critical section | serialization/conflicts/independent-fields tests |
| `replace_field_lock_with_locklib_lock` | подмена всей lock-группы на один dev-mode anti-deadlock lock с проверкой `expected_group_fields` | reentrant/deadlock tests |
| `start_barrier` | helper для создания `Barrier(n)` под конкретный тест | stress-тесты |
| `thread_safety` marker | отдельный marker для набора thread-safety тестов | весь каталог `tests/thread_safety` |

### `tests/thread_safety/test_storage.py`

Назначение:

- lock topology и группировка mutex-ов.

| Тест | Что проверяет | Helper-ы |
|---|---|---|
| `test_share_mutex_with_is_transitive` | транзитивное объединение lock-группы | не нужны |
| `test_share_mutex_with_and_conflicts_merge_into_one_group` | объединение `share_mutex_with` + `conflicts` | не нужны |
| `test_independent_fields_use_different_mutexes` | раздельные поля не делят lock | не нужны |
| `test_two_instances_do_not_share_mutex_groups` | mutex-ы независимы между instance-ами, если этот тест нужен сверх unit-аналога | не нужны |

### `tests/thread_safety/test_known_limitations.py`

Назначение:

- фиксация известных ограничений текущей реализации отдельно от основного контрактного слоя.

| Тест | Что проверяет | Helper-ы |
|---|---|---|
| `test_lock_group_topology_is_order_dependent_for_connected_graph` | order-sensitive контрпример фиксирует known limitation текущего алгоритма сборки lock-групп | не нужны |
| `test_cross_lock_group_abba_deadlock_is_known_limitation` | ABBA deadlock между независимыми lock-группами задокументирован как known limitation | не нужны или отдельный demo helper |

### `tests/thread_safety/fields/test_base.py`

Назначение:

- все реальные контрактные проверки конкурентного поведения `Field`.

| Тест | Что проверяет | Helper-ы |
|---|---|---|
| `test_writes_to_same_field_are_serialized` | записи в одно поле сериализуются | `run_in_thread`, `collect_thread_outcome`, `event_log`, `make_gate_callback` |
| `test_read_with_read_lock_waits_for_writer` | `read_lock=True` реально блокирует reader | `run_in_thread`, `collect_thread_outcome`, `event_log`, `make_gate_callback` |
| `test_write_visibility_across_threads` | запись одного потока становится видимой другому | `run_in_thread`, `collect_thread_outcome`, `event_log` |
| `test_writes_to_conflicting_fields_are_serialized_by_shared_mutex` | конфликтующие поля используют одну критическую секцию и дают ожидаемый `ValueError` | `run_in_thread`, `collect_thread_outcome`, `event_log`, `make_gate_callback` |
| `test_writes_to_non_conflicting_fields_do_not_block_each_other_on_field_lock` | независимые поля не блокируют друг друга на field lock | `run_in_thread`, `collect_thread_outcome`, `event_log`, `make_gate_callback` |
| `test_callback_exception_releases_lock` | исключение из callback не оставляет mutex захваченным | `run_in_thread`, `collect_thread_outcome`, `event_log`, `make_gate_callback` |
| `test_callback_reading_same_field_with_read_lock_raises_locklib_error` | reentrant read через callback детектируется в dev-режиме | `replace_field_lock_with_locklib_lock` |
| `test_callback_writing_same_field_raises_locklib_error` | reentrant write через callback детектируется в dev-режиме | `replace_field_lock_with_locklib_lock` |
| `test_callback_accessing_shared_mutex_field_raises_locklib_error` | повторный вход в shared mutex-группу детектируется в dev-режиме | `replace_field_lock_with_locklib_lock` |
| `test_callback_accessing_conflicting_field_raises_locklib_error` | повторный вход в conflict mutex-группу детектируется в dev-режиме | `replace_field_lock_with_locklib_lock` |
| `test_conflict_checker_accessing_locked_field_raises_locklib_error` | checker не может безопасно повторно входить в lock в dev-режиме | `replace_field_lock_with_locklib_lock` |
| `test_stress_many_threads_read_and_write_field_with_read_lock` | readers/writers при `read_lock=True` | `run_in_thread`, `collect_thread_outcome`, `start_barrier` |
| `test_stress_many_threads_write_conflicting_fields` | массовая запись в конфликтующие поля | `run_in_thread`, `collect_thread_outcome`, `start_barrier` |

### `tests/thread_safety/functions/test_asdict.py`

Назначение:

- фиксация ограничений `asdict()` в конкурентной среде.

| Тест | Что проверяет | Helper-ы |
|---|---|---|
| `test_asdict_can_return_inconsistent_snapshot` | `asdict()` может вернуть частично обновленный multi-field snapshot | `run_in_thread`, `collect_thread_outcome`, `event_log` |


## Порядок внедрения

### Этап 1. Основа

Сделать:

- `tests/thread_safety/conftest.py`
- `tests/thread_safety/test_storage.py`
- `tests/thread_safety/test_known_limitations.py`
- регистрация `thread_safety` marker в `pyproject.toml`

Сразу договориться:

- order-sensitive topology test в первой волне живет в known-limitations слое, а не среди основных контрактных тестов.

### Этап 2. Основные контрактные тесты

Сделать в `tests/thread_safety/fields/test_base.py`:

- serialization writes;
- `read_lock=True`;
- visibility;
- conflicting fields;
- independent fields;
- callback exception releases lock;

### Этап 3. Dev-mode anti-deadlock слой

Сделать:

- reentrant tests через `locklib`.

### Этап 4. Stress-слой

Сделать:

- 2 stress-теста только для наиболее частых и действительно сигнальных сценариев.

### Этап 5. `asdict()`

Сделать:

- `tests/thread_safety/functions/test_asdict.py` с тестами на ограничения snapshot API.

### Этап 6. CI

Сделать:

- зарегистрировать `thread_safety` marker в `pyproject.toml`;
- запускать `tests/thread_safety` в основном CI;
- при необходимости выделить known-limitations тесты в отдельный job или marker, чтобы они не смешивались с основным сигналом регрессий;
- использовать стандартные `thread_safety` тесты как основной сигнал регрессий, а known-limitations слой как вспомогательный диагностический набор.


## Итоговый минимальный состав первой полноценной версии

- `tests/thread_safety/conftest.py`
- `tests/thread_safety/test_storage.py` — 4 обязательных теста и 1 опциональный
- `tests/thread_safety/test_known_limitations.py` — 1-2 known-limitation теста
- `tests/thread_safety/fields/test_base.py`
  - 6 детерминированных контрактных thread-safety тестов
  - 5 dev-mode anti-deadlock тестов через `locklib`
  - 2 stress-теста
- `tests/thread_safety/functions/test_asdict.py` — 1 детерминированный тест

Итог:

- suite остается компактным;
- покрывает основные гарантии и важные ограничения;
- не опирается на `sleep()`;
- использует таймауты только как safeguard от подвешивания CI;
- честно разделяет production-контракты и dev-mode deadlock detection.
