#!/usr/bin/env python3.8

"""list various things"""

import argparse
import re
import operator
from enum import Enum
from pathlib import Path

from config import ConfigurationManager as cfg
from util_tv import parse_season_episode, parse_season
from printing import pfcs, cstr
from db_tv import EpisodeDatabase
from util import Singleton


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


class EpDbSingleton(metaclass=Singleton):
    ep_db = EpisodeDatabase()

    def get_id(self, filename: str) -> int:
        return self.ep_db.get(filename, "tvmaze")


class ListerItemTVShowEpisode():
    def __init__(self, path, show_extras=False):
        self.path = path
        self.filename = path.name
        self.extras = show_extras
        self.season, self.episode = parse_season_episode(path.name)
        self.subs = self.determine_subs()
        self.row_len = len(self.filename)

    def show_list(self):
        se_str = f"S{self.season:02d}E{self.episode:02d}"
        subs_str = "subs: "
        for sub in SubtitleLang:
            has = sub in self.subs
            if sub == SubtitleLang.Unknown:
                if has:
                    subs_str += cstr(sub.value + " ", "lyellow")
                continue
            subs_str += cstr(sub.value + " ",
                             "lgreen" if has else "dgrey")
        pfcs(
            f"  i[{self.filename: <{self.row_len}}] b[{se_str}] {subs_str}")
        if self.extras:
            self.print_extras()

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

    def print_extras(self):
        maze_id = EpDbSingleton().get_id(self.filename)
        id_str = "id: " + cstr(f"{maze_id}",
                               "lblue") if maze_id is not None else ""
        print("   " + id_str)


class ListerItemTVShowSeason():
    def __init__(self, path, episode_num, show_extras=False):
        self.season_num = parse_season(path.name)
        self.path = path
        self.episode = episode_num
        self.extras = show_extras
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
        max_len = 0
        for ep in ep_list:
            max_len = max(max_len, ep.row_len)
        for ep in ep_list:
            ep.row_len = max_len
        return ep_list

    def show_list(self):
        print(f" {self.path.name}")
        for ep in sorted(self.episode_list,
                         key=operator.attrgetter("episode")):
            ep.show_list()


class ListerItemTVShow():
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

    def show_list(self):
        for season in sorted(self.season_lists, key=operator.attrgetter("season_num")):
            season.show_list()


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
    parser = argparse.ArgumentParser(description="Multipurpouse lister")
    parser.add_argument("keywords",
                        metavar="N",
                        type=str,
                        nargs="+")
    parser.add_argument("--extras",
                        "-e",
                        action="store_true",
                        help="show extra info",
                        dest="show_extras")
    args = parser.parse_args()

    args_type = determine_type(args.keywords)
    if args_type == ListType.Unknown:
        return
    if args_type in [ListType.TVShow, ListType.TVShowSeason, ListType.TVSHowEpisode]:
        lister_show = ListerItemTVShow(
            args.keywords[1:], args_type, args.show_extras)
        lister_show.show_list()


if __name__ == "__main__":
    main()
