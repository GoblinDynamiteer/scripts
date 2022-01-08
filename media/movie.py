from pathlib import Path
from typing import Optional
from dataclasses import dataclass


from media.base import MediaItem
from media.enums import Type, Language, MOVIE_EXTRAS
from media.util import Util
from media.regex import matches_movie_regex, parse_year, parse_quality
from config import ConfigurationManager, SettingKeys


@dataclass
class MovieData:
    name: Optional[str] = None
    year: Optional[int] = None
    title: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            return
        _y = parse_year(self.name)
        if _y is None:
            _q = parse_quality(self.name)
            if _q is None:
                return
            self._split_by(_q)
        else:
            self.year = _y
            self._split_by(str(_y))

    def _split_by(self, string: str):
        _title = self.name.split(string)[0]
        self.title = self._scrub_title(_title.replace(".", " ").strip())

    def _scrub_title(self, title: str) -> str:
        _words = title.split()
        _extras = [ex.lower() for ex in MOVIE_EXTRAS]
        while _words[-1].lower() in _extras:
            del _words[-1]
        return " ".join(_words)


class Movie(MediaItem):
    def __init__(self, movie_file_or_dir_path: Path):
        MediaItem.__init__(self, movie_file_or_dir_path)
        self._mov_dir = ConfigurationManager().path(
            SettingKeys.PATH_MOVIES,
            assert_path_exists=True,
            convert_to_path=True)
        self._name: Optional[str] = None
        self._letter: Optional[str] = None
        self._correct_loc: Optional[Path] = None
        self._analyze_path()
        self._data: MovieData = MovieData(name=self.name)

    @property
    def type(self) -> Type:
        return Type.Movie

    @property
    def name(self) -> str:
        return self._name

    def has_external_subtitle(self, language: Language) -> bool:
        return False

    def is_compressed(self) -> bool:
        return False

    def is_valid(self) -> bool:
        if matches_movie_regex(self.name):
            return True
        return False

    @property
    def letter(self):
        if self._letter is None:
            self._determine_letter()
        return self._letter

    def get_correct_location(self):
        if self._correct_loc is None:
            self._determine_correct_location()
        return self._correct_loc

    def _analyze_path(self):
        if Util.is_movie(self._path.parent):
            self._name = self._path.parent.name
        elif self._path.is_file():
            self._name = self._path.stem
        elif self._path.is_dir():
            self._name = self._path.name
        else:
            self._name = self._path.name.replace(".mkv", "")

    def _determine_letter(self):
        for prefix in ["The.", "An.", "A."]:
            if self.name.startswith(prefix):
                _letter = self.name[len(prefix):len(prefix) + 1].upper()
                break
        else:
            _letter = self.name[0:1].upper()
        if str.isdigit(_letter):
            self._letter = "#"
        elif _letter in ["V", "W"]:
            self._letter = "VW"
        else:
            self._letter = _letter

    def _determine_correct_location(self):
        self._correct_loc = self._mov_dir / self.letter / self.name


def main():
    # For testing
    from media.util import MediaPaths
    from printout import print_line
    for mov in MediaPaths().movie_dirs():
        _data = MovieData(mov.name)
        print(f"{mov.name}\n{_data.title} / {_data.year}")
        print_line()


if __name__ == "__main__":
    main()
