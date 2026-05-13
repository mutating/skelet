import inspect
from collections import defaultdict
from threading import Lock
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
    get_origin,
)

from denial import InnerNoneType
from locklib import ContextLockProtocol
from printo import describe_call

from skelet.sources.abstract import AbstractSource, ExpectedType
from skelet.sources.collection import SourcesCollection
from skelet.types import InstanceSourceItem

_GetAnnotations = Callable[..., Dict[str, Any]]
_get_annotations: Optional[_GetAnnotations]
try:  # pragma: no cover
    from annotationlib import (  # type: ignore[import-not-found, unused-ignore]
        get_annotations as _annotationlib_get_annotations,
    )
except ImportError:  # pragma: no cover
    _get_annotations = cast(Optional[_GetAnnotations], getattr(inspect, 'get_annotations', None))
else:  # pragma: no cover
    _get_annotations = cast(_GetAnnotations, _annotationlib_get_annotations)


def get_annotations(obj: Any, *, globals: Any = None, locals: Any = None, eval_str: bool = False) -> Dict[str, Any]:  # noqa: A002  # pragma: no cover
    if _get_annotations is not None:
        return dict(_get_annotations(obj, globals=globals, locals=locals, eval_str=eval_str))
    return dict(getattr(obj, '__dict__', {}).get('__annotations__', {}))

sentinel = InnerNoneType()

class Storage:
    __values__: Dict[str, Any]
    __locks__: Dict[str, ContextLockProtocol]
    __field_names__: Union[List[str], Tuple[str, ...]] = ()
    __reverse_conflicts__: Dict[str, List[str]]
    __sources__: SourcesCollection  # type: ignore[type-arg]
    __instance_sources__: Optional[Sequence[InstanceSourceItem]]

    @staticmethod
    def _validate_instance_sources(raw: Optional[Sequence['InstanceSourceItem']]) -> Optional[Sequence['InstanceSourceItem']]:
        if raw is None:
            return None
        if not isinstance(raw, (list, tuple)):
            raise TypeError('_sources must be a list or a tuple.')
        for item in raw:
            if item is not Ellipsis and not isinstance(item, AbstractSource):
                raise TypeError(f'Each element of _sources must be a source or Ellipsis, got {type(item).__name__}.')
        return raw

    @staticmethod
    def _is_classvar_annotation(type_hint: Any) -> bool:
        return type_hint is ClassVar or get_origin(type_hint) is ClassVar

    @staticmethod
    def _can_be_shorthand_default(value: Any) -> bool:
        if isinstance(value, (staticmethod, classmethod, property, type)):
            return False
        return not (hasattr(value, '__get__') or hasattr(value, '__set__') or hasattr(value, '__delete__'))

    @classmethod
    def _parent_field_names(cls) -> List[str]:
        result: List[str] = []
        known_names = set()
        local_names = set(cls.__dict__)

        for parent in cls.__mro__:
            if parent is cls:
                continue
            if parent is Storage:
                break
            for field_name in getattr(parent, '__field_names__', ()):
                if field_name not in known_names and field_name not in local_names:
                    known_names.add(field_name)
                    result.append(field_name)

        return result

    @classmethod
    def _prepare_shorthand_fields(cls) -> None:
        from skelet.fields.base import Field, FieldDescriptor  # noqa: PLC0415

        annotations = dict(get_annotations(cls))
        classvar_names = {name for name, annotation in annotations.items() if cls._is_classvar_annotation(annotation)}

        for name in classvar_names:
            if isinstance(cls.__dict__.get(name), FieldDescriptor):
                raise TypeError(f'ClassVar field "{name}" cannot be defined as a skelet field.')

        for name in annotations:
            if name in classvar_names:
                continue
            if name.startswith('_'):
                raise ValueError(f'Field name "{name}" cannot start with an underscore.')

        for name in annotations:
            if name in classvar_names:
                continue

            if name not in cls.__dict__:
                field = cast(FieldDescriptor[Any, Any], Field())
                setattr(cls, name, field)
                field.__set_name__(cls, name)
                continue

            value = cls.__dict__[name]
            if isinstance(value, FieldDescriptor) or not cls._can_be_shorthand_default(value):
                continue

            field = cast(FieldDescriptor[Any, Any], Field(value))
            setattr(cls, name, field)
            field.__set_name__(cls, name)

        for name, value in tuple(cls.__dict__.items()):
            if name.startswith('_') or name in annotations:
                continue
            if isinstance(value, FieldDescriptor) or not cls._can_be_shorthand_default(value):
                continue

            field = cast(FieldDescriptor[Any, Any], Field(value))
            setattr(cls, name, field)
            field.__set_name__(cls, name)

        annotated_field_names = []
        data_field_names = []
        for name in annotations:
            if name in classvar_names:
                continue
            if isinstance(cls.__dict__.get(name), FieldDescriptor):
                annotated_field_names.append(name)

        for name, value in cls.__dict__.items():
            if name in annotations or name.startswith('_'):
                continue
            if isinstance(value, FieldDescriptor):
                data_field_names.append(name)

        result = cls._parent_field_names()
        result.extend([*annotated_field_names, *data_field_names])

        cls.__field_names__ = result if result else ()

    def __init__(self, *, _sources: Optional[Sequence['InstanceSourceItem']] = None, **kwargs: Any) -> None:
        self.__instance_sources__ = self._validate_instance_sources(_sources)

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
            if content is not sentinel:
                content = field.prepare_value(content, strict=True, validate=True, raise_all=True)
            elif field._default_factory is not None:
                content = field._default_factory()
                content = field.prepare_value(content, strict=True, validate=field.validate_default, raise_all=True)
            else:
                content = field._default

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


    def __init_subclass__(cls, reverse_conflicts: bool = True, sources: Optional[List[AbstractSource[ExpectedType]]] = None, **kwargs: Any):
            super().__init_subclass__(**kwargs)

            cls._prepare_shorthand_fields()

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
                        if not isinstance(field._default, InnerNoneType) and not isinstance(getattr(cls, conficting_field_name)._default, InnerNoneType) and reverse_conflicts and field.reverse_conflicts_on and checker(field._default, field._default, getattr(cls, conficting_field_name)._default, getattr(cls, conficting_field_name)._default):
                            other_field = getattr(cls, conficting_field_name)
                            raise ValueError(f'The {field.get_value_representation(field._default)} default value of the {field.get_field_name_representation()} conflicts with the {other_field.get_value_representation(other_field._default)} value of the {other_field.get_field_name_representation()}.')

    def __repr__(self) -> str:
        fields_content = {}
        hidden_placeholders = {}

        for field_name in self.__field_names__:
            fields_content[field_name] = getattr(self, field_name)
            if getattr(type(self), field_name).hide:
                hidden_placeholders[field_name] = '***'

        return describe_call(type(self).__name__, (), fields_content, placeholders=hidden_placeholders)  # type: ignore[arg-type]
