from typing import Optional, List, Dict
from dataclasses import dataclass
import random
from unittest.mock import call

import pytest

from media.episode import EpisodeData
from media.online_search import tvmaze
from media.show import ShowData
from media.imdb_id import IMDBId
from media.tvmaze_id import TvMazeId
from media.enums import Type
import json

from pytest_mock.plugin import MockerFixture


class MockHelper:
    @dataclass
    class EpisodeListResponseParams:
        required_season_num: int
        required_episode_num: int
        required_id: int
        num_seasons: Optional[int] = None
        num_eps_per_season: Optional[int] = None

        def __post_init__(self):
            if self.num_seasons is None:
                self.num_seasons = self.required_season_num + 2
            else:
                assert self.required_season_num <= self.num_seasons
            if self.num_eps_per_season is None:
                self.num_eps_per_season = self.required_episode_num + 5
            else:
                assert self.required_episode_num <= self.num_eps_per_season

    @staticmethod
    def gen_mock(mocker, maze_id: int, title: str, genres: Optional[List[str]] = None, resp_ok: bool = True):
        def _gen_response() -> bytes:
            if genres is None:
                _genres = ["Drama", "Adventure", "Fantasy"]
            _dict = {
                "id": maze_id,
                "name": title,
                "url": f"https://www.tvmaze.com/shows/{maze_id}/{title.replace(' ', '-').lower()}",
                "genres": genres,
            }
            return json.dumps(_dict).encode(encoding="utf-8")

        cm = mocker.MagicMock()
        cm.getcode.return_value = 200 if resp_ok else 404
        cm.read.return_value = _gen_response()
        return cm

    @staticmethod
    def gen_mock_episode_list(mocker, params: EpisodeListResponseParams, resp_ok: bool = True):
        def _gen_ep(ep_id: int, season: int, episode: int) -> dict:
            return {
                "id": ep_id,
                "name": f"EpisodeName Chapter {params.num_eps_per_season * (season - 1) + episode}",
                "season": season,
                "number": episode,
                "_links":
                    {"self": {"href": f"https://api.tvmaze.com/episodes/{ep_id}"}}
            }

        def _gen_response() -> bytes:
            _list: List[Dict] = []
            for season in range(1, params.num_seasons + 1):
                for ep in range(1, params.num_eps_per_season + 1):
                    if params.required_season_num == season and params.required_episode_num == ep:
                        _id = params.required_id
                    else:
                        _id = random.randint(1000, 99999)
                    _list.append(_gen_ep(_id, season, ep))
            return json.dumps(_list).encode(encoding="utf-8")

        cm = mocker.MagicMock()
        cm.getcode.return_value = 200 if resp_ok else 404
        cm.read.return_value = _gen_response()
        return cm

    @staticmethod
    def gen_mock_episode(mocker, ep_id: int, season: int, episode: int, name: str = "", resp_ok: bool = True):
        def _gen_ep() -> bytes:
            _dict = {
                "id": ep_id,
                "name": name or f"EpisodeName Chapter {random.randint(10, 200)}",
                "season": season,
                "number": episode,
                "_links":
                    {"self": {"href": f"https://api.tvmaze.com/episodes/{ep_id}"}}
            }
            return json.dumps(_dict).encode(encoding="utf-8")

        cm = mocker.MagicMock()
        cm.getcode.return_value = 200 if resp_ok else 404
        cm.read.return_value = _gen_ep()
        return cm

    @staticmethod
    def gen_mock_show_not_found(mocker):
        cm = mocker.MagicMock()
        cm.getcode.return_value = 200
        cm.read.return_value = r'{"name":"Not Found","message":"","code":0,"status":404}'.encode("utf-8")
        return cm


