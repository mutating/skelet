from typing import Dict, Any
from skelet.storage import Storage


def asdict(storage: Storage) -> Dict[str, Any]:
    if not isinstance(storage, Storage):
        raise TypeError('asdict() should be called on Storage class instances')

    result = {}

    for field_name, value in storage.__values__.items():
        result[field_name] = value

    return result
