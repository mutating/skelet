from typing import TypeVar, Type, Any, Optional, Generic, cast
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

    def __get__(self, instance: Storage, instance_class: Type[Storage]) -> ValueType:
        if not isinstance(instance, Storage):
            raise TypeError(f"Field \"{self.name}\" can only be used in Storage instances.")

        with instance.lock:
            return instance.__fields__.get(cast(str, self.name), self.default)

    def __set__(self, instance: Storage, value: ValueType) -> None:
        if self.read_only:
            raise AttributeError(f'Field "{self.name}" is read-only.')

        with instance.lock:
            instance.__fields__[cast(str, self.name)] = value

    def __delete__(self, instance: Any) -> None:
        raise AttributeError(f"You can't delete the \"{self.name}\" attribute.")
