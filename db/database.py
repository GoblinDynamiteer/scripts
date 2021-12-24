from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto


class DatabaseType(Enum):
    JSON = auto()
    Mongo = auto()


class KeyType(Enum):
    Integer = auto()
    String = auto()
    List = auto()
    Boolean = auto()


@dataclass
class Key:
    name: str
    type: KeyType = KeyType.String
    primary: bool = False
    optional: bool = True

    def __str__(self):
        return self.name

    def matches_type(self, obj: Any) -> bool:
        if obj is None and self.optional:
            return not self.primary
        if isinstance(obj, str) and self.type == KeyType.String:
            return True
        if isinstance(obj, int) and self.type == KeyType.Integer:
            return True
        if isinstance(obj, bool) and self.type == KeyType.Boolean:
            return True
        if isinstance(obj, list) and self.type == KeyType.List:
            return True
        return False


class Entry:
    def __init__(self, data: Optional[Dict] = None):
        self._data: Dict[str] = data or {}

    def update(self, key: str, val: Any):
        self._data[key] = val

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key, None)

    def data(self) -> Dict:
        return self._data

    def __str__(self):
        return f"Entry: {self._data}"

    def __eq__(self, other: "Entry"):
        return self._data == other._data


class DataBase(ABC):
    def __init__(self):
        self._keys: List[Key] = []
        self._entry_primary_value_cache: Optional[Tuple[Any]] = None

    @abstractmethod
    def save(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def load(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_entry(self, entry_primary_value: str) -> Optional[Entry]:
        raise NotImplementedError

    @abstractmethod
    def entry_primary_values(self) -> Tuple[Any]:
        raise NotImplementedError

    @abstractmethod
    def find(self,
             filter_by: Optional[Dict[str, Any]] = None,
             sort_by_key: Optional[str] = None,
             limit: Optional[int] = None,
             reversed_sort: bool = False) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def update_entry(self, entry: Entry) -> bool:
        raise NotImplementedError

    @abstractmethod
    def insert_entry(self, entry: Entry) -> bool:
        raise NotImplementedError

    @abstractmethod
    def find_duplicates(self, key: Union[Key, str]) -> Dict[Any, List[str]]:
        raise NotImplementedError

    @property
    def primary_key(self) -> Optional[Key]:
        for key in self._keys:
            if key.primary:
                return key
        return None

    def __contains__(self, primary_key_value: Any):
        if self._entry_primary_value_cache is None:
            self._entry_primary_value_cache = self.entry_primary_values()
        return primary_key_value in self._entry_primary_value_cache

    def __iter__(self):
        for name in self.entry_primary_values():
            yield name

    def set_valid_keys(self, key_list: List[Key]):
        for key in key_list:
            self._add_key(key)
        if not self.primary_key:
            self._keys[0].primary = True

    def get_keys(self) -> List[Key]:
        for key in self._keys:
            yield key

    def update(self, entry: str, **data) -> bool:
        _entry = self.get_entry(entry)
        if not _entry:
            raise ValueError(f"cannot update entry {entry}, is not in database")
        for column, value in data.items():
            _key = self._get_key(column)
            if _key is None:
                raise ValueError(f"cannot update entry {entry}, {column} is not a valid key")
            if not _key.matches_type(value):
                raise TypeError(f"value {value} is not of type {_key.type.name}")
            _entry.update(_key.name, value)
        self.update_entry(_entry)
        return True

    def insert(self, **data) -> bool:
        if self.primary_key.name not in data.keys():
            raise ValueError(f"data does not contain primary key: {self.primary_key.name}")
        new_entry = Entry()
        for column, value in data.items():
            _key = self._get_key(column)
            if _key is None:
                raise ValueError(f"cannot insert entry, {column} is not a valid key")
            if not _key.matches_type(value):
                raise TypeError(f"value {value} is not of type {_key.type.name} for key {_key}")
            if self.primary_key.name == column:
                _entry = self.get_entry(value)
                if _entry is not None:
                    raise ValueError(f"entry {self.primary_key.name}={value} already exists! use update instead!")
            self._entry_primary_value_cache = None
            new_entry.update(column, value)
        return self.insert_entry(new_entry)

    def get(self, entry_name: str, column: Union[Key, str]) -> Optional[Any]:
        _entry = self.get_entry(entry_name)
        if not _entry:
            return None
        return _entry.get(str(column))

    def _add_key(self, key: Key):
        if key.primary and self.primary_key:
            raise ValueError(f"cannot add a second primary key: {key}")
        for _key in self._keys:
            if _key.name == key.name:
                raise ValueError(f"cannot add {key}, name \"{key.name}\" is already taken")
        self._keys.append(key)

    def _get_key(self, key: Union[Key, str]) -> Optional[Key]:
        for _key in self._keys:
            if key == _key or key == _key.name:
                return _key
        return None
