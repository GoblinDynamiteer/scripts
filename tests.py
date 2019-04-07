#!/usr/bin/env python3.6

''' Subtitle tools '''

import unittest
import util_movie
import util_tv
import printing


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


class TestStrOut(unittest.TestCase):

    def to_color_str(self):
        self.assertEqual(printing.to_color_str("ToColor", "red"),
                         "\033[38;5;196mToColor\033[0m")


if __name__ == '__main__':
    unittest.main()
