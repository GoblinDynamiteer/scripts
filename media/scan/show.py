from media.scan.scanner import MediaScanner, ScanType
from db.db_tv import ShowDatabase, EpisodeDatabase
from media.util import MediaPaths
from media.show import Show
from media.episode import Episode
from media.imdb_id import IMDBId
from media.online_search import tvmaze
from utils.datetime_utils import now_timestamp
from printout import print_line


class ShowScanner(MediaScanner):
    def __init__(self, update_database: bool = False, verbose: bool = False):
        MediaScanner.__init__(self, update_database, verbose=verbose)
        self.set_log_prefix("SHOW_SCANNER")
        self._db_show: ShowDatabase = ShowDatabase()
        self._db_ep: EpisodeDatabase = EpisodeDatabase()
        self._media_paths = MediaPaths()

    def scan(self) -> int:
        _count = 0
        for show_dir in self._media_paths.show_dirs():
            if self.should_skip_dir(show_dir):
                continue
            if show_dir.name not in self._db_show:
                self._process_new_show(Show(show_dir))
        for episode_file in self._media_paths.episode_files():
            if episode_file.name not in self._db_ep:
                self._process_new_episode(Episode(episode_file))
                _count += 1
        return _count

    @property
    def _tv_maze(self) -> tvmaze.TvMaze:
        return self.online_search_tool(ScanType.TvShow)

    def _process_new_show(self, show: Show):
        if not show.is_valid():
            self.warn_fs(f"w[{str(show)}] is not valid! Skipping...")
            return
        self.log_fs(f"processing new show: i[{show.name}]...", force=True)
        _id = IMDBId(show.path)  # TODO: or tvmaze_id
        if _id.valid():
            self.log_fs(f"searching using imdb: o[{_id}]")
            result = self._tv_maze.show_search(_id)
        else:
            self.log_fs(f"searching using data: o[{show.data}]")
            result = self._tv_maze.show_search(show.data)
        if result and result.valid:
            self.log(f"got: {result}")
        self._add_show_to_db(show, result)

    def _process_new_episode(self, episode: Episode):
        if not episode.is_valid():
            self.warn_fs(f"w[{episode.name}] is not valid! Skipping...")
            return
        self.log_fs(f"processing new episode: i[{episode.name}]...", force=True)
        _id = IMDBId(episode.show_path)  # TODO: or tvmaze_id
        if _id.valid():
            self.log_fs(f"searching using imdb: o[{_id}]")
            result = self._tv_maze.episode_search(_id,
                                                  episode_num=episode.episode_num,
                                                  season_num=episode.season_num)
        else:
            self.log_fs(f"searching using data: o[{episode.data}]")
            result = self._tv_maze.episode_search(episode.data)
        if result and result.valid:
            self.log(f"got: {result}")
        self._add_episode_to_db(episode, result)

    def _add_episode_to_db(self, ep: Episode, search_result: tvmaze.TvMazeEpisodeSearchResult):
        _db_entry = {
            "tvshow": ep.show_name,
            "filename": ep.name,
            "scanned": now_timestamp(),
            "season_number": ep.season_num,
            "episode_number": ep.episode_num,
            "removed": False,
        }
        if search_result.valid:
            if search_result.id is not None:
                _db_entry["tvmaze"] = int(search_result.id)
            if search_result.title is not None:
                _db_entry["title"] = search_result.title
            if search_result.aired_timestamp is not None:
                _db_entry["released"] = search_result.aired_timestamp
        if self._update_db:
            self._db_ep.add(**_db_entry)
        else:
            self.log("not adding to database...")
            self.log_fs(f"data: i[{_db_entry}]")
        print_line()

    def _add_show_to_db(self, show: Show, search_result: tvmaze.TvMazeShowSearchResult):
        _db_entry = {
            "folder": show.name,
            "scanned": now_timestamp(),
            "removed": False,
        }
        if search_result.valid:
            if search_result.id is not None:
                _db_entry["tvmaze"] = int(search_result.id)
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
