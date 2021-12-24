#!/usr/bin/env python3

from typing import Dict, Optional, List, Tuple
import json
from pathlib import Path
from argparse import ArgumentParser

from config import ConfigurationManager, SettingKeys
from db.db_media import MediaType, MediaDatabase
from printout import pfcs


def db_json_convert_old_format(source: Path, destination: Path, primary_key_name: str) -> None:
    _imported_json: Optional[Dict] = None
    with open(source, "r") as _fp:
        _imported_json = json.load(_fp)
    _converted_list: List[Dict] = []
    for key, value in _imported_json.items():
        assert isinstance(value, dict) is True
        value[primary_key_name] = key
        _converted_list.append(value)
    assert len(_imported_json) == len(_converted_list)
    with open(destination, "w") as _fp:
        json.dump(_converted_list, _fp, indent=2)
    print(f"converted {source} -> {destination}")


def compare_mongo_json_media_databases(media_type: Optional[MediaType] = None):
    if media_type is None:
        _types = [mt for mt in MediaType]
    else:
        _types = [media_type]
    for media_type in _types:
        print(f"running comparison on type: {media_type.name}")
        _db_json = MediaDatabase.get_database(media_type, use_json_db=True)
        _db_mongo = MediaDatabase.get_database(media_type, use_json_db=False)
        if any([db is None for db in (_db_json, _db_mongo)]):
            print("could not get both json and mongo databases")
            return
        _keys = _db_json.get_keys()
        for item in _db_json:
            if item not in _db_mongo:
                pfcs(f"o[{item}] -> not in mongo db!")
            else:
                _entry_j = _db_json._db.get_entry(item)
                _entry_m = _db_mongo._db.get_entry(item)
                if _entry_m == _entry_j:
                    continue
                pfcs(f"entries diff:\n  i[{_entry_j}] \nvs\n   o[{_entry_m}]")


def get_args():
    parser = ArgumentParser("Db Utils")
    parser.add_argument("command",
                        choices=("convert", "compare"))
    parser.add_argument("--type",
                        "-t",
                        dest="media_type",
                        type=str,
                        default=None,
                        choices=[mt.name.lower() for mt in MediaType])
    return parser.parse_args()


def main():
    args = get_args()
    if args.command == "convert":
        _items: List[Tuple] = [
            (SettingKeys.PATH_MOVIE_DATABASE, "folder"),
            (SettingKeys.PATH_TVSHOW_DATABASE, "folder"),
            (SettingKeys.PATH_EPISODE_DATABASE, "filename"),
            (SettingKeys.PATH_EPISODE_DATABASE, "filename"),
            (SettingKeys.PATH_TV_CACHE_DATABASE, "season_dir"),
            (SettingKeys.PATH_MOVIE_CACHE_DATABASE, "letter_dir"),
        ]

        for setting_key, primary_key_name in _items:
            _source: Path = ConfigurationManager().path(setting_key, convert_to_path=True,
                                                        assert_path_exists=True)
            _destination = _source.with_name(f"CONVERTED_{_source.name}")
            db_json_convert_old_format(_source, _destination, primary_key_name=primary_key_name)
    elif args.command == "compare":
        compare_mongo_json_media_databases(MediaType.from_string(args.media_type))


if __name__ == "__main__":
    main()
