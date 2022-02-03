from pathlib import Path
from typing import Dict

import config
from media.util import MediaPaths, Util


class TestUtilMediaPaths:
    def test_movie_dir(self, tmp_path, mocker):
        _path = tmp_path / "mov"
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _path
        assert MediaPaths().movie_dir() == _path

    def test_tv_dir(self, tmp_path, mocker):
        _path = tmp_path / "tv"
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _path
        assert MediaPaths().tv_dir() == _path

    def test_movie_letter_dirs(self, tmp_path, mocker):
        _mov_path = tmp_path / "mov"
        _mov_path.mkdir()
        assert _mov_path.is_dir() is True
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _mov_path
        _paths: Dict[str, Path] = {}
        for let in {'#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                    'T', 'U', 'VW', 'X', 'Y', 'Z'}:
            _paths[let] = _mov_path / let
            _paths[let].mkdir()
            assert _paths[let].is_dir() is True
        _invalid_path = _mov_path / ".invalid"
        _invalid_path.mkdir()
        assert _invalid_path.is_dir() is True
        for path in MediaPaths().movie_letter_dirs():
            assert path in _paths.values()

    def test_show_dirs(self, tmp_path, mocker):
        _tv_path = tmp_path / "mov"
        _tv_path.mkdir()
        assert _tv_path.is_dir() is True
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _tv_path
        _paths: Dict[str, Path] = {}
        for num in range(10):
            _show_name = f"Show Number {num}"
            _paths[_show_name] = _tv_path / _show_name
            _paths[_show_name].mkdir()
            assert _paths[_show_name].is_dir() is True
        for path in MediaPaths().show_dirs():
            assert path in _paths.values()


class TestUtilMovie:
    def test_is_movie_true_720p_year_bluray_from_str(self):
        assert Util.is_movie("Movie.With.Some.Cool.Name.1995.720p.BluRay.X264-GROUP")
        assert Util.is_movie("Movie.2021.720p.BluRay.X264-GROUP")
        assert Util.is_movie("Film.1988.Special.Edition.720p.INTERNAL.BluRay.x264-GRP")

    def test_is_movie_true_1080p_year_bluray_from_str(self):
        assert Util.is_movie("Movie.With.Some.Cool.Name.1982.1080p.BluRay.X264-GROUP")
        assert Util.is_movie("Movie.2021.1080p.BluRay.X264-GROUP")

    def test_is_movie_false_episode_str(self):
        assert not Util.is_movie("Show.S04E10.720p.BluRay.x264-GRP.mkv")

    def test_is_movie_false_from_str(self):
        assert not Util.is_movie("Just Some Random String")


class TestUtilShow:
    def test_is_episode_true_from_str(self):
        assert Util.is_episode("Show.S04E10.720p.BluRay.x264-GRP.mkv")

    def test_is_episode_false_from_str(self):
        assert not Util.is_episode("Show.S04.720p.BluRay.x264-GRP.mkv")

    def test_is_season_true_from_str(self):
        assert Util.is_season("The.Family.Show.S01.1080p.HDTV.x264-Grp")

    def test_is_season_true_from_str_internal(self):
        assert Util.is_season("Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME")

    def test_is_season_false_from_str(self):
        assert not Util.is_season("The.Children.Show.S01E01.1080p.BluRay.x264-Grp")