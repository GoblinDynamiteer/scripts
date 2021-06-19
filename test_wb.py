from wb_new import *

from config import ConfigurationManager


class TestFileListItem:
    def test_is_x(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.is_file is False
        assert fi.is_dir is True
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.is_file is True
        assert fi.is_dir is False

    def test_parent(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.parent() == Path("/home/user/files/")
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.parent() == Path("/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/")

    def test_is_parent_of(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi_parent = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar"
        fi_child = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi_parent.is_parent_of(fi_child) is True

    def test_is_top_level(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[wb]", "username=donald"]))
        ConfigurationManager().set_config_file(_file)
        _find_str = "/home/donald/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.is_top_level() is True

    def test_assert_top_dir_is_invalid(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[wb]", "username=ronald"]))
        ConfigurationManager().set_config_file(_file)
        _find_str = "/home/ronald/files/"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.valid is False

    def test_valid_file(self):
        _find_str = "/home/donald/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.valid is True
        _find_str = "/home/donald/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.nfo"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.valid is False

    def test_string_scrubbing(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar\n "
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.valid is True
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.r00\n "
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.valid is False

    def test_parent_invalid(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/Sample/sample.mkv"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.valid is False

    def test_is_relative_of(self):
        _base_str = "/home/user/files/Some.Kind.of.Show.S02.1080p.WEB.h264-COOLGRP/"
        fi_base = FileListItem(_base_str, item_type=FileListItem.ItemType.Dir)
        _sub_dir_str = _base_str + "Some.Kind.of.Show.S02E01.1080p.WEB.h264-COOLGRP/"
        fi_sub_dir = FileListItem(_sub_dir_str, item_type=FileListItem.ItemType.Dir)
        _file_str = _sub_dir_str + "skoss02e01-clgrp.rar"
        fi_file = FileListItem(_file_str, item_type=FileListItem.ItemType.File)
        assert fi_sub_dir.is_parent_of(fi_file)
        assert fi_base.is_relative_of(fi_file)

    def test_str_remove_prefix(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[wb]", "username=donald"]))
        ConfigurationManager().set_config_file(_file)
        _find_str = "/home/donald/files/Some.Kind.of.Show.S02.1080p.WEB.h264-COOLGRP/"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert str(fi) == "Some.Kind.of.Show.S02.1080p.WEB.h264-COOLGRP/"

    def test_valid_dir(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.valid is True
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/Sample"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.valid is False

    def test_is_video(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.mkv"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.is_video is True
        assert fi.is_rar is False
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert fi.is_video is False

    def test_is_rar(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        assert fi.is_rar is True
        assert fi.is_video is False
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        assert  fi.is_rar is False

    def test_contains_videos(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi_parent = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.mkv"
        fi_sub = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        fi_parent.add_sub_item(fi_sub)
        assert fi_parent.contains_videos()

    def test_index(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        fi.index = 123
        assert fi.index == 123

    def test_sub_items(self):
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP"
        fi_parent = FileListItem(_find_str, item_type=FileListItem.ItemType.Dir)
        _find_str = "/home/user/files/Some.Kind.of.Movie.2021.1080p.WEB.h264-COOLGRP/smkm-clgrp.rar"
        fi_sub = FileListItem(_find_str, item_type=FileListItem.ItemType.File)
        fi_parent.add_sub_item(fi_sub)
        _sub = list(fi_parent.sub_items())
        assert len(_sub) == 1
        assert _sub[0] is fi_sub