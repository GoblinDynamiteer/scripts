from media.online_search.omdb import OMDbMovieSearchResult


class TestOMDbMovieSearchResult:
    RESULT_MATRIX = {"Title": "Matrix", "Year": "1993", "Rated": "N/A", "Released": "01 Mar 1993", "Runtime": "60 min",
                     "Genre": "Action, Drama, Fantasy", "Director": "N/A", "Writer": "Grenville Case",
                     "Actors": "Nick Mancuso, Phillip Jarrett, Carrie-Anne Moss",
                     "Plot": "Steven Matrix is one of the underworld's foremost hitmen until his luck runs out, and someone puts a contract out on him. Shot in the forehead by a .22 pistol, Matrix \"dies\" and finds himself in \"The City In Between\", where he is ...",
                     "Language": "English", "Country": "Canada", "Awards": "1 win",
                     "Poster": "https://m.media-amazon.com/images/M/MV5BYzUzOTA5ZTMtMTdlZS00MmQ5LWFmNjEtMjE5MTczN2RjNjE3XkEyXkFqcGdeQXVyNTc2ODIyMzY@._V1_SX300.jpg",
                     "Ratings": [{"Source": "Internet Movie Database", "Value": "7.7/10"}], "Metascore": "N/A",
                     "imdbRating": "7.7", "imdbVotes": "187", "imdbID": "tt0106062", "Type": "series",
                     "totalSeasons": "N/A", "Response": "True"}
    RESULT_EMPTY = {}

    def test_year_1993_converts_to_int(self):
        result = OMDbMovieSearchResult(self.RESULT_MATRIX)
        assert result.year == 1993

    def test_year_key_missing_converts_to_none(self):
        _res = self.RESULT_MATRIX.copy()
        del _res["Year"]
        result = OMDbMovieSearchResult(_res)
        assert result.year is None

    def test_year_invalid_converts_to_none(self):
        _res = self.RESULT_MATRIX.copy()
        _res["Year"] = "1923X"
        result = OMDbMovieSearchResult(_res)
        assert result.year is None
