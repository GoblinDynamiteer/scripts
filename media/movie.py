from pathlib import Path
from typing import Optional

from media.base import MediaItem
from media.enums import Type, Language
from media.util import Util
from config import ConfigurationManager, SettingKeys


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
