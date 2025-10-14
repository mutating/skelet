from typing import TypeVar, Type, Any, Optional, Generic, Union, Callable, Dict, get_type_hints, cast
from threading import Lock

from locklib import ContextLockProtocol
from simtypes import check

from skelet.storage import Storage


ValueType = TypeVar('ValueType')

# TODO: use per-field locks to improve thread safety
class Field(Generic[ValueType]):
    def __init__(self, default: ValueType, read_only: bool = False, doc: Optional[str] = None, validation: Optional[Union[Dict[str, Callable[[ValueType], bool]], Callable[[ValueType], bool]]] = None, check_first_time: bool = True) -> None:
        self.default = default
        self.read_only = read_only
        self.doc = doc
        self.validation = validation
        self.check_first_time = check_first_time

        self.name: Optional[str] = None
        self.base_class: Optional[Type[Storage]] = None

        self.lock: ContextLockProtocol = Lock()

    def __set_name__(self, owner: Type[Storage], name: str) -> None:
        if name.startswith('_'):
            raise ValueError(f'Field name "{name}" cannot start with an underscore.')

        with self.lock:
            if self.base_class is not None:
                raise TypeError(f'{self.get_field_name_representation()} cannot be used in {owner.__name__} because it is already used in {self.base_class.__name__}.')
            if not issubclass(owner, Storage):
                raise TypeError(f'{self.get_field_name_representation()} can only be used in Storage subclasses.')

            self.name = name
            self.base_class = owner

            self.set_field_names(owner, name)
            self.check_type_hints(owner, name, self.default)
            if self.check_first_time:
                self.check_value(self.default)

    def __get__(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        if instance is None:
            return self

        with instance._lock:
            return instance.__fields__.get(cast(str, self.name), self.default)

    def __set__(self, instance: Storage, value: ValueType) -> None:
        if self.read_only:
            raise AttributeError(f'{self.get_field_name_representation()} is read-only.')

        self.check_type_hints(cast(Type[Storage], self.base_class), cast(str, self.name), value)
        self.check_value(value)

        with instance._lock:
            instance.__fields__[cast(str, self.name)] = value

    def __delete__(self, instance: Any) -> None:
        raise AttributeError(f"You can't delete the {self.get_field_name_representation()} value.")

    def set_field_names(self, owner: Type[Storage], name: str) -> None:
        if '__field_names__' not in owner.__dict__:
            owner.__field_names__ = []
            known_names = set()
            for parent in owner.__mro__:  # pragma: no cover
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

        if name not in known_names:  # pragma: no cover
            owner.__field_names__.append(name)

    def check_type_hints(self, owner: Type[Storage], name: str, value: ValueType) -> None:
        class SecondNone:
            pass

        type_hint = get_type_hints(owner).get(name, SecondNone())

        if isinstance(type_hint, SecondNone):
            return

        if not check(type_hint, value):
            raise TypeError(f'The value "{value}" ({type(value).__name__}) of the {self.get_field_name_representation()} does not match the type {type_hint.__name__}.')

    def get_field_name_representation(self) -> str:
        if self.doc is None:
            return f'"{self.name}" field'
        return f'"{self.name}" field ({self.doc})'

    def check_value(self, value: ValueType) -> None:
        if self.validation is not None:
            if isinstance(self.validation, dict):
                for message, validator in self.validation.items():
                    if not validator(value):
                        raise ValueError(message)
            else:
                if not self.validation(value):
                    raise ValueError(f'The value "{value}" ({type(value).__name__}) of the {self.get_field_name_representation()} does not match the validation function.')
