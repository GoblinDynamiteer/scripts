#!/usr/bin/env python3

from typing import Dict, Optional, Union
from enum import Enum, auto
import json
import urllib.parse
import urllib.request

from argparse import ArgumentParser

from base_log import BaseLog
from media.online_search.result import SearchResult
from media.show import ShowData
from media.episode import EpisodeData
from media.imdb_id import IMDBId


class TvMazeSearchResult(SearchResult):
    @property
    def valid(self):
        return "id" in self._raw

    @property
    def year(self):
        return self._raw.get("premiered", None)

    @property
    def title(self):
        return self._raw.get("name", None)

    @property
    def genre(self):
        return self._raw.get("genre", None)

    @property
    def id(self):
        return self._raw.get("id", None)


class SearchType(Enum):
    Show = auto()
    Episode = auto()


class TvMaze(BaseLog):
    URL = "http://api.tvmaze.com"
    _results: Dict[str, TvMazeSearchResult] = {}

    def __init__(self, verbose=False):
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("TVMaze")
        self.log("init")

    def _search(self, url):
        self.log_fs(f"searching... url: i[{url}]")
        _res = urllib.request.urlopen(url, timeout=4).read().decode("utf-8")
        return json.loads(_res)

    def _url_from_imdb(self, imdb_id: IMDBId, search_type: SearchType) -> Optional[str]:
        if not imdb_id.valid():
            self.error("IMDbId invalid, cannot build search request")
            return None
        _args = {"imdb": str(imdb_id)}
        if search_type == SearchType.Show:
            return f"{self.URL}/lookup/shows?{urllib.parse.urlencode(_args)}"
        elif search_type == SearchType.Episode:
            raise NotImplementedError("not yet...")
        raise ValueError(f"invalid search type: {search_type}")

    def _url_from_show_data(self, data: ShowData) -> Optional[str]:
        if not data.title:
            self.error("title is required, cannot build search request")
            return None
        _args = {"q": data.title}
        return f"{self.URL}/singlesearch/shows?{urllib.parse.urlencode(_args)}"

    def show_search(self, data: Union[ShowData, IMDBId]):
        if not data:
            self.error("search requires either ShowData or IMDBId to be set")
            return None
        if isinstance(data, IMDBId):
            url = self._url_from_imdb(data, search_type=SearchType.Show)
        elif isinstance(data, ShowData):
            url = self._url_from_show_data(data)
        else:
            self.error(f"invalid search data type: {type(data)}")
            return None
        _existing = self._results.get(url, None)
        if _existing is not None:
            return _existing
        _ret = TvMazeSearchResult(self._search(url))
        self._results[url] = _ret
        return _ret

    def episode_search(self, data: Union[EpisodeData, IMDBId]):
        raise NotImplementedError("not yet...")


def main():
    parser = ArgumentParser()
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--id", "-i", type=str, default=None)
    grp.add_argument("--title", "-t", type=str, default=None)
    args = parser.parse_args()
    _tvmaze = TvMaze(verbose=True)
    if args.title:
        data = ShowData(title=args.title)
    else:
        data = IMDBId(args.id)
    res: Optional[TvMazeSearchResult] = _tvmaze.show_search(data)
    if res is None or not res.valid:
        print("could not get a valid search result!")
    else:
        res.print()


if __name__ == "__main__":
    main()
