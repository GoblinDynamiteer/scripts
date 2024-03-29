#!/usr/bin/env python3

from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from config import ConfigurationManager, SettingKeys

from db.database import Key, KeyType, DatabaseType
from db.db_media import MediaDatabase, MediaDbSettings


def _to_text_added(episode_data: Dict) -> str:
    date = datetime.fromtimestamp(episode_data["scanned"]).strftime('%Y-%m-%d')
    _se = f'S{episode_data["season_number"]:02d}E{episode_data["episode_number"]:02d}'
    _filename = episode_data["filename"]
    return f'[{date}] [{episode_data["tvshow"]}] [{_se}] [{_filename}]\n'


def _to_text_removed(episode_data: Dict) -> str:
    date = datetime.fromtimestamp(episode_data["removed_date"]).strftime('%Y-%m-%d')
    _se = f'S{episode_data["season_number"]:02d}E{episode_data["episode_number"]:02d}'
    _filename = episode_data["filename"]
    return f'[{date}] [{episode_data["tvshow"]}] [{_se}] [{_filename}]\n'


class ShowDatabase(MediaDatabase):
    def __init__(self, file_path: Optional[Path] = None, use_json_db: bool = False):
        keys = [
            Key("folder", primary=True),
            Key("title", optional=False),
            Key("year", type=KeyType.Integer),
            Key("imdb"),
            Key("tvmaze", type=KeyType.Integer),
            Key(self.SCANNED_KEY_STR, type=KeyType.Integer),
            Key(self.REMOVED_KEY_STR, type=KeyType.Boolean),
            Key(self.REMOVED_DATE_KEY_STR, type=KeyType.Integer),
        ]

        if use_json_db:
            if file_path is None:
                _path = ConfigurationManager().path(SettingKeys.PATH_TVSHOW_DATABASE,
                                                    assert_path_exists=True,
                                                    convert_to_path=True)
            else:
                _path = file_path
            _settings = MediaDbSettings(type=DatabaseType.JSON, path=_path)
        else:
            _settings = MediaDbSettings(type=DatabaseType.Mongo, database_name="media", collection_name="shows")

        _settings.log_prefix_second = "show"
        MediaDatabase.__init__(self, _settings)
        self._db.set_valid_keys(keys)
        self._db.load()

    def __contains__(self, show: str):
        return show in self._db

    def add(self, **data):
        self._db.insert(**data)

    def update(self, show_folder: str, **data):
        self._db.update(show_folder, **data)

    def all_shows(self):
        for item in self._db.find():
            yield item


class EpisodeDatabase(MediaDatabase):
    def __init__(self, file_path: Optional[Path] = None, use_json_db: bool = False):
        keys = [
            Key("filename", primary=True),
            Key("season_number", type=KeyType.Integer, optional=False),
            Key("episode_number", type=KeyType.Integer, optional=False),
            Key("released", type=KeyType.Integer),
            Key("tvshow", optional=False),
            Key("imdb"),
            Key("tvmaze", type=KeyType.Integer),
            Key("title", type=KeyType.String),
            Key(self.SCANNED_KEY_STR, type=KeyType.Integer),
            Key(self.REMOVED_KEY_STR, type=KeyType.Boolean),
            Key(self.REMOVED_DATE_KEY_STR, type=KeyType.Integer),
        ]

        if use_json_db:
            if file_path is None:
                _path = ConfigurationManager().path(SettingKeys.PATH_EPISODE_DATABASE,
                                                    assert_path_exists=True,
                                                    convert_to_path=True)
            else:
                _path = file_path
            _settings = MediaDbSettings(type=DatabaseType.JSON, path=_path)
        else:
            _settings = MediaDbSettings(type=DatabaseType.Mongo, database_name="media", collection_name="episodes")

        _settings.log_prefix_second = "episode"
        MediaDatabase.__init__(self, _settings)
        self._db.set_valid_keys(keys)
        self._db.load()

    def export_latest_added_episodes(self):
        _path = ConfigurationManager().path(SettingKeys.PATH_TV,
                                            convert_to_path=True,
                                            assert_path_exists=True)
        _path = _path / "latest.txt"
        self.export_latest_added(to_str_func=_to_text_added, text_file_path=_path)

    def export_latest_removed_episodes(self):
        _path = ConfigurationManager().path(SettingKeys.PATH_TV,
                                            convert_to_path=True,
                                            assert_path_exists=True)
        _path = _path / "removed.txt"
        self.export_latest_removed(to_str_func=_to_text_removed, text_file_path=_path)

    def add(self, **data):
        self._db.insert(**data)

    def update(self, file_name: str, **data):
        self._db.update(file_name, **data)

    def all_episodes(self):
        for item in self._db.find():
            yield item

    def __contains__(self, file_name: str):
        return file_name in self._db


def main():
    from argparse import Namespace, ArgumentParser

    def get_args() -> Namespace:
        parser = ArgumentParser()
        parser.add_argument("--filter", default=None, type=str)
        parser.add_argument("--limit", default=None, type=int)
        return parser.parse_args()

    db = EpisodeDatabase()
    args = get_args()
    count = 0
    for ep in db.all_episodes():
        if args.filter is not None:
            if args.filter not in ep.get("filename", ""):
                continue
        count += 1
        print(ep)
        if args.limit == count:
            break


if __name__ == "__main__":
    main()
