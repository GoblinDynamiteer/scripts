#!/usr/bin/env python3.8

"Unit tests"

import os
import platform
import string
import tempfile
import unittest
import config
from pathlib import Path

import db_json
import lister
import printing
import tvmaze
import util
import util_movie
import util_tv


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.cm = config.ConfigurationManager()
        self.cm.set_verbose(True)

    def test_custom_file(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True) as cf:
            val = "test_value_123"
            key = "test_key"
            lines = ["[default]\n", f"{key}={val}\n"]
            cf.writelines(lines)
            cf.flush()
            self.cm.set_config_file(Path(cf.name))
            self.assertEqual(val, self.cm.get(key))

    def test_default_value(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True) as cf:
            val = "test_value_123"
            key = "test_key"
            lines = ["[default]\n", f"{key}={val}\n"]
            cf.writelines(lines)
            cf.flush()
            self.cm.set_config_file(Path(cf.name))
            self.assertEqual(None, self.cm.get("none_existinging"))
            self.assertEqual("hello", self.cm.get(
                "none_existinging", default="hello"))

    def test_convert(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True) as cf:
            val = "123"
            key_int = "test_int"
            key_path = "test_path"
            lines = ["[default]\n",
                     f"{key_int}={val}\n"
                     f"{key_path}={cf.name}"]
            cf.writelines(lines)
            cf.flush()
            self.cm.set_config_file(Path(cf.name))
            self.assertEqual(123, self.cm.get(key_int, convert=int))
            self.assertEqual(Path(cf.name), self.cm.get(
                key_path, convert=Path))

    def tearDown(self):
        self.cm.set_default_config_file()
        self.cm.set_verbose(False)


class TestUtilMovie(unittest.TestCase):

    def test_is_movie(self):
        m = util_movie.is_movie
        self.assertEqual(m(
            'TvShow.S02.720p.HDTV.x264-SceneName'), False)
        self.assertEqual(m(
            'MovieName.2014.720p.BluRay.x264-aFP'), True)
        self.assertEqual(m(
            'MovieName.2160p.BluRay.x264-aFP'), True)


class TestUtilTv(unittest.TestCase):

    def test_season_episode_parser(self):
        m = util_tv.parse_season_episode
        self.assertEqual(m('TvShow.S02.720p.HDTV.x264-SceneName'), (2, None))
        self.assertEqual(m('TvShow.S32E12.720p.HDTV.x264-SceneName'), (32, 12))
        self.assertEqual(
            m('TvShow.E12.720p.HDTV.x264-SceneName'), (None, None))

    def test_parse_season(self):
        m = util_tv.parse_season
        self.assertEqual(m('TvShow.S02.720p.HDTV.x264-SceneName'), 2)
        self.assertEqual(m('TvShow.S32E12.720p.HDTV.x264-SceneName'), 32)
        self.assertEqual(
            m('TvShow.E12.720p.HDTV.x264-SceneName'), None)

    def test_is_episode(self):
        m = util_tv.is_episode
        self.assertEqual(m('TvShow.S02.720p.HDTV.x264-SceneName'), False)
        self.assertEqual(m('TvShow.S32E12.720p.HDTV.x264-SceneName'), True)
        self.assertEqual(
            m('TvShow.E12.720p.HDTV.x264-SceneName'), False)

    def test_is_season(self):
        m = util_tv.is_season
        self.assertEqual(m('TvShow.S02.720p.HDTV.x264-SceneName'), True)
        self.assertEqual(m('TvShow.S32E12.720p.HDTV.x264-SceneName'), False)
        self.assertEqual(
            m('TvShow.E12.720p.HDTV.x264-SceneName'), False)

    def test_season_num_to_str(self):
        m = util_tv.season_num_to_str
        self.assertEqual(m(1), 'S01')
        self.assertEqual(m(42, upper_case=False), 's42')
        self.assertEqual(m(300, upper_case=False), 's300')
        self.assertEqual(m("a"), '')
        self.assertEqual(m(-1), '')

    def test_episode_num_to_str(self):
        m = util_tv.episode_num_to_str
        self.assertEqual(m(1), 'E01')
        self.assertEqual(m(42, upper_case=False), 'e42')
        self.assertEqual(m(300, upper_case=False), 'e300')
        self.assertEqual(m("a"), '')
        self.assertEqual(m(-1), '')

    def test_season_episode_str_list(self):
        m = util_tv.season_episode_str_list
        ret_list = [f'S01E{e:02d}' for e in range(1, 11)]
        self.assertEqual(m(1, 1, 10), ret_list)
        self.assertEqual(m(1, 'a', 10), [])
        self.assertEqual(m('a', 33, 10), [])
        self.assertEqual(m(3, 33, 'a'), [])
        self.assertEqual(m(-2, -1, 2), [])
        ret_list = [f'S32E{e:02d}' for e in range(200, 4, -1)]
        self.assertEqual(m(32, 200, 5), ret_list)


