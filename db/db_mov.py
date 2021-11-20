#!/usr/bin/env python3

from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from config import ConfigurationManager, SettingKeys
from db.database import Key, KeyType, DatabaseType
from db.db_media import MediaDatabase, MediaDbSettings


def _to_text_added(movie_data: Dict) -> str:
    date = datetime.fromtimestamp(
        movie_data["scanned"]).strftime("%Y-%m-%d")
    year = title = ""
    if "year" in movie_data:
        year = movie_data["year"]
    if "title" in movie_data:
        title = movie_data["title"]
    ret_str = f"[{date}] [{movie_data['folder']}]"
    if year:
        ret_str += f" [{year}]"
    if title:
        ret_str += f" [{title}]"
    return ret_str + "\n"


def _to_text_removed(movie_data: Dict) -> str:
    date = datetime.fromtimestamp(
        movie_data["removed_date"]).strftime("%Y-%m-%d")
    year = title = ""
    if "year" in movie_data:
        year = movie_data["year"]
    if "title" in movie_data:
        title = movie_data["title"]
    ret_str = f"[{date}] [{movie_data['folder']}]"
    if year:
        ret_str += f" [{year}]"
    if title:
        ret_str += f" [{title}]"
    return ret_str + "\n"


class MovieDatabase(MediaDatabase):
    def __init__(self, file_path: Optional[Path] = None):
        if file_path is None:
            _path = ConfigurationManager().path(SettingKeys.PATH_MOVIE_DATABASE,
                                                assert_path_exists=True,
                                                convert_to_path=True)
        else:
            _path = file_path
        keys = [
            Key("folder", primary=True),
            Key("title"),
            Key("year", type=KeyType.Integer),
            Key("imdb"),
            Key(self.SCANNED_KEY_STR, type=KeyType.Integer),
            Key(self.REMOVED_KEY_STR, type=KeyType.Boolean),
            Key(self.REMOVED_DATE_KEY_STR, type=KeyType.Integer),
        ]
        _settings = MediaDbSettings(type=DatabaseType.JSON, path=_path)

        MediaDatabase.__init__(self, _settings)
        self._db.set_valid_keys(keys)
        self._db.load()

    def __contains__(self, movie: str):
        return movie in self._db

    def export_latest_added_movies(self):
        _path = ConfigurationManager().path(SettingKeys.PATH_MOVIES,
                                            convert_to_path=True,
                                            assert_path_exists=True)
        _path = _path / "latest.txt"
        self.export_latest_added(to_str_func=_to_text_added, text_file_path=_path)

    def export_latest_removed_movies(self):
        _path = ConfigurationManager().path(SettingKeys.PATH_MOVIES,
                                            convert_to_path=True,
                                            assert_path_exists=True)
        _path = _path / "removed.txt"
        self.export_latest_removed(to_str_func=_to_text_removed, text_file_path=_path)

    def add(self, **data):
        self._db.insert(**data)

    def update(self, folder: str, **data):
        self._db.update(folder, **data)

    def all_movies(self):
        for item in self._db.find():
            yield item
