from wb_new import *

from config import ConfigurationManager

from pytest import fixture


@fixture(scope="session", autouse=True)
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
                r"/home/jk/files/SE.SUBPACKS.02.03.2012-Collection/" \
                r"Cool.Movie.2004.NORDiC.SUBPACK.x264-Grp/cmv.x264-grp.rar"
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