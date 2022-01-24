#!/usr/bin/env python3

from typing import Dict, Optional, Union
import json
import urllib.parse
import urllib.request
from argparse import ArgumentParser

from base_log import BaseLog
from config import ConfigurationManager, SettingKeys
from media.movie import MovieData
from media.imdb_id import IMDBId
from media.online_search.result import SearchResult


class OMDbMovieSearchResult(SearchResult):
    pass


class OMDb(BaseLog):
    URL = "http://www.omdbapi.com"
    _results: Dict[str, OMDbMovieSearchResult] = {}

    def __init__(self, verbose=False):
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("OMDb")
        self._api_key: Optional[str] = ConfigurationManager().get(SettingKeys.API_KEY_OMDB, assert_exists=True)
        self.log("init")

    @property
    def valid(self):
        return self._api_key is not None

    def _search(self, url):
        self.log_fs(f"searching... url: i[{url}]")
        _res = urllib.request.urlopen(url, timeout=4).read().decode("utf-8")
        return json.loads(_res)

    def _args(self) -> Dict[str, str]:
        return {"apikey": self._api_key, "type": "movie"}

    def _url_from_imdb(self, imdb_id: IMDBId) -> Optional[str]:
        if not imdb_id.valid():
            self.error("IMDbId invalid, cannot build search request")
            return None
        _args = self._args()
        _args["i"] = str(imdb_id)
        return f"{self.URL}?{urllib.parse.urlencode(_args)}"

    def _url_from_movie_data(self, data: MovieData) -> Optional[str]:
        year, title = data.year, data.title
        if not title:
            self.error("title is required, cannot build search request")
            return None
        _args = self._args()
        _args["t"] = title
        if year:
            _args["y"] = str(year)
        return f"{self.URL}?{urllib.parse.urlencode(_args)}"

    def movie_search(self, data: Union[MovieData, IMDBId]) -> Optional[OMDbMovieSearchResult]:
        if not data:
            self.error("search requires either MovieData or IMDBId to be set")
            return None
        if isinstance(data, IMDBId):
            url = self._url_from_imdb(data)
        elif isinstance(data, MovieData):
            url = self._url_from_movie_data(data)
        else:
            self.error(f"invalid search data type: {type(data)}")
            return None
        _existing = self._results.get(url, None)
        if _existing is not None:
            return _existing
        _ret = OMDbMovieSearchResult(self._search(url))
        self._results[url] = _ret
        return _ret


def main():
    parser = ArgumentParser()
    parser.add_argument("--year", "-y", type=int, default=None)
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--id", "-i", type=str, default=None)
    grp.add_argument("--title", "-t", type=str, default=None)
    args = parser.parse_args()
    _omdb = OMDb()
    if args.title:
        data = MovieData(title=args.title, year=args.year)
    else:
        data = IMDBId(args.id)
    res: Optional[OMDbMovieSearchResult] = _omdb.movie_search(data)
    if res is None or not res.valid:
        print("could not get a valid search result!")
    else:
        res.print()


if __name__ == "__main__":
    main()
