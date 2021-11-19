#!/usr/bin/env python3

"""list various things"""

import argparse
import re
import operator
from enum import Enum
from pathlib import Path

from config import ConfigurationManager as cfg
from util_tv import parse_season_episode, parse_season
from printout import pfcs, cstr, print_line, Color, fcs
from util import date_str_to_timestamp, now_timestamp
from tvmaze import TvMazeData
from util_movie import valid_letters as mov_letters, get_movie_nfo_imdb_id
from omdb import OMDb


class RegexStr(Enum):
    SeasonEpiosde = r"[Ss]\d{2}[Ee]\d{2}"
    Season = r"[Ss]\d{2}"


class ListType(Enum):
    Unknown = 0
    Movie = 1
    TVShow = 2
    TVShowSeason = 3
    TVSHowEpisode = 4


class SubtitleLang(Enum):
    English = "en"
    Swedish = "sv"
    Unknown = "unkown"


class ListerItemTVMissingShowEpisode:
    def __init__(self, show_name, tvmaze_data):
        self.data = tvmaze_data
        self.season = tvmaze_data.get("season", 0)
        self.episode = tvmaze_data.get("number", 0)
        se_str = f"S{self.season:02d}E{self.episode:02d}"
        self.name = f"{show_name.replace(' ', '.')}.{se_str}"
        self.row_len = len(self.name)

    def show_list(self, one_line: bool = False):
        _missing_str = fcs(f"  o[{self.name} >> MISSING <<]")
        if not one_line:
            _missing_str += "\n     "
        id_str = "id: " + cstr(f"{self.data.get('id', 0)}", Color.LightBlue)
        aired_str = "aired: " + cstr(self.data.get("airdate"), Color.LightBlue)
        name_str = "\"" + cstr(self.data.get("name"), Color.LightBlue) + "\""
        print(f"{_missing_str} {name_str} {id_str} {aired_str}")


class ListerItemTVShowEpisode:
    def __init__(self, path, show_extras=False):
        self.show_name = path.parents[1].name
        self.path = path
        self.filename = path.name
        self.extras = show_extras
        self.season, self.episode = parse_season_episode(path.name)
        self.subs = self.determine_subs()
        self.row_len = len(self.filename)

    def show_list(self, one_line: bool = False):
        se_str = f"S{self.season:02d}E{self.episode:02d}"
        subs_str = "subs: "
        for sub in SubtitleLang:
            has = sub in self.subs
            if sub == SubtitleLang.Unknown:
                if has:
                    subs_str += cstr(sub.value + " ", Color.LightYellow)
                continue
            subs_str += cstr(sub.value + " ",
                             Color.LightGreen if has else Color.DarkGrey)
        _output = fcs(f"  i[{self.filename: <{self.row_len}}]")
        if not one_line:
            _output += "\n     "
        _output += fcs(f" b[{se_str}] {subs_str}")
        print(_output, end=" " if one_line and self.extras else "\n")
        if self.extras:
            self.print_extras(only_airdate=one_line)

    def determine_subs(self):
        path_en_srt = self.path.with_suffix(".en.srt")
        path_sv_srt = self.path.with_suffix(".sv.srt")
        path_unknown_srt = self.path.with_suffix(".srt")
        subs = []
        if path_en_srt.is_file():
            subs.append(SubtitleLang.English)
        if path_sv_srt.is_file():
            subs.append(SubtitleLang.Swedish)
        if path_unknown_srt.is_file():
            subs.append(SubtitleLang.Unknown)
        return subs

    def print_extras(self, only_airdate: bool = False):
        from db.db_tv import EpisodeDatabaseSingleton, ShowDatabaseSingleton
        maze_id = EpisodeDatabaseSingleton().get_id(self.filename)
        show_maze_id = ShowDatabaseSingleton().get_id(self.show_name)
        ep_maze_data = {}
        for entry in TvMazeData().get_json_all_episodes(show_maze_id):
            if entry.get("season", 0) == self.season and entry.get("number", 0) == self.episode:
                ep_maze_data = entry
                break
        aired_str = "aired: " + cstr(ep_maze_data.get("airdate"), Color.LightBlue)
        if only_airdate:
            print(aired_str)
            return
        id_str = "id: " + cstr(f"{maze_id}",
                               Color.LightBlue) if maze_id is not None else ""
        name_str = "\"" + cstr(ep_maze_data.get("name"), Color.LightBlue) + "\""
        print(f"      {name_str} {id_str} {aired_str}")


