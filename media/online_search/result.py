import json
from typing import Any, Optional, List
from abc import ABC, abstractmethod


class SearchResult(ABC):
    def __init__(self, data):
        self._raw = data

    def print(self):
        if not self._raw:
            print(None)
        _str = json.dumps(self._raw, indent=4)
        print(_str)

    def __repr__(self):
        return json.dumps(self._raw, indent=4)

    @property
    @abstractmethod
    def valid(self) -> bool:
        raise NotImplemented()

    @property
    @abstractmethod
    def year(self) -> Optional[int]:
        raise NotImplemented()

    @property
    @abstractmethod
    def title(self) -> Optional[str]:
        raise NotImplemented()

    @property
    @abstractmethod
    def genres(self) -> Optional[List[str]]:
        raise NotImplemented()

    @property
    @abstractmethod
    def id(self) -> Any:
        raise NotImplemented()
