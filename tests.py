#!/usr/bin/env python3

''' Subtitle tools '''

import unittest

import db_json
import printing
import tvmaze
import util_movie
import util_tv
import os


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

    def tearDown(self):
        try:
            os.remove(self.file)
        except FileNotFoundError:
            pass


class TestStrOut(unittest.TestCase):

    def to_color_str(self):
        self.assertEqual(printing.to_color_str("ToColor", "red"),
                         "\033[38;5;196mToColor\033[0m")


if __name__ == '__main__':
    unittest.main()
