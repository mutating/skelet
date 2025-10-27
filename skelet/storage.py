from typing import List, Dict, Any
from threading import Lock
from collections import defaultdict

from printo import descript_data_object
from locklib import ContextLockProtocol


class Storage:
    __fields__: Dict[str, Any]  # pragma: no cover
    __locks__: Dict[str, ContextLockProtocol]
    __field_names__: List[str] = []  # pragma: no cover
    __reverse_conflicts__: Dict[str, List[str]]

    def __init__(self, **kwargs: Any) -> None:
        self.__fields__: Dict[str, Any] = {}
        self.__locks__ = {field_name: Lock() for field_name in self.__field_names__}

        deduplicated_fields = set(self.__field_names__)
        for key, value in kwargs.items():
            if key not in deduplicated_fields:
                raise KeyError(f'The "{key}" field is not defined.')
            setattr(self, key, value)

        for field_name in self.__field_names__:
            field = getattr(type(self), field_name)
            lock = self.__locks__[field_name]
            if field.conflicts is not None:
                for another_field_name in field.conflicts:
                    self.__locks__[another_field_name] = lock

    def __init_subclass__(cls, reverse_conflicts: bool = True, **kwargs: Any):
            super().__init_subclass__(**kwargs)

            deduplicated_field_names = set(cls.__field_names__)

            cls.__reverse_conflicts__ = defaultdict(list)
            for field_name in cls.__field_names__:
                field = getattr(cls, field_name)

                if field.conflicts is not None:
                    for other_field_name in field.conflicts:
                        if field.reverse_conflicts_on and reverse_conflicts:
                            cls.__reverse_conflicts__[other_field_name].append(field_name)

            for field_name in cls.__field_names__:
                field = getattr(cls, field_name)

                if field.conflicts is not None:
                    for conficting_field_name, checker in field.conflicts.items():
                        if conficting_field_name not in deduplicated_field_names:
                            raise NameError(f'You have set a conflict condition for {field.get_field_name_representation()} with field "{conficting_field_name}", but the field "{conficting_field_name}" does not exist in the class {cls.__name__}.')
                        elif reverse_conflicts and field.reverse_conflicts_on and checker(field.default, field.default, getattr(cls, conficting_field_name).default, getattr(cls, conficting_field_name).default):
                            other_field = getattr(cls, conficting_field_name)
                            raise ValueError(f'The {field.get_value_representation(field.default)} ({type(field.default).__name__}) default value of the {field.get_field_name_representation()} conflicts with the {other_field.get_value_representation(other_field.default)} ({type(other_field.default).__name__}) value of the {other_field.get_field_name_representation()}.')

    def __repr__(self) -> str:
        fields_content = {}
        secrets = {}

        for field_name in self.__field_names__:
            fields_content[field_name] = getattr(self, field_name)
            if getattr(type(self), field_name).secret:
                secrets[field_name] = '***'

        return descript_data_object(type(self).__name__, (), fields_content, placeholders=secrets)  # type: ignore[arg-type]