class TestTvMaze(unittest.TestCase):

    def test_id_from_show_name(self):
        m = tvmaze.id_from_show_name
        self.assertEqual(m('Game of Thrones'), 82)
        self.assertEqual(m('westworld'), 1371)
        self.assertEqual(m('vi på saltkråkan'), 36783)
        self.assertEqual(m('purple tentacles evil comeback'), None)

    def test_show_search(self):
        m = tvmaze.show_search
        self.assertRaises(ValueError, m, '')
        self.assertRaises(TypeError, m, None)
        self.assertRaises(TypeError, m, 123)


class TestDb(unittest.TestCase):
    def setUp(self):
        self.file = "_testdb.json"
        self.db = db_json.JSONDatabase(self.file)
        self.db.set_valid_keys(['name', 'age', 'sex'])
        self.db.set_key_type('name', str)
        self.db.set_key_type('age', int)
        self.db.set_key_type('sex', str)

    def test_ok(self):
        self.assertTrue(self.db.insert({'name': 'Harold'}))
        self.assertFalse(self.db.insert({'name': 'Harold'}))
        self.assertTrue(self.db.update('Harold', 'age', 72))
        self.assertTrue(self.db.update('Harold', 'sex', 'male'))
        self.assertFalse(self.db.update('Harold', 'age', []))
        self.assertTrue(self.db.insert(
            {'name': 'Andrea', 'sex': 'female', 'age': 32}))
        self.assertFalse(self.db.insert(
            {'name': 'Leah', 'sex': 2, 'age': 32}))
        self.assertTrue(self.db.insert(
            {'name': 'Leah', 'sex': 'N/A', 'age': 32}))
        self.assertTrue('Harold' in self.db)
        self.assertFalse('Monica' in self.db)
        name_list = ['Harold', 'Andrea', 'Leah']
        for num, name in enumerate(self.db):
            self.assertTrue(name == name_list[num])
        self.assertEqual(self.db.find('age', 32), ['Andrea', 'Leah'])
        self.assertEqual(self.db.find_duplicates(
            'age'), {32: ['Andrea', 'Leah']})
        self.db.insert({'name': 'Boris', 'age': 72})
        self.assertEqual(self.db.find_duplicates(
            'age'), {32: ['Andrea', 'Leah'], 72: ['Harold', 'Boris']})

    def tearDown(self):
        try:
            os.remove(self.file)
        except FileNotFoundError:
            pass


class TestStrOut(unittest.TestCase):

    def test_to_color_str(self):
        self.assertEqual(printing.to_color_str("ToColor", "red"),
                         "\033[38;5;196mToColor\033[0m")


class TestUtilStr(unittest.TestCase):

    def test_remove_chars(self):
        self.assertEqual(
            "ab", util.remove_chars_from_string("abcd", ["c", "d"]))
        self.assertEqual(
            "WoodPecker", util.remove_chars_from_string("W,ood.Peck_er", string.punctuation))

    def test_string_similarity(self):
        self.assertEqual(util.check_string_similarity(
            "a.b", "a_b,", remove_chars=string.punctuation), 1.0)
        string_orig = "The.Good.the.Bad.and.the.Ugly.1966.iNTERNAL" \
                      ".1080p.EXTENDED.REMASTERED.BluRay.X264-CLASSiC"
        check1 = "The Good The Bad & The Ugly Bluray"
        check2 = "The Good The Weird and the Looney BLuray 1080p"
        ratio1 = util.check_string_similarity(
            string_orig, check1, remove_chars=string.punctuation)
        ratio2 = util.check_string_similarity(
            string_orig, check2, remove_chars=string.punctuation)
        self.assertGreater(ratio1, ratio2)