class TestTvMazeShowSearch:
    def test_search_using_show_data(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 123, title="Some Cool Show")
        res = _tvmaze.show_search(ShowData(title="Some Cool Show"))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/singlesearch/shows?q=Some+Cool+Show", timeout=4)
        assert res.valid is True
        assert int(res.id) == 123
        assert res.title == "Some Cool Show"

    def test_search_using_imdb(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 666, title="Another Cool Show")
        res = _tvmaze.show_search(IMDBId("tt0944947"))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/lookup/shows?imdb=tt0944947", timeout=4)
        assert res.valid is True
        assert int(res.id) == 666
        assert res.title == "Another Cool Show"

    def test_search_using_tv_maze_id(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 777, title="A Title")
        res = _tvmaze.show_search(TvMazeId(777, media_type=Type.Show))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/shows/777", timeout=4)
        assert res.valid is True
        assert int(res.id) == 777
        assert res.title == "A Title"

    def test_search_using_string(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 456, title="A Show I Want To Find")
        res = _tvmaze.show_search("A Show I Want To Find")
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/singlesearch/shows?q=A+Show+I+Want+To+Find", timeout=4)
        assert res.valid is True
        assert int(res.id) == 456
        assert res.title == "A Show I Want To Find"

    def test_search_show_not_found(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock_show_not_found(mocker)
        res = _tvmaze.show_search(TvMazeId(99999999999, media_type=Type.Show))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/shows/99999999999", timeout=4)
        assert res.valid is False

    def test_search_show_use_cache(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=True)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 779, title="A Title")
        _ = _tvmaze.show_search(TvMazeId(779, media_type=Type.Show))
        _ = _tvmaze.show_search(TvMazeId(779, media_type=Type.Show))
        _ = _tvmaze.show_search(TvMazeId(779, media_type=Type.Show))
        res = _tvmaze.show_search(TvMazeId(779, media_type=Type.Show))
        urllib_mock.assert_called_once_with(r"http://api.tvmaze.com/shows/779", timeout=4)
        assert res.valid is True
        assert int(res.id) == 779
        assert res.title == "A Title"


