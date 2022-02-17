from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from media.base import MediaItem
from media.util import MediaPaths
from media.enums import Type, Language
from media.regex import matches_season_subdir, parse_year, parse_quality, parse_season_and_episode


@dataclass
class ShowData:
    name: Optional[str] = None  # Name of directory
    year: Optional[int] = None
    title: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            return
        _s, _e = parse_season_and_episode(self.name)
        if _e is not None:
            raise  # TODO: handle
        if _s is not None:
            _season_str = f".S{_s:02d}."
            if _season_str not in self.name:
                raise  # TODO: handle
            self._split_by(_season_str)
            return
        self.title = self.name

    def _split_by(self, string: str):
        _title = self.name.split(string)[0]
        self.title = _title.replace(".", " ").strip()


class Show(MediaItem):
    def __init__(self, show_dir_path: Path):
        MediaItem.__init__(self, show_dir_path)
        self._tv_dir = MediaPaths().tv_dir()
        self._data: ShowData = ShowData(name=self.name)
        self._correct_loc: Optional[Path] = None

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def data(self) -> ShowData:
        return self._data

    @property
    def type(self) -> Type:
        return Type.Show

    def has_external_subtitle(self, language: Language) -> bool:
        return False

    def is_compressed(self) -> bool:
        return False

    def get_correct_location(self) -> Path:
        return self._tv_dir / self.name

    def is_valid(self) -> bool:
        # TODO: this will not be valid for unprocessed release...
        for sub_item in self.path.iterdir():
            if sub_item.is_dir():
                if matches_season_subdir(sub_item.name):
                    return True
        return False

    def __repr__(self):
        return f"{self.path.resolve()} : [{self.name}] valid: {self.is_valid()}"


def main():
    for show_dir in MediaPaths().show_dirs():
        _show = Show(show_dir)
        print(_show)


if __name__ == "__main__":
    main()
