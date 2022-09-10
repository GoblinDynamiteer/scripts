from enum import Enum, auto
from typing import List, Union, Dict
from base_log import BaseLog
from abc import ABC, abstractmethod
from pathlib import Path

from media.online_search.omdb import OMDb
from media.online_search.tvmaze import TvMaze
from config import ConfigurationManager, SettingKeys, SettingSection


class ScanType(Enum):
    Movie = auto()
    TvShow = auto()
    MovieDiagnostics = auto()
    TvShowDiagnostics = auto()


class MediaScanner(ABC, BaseLog):
    def __init__(self, update_database: bool = True, verbose: bool = False):
        BaseLog.__init__(self, verbose=verbose)
        self._verbose_logging: bool = verbose
        self._update_db: bool = update_database
        self._ignore_dir_names: List[str] = self._load_ignored_dirs()
        self._search_tools: Dict[ScanType, Union[TvMaze, OMDb]] = {}
        self.set_log_prefix("MEDIA_SCANNER")

    @abstractmethod
    def scan(self) -> int:
        raise NotImplementedError

    def should_skip_dir(self, dir_name: Union[str, Path]):
        if isinstance(dir_name, Path):
            return dir_name.name in self._ignore_dir_names
        return dir_name in self._ignore_dir_names

    def online_search_tool(self, scan_type: ScanType) -> Union[OMDb, TvMaze]:
        _ret = self._search_tools.get(scan_type, None)
        if _ret is not None:
            return _ret
        if scan_type == ScanType.Movie:
            _obj = OMDb(verbose=self._verbose_logging)
            self._search_tools[scan_type] = _obj
            return _obj
        if scan_type == ScanType.TvShow:
            _obj = TvMaze(verbose=self._verbose_logging)
            self._search_tools[scan_type] = _obj
            return _obj
        raise ValueError(f"cannot create search tool for type: {scan_type}")

    @staticmethod
    def _load_ignored_dirs() -> List[str]:
        _cfg = ConfigurationManager()
        _ret = _cfg.get(key=SettingKeys.SCANNER_IGNORE_DIRS, section=SettingSection.MediaScanner, default=None)
        if _ret is None:
            return []
        return _ret.split(",")



