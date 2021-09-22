
from enum import Enum
from datetime import datetime

from base_log import BaseLog


class EpisodeData(BaseLog):
    class Keys(Enum):
        ShowName = "show_name"
        EpisodeName = "episode_name"
        DateAired = "date_aired"
        SeasonNumber = "season_number"
        EpisodeNumber = "episode_number"
        Id = "id"
        Url = "url"

    def __init__(self, episode_data=None, verbose=False):
        super().__init__(verbose=verbose)
        self.set_log_prefix("EPISODE_DATA")
        self._raw_dict = episode_data
        self._data = {}

    def url(self):
        raise NotImplementedError()

    def subtitle_url(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    def _get(self, key: Keys, default=None):
        return self._data.get(key, default)

    def _set(self, key: Keys, value):
        self._data[key] = value

    @property
    def raw(self):
        return self._raw_dict

    @property
    def airdate(self) -> datetime:
        return self._get(self.Keys.DateAired) or datetime.fromtimestamp(0)

    @property
    def show(self) -> str:
        return self._get(self.Keys.ShowName) or ""

    @property
    def s(self) -> int:
        return self._get(self.Keys.SeasonNumber) or 0

    @property
    def e(self) -> int:
        return self._get(self.Keys.EpisodeNumber) or 0

    @property
    def name(self) -> str:
        return self._get(self.Keys.EpisodeName) or "N/A"

    @property
    def season(self) -> int:
        return self.s

    @property
    def episode(self) -> int:
        return self.e

    @property
    def id(self):
        return self._get(self.Keys.Id) or 0
