from enum import Enum, auto

from base_log import BaseLog
from abc import ABC, abstractmethod


class ScanType(Enum):
    Movie = auto()
    TvShow = auto()
    MovieDiagnostics = auto()
    TvShowDiagnostics = auto()


class MediaScanner(ABC, BaseLog):
    def __init__(self, dont_update_database: bool = False):
        BaseLog.__init__(self, verbose=True)
        self._update_db: bool = not dont_update_database
        self.set_log_prefix("MEDIA_SCANNER")

    @abstractmethod
    def scan(self):
        raise NotImplementedError