class TestTvMazeEpisodeSearch:
    def test_search_using_show_data(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        _title = "Some Cool Show"
        _q = _title.replace(' ', '+')
        _ep_id = 123
        _show_id = 888
        _s, _e = 2, 1
        _url_show = f"http://api.tvmaze.com/singlesearch/shows?q={_q}"
        _url_list = f"http://api.tvmaze.com/shows/{_show_id}/episodes"

        def _call_mapping(arg, timeout):
            assert timeout == 4
            _p = MockHelper.EpisodeListResponseParams(required_season_num=_s,
                                                      required_episode_num=_e,
                                                      required_id=_ep_id)
            _map = {_url_show: MockHelper.gen_mock(mocker,
                                                   _show_id,
                                                   title=_title),
                    _url_list: MockHelper.gen_mock_episode_list(mocker,
                                                                _p)}
            return _map[arg]

        urllib_mock.side_effect = _call_mapping
        res = _tvmaze.episode_search(ShowData(title=_title), season_num=2, episode_num=1)
        urllib_mock.assert_has_calls([call(_url_show, timeout=4), call(_url_list, timeout=4)])
        assert res.valid is True
        assert res.episode == _e
        assert res.season == _s
        assert int(res.id) == _ep_id

    def test_search_using_episode_data(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        _title = "Dreadliest Carts"
        _q = _title.replace(' ', '+')
        _ep_id = 44
        _show_id = 789
        _s, _e = 10, 12
        _url_show = f"http://api.tvmaze.com/singlesearch/shows?q={_q}"
        _url_list = f"http://api.tvmaze.com/shows/{_show_id}/episodes"

        def _call_mapping(arg, timeout):
            assert timeout == 4
            _p = MockHelper.EpisodeListResponseParams(required_season_num=_s,
                                                      required_episode_num=_e,
                                                      required_id=_ep_id)
            _map = {_url_show: MockHelper.gen_mock(mocker,
                                                   _show_id,
                                                   title=_title),
                    _url_list: MockHelper.gen_mock_episode_list(mocker,
                                                                _p)}
            return _map[arg]

        urllib_mock.side_effect = _call_mapping
        res = _tvmaze.episode_search(EpisodeData(show_title=_title, episode_number=_e, season_number=_s))
        urllib_mock.assert_has_calls([call(_url_show, timeout=4), call(_url_list, timeout=4)])
        assert res.valid is True
        assert res.episode == _e
        assert res.season == _s
        assert int(res.id) == _ep_id

    def test_search_using_show_tv_maze_id(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        _title = "MessyChef Junior"
        _q = _title.replace(' ', '+')
        _ep_id = 87654
        _show_id = 6368
        _s, _e = 3, 55
        _url_show = f"http://api.tvmaze.com/shows/{_show_id}"
        _url_list = f"http://api.tvmaze.com/shows/{_show_id}/episodes"

        def _call_mapping(arg, timeout):
            assert timeout == 4
            _p = MockHelper.EpisodeListResponseParams(required_season_num=_s,
                                                      required_episode_num=_e,
                                                      required_id=_ep_id)
            _map = {_url_show: MockHelper.gen_mock(mocker,
                                                   _show_id,
                                                   title=_title),
                    _url_list: MockHelper.gen_mock_episode_list(mocker,
                                                                _p)}
            return _map[arg]

        urllib_mock.side_effect = _call_mapping
        res = _tvmaze.episode_search(TvMazeId(_show_id, media_type=Type.Show), episode_num=_e, season_num=_s)
        urllib_mock.assert_has_calls([call(_url_show, timeout=4), call(_url_list, timeout=4)])
        assert res.valid is True
        assert res.episode == _e
        assert res.season == _s
        assert int(res.id) == _ep_id

    def test_search_using_episode_tv_maze_id(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        urllib_mock = mocker.patch("urllib.request.urlopen")
        _title = "MessyChef Junior"
        _q = _title.replace(' ', '+')
        _ep_id = 87654
        _s, _e = 3, 55
        _url_show = f"http://api.tvmaze.com/episodes/{_ep_id}"
        urllib_mock.return_value = MockHelper.gen_mock_episode(mocker, _ep_id, _s, _e, name="Sloppy CrabCakes")
        res = _tvmaze.episode_search(TvMazeId(_ep_id, media_type=Type.Episode))
        urllib_mock.assert_called_with(_url_show, timeout=4)
        assert res.valid is True
        assert int(res.id) == _ep_id
        assert res.episode == _e
        assert res.season == _s
        assert res.title == "Sloppy CrabCakes"


class TestTvMazeExceptions:
    def test_show_search_status_code_not_ok(self, mocker: MockerFixture):
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 1, title="Show", resp_ok=False)
        _tvmaze = tvmaze.TvMaze(use_cache=False)
        with pytest.raises(ConnectionError):
            _tvmaze.show_search(IMDBId("tt0944948"))


class TestTvMazeSearchResult:
    def test_show_result_invalid(self):
        res = tvmaze.TvMazeShowSearchResult({})
        assert res.valid is False
        res = tvmaze.TvMazeShowSearchResult({"key": "value"})
        assert res.valid is False
        res = tvmaze.TvMazeShowSearchResult({"name": "Some Cool Show"})
        assert res.valid is False
        res = tvmaze.TvMazeShowSearchResult(None)
        assert res.valid is False
        res = tvmaze.TvMazeShowSearchResult("String")
        assert res.valid is False

    def test_episode_result_invalid(self):
        res = tvmaze.TvMazeEpisodeSearchResult({})
        assert res.valid is False
        res = tvmaze.TvMazeEpisodeSearchResult({"key": "value"})
        assert res.valid is False
        res = tvmaze.TvMazeEpisodeSearchResult({"name": "Some Cool Show"})
        assert res.valid is False
        res = tvmaze.TvMazeEpisodeSearchResult(None)
        assert res.valid is False
        res = tvmaze.TvMazeEpisodeSearchResult("String")
        assert res.valid is False
