#!/usr/bin/env python3

from typing import Dict, Optional, List, Tuple

import json
from pathlib import Path

from config import ConfigurationManager, SettingKeys


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


def main():
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


if __name__ == "__main__":
    main()
