from pathlib import Path
from string import ascii_letters

from media.movie import Movie, MovieData
from media.show import Show, ShowData
from media.regex import parse_season_and_episode, parse_year, parse_quality
import config


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

    def test_parse_year_multiple_present(self):
        assert parse_year("Movie.2000.2015.1080p.WEB-DL.DD5.1.H264-Grp.mkv") == 2015
        assert parse_year("Movie.2000.2015.1972.1080p.WEB-DL.DD5.1.H264-Grp.mkv") == 1972

    def test_parse_year(self):
        assert parse_year("Movie.1983.1080p.WEB-DL.DD5.1.H264-Grp.mkv") == 1983

    def test_parse_year_not_present(self):
        assert parse_year("Movie.1080p.WEB-DL.DD5.1.H264-Grp.mkv") is None

    def test_parse_quality_1080p(self):
        assert parse_quality("Movie.1983.1080p.WEB-DL.DD5.1.H264-Grp.mkv") == "1080p"

    def test_parse_quality_720p(self):
        assert parse_quality("Movie.1983.720p.WEB-DL.DD5.1.H264-Grp.mkv") == "720p"


class TestShow:
    SHOW_PATH = Path.home() / "TVShows"

    def test_name_from_dir(self, tmp_path, mocker):
        _dir = tmp_path / "Show.Name.S01.1080p.WEB-DL.DDP2.0.x264-GrpName"
        _dir.mkdir()
        _path_mock = mocker.patch.object(config.ConfigurationManager, "path")
        _path_mock.return_value = self.SHOW_PATH
        show = Show(_dir)
        assert show.name == "Show.Name.S01.1080p.WEB-DL.DDP2.0.x264-GrpName"


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


class TestMovieData:
    def test_parse_title_and_year(self):
        md = MovieData("Movie.2015.1080p.WEB-DL.DD5.1.H264-Grp")
        assert md.title == "Movie"
        assert md.year == 2015

    def test_parse_title_year_missing(self):
        md = MovieData("Movie.With.Cool.Title.720p.WEB-DL.DD5.1.H264-Grp")
        assert md.title == "Movie With Cool Title"
        assert md.year is None

    def test_parse_title_with_language_tag(self):
        md = MovieData("Movie.Title.2010.SWEDiSH.720p.BluRay.x264-iMAGRP")
        assert md.title == "Movie Title"
        assert md.year == 2010

    def test_parse_title_with_limited_tag(self):
        md = MovieData("Movie.Title.1966.LIMITED.720p.BluRay.x264-iMAGRP")
        assert md.title == "Movie Title"
        assert md.year == 1966

    def test_parse_title_with_limited_tag_year_missing(self):
        md = MovieData("Movie.Title.LIMITED.720p.BluRay.x264-iMAGRP")
        assert md.title == "Movie Title"
        assert md.year is None