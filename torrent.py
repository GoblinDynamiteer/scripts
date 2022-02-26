from typing import List, Dict, Optional
from dataclasses import dataclass

import requests
import urllib.parse

from config import ConfigurationManager, SettingKeys, SettingSection

import logging


@dataclass
class TorrentSearchSettings:
    host: str
    port: int
    api_key: str
    available_indexers: List[str]


class TorrentSearch:
    """" Torrent searcher using Jacket (https://github.com/Jackett/Jackett) """

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._settings: Optional[TorrentSearchSettings] = None
        self._load_settings()

    def _load_settings(self):
        _cfg = ConfigurationManager()
        _indexers: List[str] = []
        ss = SettingSection.Torrent
        for sk in [SettingKeys.TORRENT_INDEXERS_PUBLIC, SettingKeys.TORRENT_INDEXERS_PRIVATE]:
            _indexers.extend(_cfg.get(sk, section=ss, default="").split(","))
        if not _indexers:
            raise ValueError("no available indexers in configuration!")
        self._settings = TorrentSearchSettings(
            host=_cfg.get(SettingKeys.JACKET_HOST, section=ss, assert_exists=True),
            port=_cfg.get(SettingKeys.JACKET_PORT, convert=int, section=ss, assert_exists=True),
            api_key=_cfg.get(SettingKeys.API_KEY_JACKET, section=ss, assert_exists=True),
            available_indexers=_indexers)
        self._logger.debug(self._settings)

    def _args(self, query: str = "", indexers: Optional[List[str]] = None) -> Dict[str, str]:
        _ret = {"apikey": self._settings.api_key}
        if indexers is not None:
            _ret[r"Tracker[]"] = indexers
        _ret["Query"] = query
        return _ret

    @property
    def url(self) -> str:
        return f"http://{self._settings.host}:{self._settings.port}/api/v2.0/indexers/all/results"

    def search(self, query: str = "", indexers: Optional[List[str]] = None) -> List:
        _url = f"{self.url}?{urllib.parse.urlencode(self._args(query, indexers), doseq=True)}"
        self._logger.debug(f"executing: {_url}")
        _res = requests.get(_url)
        _data = _res.json()
        return _data


def main():
    logging.basicConfig(format="[%(asctime)s] %(levelname)10s %(module)s::%(name)s <%(funcName)s> %(message)s",
                        level=logging.DEBUG,
                        datefmt="%I:%M:%S")
    logger = logging.getLogger(__name__)
    logger.info("hello")
    ts = TorrentSearch()
    from pprint import pprint
    pprint(ts.search("big buck bunny"))


if __name__ == "__main__":
    main()
