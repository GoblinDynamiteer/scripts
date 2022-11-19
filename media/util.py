from pathlib import Path
from typing import Union, List, Dict, Generator

from config import ConfigurationManager, SettingKeys
from singleton import Singleton

from media.enums import MOVIE_LETTERS
from media.regex import matches_movie_regex, parse_season_and_episode, matches_season_regex


class MediaPaths(metaclass=Singleton):
    def __init__(self):
        self._data: Dict[str, Union[Path, List[Path]]] = {}

    def movie_dir(self) -> Path:
        _path = self._data.get("movie_dir", None)
        if _path:
            return _path
        _path = ConfigurationManager().path(SettingKeys.PATH_MOVIES,
                                            assert_path_exists=True,
                                            convert_to_path=True)
        self._data["movie_dir"] = _path
        return _path

    def tv_dir(self) -> Path:
        _path = self._data.get("tv_dir", None)
        if _path:
            return _path
        _path = ConfigurationManager().path(SettingKeys.PATH_TV,
                                            assert_path_exists=True,
                                            convert_to_path=True)
        self._data["tv_dir"] = _path
        return _path

    def movie_letter_dirs(self) -> Generator[Path, None, None]:
        for _sub_dir in self.movie_dir().iterdir():
            if _sub_dir.name.upper() not in MOVIE_LETTERS:
                continue
            yield _sub_dir

    def movie_dirs(self) -> Generator[Path, None, None]:
        for _letter_dir in self.movie_letter_dirs():
            for _movie_dir in _letter_dir.iterdir():
                yield _movie_dir

    def movie_files(self) -> Generator[Path, None, None]:
        for _mov_dir in self.movie_dirs():
            for _file in _mov_dir.rglob("*.*"):
                if _file.suffix in (".mkv", ".avi", ".mp4"):
                    yield _file

    def show_dirs(self) -> Generator[Path, None, None]:
        for _item in self.tv_dir().iterdir():
            if _item.is_dir():
                yield _item

    def episode_files(self) -> Generator[Path, None, None]:
        for _show_dir in self.show_dirs():
            for _file in _show_dir.rglob("*.*"):
                if _file.suffix in (".mkv", ".avi", ".mp4"):
                    yield _file


class Util:
    @staticmethod
    def is_movie(item: Union[str, Path]) -> bool:
        item = Util._to_string(item)
        if Util.is_episode(item):
            return False
        return matches_movie_regex(item)

    @staticmethod
    def is_episode(item: Union[str, Path]) -> bool:
        item = Util._to_string(item)
        return all([x is not None for x in parse_season_and_episode(item)])

    @staticmethod
    def is_season(item: Union[str, Path]) -> bool:
        item = Util._to_string(item)
        return matches_season_regex(item)

    @staticmethod
    def _to_string(item: Union[str, Path]) -> str:
        if isinstance(item, Path):
            return item.name
        elif not isinstance(item, str):
            raise TypeError(f"incorrect type {type(item)}")
        return item
