from typing import Dict, Any
from threading import Lock


class Storage:
    __fields__: Dict[str, Any]

    def __init__(self):
        self.__fields__: Dict[str, Any] = {}
        self.lock = Lock()
