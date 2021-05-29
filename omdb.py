#!/usr/bin/env python3

import json
import pprint
import urllib.parse
import urllib.request
from argparse import ArgumentParser

import util
from util import BaseLog, Singleton
from config import ConfigurationManager


class OMDbMovieSearchResult:
    def __init__(self, data):
        self._raw = data

    def print(self):
        if not self._raw:
            print(None)
        _str = json.dumps(self._raw, indent=4)
        print(_str)

    def __repr__(self):
        return json.dumps(self._raw, indent=4)

    @property
    def valid(self):
        return "Title" in self._raw

    @property
    def year(self):
        return self._raw.get("Year", None)

    @property
    def title(self):
        return self._raw.get("Title", None)

    @property
    def genre(self):
        return self._raw.get("Genre", None)

    @property
    def id(self):
        return self._raw.get("imdbID", None)


class OMDb(BaseLog):
    URL = "http://www.omdbapi.com"
    _results = {}

    def __init__(self, verbose=False):
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("OMDb")
        self._api_key = ConfigurationManager().get("omdb_api_key", default=None)
        self._url_args = {"apikey": self._api_key, "type": "movie"}
        self.log("init")

    @property
    def valid(self):
        return self._api_key is not None

    def _search(self, url):
        try:
            _res = urllib.request.urlopen(url, timeout=4).read().decode("utf-8")
            return json.loads(_res)
        except:
            pass
        return {}

    def movie_search(self, title=None, imdb_id=None, year=None):
        if not title and not imdb_id:
            return OMDbMovieSearchResult({})
        if util.is_imdbid(imdb_id):
            self._url_args["i"] = util.parse_imdbid(imdb_id)
        elif title:
            self._url_args["t"] = title
        if util.is_valid_year(year):
            self._url_args["y"] = year
        url = f"{self.URL}?{urllib.parse.urlencode(self._url_args)}"
        for key in ["i", "y", "t"]:
            self._url_args.pop(key, None)
        _existing = self._results.get(url, None)
        if _existing:
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
    pp = pprint.PrettyPrinter(indent=4)
    _omdb = OMDb()
    pp.pprint(_omdb.movie_search(title=args.title, year=args.year, imdb_id=args.id))


if __name__ == "__main__":
    main()
