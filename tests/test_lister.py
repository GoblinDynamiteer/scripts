
from lister import determine_type, ListType, ListerItemTVShow


class TestLister:

    def test_args_type_tv_season(self):
        arg = "tv better call saul s01".split(" ")
        assert determine_type(arg) == ListType.TVShowSeason
        arg = "show firefly s01".split(" ")
        assert determine_type(arg) == ListType.TVShowSeason
        arg = "show the walking dead s08".split(" ")
        assert determine_type(arg) == ListType.TVShowSeason

    def test_args_type_movie(self):
        arg = "movie star wars return of the jedi".split(" ")
        assert determine_type(arg) == ListType.Movie
        arg = "mov kill bill".split(" ")
        assert determine_type(arg) == ListType.Movie
        arg = "film mad max fury road".split(" ")
        assert determine_type(arg) == ListType.Movie

    def test_args_type_unknown(self):
        arg = "donald duck".split(" ")
        assert determine_type(arg) == ListType.Unknown
        arg = []
        assert determine_type(arg) == ListType.Unknown

    def test_obj_show(self, mocker):
        _mock = mocker.patch("lister.ListerItemTVShow.determine_paths", return_value=[])
        arg = "tv breaking bad s01e05".split(" ")
        obj = ListerItemTVShow(arg, ListType.TVSHowEpisode)
        assert obj.season == 1
        assert obj.episode == 5

        arg = "tv firefly s04".split(" ")  # wishful thinking...
        obj = ListerItemTVShow(arg, ListType.TVShowSeason)
        assert obj.season == 4
        assert obj.episode is None

        arg = "tv Game of Throned".split(" ")
        obj = ListerItemTVShow(arg, ListType.TVShowSeason)
        assert obj.season is None
        assert obj.episode is None

        assert _mock.call_count == 3
