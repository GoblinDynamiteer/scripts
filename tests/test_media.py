
from typing import Dict
from pathlib import Path
from string import ascii_letters

from media.movie import Movie
from media.util import Util, MediaPaths
from media.regex import parse_season_and_episode
import config


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
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _mov_path
        _mov_path.mkdir()
        _paths: Dict[str, Path] = {}
        for let in {'#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                    'T', 'U', 'VW', 'X', 'Y', 'Z'}:
            _paths[let] = _mov_path / let
            _paths[let].mkdir()
        _invalid_path = _mov_path / ".invalid"
        _invalid_path.mkdir()
        for path in MediaPaths().movie_letter_dirs():
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

    def test_is_season_false_from_str(self):
        assert not Util.is_season("The.Children.Show.S01E01.1080p.BluRay.x264-Grp")


class TestRegex:
    def test_parse_season_and_episode_both_present_str(self):
        assert parse_season_and_episode("Show.S04E10.720p.BluRay.x264-GRP.mkv") == (4, 10)

    def test_parse_season_and_episode_only_season_present_str(self):
        assert parse_season_and_episode("Show.S04.720p.BluRay.x264-GRP.mkv") == (4, None)

    def test_parse_season_and_episode_only_none_present_str(self):
        assert parse_season_and_episode("Show.720p.BluRay.x264-GRP.mkv") == (None, None)

    def test_parse_season_and_episode_both_present_str_spaces(self):
        assert parse_season_and_episode("Show S04E10 720p BluRay x264-GRP.mkv") == (4, 10)

    def test_parse_season_and_episode_only_season_present_str_spaces(self):
        assert parse_season_and_episode("Show S04 720p BluRay x264-GRP.mkv") == (4, None)

    def test_parse_season_and_episode_only_none_present_str_spaces(self):
        assert parse_season_and_episode("Show 720p BluRay x264-GRP.mkv") == (None, None)


class TestMovie:
    MOV_PATH = Path.home() / "Movies"

    def test_name_from_file(self, tmp_path, mocker):
        _file = tmp_path / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv"
        _file.touch()
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        mov = Movie(_file)
        assert mov.name == "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp"

    def test_correct_loc_parent_is_not_movie_dir(self, tmp_path, mocker):
        _file = tmp_path / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv"
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        _file.touch()
        mov = Movie(_file)
        assert mov.get_correct_location() == self.MOV_PATH / "M" / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp"

    def test_correct_loc_parent_is_movie_dir(self, tmp_path, mocker):
        _file = tmp_path / "SMovie.2015.720p.WEB-DL.DD5.1.H264-Grp" / "smv1080p-grp.mkv"
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        _file.parent.mkdir()
        _file.touch()
        mov = Movie(_file)
        assert mov.get_correct_location() == self.MOV_PATH / "S" / "SMovie.2015.720p.WEB-DL.DD5.1.H264-Grp"

    def test_correct_letter_numbers(self, tmp_path, mocker):
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        for _num in range(0, 100):
            _file = tmp_path / f"{_num}.Movie.2015.720p.WEB-DL.DD5.1.H264-Grp" / f"{_num}.smv1080p-grp.mkv"
            mov = Movie(_file)
            assert mov.letter == "#"

    def test_correct_letter_numbers_an_a_the(self, tmp_path, mocker):
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        for _num in range(0, 100):
            for prefix in ["An.", "A.", "The."]:
                _file = tmp_path / f"{prefix}{_num}.Movie.2015.720p.WEB-DL.DD5.1.H264-Grp" / f"{_num}smv1080p-grp.mkv"
                mov = Movie(_file)
                assert mov.letter == "#"

    def test_correct_letter_vw(self, tmp_path, mocker):
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        for v in ["v", "V", "W", "w"]:
            _file = tmp_path / f"{v}.Movie.2015.720p.WEB-DL.DD5.1.H264-Grp" / f"{v}.smv1080p-grp.mkv"
            mov = Movie(_file)
            assert mov.letter == "VW"

    def test_correct_letter_vw_an_a_the(self, tmp_path, mocker):
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        for v in ["v", "V", "W", "w"]:
            for prefix in ["An.", "A.", "The."]:
                _file = tmp_path / f"{prefix}{v}Movie.2015.720p.WEB-DL.DD5.1.H264-Grp" / f"mv-grp.mkv"
                mov = Movie(_file)
                assert mov.letter == "VW"

    def test_correct_letters(self, tmp_path, mocker):
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        for letter in [let for let in ascii_letters if let not in ["v", "V", "W", "w"]]:
            _file = tmp_path / f"{letter}Movie.2015.720p.WEB-DL.DD5.1.H264-Grp" / f"{letter}.smv1080p-grp.mkv"
            mov = Movie(_file)
            assert mov.letter == letter.upper()

    def test_correct_letters_vw_an_a_the(self, tmp_path, mocker):
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.MOV_PATH
        for letter in [let for let in ascii_letters if let not in ["v", "V", "W", "w"]]:
            for prefix in ["An.", "A.", "The."]:
                _file = tmp_path / f"{prefix}{letter}Movie.2015.720p.WEB-DL.DD5.1.H264-Grp" / f"abc-grp.mkv"
                mov = Movie(_file)
                assert mov.letter == letter.upper()

    def test_exists(self, tmp_path, mocker):
        _file = tmp_path / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv"
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _file.parent
        mov = Movie(_file)
        assert not mov.exists_on_disk()
        _file.touch()
        assert mov.exists_on_disk()

    def test_valid(self, tmp_path, mocker):
        _file = tmp_path / "Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv"
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = _file.parent
        mov = Movie(_file)
        assert mov.is_valid() is True
