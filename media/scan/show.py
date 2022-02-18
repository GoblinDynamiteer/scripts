from media.scan.scanner import MediaScanner
from db.db_tv import ShowDatabase, EpisodeDatabase
from media.util import MediaPaths
from media.show import Show
from media.imdb_id import IMDBId
from media.online_search import tvmaze
from utils.datetime_utils import now_timestamp
from printout import print_line


class ShowScanner(MediaScanner):
    def __init__(self, update_database: bool = False):
        MediaScanner.__init__(self, update_database)
        self.set_log_prefix("SHOW_SCANNER")
        self._db_show: ShowDatabase = ShowDatabase()
        self._db_ep: EpisodeDatabase = EpisodeDatabase()
        self._media_paths = MediaPaths()
        self._tv_maze = tvmaze.TvMaze(verbose=True)

    def scan(self):
        for show_dir in self._media_paths.show_dirs():
            if show_dir.name not in self._db_show:
                self._process_new_show(Show(show_dir))

    def _process_new_show(self, show: Show):
        if not show.is_valid():
            self.warn_fs(f"w[{show.name}] is not valid! Skipping...")
            return
        self.log_fs(f"processing new: i[{show.name}]...")
        _id = IMDBId(show.path)  # TODO: or tvmaze_id
        if _id.valid():
            self.log_fs(f"searching using imdb: o[{_id}]")
            result = self._tv_maze.show_search(_id)
        else:
            self.log_fs(f"searching using data: o[{show.data}]")
            result = self._tv_maze.show_search(show.data)
        self._add_show_to_db(show, result)

    def _add_show_to_db(self, show: Show, search_result: tvmaze.TvMazeShowSearchResult):
        _db_entry = {
            "folder": show.name,
            "scanned": now_timestamp(),
        }
        if search_result.valid:
            if search_result.id is not None:
                _db_entry["tvmaze"] = search_result.id
            if search_result.title is not None:
                _db_entry["title"] = search_result.title
            if search_result.year is not None:
                _db_entry["year"] = search_result.year
        if self._update_db:
            self._db_show.add(**_db_entry)
        else:
            self.log("not adding to database...")
            self.log_fs(f"data: i[{_db_entry}]")
        print_line()


def main():
    scanner = ShowScanner(update_database=False)
    scanner.scan()


if __name__ == "__main__":
    main()