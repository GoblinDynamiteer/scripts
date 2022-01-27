from typing import Optional, List

import pytest

from media.online_search import tvmaze
from media.show import ShowData
from media.imdb_id import IMDBId
from media.tvmaze_id import TvMazeId
from media.enums import Type
import json

from pytest_mock.plugin import MockerFixture


class MockHelper:
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
    def gen_mock_show_not_found(mocker):
        cm = mocker.MagicMock()
        cm.getcode.return_value = 200
        cm.read.return_value = r'{"name":"Not Found","message":"","code":0,"status":404}'.encode("utf-8")
        return cm


class TestTvMazeSearch:
    def test_show_search_using_show_data(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze()
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 123, title="Some Cool Show")
        res = _tvmaze.show_search(ShowData(title="Some Cool Show"))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/singlesearch/shows?q=Some+Cool+Show", timeout=4)
        assert res.valid is True
        assert int(res.id) == 123
        assert res.title == "Some Cool Show"

    def test_show_search_using_imdb(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze()
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 666, title="Another Cool Show")
        res = _tvmaze.show_search(IMDBId("tt0944947"))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/lookup/shows?imdb=tt0944947", timeout=4)
        assert res.valid is True
        assert int(res.id) == 666
        assert res.title == "Another Cool Show"

    def test_show_search_using_tv_maze_id(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze()
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 777, title="A Title")
        res = _tvmaze.show_search(TvMazeId(777, media_type=Type.Show))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/shows/777", timeout=4)
        assert res.valid is True
        assert int(res.id) == 777
        assert res.title == "A Title"

    def test_show_search_show_not_found(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze()
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock_show_not_found(mocker)
        res = _tvmaze.show_search(TvMazeId(99999999999, media_type=Type.Show))
        urllib_mock.assert_called_with(r"http://api.tvmaze.com/shows/99999999999", timeout=4)
        assert res.valid is False

    def test_show_search_show_use_cache(self, mocker: MockerFixture):
        _tvmaze = tvmaze.TvMaze()
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


class TestTvMazeExceptions:
    def test_show_search_status_code_not_ok(self, mocker: MockerFixture):
        urllib_mock = mocker.patch("urllib.request.urlopen")
        urllib_mock.return_value = MockHelper.gen_mock(mocker, 1, title="Show", resp_ok=False)
        _tvmaze = tvmaze.TvMaze()
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