class ListerItemTVShowSeason:
    def __init__(self, path, episode_num, show_extras=False):
        self.season_num = parse_season(path.name)
        self.path = path
        self.episode = episode_num
        self.extras = show_extras
        self.show_name = path.parents[0].name
        self.episode_list = self.init_episode_list()

    def init_episode_list(self):
        ep_list = []
        for sub_path in self.path.iterdir():
            if sub_path.is_dir():
                continue  # should not be present, but just in case
            if sub_path.suffix in [".mkv", ".mp4", ".flv"]:  # TODO all relevant exts?
                if self.episode:
                    if f"E{self.episode:02d}" in sub_path.name.upper():
                        ep_list.append(ListerItemTVShowEpisode(
                            sub_path, self.extras))
                else:
                    ep_list.append(ListerItemTVShowEpisode(
                        sub_path, self.extras))
        if self.extras and not self.episode:
            from db.db_tv import EpisodeDatabaseSingleton, ShowDatabaseSingleton
            existing_nums = sorted([en.episode for en in ep_list])
            show_maze_id = ShowDatabaseSingleton().get_id(self.show_name)
            for entry in TvMazeData().get_json_all_episodes(show_maze_id):
                if entry.get("season", 0) != self.season_num:
                    continue
                if entry.get("number", 0) not in existing_nums:
                    timestamp = date_str_to_timestamp(
                        entry["airdate"], r'%Y-%m-%d')
                    has_aired = timestamp < now_timestamp()
                    if has_aired:
                        ep_list.append(ListerItemTVMissingShowEpisode(
                            self.show_name, entry))
        max_len = 0
        for ep in ep_list:
            max_len = max(max_len, ep.row_len)
        for ep in ep_list:
            ep.row_len = max_len
        return ep_list

    def show_list(self, one_line: bool = False):
        print(f" {self.path.name}")
        for ep in sorted(self.episode_list,
                         key=operator.attrgetter("episode")):
            ep.show_list(one_line=one_line)


class ListerItemTVShow:
    def __init__(self, args: list, list_type: ListType, show_extras=False):
        self.show_path = None
        self.type = list_type
        self.extras = show_extras
        if list_type == ListType.TVShow:
            self.args = args
            self.season = None
            self.episode = None
        else:
            self.args = args[:-1]
            self.season, self.episode = parse_season_episode(args[-1])
        self.paths = self.determine_paths()
        self.season_lists = self.init_season_lists()

    def init_season_lists(self):
        season_lists = []
        for path in self.paths:
            for sub_path in path.iterdir():
                if not sub_path.is_dir():
                    continue
                if self.season:
                    if f"S{self.season:02d}" == sub_path.name.upper():
                        season_lists.append(
                            ListerItemTVShowSeason(sub_path, self.episode, self.extras))
                else:
                    season_lists.append(
                        ListerItemTVShowSeason(sub_path, self.episode, self.extras))
        return season_lists

    def determine_paths(self):
        tv_path = Path(cfg().path("tv"))
        matches = []
        for sub_path in tv_path.iterdir():
            if not sub_path.is_dir():
                continue
            path_parts = sub_path.name.lower().split(" ")
            if all([x.lower() in path_parts for x in self.args]):
                matches.append(sub_path)
        return matches

    def show_list(self, one_line: bool = False):
        for season in sorted(self.season_lists, key=operator.attrgetter("season_num")):
            season.show_list(one_line=one_line)


