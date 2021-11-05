#!/usr/bin/env python3

'''TV Episode/Show Database handler'''

import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import config
import db_json
import printout
import util
import util_tv
from printout import pfcs

from singleton import Singleton

CFG = config.ConfigurationManager()
EPISODE_DATABASE_PATH = CFG.get('path_epdb')
SHOW_DATABASE_PATH = CFG.get('path_showdb')
CSTR = printout.to_color_str


def _to_text(episode_filename, episode_data, use_removed_date=False):
    if use_removed_date:
        date = datetime.fromtimestamp(
            episode_data['removed_date']).strftime('%Y-%m-%d')
    else:
        date = datetime.fromtimestamp(
            episode_data['scanned']).strftime('%Y-%m-%d')
    try:
        season_episode = f'S{episode_data["season_number"]:02d}E{episode_data["episode_number"]:02d}'
    except KeyError:
        print("ERROR ON", episode_data)
        return ""
    return f'[{date}] [{episode_data["tvshow"]}] [{season_episode}] [{episode_filename}]\n'


class ShowDatabase(db_json.JSONDatabase):
    ''' TV/Show Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, SHOW_DATABASE_PATH)
        self.set_valid_keys(['folder', 'title', 'year', 'imdb',
                             'tvmaze', 'scanned', 'removed', 'removed_date'])
        self.set_key_type('folder', str)
        self.set_key_type('title', str)
        self.set_key_type('year', int)
        self.set_key_type('imdb', str)
        self.set_key_type('tvmaze', int)
        self.set_key_type('scanned', int)  # unix timestamp
        self.set_key_type('removed', bool)
        self.set_key_type('removed_date', int)

    def is_removed(self, folder):
        if folder in self.json:
            return self.json[folder].get('removed', False)
        return False

    def mark_removed(self, folder):
        self.update(folder, 'removed', True)
        self.update(folder, 'removed_date', util.now_timestamp())
        print(f'marked {CSTR(folder, "orange")} as removed')


class EpisodeDatabase(db_json.JSONDatabase):
    ''' TV/Episode Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, EPISODE_DATABASE_PATH)
        self.set_valid_keys(['filename', 'season_number', 'released', 'tvshow',
                             'episode_number', 'tvmaze', 'scanned', 'removed', 'removed_date'])
        self.set_key_type('filename', str)
        self.set_key_type('tvshow', str)
        self.set_key_type('season_number', int)
        self.set_key_type('episode_number', int)
        self.set_key_type('released', int)  # unix timestamp
        self.set_key_type('tvmaze', int)
        self.set_key_type('scanned', int)  # unix timestamp
        self.set_key_type('removed', bool)
        self.set_key_type('removed_date', int)

    def is_removed(self, filename):
        if filename in self.json:
            return self.json[filename].get('removed', False)
        return False

    def mark_removed(self, filename):
        try:
            self.update(filename, 'removed', True)
            self.update(filename, 'removed_date', util.now_timestamp())
            print(f'marked {CSTR(filename, "orange")} as removed')
        except:
            pass

    def last_added(self, num=10):
        ''' Get the most recently added episodes '''
        sorted_dict = self.sorted('scanned', reversed_sort=True)
        count = 0
        last_added_dict = {}
        for folder, data in sorted_dict.items():
            last_added_dict[folder] = data
            count += 1
            if count == num:
                return last_added_dict
        return last_added_dict

    def export_latest_added(self, target=os.path.join(CFG.get('path_tv'), 'latest.txt')):
        ''' Exports the latest added episodes to text file '''
        last_added = self.last_added(num=1000)
        last_added_text = [_to_text(e, last_added[e]) for e in last_added]
        try:
            with open(target, 'w') as last_added_file:
                last_added_file.writelines(last_added_text)
            print(f'wrote {len(last_added)} lines to {CSTR(target, "green")}')
        except:
            print(CSTR('could not save latest.txt', 'red'))

    def last_removed(self, num=10):
        ''' Get the most recently removed episodes '''
        sorted_dict = self.sorted('removed_date', reversed_sort=True)
        count = 0
        last_removed_dict = {}
        for folder, data in sorted_dict.items():
            last_removed_dict[folder] = data
            count += 1
            if count == num:
                return last_removed_dict
        return last_removed_dict

    def export_last_removed(self, target=os.path.join(CFG.path('tv'), 'removed.txt')):
        ''' Exports the latest removed episodes to text file '''
        last_removed = self.last_removed(num=1000)
        last_removed_text = [_to_text(ep, last_removed[ep], use_removed_date=True)
                             for ep in last_removed]
        try:
            with open(target, 'w') as last_removed_file:
                last_removed_file.writelines(last_removed_text)
            print(
                f'wrote {len(last_removed)} lines to {CSTR(target, "green")}')
        except:
            print(CSTR('could not save removed.txt', 'red'))


class ShowDatabaseSingleton(metaclass=Singleton):
    _db = ShowDatabase()

    def db(self):
        return self._db

    def get_id(self, show_name: str) -> int:
        return self._db.get(show_name, "tvmaze")


class EpisodeDatabaseSingleton(metaclass=Singleton):
    _db = EpisodeDatabase()

    def db(self):
        return self._db

    def get_id(self, filename: str) -> int:
        return self._db.get(filename, "tvmaze")


if __name__ == "__main__":
    PARSER = ArgumentParser()
    PARSER.add_argument("show_folder", type=str)
    PARSER.add_argument("--setimdb", "-i", type=str)
    PARSER.add_argument("--rescan", "-r", action="store_true")
    ARGS = PARSER.parse_args()
    SHOW_DB = ShowDatabaseSingleton().db()
    if ARGS.show_folder not in SHOW_DB:
        pfcs(f"w[{ARGS.show_folder}] not in show database")
        sys.exit(1)
    if SHOW_DB.is_removed(ARGS.show_folder):
        pfcs(f"w[{ARGS.show_folder}] is marked removed, not processing")
        sys.exit(1)
    pfcs(f"processing g[{ARGS.show_folder}]")
    if ARGS.setimdb:
        if ARGS.show_folder not in util_tv.list_all_shows():
            pfcs(f"could not find w[{ARGS.show_folder}] on disk!")
            sys.exit(1)
        if not util_tv.save_nfo(ARGS.show_folder, ARGS.setimdb):
            pfcs(f"failed to save tvshow.nfo in w[{ARGS.show_folder}]!")
            sys.exit(1)
    NEED_SAVE = False
    if ARGS.rescan:
        from scan import process_new_show  # prevents circular import...
        pfcs(f"rescanning tvmaze for g[{ARGS.show_folder}]")
        DATA = process_new_show(ARGS.show_folder)
        for key in ["tvmaze", "title", "imdb", "year"]:
            if key in DATA:
                if SHOW_DB.update(ARGS.show_folder, key, DATA[key]):
                    pfcs(f"set b[{key}] = {DATA[key]}")
                    NEED_SAVE = True
    if NEED_SAVE:
        SHOW_DB.save()
