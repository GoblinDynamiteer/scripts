import unittest

import util_movie


class TestUtilMovie(unittest.TestCase):

    def test_is_movie(self):
        m = util_movie.is_movie
        self.assertEqual(m(
            'TvShow.S02.720p.HDTV.x264-SceneName'), False)
        self.assertEqual(m(
            'MovieName.2014.720p.BluRay.x264-aFP'), True)
        self.assertEqual(m(
            'MovieName.2160p.BluRay.x264-aFP'), True)