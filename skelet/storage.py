from typing import List, Dict, Any
from threading import Lock

from printo import descript_data_object


class Storage:
    __fields__: Dict[str, Any]  # pragma: no cover
    __field_names__: List[str] = []  # pragma: no cover

    def __init__(self, **kwargs: Any) -> None:
        self.__fields__: Dict[str, Any] = {}
        self.__locks__ = {field_name: Lock() for field_name in self.__field_names__}

        deduplicated_fields = set(self.__field_names__)
        for key, value in kwargs.items():
            if key not in deduplicated_fields:
                raise KeyError(f'The "{key}" field is not defined.')
            setattr(self, key, value)

    def __repr__(self) -> str:
        fields_content = {}
        secrets = {}

        for field_name in self.__field_names__:
            fields_content[field_name] = getattr(self, field_name)
            if getattr(type(self), field_name).secret:
                secrets[field_name] = '***'

        return descript_data_object(type(self).__name__, (), fields_content, placeholders=secrets)
