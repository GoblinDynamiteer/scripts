#!/usr/bin/env python3
from typing import Optional, List, Callable, Dict
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto

from printout import Color, cstr
import util
from db.db_json import JSONDatabase
from db.db_mongo import MongoDatabase, MongoDbSettings
from db.database import DatabaseType, DataBase
from base_log import BaseLog


@dataclass
class MediaDbSettings:
    type: DatabaseType
    path: Optional[Path] = None
    collection_name: Optional[str] = None
    database_name: Optional[str] = None


class MediaType(Enum):
    Movie = auto()
    Episode = auto()
    Show = auto()

    @classmethod
    def from_string(cls, string: str) -> Optional["MediaType"]:
        if not isinstance(string, str):
            return None
        for mt in cls:
            if mt.name.lower() == string.lower():
                return mt
        return None


class MediaDatabase(BaseLog):
    SCANNED_KEY_STR = "scanned"
    REMOVED_DATE_KEY_STR = "removed_date"
    REMOVED_KEY_STR = "removed"

    def __init__(self, settings: MediaDbSettings):
        BaseLog.__init__(self, verbose=True, use_timestamps=True)
        self._db: Optional[DataBase] = None
        self._settings: MediaDbSettings = settings
        self.set_log_prefix("MediaDb")
        self._init()

    @staticmethod
    def get(media_type: MediaType, use_json_db: bool = False) -> Optional["MediaDatabase"]:
        if media_type == MediaType.Movie:
            from db.db_mov import MovieDatabase
            return MovieDatabase(use_json_db=use_json_db)
        return None

    def _init(self):
        if self._settings.type == DatabaseType.JSON:
            assert self._settings.path is not None
            self._db = JSONDatabase(self._settings.path)
            self.log("init JSON")
        elif self._settings.type == DatabaseType.Mongo:
            assert self._settings.collection_name is not None
            assert self._settings.database_name is not None
            import config
            _conf = config.ConfigurationManager()
            _settings = MongoDbSettings(
                ip=_conf.get(config.SettingKeys.MONGO_IP, assert_exists=True),
                username=_conf.get(config.SettingKeys.MONGO_USERNAME, assert_exists=True),
                password=_conf.get(config.SettingKeys.MONGO_PASSWORD, assert_exists=True),
                database_name=self._settings.database_name,
                collection_name=self._settings.collection_name
            )
            self._db = MongoDatabase(_settings)
            self.log("init Mongo")
        else:
            raise ValueError(f"invalid db type: {self._settings.type}")

    def _get_last_of(self, key: str, limit: int) -> List[Dict]:
        return self._db.find(sort_by_key=key, reversed_sort=True, limit=limit)

    def last_added(self, limit: int):
        return self._get_last_of(self.SCANNED_KEY_STR, limit)

    def last_removed(self, limit: int):
        return self._get_last_of(self.REMOVED_DATE_KEY_STR, limit)

    def mark_removed(self, item: str):
        self._db.update(item, removed=True, removed_date=util.now_timestamp())
        self.log(f"marked {cstr(item, Color.Orange)} as removed")

    def is_removed(self, item: str):
        _entry = self._db.get_entry(item)
        if not _entry:
            return False
        return _entry.get(self.REMOVED_KEY_STR) is True

    def export_latest_added(self, to_str_func: Callable[[Dict], str], text_file_path: Path):
        _latest = self.last_added(limit=1000)
        _latest_str: List[str] = [to_str_func(item) for item in _latest]
        with open(text_file_path, "w") as _fp:
            _fp.writelines(_latest_str)
        self.log(f"wrote to {cstr(str(text_file_path), Color.LightGreen)}")

    def export_latest_removed(self, to_str_func: Callable[[Dict], str], text_file_path: Path):
        _latest = self.last_removed(limit=1000)
        _latest_str: List[str] = [to_str_func(item) for item in _latest]
        with open(text_file_path, "w") as _fp:
            _fp.writelines(_latest_str)
        self.log(f"wrote to {cstr(str(text_file_path), Color.LightGreen)}")
