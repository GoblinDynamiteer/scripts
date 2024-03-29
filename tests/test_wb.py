from config import ConfigurationManager

from pathlib import Path, PurePosixPath

from wb.helper_methods import parse_download_arg, gen_find_cmd
from wb.item import FileListItem
from wb.list import FileList

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_config(tmpdir_factory):
    _file = Path(tmpdir_factory.mktemp("settings").join("_settings.txt"))
    with open(_file, "w") as settings_file:
        settings_file.write("\n".join(["[wb]", "username=johndoe"]))
    ConfigurationManager().set_config_file(_file)


class TestHelperMethods:
    def test_gen_find_cmd(self):
        _expected = r'find /home/johndoe/files \( -iname "*.mkv" -o -iname "*.rar" \)' \
                    r' -printf "%T@ | %s | %p\n" | sort -n'
        assert gen_find_cmd(["mkv", "rar"]) == _expected

    def test_parse_download_arg(self):
        arg = "1,2,3"
        assert parse_download_arg(arg, 1000) == [1, 2, 3]
        arg = "222-225"
        assert parse_download_arg(arg, 1000) == [222, 223, 224, 225]
        arg = "666,222-225"
        assert parse_download_arg(arg, 1000) == [666, 222, 223, 224, 225]
        arg = "666,222-225,2-3"
        assert parse_download_arg(arg, 1000) == [666, 222, 223, 224, 225, 2, 3]
        arg = "6-10"
        assert parse_download_arg(arg, 1000) == [6, 7, 8, 9, 10]
        arg = "Show.S06E02"
        assert parse_download_arg(arg, 1000) == ["Show.S06E02"]
        arg = "Show.S06E02,2"
        assert parse_download_arg(arg, 1000) == ["Show.S06E02", 2]
        arg = "Show.S06E02,2-5"
        assert parse_download_arg(arg, 1000) == ["Show.S06E02", 2, 3, 4, 5]
        arg = "124-123"  # invalid range
        assert parse_download_arg(arg, 1000) == []
        arg = "124-123,111-115"  # invalid range + valid range
        assert parse_download_arg(arg, 1000) == [111, 112, 113, 114, 115]

    def test_parse_download_arg_get_last(self):
        arg = "-5"
        assert parse_download_arg(arg, 10) == [6, 7, 8, 9, 10]
        arg = "-1"
        assert parse_download_arg(arg, 9812312) == [9812312]
        arg = "5-10,-2"
        assert parse_download_arg(arg, 100) == [5, 6, 7, 8, 9, 10, 99, 100]
        arg = "2,-3"
        assert parse_download_arg(arg, 100) == [2, 98, 99, 100]


