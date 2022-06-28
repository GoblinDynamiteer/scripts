from media.scan.scanner import MediaScanner
from db.db_mov import MovieDatabase
from media.util import MediaPaths
from media.movie import Movie
from media.imdb_id import IMDBId
from media.online_search import omdb
from utils.datetime_utils import now_timestamp
from printout import print_line


class MovieScanner(MediaScanner):
    def __init__(self, update_database: bool = False, verbose: bool = False):
        MediaScanner.__init__(self, update_database, verbose=verbose)
        self.set_log_prefix("MOVIE_SCANNER")
        self._db: MovieDatabase = MovieDatabase()
        self._media_paths = MediaPaths()
        self._omdb = omdb.OMDb(verbose=verbose)

    def scan(self) -> int:
        _count = 0
        for movie_dir in self._media_paths.movie_dirs():
            if movie_dir.name not in self._db:
                self._process_new_movie(Movie(movie_dir))
                _count += 1
        return _count

    def _process_new_movie(self, movie: Movie):
        if not movie.is_valid():
            self.warn_fs(f"w[{movie}] is not valid! Skipping...")
            return
        self.log_fs(f"processing new: i[{movie}]...", force=True)
        _id = IMDBId(movie.path)  # TODO: assert path is dir...
        if _id.valid():
            self.log_fs(f"searching using imdb: o[{_id}]")
            result = self._omdb.movie_search(_id)
        else:
            self.log_fs(f"searching using data: o[{movie.data}]")
            result = self._omdb.movie_search(movie.data)
        self._add_to_db(movie, result)

    def _add_to_db(self, movie: Movie, search_result: omdb.OMDbMovieSearchResult):
        _db_entry = {
            "folder": movie.name,
            "scanned": now_timestamp(),
        }
        if search_result.valid:
            if search_result.id is not None:
                _db_entry["imdb"] = str(search_result.id)
            if search_result.title is not None:
                _db_entry["title"] = search_result.title
            if search_result.year is not None:
                _db_entry["year"] = search_result.year
        if self._update_db:
            self._db.add(**_db_entry)
        else:
            self.log("not adding to database...")
            self.log_fs(f"data: i[{_db_entry}]")
        print_line()


def main():
    scanner = MovieScanner(update_database=False)
    scanner.scan()


if __name__ == "__main__":
    main()
