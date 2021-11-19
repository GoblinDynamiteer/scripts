#!/usr/bin/env python3

import argparse
from datetime import datetime

from db_json import JSONDatabase
import util
import util_movie
from config import ConfigurationManager
from printout import pfcs, Color, cstr

from singleton import Singleton


def _to_text(movie_folder, movie_data, use_removed_date=False):
    if use_removed_date:
        date = datetime.fromtimestamp(
            movie_data["removed_date"]).strftime("%Y-%m-%d")
    else:
        date = datetime.fromtimestamp(
            movie_data["scanned"]).strftime("%Y-%m-%d")
    year = title = ""
    if "year" in movie_data:
        year = movie_data["year"]
    if "title" in movie_data:
        title = movie_data["title"]
    ret_str = f"[{date}] [{movie_folder}]"
    if year:
        ret_str += f" [{year}]"
    if title:
        ret_str += f" [{title}]"
    return ret_str + "\n"


class MovieDatabase(JSONDatabase):
    def __init__(self):
        JSONDatabase.__init__(self, ConfigurationManager().path("movdb", assert_path_exists=True))
        self.set_valid_keys(
            ["folder", "title", "year", "imdb", "scanned", "removed", "removed_date"])
        self.set_key_type("folder", str)
        self.set_key_type("title", str)
        self.set_key_type("year", int)
        self.set_key_type("imdb", str)
        self.set_key_type("scanned", int)  # unix timestamp
        self.set_key_type("removed", bool)
        self.set_key_type("removed_date", int)

    def last_added(self, num=10):
        sorted_dict = self.sorted("scanned", reversed_sort=True)
        count = 0
        last_added_dict = {}
        for folder, data in sorted_dict.items():
            last_added_dict[folder] = data
            count += 1
            if count == num:
                return last_added_dict
        return last_added_dict

    def last_removed(self, num=10):
        sorted_dict = self.sorted("removed_date", reversed_sort=True)
        count = 0
        last_removed_dict = {}
        for folder, data in sorted_dict.items():
            last_removed_dict[folder] = data
            count += 1
            if count == num:
                return last_removed_dict
        return last_removed_dict

    def mark_removed(self, folder):
        try:
            self.update(folder, "removed", True)
            self.update(folder, "removed_date", util.now_timestamp())
            print(f"marked {cstr(folder, Color.Orange)} as removed")
        except Exception as _:
            pass

    def is_removed(self, folder):
        if folder in self.json:
            return self.json[folder].get("removed", False)
        return False

    def export_latest_added(self):
        _path = ConfigurationManager().path("film",
                                            convert_to_path=True,
                                            assert_path_exists=True)
        if _path is None:
            print(cstr("could not retrieve path to \"film\"", Color.Error))
            return
        _path = _path / "latest.txt"
        last_added = self.last_added(num=1000)
        last_added_text = [_to_text(m, last_added[m]) for m in last_added]
        try:
            with open(_path, "w") as _fp:
                _fp.writelines(last_added_text)
            print(f"wrote to {cstr(str(_path), Color.LightGreen)}")
        except Exception as _:
            print(cstr("could not save latest.txt", Color.Error))

    def export_last_removed(self):
        _path = ConfigurationManager().path("film",
                                            convert_to_path=True,
                                            assert_path_exists=True)
        if _path is None:
            print(cstr("could not retrieve path to \"film\"", Color.Error))
            return
        _path = _path / "removed.txt"
        last_removed = self.last_removed(num=1000)
        last_removed_text = [_to_text(m, last_removed[m], use_removed_date=True)
                             for m in last_removed]
        try:
            with open(_path, "w") as last_added_file:
                last_added_file.writelines(last_removed_text)
            print(f"wrote to {cstr(str(_path), Color.LightGreen)}")
        except Exception as _:
            print(cstr("could not save removed.txt", Color.Error))

    def all_movies(self):
        for item in self.all():
            if not self.json.get("removed", False):
                yield item


class MovieDatabaseSingleton(metaclass=Singleton):
    _db = MovieDatabase()

    def db(self):
        return self._db


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setimdb",
                        "-i",
                        type=str)
    parser.add_argument("--rescan",
                        "-r",
                        action="store_true")
    _grp = parser.add_mutually_exclusive_group()
    _grp.add_argument("--gen-latest-added",
                      "-g",
                      action="store_true",
                      dest="gen_latest")
    _grp.add_argument("--movie",
                      type=str,
                      required=False,
                      default=None)
    return parser.parse_args()


def main():
    args = get_args()
    database = MovieDatabase()
    if args.gen_latest:
        database.export_latest_added()
        return
    if args.movie is None:
        for _mov in database.all_movies():
            print(_mov)
        return
    if args.movie not in database:
        pfcs(f"w[{args.movie}] not in movie database")
        return
    if database.is_removed(args.movie):
        pfcs(f"w[{args.movie}] is marked removed, not processing")
        return
    pfcs(f"processing g[{args.movie}]")
    if args.setimdb:
        if not util_movie.exists(args.movie):
            pfcs(f"could not find w[{args.movie}] on disk!")
            return
        util_movie.create_movie_nfo(
            args.movie, args.setimdb, debug_print=True)
    need_save = False
    if args.rescan:
        from scan import process_new_movie  # prevents circular import...
        pfcs(f"rescanning omdb-data for g[{args.movie}]")
        scan_result_data = process_new_movie(args.movie)
        for key in ["title", "year", "imdb"]:
            if key in scan_result_data:
                if database.update(args.movie, key, scan_result_data[key]):
                    pfcs(f"set b[{key}] = {scan_result_data[key]}")
                    need_save = True
    if need_save:
        database.save()


if __name__ == "__main__":
    main()
