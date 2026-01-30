from typing import TypeVar, Type, Any, Optional, Generic, Union, Callable, Dict, List, get_type_hints, get_origin, cast

try:
    from types import EllipsisType  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    EllipsisType = type(...)  # type: ignore[misc]

from threading import Lock
from collections.abc import Sequence
from sys import version_info

from locklib import ContextLockProtocol
from simtypes import check
from denial import InnerNoneType

from skelet.storage import Storage
from skelet.sources.abstract import AbstractSource
from skelet.sources.collection import SourcesCollection


ValueType = TypeVar('ValueType')

if version_info < (3, 9):  # pragma: no cover
    SequenceWithStrings = Sequence
else:  # pragma: no cover
    SequenceWithStrings = Sequence[str]  # type: ignore[misc, assignment]

sentinel = InnerNoneType()

class Field(Generic[ValueType]):
    def __init__(
        self,
        default: Union[ValueType, InnerNoneType] = sentinel,
        /,
        default_factory: Optional[Callable[[], ValueType]] = None,
        doc: Optional[str] = None,
        alias: Optional[str] = None,
        sources: Optional[List[Union[AbstractSource, EllipsisType]]] = None,
        read_only: bool = False,
        validation: Optional[Union[Dict[str, Callable[[ValueType], bool]], Callable[[ValueType], bool]]] = None,
        validate_default: bool = True,
        secret: bool = False,
        change_action: Optional[Callable[[ValueType, ValueType, Storage], Any]] = None,
        read_lock: bool = False,
        conflicts: Optional[Dict[str, Callable[[ValueType, ValueType, Any, Any], bool]]] = None,
        reverse_conflicts: bool = True,
        conversion: Optional[Callable[[ValueType], ValueType]] = None,
        share_mutex_with: Optional[SequenceWithStrings] = None,
    ) -> None:
        if default_factory is not None and default is not sentinel:
            raise ValueError('You can define a default value or a factory for default values, but not all at the same time.')

        if conversion is not None and default is not sentinel:
            self._default_before_conversion: Union[ValueType, InnerNoneType] = default
            self._default: Union[ValueType, InnerNoneType] = conversion(cast(ValueType, default))
        else:
            self._default_before_conversion = sentinel
            self._default = default

        self._default_factory = default_factory
        self.read_only = read_only
        self.doc = doc
        self.alias = alias
        self.sources = sources
        self.validation = validation
        self.validate_default = validate_default
        self.secret = secret
        self.change_action = change_action
        self.conflicts = conflicts
        self.reverse_conflicts_on = reverse_conflicts
        self.conversion = conversion
        self.share_mutex_with = share_mutex_with

        self.name: Optional[str] = None
        self.base_class: Optional[Type[Storage]] = None
        self.exception: Optional[BaseException] = None
        self.type_hint = Any

        self.lock: ContextLockProtocol = Lock()

        if read_lock:
            self.real_get = self.locked_get  # type: ignore[method-assign]
        else:
            self.real_get = self.unlocked_get  # type: ignore[method-assign]

    def __set_name__(self, owner: Type[Storage], name: str) -> None:
        if name.startswith('_'):
            self.raise_exception_in_storage(ValueError(f'Field name "{name}" cannot start with an underscore.'), raising_on=False)

        with self.lock:
            self.name = name
            if self.alias is None:
                self.alias = self.name
            self.type_hint = get_type_hints(owner).get(name, Any)

            if self.base_class is not None:
                self.raise_exception_in_storage(TypeError(f'{self.get_field_name_representation()} cannot be used in {owner.__name__} because it is already used in {self.base_class.__name__}.'), raising_on=False)

            if not issubclass(owner, Storage):
                self.raise_exception_in_storage(TypeError(f'{self.get_field_name_representation()} can only be used in Storage subclasses.'), raising_on=True)

            self.base_class = owner

            if self._default_before_conversion is not sentinel:
                self.check_type_hints(owner, name, cast(ValueType, self._default_before_conversion))

            self.set_field_names(owner, name)
            if self._default is not sentinel:
                self.check_type_hints(owner, name, cast(ValueType, self._default))
                if self.validate_default:
                    self.check_value(cast(ValueType, self._default))

    def __get__(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        if instance is None:
            return self

        return self.real_get(instance, instance_class)

    def real_get(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        raise NotImplementedError('If you see this error, it means something is broken.')  # pragma: no cover

    def locked_get(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        with self.get_field_lock(instance):
            return self.unlocked_get(instance, instance_class)

    def unlocked_get(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        return cast(ValueType, instance.__values__.get(cast(str, self.name)))

    def __set__(self, instance: Storage, value: ValueType) -> None:
        if self.read_only:
            raise AttributeError(f'{self.get_field_name_representation()} is read-only.')

        self.check_type_hints(cast(Type[Storage], self.base_class), cast(str, self.name), value, raise_all=True)

        if self.conversion is not None:
            value = self.conversion(value)
            self.check_type_hints(cast(Type[Storage], self.base_class), cast(str, self.name), value, raise_all=True)

        self.check_value(value, raise_all=True)

        with self.get_field_lock(instance):
            old_value = self.unlocked_get(instance, type(instance))
            if self.conflicts is not None:
                for other_field_name, checker in self.conflicts.items():
                    other_field = getattr(type(instance), other_field_name)
                    other_field_value = other_field.unlocked_get(instance, type(instance))
                    if checker(old_value, value, other_field_value, other_field_value):
                        raise ValueError(f'The new {self.get_value_representation(value)} value of the {self.get_field_name_representation()} conflicts with the {other_field.get_value_representation(other_field_value)} value of the {other_field.get_field_name_representation()}.')

            if self.name in instance.__reverse_conflicts__:
                for other_field_name in instance.__reverse_conflicts__[self.name]:
                    other_field = getattr(type(instance), other_field_name)
                    other_field_value = other_field.unlocked_get(instance, type(instance))
                    other_field_checker = other_field.conflicts[self.name]
                    if other_field_checker(other_field_value, other_field_value, old_value, value):
                        raise ValueError(f'The new {self.get_value_representation(value)} value of the {self.get_field_name_representation()} conflicts with the {other_field.get_value_representation(other_field_value)} value of the {other_field.get_field_name_representation()}.')

            instance.__values__[cast(str, self.name)] = value
            if self.change_action is not None and value != old_value:
                self.change_action(old_value, value, instance)

    def __delete__(self, instance: Any) -> None:
        raise AttributeError(f"You can't delete the {self.get_field_name_representation()} value.")

    def set_field_names(self, owner: Type[Storage], name: str) -> None:
        if '__field_names__' not in owner.__dict__:
            owner.__field_names__ = []
            known_names = set()
            for parent in owner.__mro__:  # pragma: no branch
                if parent is owner:
                    continue
                elif parent is Storage:
                    break
                else:
                    for field_name in cast(Storage, parent).__field_names__:
                        if field_name not in known_names:
                            known_names.add(field_name)
                            owner.__field_names__.append(field_name)
        else:
            known_names = set(owner.__field_names__)

        if name not in known_names:  # pragma: no branch
            owner.__field_names__.append(name)

    def check_type_hints(self, owner: Type[Storage], name: str, value: ValueType, strict: bool = False, raise_all: bool = False) -> None:
        if not check(value, self.type_hint, strict=strict):  # type: ignore[arg-type]
            origin = get_origin(self.type_hint)
            type_hint_name = self.type_hint.__name__ if origin is None else origin.__name__ if hasattr(origin, '__name__') else repr(origin)  # type: ignore[attr-defined]
            self.raise_exception_in_storage(TypeError(f'The value {self.get_value_representation(value)} of the {self.get_field_name_representation()} does not match the type {type_hint_name}.'), raise_all)

    def get_field_name_representation(self) -> str:
        if self.doc is None:
            return f'"{self.name}" field'
        return f'"{self.name}" field ({self.doc})'

    def check_value(self, value: ValueType, raise_all: bool = False) -> None:
        if self.validation is not None:
            if isinstance(self.validation, dict):
                for message, validator in self.validation.items():
                    if not validator(value):
                        self.raise_exception_in_storage(ValueError(message), raise_all)
            else:
                if not self.validation(value):
                    self.raise_exception_in_storage(ValueError(f'The value {self.get_value_representation(value)} of the {self.get_field_name_representation()} does not match the validation.'), raise_all)

    def get_field_lock(self, instance: Storage) -> ContextLockProtocol:
        return instance.__locks__[cast(str, self.name)]

    def get_value_representation(self, value: ValueType) -> str:
        base = '***' if self.secret else f'{repr(value)}'
        return f'{base} ({type(value).__name__})'

    def raise_exception_in_storage(self, exception: BaseException, raising_on: bool) -> None:
        if raising_on:
            raise exception
        self.exception = exception

    def get_sources(self, instance: Storage) -> SourcesCollection:
        if self.sources is None:
            return instance.__sources__

        result = []
        there_is_ellipsis = False

        for source in self.sources:
            if source is Ellipsis:
                there_is_ellipsis = True
            else:
                result.append(source)

        if there_is_ellipsis:
           result.extend(instance.__sources__.sources)

        return SourcesCollection(result)
