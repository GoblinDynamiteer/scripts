from enum import Enum, auto
from typing import Optional, Union, Any, List, Dict
from dataclasses import dataclass

import pymongo  # Do not use "from pymongo import MongoClient", mongomock in unit tests require this way...
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.collection import Collection

from db.database import DataBase, Key, Entry, KeyType


@dataclass
class MongoDbSettings:
    ip: str
    username: str
    password: str
    database_name: str
    collection_name: str
    port: int = 27017


class MongoDatabase(DataBase):
    class State(Enum):
        NotInitialized = auto()
        Connected = auto()
        FailedToConnect = auto()

    def __init__(self, settings: MongoDbSettings):
        super().__init__()
        self._new_entries = List[Entry]
        self._client: Optional[pymongo.MongoClient] = None
        self._collection: Optional[Collection] = None
        self._state: MongoDatabase.State = self.State.NotInitialized
        self._settings: MongoDbSettings = settings
        self._connect()

    def _connect(self) -> bool:
        if self._state == self.State.Connected:
            return True
        if self._client is None:
            self._client = pymongo.MongoClient(self._settings.ip,
                                               self._settings.port,
                                               username=self._settings.username,
                                               password=self._settings.password,
                                               serverSelectionTimeoutMS=1000)
            try:
                self._client.server_info()
            except ServerSelectionTimeoutError as _:
                self._state = self.State.FailedToConnect
                raise ConnectionError("Failed to connect to mongodb!")
        _db_name = self._settings.database_name
        if _db_name not in self._client.list_database_names():
            raise ValueError(f"database {_db_name} does not exist!")
        _db = self._client[_db_name]
        _coll_name = self._settings.collection_name
        if _coll_name not in _db.list_collection_names():
            raise ValueError(f"collection {_coll_name} does not exist in db {_coll_name}")
        self._collection = self._client[_db_name][_coll_name]

    def save(self) -> bool:
        pass

    def load(self) -> bool:
        pass

    def get_entry(self, entry_primary_value: str) -> Optional[Entry]:
        _entry = self._collection.find_one(
            filter={self.primary_key.name: entry_primary_value})
        if _entry is None:
            return None
        _ = _entry.pop("_id")  # Remove MongoDb Id
        return Entry(dict(_entry))

    def entry_names(self) -> List[str]:
        return [_cur.get(self.primary_key.name) for _cur in self._collection.find(filter={})]

    def find(self, filter_by: Optional[Dict[str, Any]] = None, sort_by_key: Optional[str] = None,
             limit: Optional[int] = None, reversed_sort: bool = False) -> List[Dict]:
        _query = filter_by or {}
        if filter_by is not None:
            _query = filter_by
        _cur = self._collection.find(_query)
        if not _cur:
            return []
        if sort_by_key:
            _cur.sort(str(sort_by_key), pymongo.DESCENDING if reversed_sort else pymongo.ASCENDING)
        _ret = []
        for item in _cur:
            _ = item.pop("_id")  # Remove MongoDb Id
            _ret.append(dict(item))
            if len(_ret) == limit:
                break
        return _ret

    def update_entry(self, entry: Entry) -> bool:
        _val = entry.get(self.primary_key.name)
        result = self._collection.update_one(
            filter={self.primary_key.name: _val},
            update={"$set": entry.data()}
        )
        return result.acknowledged

    def insert_entry(self, entry: Entry) -> bool:
        _id = self._collection.insert_one(entry.data())
        return _id is not None

    def find_duplicates(self, key: Union[Key, str]) -> Dict[Any, List[str]]:
        _all = {}
        for _cur in self._collection.find(filter={str(key): {"$exists": True}}):
            _val = _cur.get(str(key))
            if _val in _all:
                _all[_val].append(_cur.get(self.primary_key.name))
            else:
                _all[_val] = [_cur.get(self.primary_key.name)]
        return {k: v for k, v in _all.items() if len(v) > 1}

    def get(self, entry_name: str, column: Union[Key, str]) -> Optional[Any]:
        _entry: Optional[Entry] = self.get_entry(entry_name)
        if _entry is None:
            return None
        return _entry.get(str(column))