class TestFileListItem:
    def test_parse_valid_episode(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.1080p.WEB.H264-GROUPNAME/" \
                r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME.mkv"
        _item = FileListItem(_line)
        assert _item.valid is True
        assert _item.name == "Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME.mkv"
        assert _item.size == 4025725826
        assert _item.timestamp == 1623879181
        assert _item.path == PurePosixPath(
            r"/home/johndoe/files/Show.S04.1080p.WEB.H264-GROUPNAME/"
            r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME.mkv"
        )

    def test_parse_invalid_movie_sample(self):
        _line = r"1611998314.0000000000 | 45986355 | " \
                r"/home/johndoe/files/The.Movie.2021.1080p.WEB.H264-GROUPNAME/Sample/" \
                r"the.movie.2021.1080p.web.h264-grp-sample.mkv"
        _item = FileListItem(_line)
        assert _item.valid is False

    def test_parse_invalid_subpack(self):
        _line = r"1611998314.0000000000 | 196154 | " \
                r"/home/johndoe/files/SE.SUBPACKS.02.03.2012-Collection/" \
                r"Cool.Movie.2004.NORDiC.SUBPACK.x264-Grp/cmv.x264-grp.rar"
        _item = FileListItem(_line)
        assert _item.valid is False

    def test_parse_invalid_subs(self):
        _line = r"1611998314.0000000000 | 196154 | " \
                r"/home/johndoe/files/Movie.2017.720p.BluRay.x264-Group/" \
                r"Subs/" \
                r"movie.2017.720p.bluray.x264-group.rar"
        _item = FileListItem(_line)
        assert _item.valid is False

    def test_parse_invalid_lines(self):
        _line = r"1611998314.0000000000 45986355 | " \
                r"/home/johndoe/files/SomeFile.mkv"
        _item = FileListItem(_line)
        assert _item.valid is False
        _line = r"1611998314.0000000000 | 45986355 | " \
                r"not_correct_path"
        _item = FileListItem(_line)
        assert _item.valid is False
        _line = r"1611998314.0000000000 | xxxxx | " \
                r"/home/johndoe/files/SomeFile.mkv"
        _item = FileListItem(_line)
        assert _item.valid is False
        _line = r"xxxxx | 45986355 | " \
                r"/home/johndoe/files/SomeFile.mkv"
        _item = FileListItem(_line)
        assert _item.valid is False

    def test_parse_valid_rar_part01(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp/" \
                r"some.cool.movie.2007.1080p.bluray.dts.x264-grp.part01.rar"
        _item = FileListItem(_line)
        assert _item.valid is True

    def test_parse_invalid_rar_not_part01(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp/" \
                r"some.cool.movie.2007.1080p.bluray.dts.x264-grp.part{:02d}.rar"
        for part_num in range(2, 100):
            _item = FileListItem(_line.format(part_num))
            assert _item.valid is False

    def test_parse_invalid_rar_not_part001(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp/" \
                r"some.cool.movie.2007.1080p.bluray.dts.x264-grp.part{:03d}.rar"
        for part_num in range(2, 100):
            _item = FileListItem(_line.format(part_num))
            assert _item.valid is False

    def test_parse_invalid_sample_dir(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp/" \
                r"Sample/smpl.mkv"
        _item = FileListItem(_line)
        assert _item.valid is False

    def test_set_index(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.1080p.WEB.H264-GROUPNAME/" \
                r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME.mkv"
        _item = FileListItem(_line)
        assert _item.index is None
        _item.index = 0
        assert _item.index == 0
        _item.index = 999
        assert _item.index == 999

    def test_is_movie_rar_in_dir(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp/" \
                r"some.cool.movie.2007.1080p.bluray.dts.x264-grp.rar"
        _item = FileListItem(_line)
        assert _item.is_rar is True
        assert _item.is_video is False
        assert _item.is_movie is True
        assert _item.is_tvshow is False

    def test_is_movie_mkv_in_dir(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp/" \
                r"some.cool.movie.2007.1080p.bluray.dts.x264-grp.mkv"
        _item = FileListItem(_line)
        assert _item.is_rar is False
        assert _item.is_video is True
        assert _item.is_movie is True
        assert _item.is_tvshow is False

    def test_is_movie_mkv(self):
        _line = r"1611998314.0000000000 | 50000000 | " \
                r"/home/johndoe/files/Some.Cool.Movie.2007.1080p.BluRay.DTS.x264-Grp.mkv"
        _item = FileListItem(_line)
        assert _item.is_rar is False
        assert _item.is_video is True
        assert _item.is_movie is True
        assert _item.is_tvshow is False

    def test_is_episode_rar_in_dir(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        assert _item.is_rar is True
        assert _item.is_video is False
        assert _item.is_movie is False
        assert _item.is_tvshow is True

    def test_is_episode_rar_in_season_pack_dir(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        assert _item.is_rar is True
        assert _item.is_video is False
        assert _item.is_movie is False
        assert _item.is_tvshow is True

    def test_is_episode_mkv_in_dir(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.mkv"
        _item = FileListItem(_line)
        assert _item.is_rar is False
        assert _item.is_video is True
        assert _item.is_movie is False
        assert _item.is_tvshow is True

    def test_is_episode_mkv_in_season_pack_dir(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.mkv"
        _item = FileListItem(_line)
        assert _item.is_rar is False
        assert _item.is_video is True
        assert _item.is_movie is False
        assert _item.is_tvshow is True
        assert _item.media_type == FileListItem.MediaType.Episode

    def test_is_episode_mkv(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME.mkv"
        _item = FileListItem(_line)
        assert _item.is_rar is False
        assert _item.is_video is True
        assert _item.is_movie is False
        assert _item.is_tvshow is True
        assert _item.media_type == FileListItem.MediaType.Episode

    def test_parent_name_season_pack(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.mkv"
        _item = FileListItem(_line)
        assert _item.parent_name == "Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME"

    def test_parent_name_episode_mkv(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME.mkv"
        _item = FileListItem(_line)
        assert _item.parent_name is None

    def test_parent_is_season_dir(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.mkv"
        _item = FileListItem(_line)
        assert _item.parent_is_season_dir is True

    def test_parent_is_not_season_dir(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.mkv"
        _item = FileListItem(_line)
        assert _item.parent_is_season_dir is False

    def test_download_path_rar_file(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        assert _item.remote_download_path == PurePosixPath(
            r"/home/johndoe/files/Show.S04.iNTERNAL.1080p.WEB.H264-GROUPNAME/"
            r"Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/"
        )

    def test_download_path_vid_file(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/" \
                r"show.s04e02.1080p.web-grpname.mkv"
        _item = FileListItem(_line)
        assert _item.remote_download_path == PurePosixPath(
            r"/home/johndoe/files/Show.S04E02.iNTERNAL.1080p.WEB.H264-GROUPNAME/"
            r"show.s04e02.1080p.web-grpname.mkv")

    def test_download_path_rar_file_parent_is_dl_dir_raises_error(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/show.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        with pytest.raises(AssertionError):
            _ = _item.remote_download_path

    def test_matches_filter_none_empty_list_and_empty_str(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/show.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        assert _item.matches_filter(None) is True
        assert _item.matches_filter("") is True
        assert _item.matches_filter([]) is True

    def test_matches_filter_str_non_case_sensitive(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/VeryCoolShow.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        assert _item.matches_filter("verycool") is True
        assert _item.matches_filter("VERYCOOLSHOW") is True
        assert _item.matches_filter("YCooLShoW") is True

    def test_matches_filter_str_case_sensitive(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/VeryCoolShow.s04e02.1080p.web-grpname.rar"
        _item = FileListItem(_line)
        assert _item.matches_filter("verycool", case_sensitive=True) is False
        assert _item.matches_filter("VeryCoolShow", case_sensitive=True) is True
        assert _item.matches_filter("CoolShow", case_sensitive=True) is True

    def test_matches_filter_list_non_case_sensitive(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/The.AweSome.Cool.Show.S04E01.1080p.WEB-grpname.rar"
        _item = FileListItem(_line)
        assert _item.matches_filter(["awesome", "show", "s04e01"]) is True
        assert _item.matches_filter(["SHOW", "1080p"]) is True
        assert _item.matches_filter(["awesome", "show", "s04e03"]) is False

    def test_matches_filter_list_case_sensitive(self):
        _line = r"1623879181.7519188610 | 4025725826 | " \
                r"/home/johndoe/files/The.AweSome.Cool.Show.S04E01.1080p.WEB-grpname.rar"
        _item = FileListItem(_line)
        assert _item.matches_filter(["awesome", "show", "s04e01"], case_sensitive=True) is False
        assert _item.matches_filter(["AweSome", "1080p"], case_sensitive=True) is True


class TestFileList:
    TEMPLATE_SHOW = r"{} | {} | " \
                    r"/home/johndoe/files/Show.{}.1080p.WEB.H264-GROUPNAME.mkv"
    TEMPLATE_MOV = r"{} | {} | " \
                   r"/home/johndoe/files/{}.720p.WEB.H264-GROUPNAME.mkv"

    def test_parse(self):
        _find_output = [self.TEMPLATE_SHOW.format("1", "100000", "S01E01"),
                        self.TEMPLATE_SHOW.format("2", "100000", "S01E02"),
                        self.TEMPLATE_MOV.format("3", "100000", "CoolMovie")]
        _list = FileList()
        _list.parse_find_cmd_output(_find_output, "server1")
        _items = _list.items()
        assert len(_items) == 3
        _item1 = _items[0]
        _item2 = _items[1]
        _item3 = _items[2]
        assert _item1.name == "Show.S01E01.1080p.WEB.H264-GROUPNAME.mkv"
        assert _item1.server_id == "server1"
        assert _item2.name == "Show.S01E02.1080p.WEB.H264-GROUPNAME.mkv"
        assert _item3.name == "CoolMovie.720p.WEB.H264-GROUPNAME.mkv"

    def test_get_by_index(self):
        _find_output = [self.TEMPLATE_SHOW.format("1", "100000", "S01E01"),
                        self.TEMPLATE_SHOW.format("2", "100000", "S01E02")]
        _list = FileList()
        _list.parse_find_cmd_output(_find_output, "server1")
        _items = _list.items()
        _item1 = _items[0]
        _item2 = _items[1]
        assert _list.get(1) == _item1
        assert _list.get(2) == _item2

    def test_get_by_name_string(self):
        _find_output = [self.TEMPLATE_SHOW.format("1", "100000", "S01E01"),
                        self.TEMPLATE_SHOW.format("2", "100000", "S01E02")]
        _list = FileList()
        _list.parse_find_cmd_output(_find_output, "server1")
        _items = _list.items()
        _item1 = _items[0]
        _item2 = _items[1]
        assert _list.get("Show.S01E01.1080p.WEB.H264-GROUPNAME.mkv") == _item1
        assert _list.get("Show.S01E02.1080p.WEB.H264-GROUPNAME.mkv") == _item2

    def test_get_assert_raises_exception(self):
        _find_output = [self.TEMPLATE_SHOW.format("1", "100000", "S01E01"),
                        self.TEMPLATE_SHOW.format("2", "100000", "S01E02")]
        _list = FileList()
        _list.parse_find_cmd_output(_find_output, "server1")
        with pytest.raises(TypeError):
            _list.get(123.123)
