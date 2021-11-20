from enum import Enum, auto
from typing import Optional, Union, Any, List

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.collection import Collection

from db.database import DataBase, Key, Entry


class MongoDatabase(DataBase):
    class State(Enum):
        NotInitialized = auto()
        Connected = auto()
        FailedToConnect = auto()

    def __init__(self, database_name: str, collection_name: str):
        super().__init__()
        self._new_entries = List[Entry]
        self._client: Optional[MongoClient] = None
        self._collection: Optional[Collection] = None
        self._state: MongoDatabase.State = self.State.NotInitialized
        self._connect(database_name, collection_name)

    def _connect(self, database_name: str, collection_name: str) -> bool:
        if self._state == self.State.Connected:
            return True
        if self._client is None:
            self._client = MongoClient("localhost",
                                       27017,
                                       username="placehoder_root",
                                       password="placehoder_password",
                                       serverSelectionTimeoutMS=1000)
            try:
                self._client.server_info()
            except ServerSelectionTimeoutError as _:
                self._state = self.State.FailedToConnect
                raise ConnectionError("Failed to connect to mongodb!")
        if database_name not in self._client.list_database_names():
            raise ValueError(f"database {database_name} does not exist!")
        _db = self._client[database_name]
        if collection_name not in _db.list_collection_names():
            raise ValueError(f"collection {collection_name} does not exist in db {database_name}")
        self._collection = self._client[database_name][collection_name]

    def save(self) -> bool:
        pass

    def load(self) -> bool:
        pass

    def get(self, primary_key: Union[Key, str], column: Union[Key, str]) -> Optional[Any]:
        _entry = self._collection.find_one()
        return super().get(primary_key, column)


if __name__ == "__main__":
    database = MongoDatabase("media", "episodes")
