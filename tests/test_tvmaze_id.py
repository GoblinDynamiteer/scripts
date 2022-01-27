import pytest

from media.tvmaze_id import TvMazeId
from media.enums import Type


class TestTvMazeIdStringParse:
    def test_single(self):
        tvid = TvMazeId("https://www.tvmaze.com/episodes/185053/")
        assert str(tvid) == "185053"
        assert tvid.has_multiple_ids() is False
        assert tvid.valid() is True
        tvid = TvMazeId("xxx 185053 zzz")
        assert str(tvid) == "185053"
        assert tvid.has_multiple_ids() is False
        assert tvid.valid() is True

    def test_multiple(self):
        tvid = TvMazeId("https://www.tvmaze.com/episodes/185053/ https://www.tvmaze.com/shows/60")
        assert str(tvid) == "185053"
        assert tvid.has_multiple_ids() is True
        assert tvid.valid() is True

    def test_multiple_same_id(self):
        tvid = TvMazeId("https://www.tvmaze.com/episodes/185053/ 185053")
        assert str(tvid) == "185053"
        assert tvid.has_multiple_ids() is False
        assert tvid.valid() is True

    def test_invalid(self):
        tvid = TvMazeId("something else")
        assert str(tvid) == ""
        assert tvid.has_multiple_ids() is False
        assert tvid.valid() is False


class TestTvMazeIdInt:
    def test_num(self):
        tvid = TvMazeId(123)
        assert str(tvid) == "123"
        assert tvid.has_multiple_ids() is False
        assert tvid.valid() is True


class TestTvMazeIdType:
    def test_default(self):
        tvid = TvMazeId(123)
        assert tvid.type == Type.Show

    def test_set_show(self):
        tvid = TvMazeId(123, media_type=Type.Show)
        assert tvid.type == Type.Show

    def test_set_episode(self):
        tvid = TvMazeId(123, media_type=Type.Episode)
        assert tvid.type == Type.Episode


class TestTvMazeIdExceptions:
    def test_pass_incorrect_type(self):
        with pytest.raises(TypeError):
            TvMazeId({})
        with pytest.raises(TypeError):
            TvMazeId(123.123)
        with pytest.raises(TypeError):
            TvMazeId(TvMazeId("https://www.tvmaze.com/episodes/185053/"))

    def test_int_non_positive(self):
        with pytest.raises(ValueError):
            TvMazeId(0)
        with pytest.raises(ValueError):
            TvMazeId(-1)
        with pytest.raises(ValueError):
            TvMazeId(-9999999999)

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            TvMazeId(123, media_type=Type.Movie)
        with pytest.raises(TypeError):
            TvMazeId(123, media_type="String")