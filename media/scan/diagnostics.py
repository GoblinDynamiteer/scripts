from typing import Optional, List
from enum import Enum
import os

from base_log import BaseLog
from db.db_mov import MovieDatabase
from config import ConfigurationManager, SettingKeys, SettingSection
from media.util import MediaPaths, VALID_FILE_EXTENSIONS
from utils.file_utils import FileInfo

from printout import pfcs


class DiagnosticsScanner(BaseLog):
    class Type(Enum):
        Movie = "movie"
        TV = "tv"

    def __init__(self, verbose: bool = False, simulate: bool = False):
        BaseLog.__init__(self, verbose=verbose)
        self._verbose_logging: bool = verbose
        self._simulate: bool = simulate
        self._movie_db: Optional[MovieDatabase] = None
        self.set_log_prefix("DIAG_SCAN")
        self._spacer = 23 * " "  # Time stamp str len + log prefix len. TODO: move this feature to printout
        self._use_timestamp = True

    def find_duplicate_movies(self) -> int:
        self.set_log_prefix_2("duplicates")
        self.log("scanning for duplicate movies...")
        self._init_movie_db()
        _allowed: List[str] = ConfigurationManager().get(
            assert_exists=True,
            section=SettingSection.MediaScanner,
            key=SettingKeys.SCANNER_ALLOWED_DUPLICATES).split(",")

        _count = 0
        for imdb_id, movies in self._movie_db.find_duplicates().items():
            _is_duplicate: bool = True
            for _needle in _allowed:
                _matching = [m for m in movies if _needle.lower() in m.lower()]
                if len(_matching) == 1:
                    _is_duplicate = False
            if _is_duplicate:
                _count += 1
                self.log_fs(f"found multiple movies for IMDb: i[{imdb_id}]:", force=True)
                for mov in movies:
                    pfcs(self._spacer + f"dg[----->] o[{mov}]")
        return _count

    def find_removed_movies(self) -> int:
        self.set_log_prefix_2("removed")
        self.log("scanning for removed movies...")
        _paths = MediaPaths()
        _count = 0
        existing = [d.name for d in MediaPaths().movie_dirs()]
        for mov in self._movie_db.all_movies(include_removed=False):
            folder = mov.get("folder")
            if folder not in existing:
                _count += 1
                self.log_fs(f"found removed: w[{folder}]...", force=True)
                if not self._simulate:
                    self._movie_db.mark_removed(folder)
        return _count

    def find_invalid_directory_contents(self, scan_type: Type) -> int:
        if scan_type == self.Type.TV:
            raise NotImplementedError("TV diag scan not implemented...")
        self.set_log_prefix_2("junk")
        self.log("scanning for invalid files/dirs...")
        _count = 0
        for _dir in MediaPaths().movie_dirs():
            _files = _dir.glob("*")
            for _file in _files:
                if _file.is_dir():
                    _count += 1
                    self.warn_fs(f"found subdir: w[{_file.name}] in i[{_dir}]", force=True)
                    if ".mkv" in _file.name:
                        pfcs(self._spacer + "dg[----->] movie file is probably in dir, should be moved!")
                elif _file.suffix not in VALID_FILE_EXTENSIONS:
                    self.warn_fs(f"invalid extension (e[{_file.suffix}]) of i[{_file.resolve()}]", force=True)
                    _count += 1
        return _count

    def check_file_and_directory_permissions(self, scan_type: Type) -> int:
        if scan_type == self.Type.TV:
            raise NotImplementedError("TV diag scan not implemented...")
        self.set_log_prefix_2("permissions")
        self.log("scanning for wrong access permissions...")
        expected = 0o644 if os.name != "nt" else 0o666
        _count = 0
        for _mov_file in MediaPaths().movie_files():
            try:
                _fi = FileInfo(_mov_file)
            except FileNotFoundError as _:
                self.warn_fs(f"r[{_mov_file}] is not a file!")
                continue
            if not _fi.has_permissions(expected):
                self.warn_fs(f"wrong access: w[{oct(_fi.stat.st_mode)}] -> i[{_mov_file}]")
                _count += 1
        return _count

    def _init_movie_db(self) -> None:
        if self._movie_db is None:
            self._movie_db = MovieDatabase()
