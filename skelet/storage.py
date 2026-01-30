from typing import List, Dict, Optional, Any
from threading import Lock
from collections import defaultdict

from printo import descript_data_object
from locklib import ContextLockProtocol
from denial import InnerNoneType

from skelet.sources.collection import SourcesCollection
from skelet.sources.abstract import AbstractSource


sentinel = InnerNoneType()

class Storage:
    __values__: Dict[str, Any]
    __locks__: Dict[str, ContextLockProtocol]
    __field_names__: List[str] = []
    __reverse_conflicts__: Dict[str, List[str]]
    __sources__: SourcesCollection

    def __init__(self, **kwargs: Any) -> None:
        self.__values__: Dict[str, Any] = {}
        self.__locks__ = {field_name: Lock() for field_name in self.__field_names__}
        deduplicated_fields = set(self.__field_names__)

        for field_name in self.__field_names__:
            field = getattr(type(self), field_name)
            lock = self.__locks__[field_name]
            if field.conflicts is not None:
                for another_field_name in field.conflicts:
                    self.__locks__[another_field_name] = lock
            if field.share_mutex_with is not None:
                for another_field_name in field.share_mutex_with:
                    self.__locks__[another_field_name] = lock

        for field_name in self.__field_names__:
            field = getattr(type(self), field_name)
            content = field.get_sources(self).type_awared_get(field.alias, field.type_hint, sentinel)
            it_is_not_default = True
            if content is not sentinel:
                field.check_type_hints(type(self), field_name, content, strict=True, raise_all=True)
                field.check_value(content, raise_all=True)
            else:
                if field._default_factory is not None:
                    content = field._default_factory()
                    field.check_type_hints(type(self), field_name, content, strict=True, raise_all=True)
                    if field.validate_default:
                        field.check_value(content, raise_all=True)
                else:
                    it_is_not_default = False
                    content = field._default

            if field.conversion is not None and it_is_not_default:
                content = field.conversion(content)
                field.check_type_hints(type(self), field_name, content, strict=True, raise_all=True)
                if field.validate_default:
                    field.check_value(content, raise_all=True)

            self.__values__[field_name] = content

        for field_name in self.__field_names__:
            field = getattr(type(self), field_name)

            if field._default_factory is not None:
                if field.conflicts is not None:
                    for conflicting_field_name, checker in field.conflicts.items():
                        if checker(self.__values__[field_name], self.__values__[field_name], self.__values__[conflicting_field_name], self.__values__[conflicting_field_name]):
                            conflicting_field = getattr(type(self), conflicting_field_name)
                            raise ValueError(f'The {field.get_value_representation(self.__values__[field_name])} deferred default value of the {field.get_field_name_representation()} conflicts with the {conflicting_field.get_value_representation(self.__values__[conflicting_field_name])} value of the {conflicting_field.get_field_name_representation()}.')

                if field_name in self.__reverse_conflicts__:
                    conflicting_field_names = self.__reverse_conflicts__[field_name]
                    for conflicting_field_name in conflicting_field_names:
                        conflicting_field = getattr(type(self), conflicting_field_name)
                        checker = conflicting_field.conflicts[field_name]
                        if checker(self.__values__[conflicting_field_name], self.__values__[conflicting_field_name], self.__values__[field_name], self.__values__[field_name]):
                            raise ValueError(f'The {conflicting_field.get_value_representation(self.__values__[conflicting_field_name])} deferred default value of the {conflicting_field.get_field_name_representation()} conflicts with the {field.get_value_representation(self.__values__[field_name])} value of the {field.get_field_name_representation()}.')

        for key, value in kwargs.items():
            if key not in deduplicated_fields:
                raise KeyError(f'The "{key}" field is not defined.')
            setattr(self, key, value)

        for field_name in self.__field_names__:
            field_content = getattr(self, field_name)
            if isinstance(field_content, InnerNoneType):
                raise ValueError(f'The value for the "{field_name}" field is undefined. Set the default value, or specify the value when creating the instance.')


    def __init_subclass__(cls, reverse_conflicts: bool = True, sources: Optional[List[AbstractSource]] = None, **kwargs: Any):
            super().__init_subclass__(**kwargs)

            for field_name in cls.__field_names__:
                field = getattr(cls, field_name)
                if field.exception is not None:
                    raise field.exception

            cls.__sources__ = SourcesCollection(sources) if sources is not None else SourcesCollection([])

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

                if field.share_mutex_with is not None:
                    for another_field_name in field.share_mutex_with:
                        if another_field_name not in deduplicated_field_names:
                            raise NameError(f'You indicated that you need to share the mutex of {field.get_field_name_representation()} with field "{another_field_name}", but field "{another_field_name}" does not exist.')

                if field.conflicts is not None:
                    for conficting_field_name, checker in field.conflicts.items():
                        if conficting_field_name not in deduplicated_field_names:
                            raise NameError(f'You have set a conflict condition for {field.get_field_name_representation()} with field "{conficting_field_name}", but the field "{conficting_field_name}" does not exist in the class {cls.__name__}.')
                        elif not isinstance(field._default, InnerNoneType) and not isinstance(getattr(cls, conficting_field_name)._default, InnerNoneType) and reverse_conflicts and field.reverse_conflicts_on and checker(field._default, field._default, getattr(cls, conficting_field_name)._default, getattr(cls, conficting_field_name)._default):
                            other_field = getattr(cls, conficting_field_name)
                            raise ValueError(f'The {field.get_value_representation(field._default)} default value of the {field.get_field_name_representation()} conflicts with the {other_field.get_value_representation(other_field._default)} value of the {other_field.get_field_name_representation()}.')

    def __repr__(self) -> str:
        fields_content = {}
        secrets = {}

        for field_name in self.__field_names__:
            fields_content[field_name] = getattr(self, field_name)
            if getattr(type(self), field_name).secret:
                secrets[field_name] = '***'

        return descript_data_object(type(self).__name__, (), fields_content, placeholders=secrets)  # type: ignore[arg-type]
