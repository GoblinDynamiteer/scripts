
from typing import List

from .lister.tv4 import Tv4PlayEpisodeLister
from .lister.discovery import DPlayEpisodeLister
from .lister.viafree import ViafreeEpisodeLister
from .lister.svtplay import SVTPlayEpisodeLister
from .lister.episode_lister import EpisodeLister


class ListerFactory:
    def __init__(self):
        self._listers: List[EpisodeLister] = []
        self.add_lister(Tv4PlayEpisodeLister)
        self.add_lister(ViafreeEpisodeLister)
        self.add_lister(SVTPlayEpisodeLister)
        self.add_lister(DPlayEpisodeLister)

    def add_lister(self, lister):
        self._listers.append(lister)

    def get_lister(self, url: str, **kwargs) -> [EpisodeLister, None]:
        for _lister in self._listers:
            if _lister.supports_url(url):
                return _lister(url, **kwargs)
        raise ValueError(f"cannot find lister for url: {url}")