class ListerItemMovie:
    def __init__(self, path: Path):
        self._path = path
        self._imdb_id = self._get_imdbid()
        self._omdb_result = OMDb().movie_search(imdb_id=self._imdb_id)

    def _get_imdbid(self):
        _id = get_movie_nfo_imdb_id(self._path.name)
        return _id

    def _print_data(self, title_str, data):
        if not data:
            return
        print(cstr(f" {title_str}:".ljust(10, " "), Color.DarkGrey), data)

    def print(self):
        _path_str = cstr(str(self._path.parent.resolve()), Color.Grey)
        _name_str = cstr(self._path.name, Color.LightGreen)
        print(f"{_path_str}/{_name_str}")
        if self._omdb_result.valid:
            self._print_data("title", self._omdb_result.title)
            self._print_data("year", self._omdb_result.year)
            self._print_data("genre", self._omdb_result.genre)
        print_line()


class ListerItemMovieDir:
    def __init__(self, args: list, show_extras=False):
        self._args = args
        self._show_extras = show_extras
        self._filter = None
        self._letter = self._determine_letter()
        self._path_list = self.determine_paths()

    def _determine_letter(self):
        try:
            if self._args[0].upper() in mov_letters():
                if len(self._args) > 1:
                    self._filter = self._args[1:]
                return self._args[0].upper()
        except IndexError:
            return None
        if self._args:
            self._filter = self._args
        return None

    def determine_paths(self):
        mov_path = Path(cfg().path("film"))
        if self._letter:
            paths = [mov_path / self._letter]
        else:
            paths = mov_path.iterdir()
        matches = []
        for path in paths:
            if path.is_file():
                continue
            for sub_path in path.iterdir():
                if not sub_path.is_dir():
                    continue
                path_parts = sub_path.name.lower().split(".")
                if self._filter:
                    if all([x.lower() in path_parts for x in self._filter]):
                        matches.append(sub_path)
                else:
                    matches.append(sub_path)
        return matches

    def show_list(self):
        for path in self._path_list:
            mov = ListerItemMovie(path)
            mov.print()


def re_list(re_str: RegexStr, str_list: list):
    matches = [re.search(re_str.value, x) for x in str_list]
    if not any(matches):
        return []
    return matches


def determine_type(arguments: list):
    if not arguments:
        return ListType.Unknown
    if arguments[0].lower() in ["tv", "show"]:
        if re_list(RegexStr.SeasonEpiosde, arguments):
            return ListType.TVSHowEpisode
        if re_list(RegexStr.Season, arguments):
            return ListType.TVShowSeason
        return ListType.TVShow
    elif arguments[0].lower() in ["mov", "movie", "film"]:
        return ListType.Movie
    return ListType.Unknown


def main():
    parser = argparse.ArgumentParser(description="Multi-purpose lister")
    parser.add_argument("keywords",
                        metavar="N",
                        type=str,
                        nargs="+")
    parser.add_argument("--extras",
                        "-e",
                        action="store_true",
                        help="show extra info",
                        dest="show_extras")
    parser.add_argument("--oneline",
                        "-o",
                        action="store_true",
                        dest="one_line")
    args = parser.parse_args()

    args_type = determine_type(args.keywords)
    if args_type == ListType.Unknown:
        return
    if args_type in [ListType.TVShow, ListType.TVShowSeason, ListType.TVSHowEpisode]:
        lister_show = ListerItemTVShow(
            args.keywords[1:], args_type, args.show_extras)
        lister_show.show_list(one_line=args.one_line)
    elif args_type == ListType.Movie:
        lister_mov = ListerItemMovieDir(args.keywords[1:], args.show_extras)
        lister_mov.show_list()


if __name__ == "__main__":
    main()
