from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from media.base import MediaItem
from media.util import MediaPaths
from media.enums import Type, Language
from media.regex import matches_season_subdir


@dataclass
class ShowData:
    name: Optional[str] = None  # Name of directory
    year: Optional[int] = None
    title: Optional[str] = None


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
