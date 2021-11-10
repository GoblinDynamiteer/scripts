import unittest

import lister


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