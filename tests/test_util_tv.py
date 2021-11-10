import unittest

import util_tv


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