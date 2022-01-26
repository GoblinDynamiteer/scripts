#!/usr/bin/env python3

from typing import Dict, Optional, Union, List, Any
from enum import Enum, auto
import json
import urllib.parse
import urllib.request

from argparse import ArgumentParser

from base_log import BaseLog
from media.online_search.result import SearchResult
from media.show import ShowData
from media.imdb_id import IMDBId
from media.tvmaze_id import TvMazeId


class TvMazeShowSearchResult(SearchResult):
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
    def genres(self):
        return self._raw.get("genres", None)

    @property
    def id(self) -> Optional[TvMazeId]:
        _id = self._raw.get("id", None)
        if _id is None:
            return None
        return TvMazeId(_id)


class TvMazeEpisodeSearchResult(SearchResult):
    @property
    def valid(self):
        return "id" in self._raw

    @property
    def year(self):
        return self._raw.get("airdate", None)

    @property
    def title(self):
        return self._raw.get("name", None)

    @property
    def genres(self):
        return None

    @property
    def season(self) -> Optional[int]:
        return self._raw.get("season", None)

    @property
    def episode(self) -> Optional[int]:
        return self._raw.get("number", None)

    @property
    def id(self) -> Optional[TvMazeId]:
        _id = self._raw.get("id", None)
        if _id is None:
            return None
        return TvMazeId(_id)


class SearchType(Enum):
    Show = auto()
    Episode = auto()


class TvMaze(BaseLog):
    URL = "http://api.tvmaze.com"
    _results: Dict[str, Union[TvMazeShowSearchResult, TvMazeEpisodeSearchResult, List]] = {}
    _cached_ep_list: Dict[str, List[TvMazeEpisodeSearchResult]] = {}

    def __init__(self, verbose=False):
        BaseLog.__init__(self, verbose=verbose)
        self.set_log_prefix("TVMaze")
        self.log("init")

    def _search(self, url) -> Any:
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

    def _url_from_show_mazeid(self, maze_id: TvMazeId) -> Optional[str]:
        if not maze_id.valid():
            return None
        return f"{self.URL}/shows/{maze_id}"

    def show_search(self, data: Union[ShowData, IMDBId, TvMazeId]) -> Optional[TvMazeShowSearchResult]:
        if not data:
            self.error("search requires either ShowData or IMDBId to be set")
            return None
        if isinstance(data, IMDBId):
            url = self._url_from_imdb(data, search_type=SearchType.Show)
        elif isinstance(data, ShowData):
            url = self._url_from_show_data(data)
        elif isinstance(data, TvMazeId):
            url = self._url_from_show_mazeid(data)
        else:
            self.error(f"invalid search data type: {type(data)}")
            return None
        _existing = self._results.get(url, None)
        if _existing is not None:
            return _existing
        _ret = TvMazeShowSearchResult(self._search(url))
        self._results[url] = _ret
        return _ret

    def episode_search_list_all(self, show_data: Union[ShowData, IMDBId, TvMazeId]) -> List[TvMazeEpisodeSearchResult]:
        _show_result = self.show_search(show_data)
        if _show_result is None:
            return []
        if str(_show_result.id) in self._cached_ep_list:
            return self._cached_ep_list[str(_show_result.id)]
        _ret = []
        _url = f"{self._url_from_show_mazeid(_show_result.id)}/episodes"
        if _url not in self._results:
            _res = self._search(_url)
            if not isinstance(_res, list):
                raise TypeError("got invalid type in search response")
            self._results[_url] = _res
        else:
            _res = self._results[_url]
        for _data in _res:
            _ep_url = _data.get("_links", {}).get("self", {}).get("href", None)
            if _ep_url is None:
                raise TypeError(f"could not get url from show list data: {_data}")
            _search_result = TvMazeEpisodeSearchResult(_data)
            _ret.append(_search_result)
            self._results[_ep_url] = _search_result
        self._cached_ep_list[str(_show_result.id)] = _ret
        return _ret

    def episode_search(self, show_data: Union[ShowData, IMDBId, TvMazeId], episode_num: int,
                       season_num: int) -> Optional[TvMazeEpisodeSearchResult]:
        for _ep in self.episode_search_list_all(show_data):
            if _ep.season == season_num and _ep.episode == episode_num:
                return _ep
        return None


def main():
    parser = ArgumentParser()
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--imdbid", "-i", type=str, default=None, dest="imdb_id")
    grp.add_argument("--mazeid", "-m", type=int, default=None, dest="maze_id")
    grp.add_argument("--title", "-t", type=str, default=None)
    args = parser.parse_args()
    _tvmaze = TvMaze(verbose=True)
    if args.title:
        data = ShowData(title=args.title)
    elif args.imdb_id:
        data = IMDBId(args.imdb_id)
    elif args.maze_id:
        data = TvMazeId(args.maze_id)
    else:
        print("no query/id")
        return
    res: Optional[TvMazeShowSearchResult] = _tvmaze.show_search(data)
    if res is None or not res.valid:
        print("could not get a valid search result!")
    else:
        from printout import print_line
        res.print()
        print_line()
        print("valid", res.valid)
        print("title", res.title)
        print("year", res.year)
        print("genres", res.genres)
        print("id", res.id)
        print_line()
        print(_tvmaze.episode_search_list_all(data))
        print_line()
        print(_tvmaze.episode_search(data, 1, 1))


if __name__ == "__main__":
    main()
