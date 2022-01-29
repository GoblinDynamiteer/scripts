from media.scan.scanner import MediaScanner
from db.db_mov import MovieDatabase
from media.util import MediaPaths
from media.movie import Movie
from media.imdb_id import IMDBId

from media.online_search import omdb


class MovieScanner(MediaScanner):
    def __init__(self, dont_update_database: bool = False):
        MediaScanner.__init__(self, dont_update_database)
        self.set_log_prefix("MOVIE_SCANNER")
        self._db: MovieDatabase = MovieDatabase()
        self._media_paths = MediaPaths()
        self._omdb = omdb.OMDb()

    def scan(self):
        for movie_dir in self._media_paths.movie_dirs():
            if movie_dir.name not in self._db:
                self._process_new_movie(Movie(movie_dir))

    def _process_new_movie(self, movie: Movie):
        if not movie.is_valid():
            self.warn_fs(f"w[{movie}] is not valid! Skipping...")
            return
        self.log_fs(f"processing new: i[{movie}]...")
        _id = IMDBId(movie.path)  # TODO: assert path is dir...
        if _id.valid():
            self.log_fs(f"searching using imdb: [{_id}]")
            result = self._omdb.movie_search(_id)
        else:
            self.log_fs(f"searching using data: [{movie.data}]")
            result = self._omdb.movie_search(movie.data)
        if result is None:
            return
        result.print()  # TODO: process result


def main():
    scanner = MovieScanner(dont_update_database=True)
    scanner.scan()


if __name__ == "__main__":
    main()
