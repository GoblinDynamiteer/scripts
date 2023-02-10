from typing import Optional, List
from enum import Enum
import os
from pathlib import Path

from base_log import BaseLog
from db.db_mov import MovieDatabase
from config import ConfigurationManager, SettingKeys, SettingSection
from media.util import MediaPaths, VALID_FILE_EXTENSIONS
from utils.file_utils import FileInfo
from utils.dir_util import DirectoryInfo

from printout import pfcs


class DiagnosticsScanner(BaseLog):
    class Type(Enum):
        Movie = "movie"
        TV = "tv"

    def __init__(self, verbose: bool = False, simulate: bool = False, fix_issues: bool = False):
        BaseLog.__init__(self, verbose=verbose)
        self._verbose_logging: bool = verbose
        self._simulate: bool = simulate
        self._movie_db: Optional[MovieDatabase] = None
        self.set_log_prefix("DIAG_SCAN")
        self._spacer = 23 * " "  # Time stamp str len + log prefix len. TODO: move this feature to printout
        self._use_timestamp = True
        self._fix_issues: bool = fix_issues

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
                        self._fix(_file)
                elif _file.suffix not in VALID_FILE_EXTENSIONS:
                    self.warn_fs(f"invalid extension (e[{_file.suffix}]) of i[{_file.resolve()}]", force=True)
                    _count += 1
        return _count

    def check_file_and_directory_permissions(self, scan_type: Type) -> int:
        if scan_type == self.Type.TV:
            raise NotImplementedError("TV diag scan not implemented...")
        self.set_log_prefix_2("permissions")
        self.log("scanning for wrong access permissions...")
        _count = 0
        expected = 0o755
        for _mov_dir in MediaPaths().movie_dirs():
            _di = DirectoryInfo(_mov_dir)
            if not _di.has_permissions(expected):
                self.warn_fs(f"wrong access: w[{oct(_di.stat.st_mode)}] -> i[{_mov_dir}]")
                self._fix(_mov_dir)
        expected = 0o644
        for _mov_file in MediaPaths().movie_files():
            try:
                _fi = FileInfo(_mov_file)
            except FileNotFoundError as _:
                self.warn_fs(f"e[{_mov_file}] is not a file!")
                continue
            except PermissionError as _:
                self.warn_fs(f"cannot access e[{_mov_file}]: permission error!")
                continue
            if not _fi.has_permissions(expected):
                self.warn_fs(f"wrong access: w[{oct(_fi.stat.st_mode)}] -> i[{_mov_file}]")
                self._fix(_mov_file)
                _count += 1
        return _count

    def _init_movie_db(self) -> None:
        if self._movie_db is None:
            self._movie_db = MovieDatabase()

    def _fix(self, item: Path):
        def _set_permission(mod: int):
            if self._simulate:
                pfcs(f"<sim> set mode {oct(mod)} of: {item}")
            else:
                item.chmod(mod)
                self.log(f"set mode {oct(mod)} of: {item}")

        if not self._fix_issues:
            return
        _sim = "(simulate)" if self._simulate else "\b"
        if input(f"Attempt to {_sim} fix? [y/n]: ") != "y":
            return
        if item.is_dir():
            if ".mkv" in item.name:
                self._fix_mkv_subdir(item)
            else:
                _set_permission(0o755)
        elif item.is_file():
            _set_permission(0o644)

    def _fix_mkv_subdir(self, sub_dir: Path):
        if self._simulate:
            pfcs(f"<sim> set mode 755 of: {sub_dir}")
        else:
            sub_dir.chmod(0o755)
            self.log_fs(f"set mode 755 of: o[{sub_dir}]")
            self.log_fs(f"rename: o[{sub_dir}] -> e[__trash]")
            sub_dir = sub_dir.rename(sub_dir.with_name("__trash"))
        assert sub_dir.is_dir()
        _sub_files = list(sub_dir.glob("*.mkv"))
        if len(_sub_files) > 1:
            self.log_fs(f"found more than one file of dir {sub_dir}, e[fix manually!]")
            return
        if not _sub_files:
            self.log_fs(f"found no sub files of dir dir {sub_dir}!")
            # TODO delete directory ...
            return
        _sub_file = _sub_files[0]
        if self._simulate:
            pfcs(f"<sim> move i[{_sub_file.name}] ..")
            pfcs(f"<sim> del i[{sub_dir}] ..")
            return
        _parent_dir: Path = sub_dir.parent
        _new_loc: Path = _parent_dir / _sub_file.name
        _sub_file = _sub_file.rename(_new_loc)
        self.log_fs(f"moved i[{_sub_file}] --> i[{_parent_dir}]")
        _sub_file.chmod(0o644)
        self.log_fs(f"set mode 644: {_sub_file}")
        sub_dir.rmdir()
        self.log_fs(f"removed: e[{sub_dir}]")