class TestUtilPaths(unittest.TestCase):
    def test_direname_of_file(self):
        if platform.system() == "Linux":
            path_to_file_str = "/home/user_name/folder_8271/filename.txt"
            correct_path = "/home/user_name/folder_8271"
        elif platform.system() == "Windows":
            path_to_file_str = "D:\\dirdir\\user_name\\folder_8271\\filename.txt"
            correct_path = "D:\\dirdir\\user_name\\folder_8271"
        else:
            return
        self.assertEqual(util.dirname_of_file(path_to_file_str), correct_path)
        self.assertEqual(util.dirname_of_file(
            Path(path_to_file_str)), correct_path)

    def test_filename_of_path(self):
        if platform.system() == "Linux":
            path_to_file_str = "/home/user_name/folder_8271/filename.txt"
            correct_path = "filename.txt"
        elif platform.system() == "Windows":
            path_to_file_str = "D:\\dirdir\\user_name\\folder_8271\\filename.txt"
            correct_path = "filename.txt"
        else:
            return
        self.assertEqual(util.filename_of_path(path_to_file_str), correct_path)
        self.assertEqual(util.filename_of_path(
            Path(path_to_file_str)), correct_path)

    def test_get_file_contents(self):
        contents = "HellOWWOOORLD12344$£@"
        fp = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        fp.write(contents)
        fp.close()
        self.assertEqual(util.get_file_contents(fp.name), [contents])
        self.assertEqual(util.get_file_contents(Path(fp.name)), [contents])
        os.remove(fp.name)


class TestLister(unittest.TestCase):
    def setUp(self):
        self.det_type = lister.determine_type
        self.type = lister.ListType

    def test_args_type_tv_season(self):
        arg = "tv better call saul s01".split(" ")
        self.assertEqual(self.det_type(arg), self.type.TVShowSeason)
        arg = "show firefly s01".split(" ")
        self.assertEqual(self.det_type(arg), self.type.TVShowSeason)
        arg = "show the walking dead s08".split(" ")
        self.assertEqual(self.det_type(arg), self.type.TVShowSeason)

    def test_args_type_movie(self):
        arg = "movie star wars return of the jedi".split(" ")
        self.assertEqual(self.det_type(arg), self.type.Movie)
        arg = "mov kill bill".split(" ")
        self.assertEqual(self.det_type(arg), self.type.Movie)
        arg = "film mad max fury road".split(" ")
        self.assertEqual(self.det_type(arg), self.type.Movie)

    def test_args_type_unknown(self):
        arg = "donald duck".split(" ")
        self.assertEqual(self.det_type(arg), self.type.Unknown)
        arg = []
        self.assertEqual(self.det_type(arg), self.type.Unknown)

    def test_obj_show(self):
        arg = "tv breaking bad s01e05".split(" ")
        lister_type = self.type.TVSHowEpisode
        obj = lister.ListerItemTVShow(arg, lister_type)
        self.assertEqual(obj.season, 1)
        self.assertEqual(obj.episode, 5)

        arg = "tv firefly s04".split(" ")  # wishful thinking...
        lister_type = self.type.TVShowSeason
        obj = lister.ListerItemTVShow(arg, lister_type)
        self.assertEqual(obj.season, 4)
        self.assertEqual(obj.episode, None)

        arg = "tv Game of Throned".split(" ")
        lister_type = self.type.TVShow
        obj = lister.ListerItemTVShow(arg, lister_type)
        self.assertEqual(obj.season, None)
        self.assertEqual(obj.episode, None)


if __name__ == '__main__':
    unittest.main()
