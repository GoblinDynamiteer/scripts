import json

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
    def valid(self):
        raise NotImplemented()

    @property
    @abstractmethod
    def year(self):
        raise NotImplemented()

    @property
    @abstractmethod
    def title(self):
        raise NotImplemented()

    @property
    @abstractmethod
    def genre(self):
        raise NotImplemented()

    @property
    @abstractmethod
    def id(self):
        raise NotImplemented()
