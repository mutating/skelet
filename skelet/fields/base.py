from typing import TypeVar, Type, Any, Optional, Generic, get_type_hints, cast
from threading import Lock

from locklib import ContextLockProtocol

from skelet.storage import Storage


ValueType = TypeVar('ValueType')

# TODO: use per-field locks to improve thread safety
class Field(Generic[ValueType]):
    def __init__(self, default: ValueType, read_only: bool = False) -> None:
        self.default = default
        self.read_only = read_only

        self.name: Optional[str] = None
        self.base_class: Optional[Type[Storage]] = None

        self.lock: ContextLockProtocol = Lock()

    def __set_name__(self, owner: Type[Storage], name: str) -> None:
        with self.lock:
            if self.base_class is not None:
                raise TypeError(f'Field "{name}" cannot be used in {owner.__name__} because it is already used in {self.base_class.__name__}.')
            if not issubclass(owner, Storage):
                raise TypeError(f'Field "{name}" can only be used in Storage subclasses.')

            self.name = name
            self.base_class = owner

            self.set_field_names(owner, name)
            self.check_type_hints(owner, name, self.default)

    def __get__(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        if instance is None:
            return self

        with instance._lock:
            return instance.__fields__.get(cast(str, self.name), self.default)

    def __set__(self, instance: Storage, value: ValueType) -> None:
        if self.read_only:
            raise AttributeError(f'Field "{self.name}" is read-only.')

        with instance._lock:
            instance.__fields__[cast(str, self.name)] = value

    def __delete__(self, instance: Any) -> None:
        raise AttributeError(f"You can't delete the \"{self.name}\" attribute.")

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
        type_hint = get_type_hints(owner).get(name)

        if type_hint is None:
            return

        if not isinstance(value, type_hint):
            raise TypeError(f'The default value must be an instance of the "{type_hint.__name__}" type.')
