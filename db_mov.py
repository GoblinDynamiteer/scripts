#!/usr/bin/env python3

import argparse
import os
from datetime import datetime

import config
import db_json
import printout
import util
import util_movie
from printout import pfcs

CFG = config.ConfigurationManager()
MOVIE_DATABASE_PATH = CFG.get('path_movdb')
CSTR = printout.to_color_str


def _to_text(movie_folder, movie_data, use_removed_date=False):
    if use_removed_date:
        date = datetime.fromtimestamp(
            movie_data['removed_date']).strftime('%Y-%m-%d')
    else:
        date = datetime.fromtimestamp(
            movie_data['scanned']).strftime('%Y-%m-%d')
    year = title = ''
    if 'year' in movie_data:
        year = movie_data['year']
    if 'title' in movie_data:
        title = movie_data['title']
    ret_str = f'[{date}] [{movie_folder}]'
    if year:
        ret_str += f' [{year}]'
    if title:
        ret_str += f' [{title}]'
    return ret_str + '\n'


class MovieDatabase(db_json.JSONDatabase):
    ''' Movie Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, MOVIE_DATABASE_PATH)
        self.set_valid_keys(
            ['folder', 'title', 'year', 'imdb', 'scanned', 'removed', 'removed_date'])
        self.set_key_type('folder', str)
        self.set_key_type('title', str)
        self.set_key_type('year', int)
        self.set_key_type('imdb', str)
        self.set_key_type('scanned', int)  # unix timestamp
        self.set_key_type('removed', bool)
        self.set_key_type('removed_date', int)

    def last_added(self, num=10):
        ''' Get the most recently added movies '''
        sorted_dict = self.sorted('scanned', reversed_sort=True)
        count = 0
        last_added_dict = {}
        for folder, data in sorted_dict.items():
            last_added_dict[folder] = data
            count += 1
            if count == num:
                return last_added_dict
        return last_added_dict

    def last_removed(self, num=10):
        ''' Get the most recently removed movies '''
        sorted_dict = self.sorted('removed_date', reversed_sort=True)
        count = 0
        last_removed_dict = {}
        for folder, data in sorted_dict.items():
            last_removed_dict[folder] = data
            count += 1
            if count == num:
                return last_removed_dict
        return last_removed_dict

    def mark_removed(self, folder):
        ''' Mark a movie as deleted '''
        try:
            self.update(folder, 'removed', True)
            self.update(folder, 'removed_date', util.now_timestamp())
            print(f'marked {CSTR(folder, "orange")} as removed')
        except:
            pass

    def is_removed(self, folder):
        if folder in self.json:
            return self.json[folder].get('removed', False)
        return False

    def export_last_added(self, target=os.path.join(CFG.get('path_film'), 'latest.txt')):
        ''' Exports the latest added movies to text file '''
        last_added = self.last_added(num=1000)
        last_added_text = [_to_text(m, last_added[m]) for m in last_added]
        try:
            with open(target, 'w') as last_added_file:
                last_added_file.writelines(last_added_text)
            print(f'wrote to {CSTR(target, "green")}')
        except:
            print(CSTR('could not save latest.txt', 'red'))

    def export_last_removed(self, target=os.path.join(CFG.get('path_film'), 'removed.txt')):
        ''' Exports the latest removed movies to text file '''
        last_removed = self.last_removed(num=1000)
        last_removed_text = [_to_text(m, last_removed[m], use_removed_date=True)
                             for m in last_removed]
        try:
            with open(target, 'w') as last_added_file:
                last_added_file.writelines(last_removed_text)
            print(f'wrote to {CSTR(target, "green")}')
        except:
            print(CSTR('could not save latest.txt', 'red'))

    def all_movies(self):
        for item in self.all():
            if not self.json.get('removed', False):
                yield item


class MovieDatabaseSingleton(metaclass=util.Singleton):
    _db = MovieDatabase()

    def db(self):
        return self._db


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('movie', type=str)
    PARSER.add_argument('--setimdb', '-i', type=str)
    PARSER.add_argument('--rescan', '-r', action="store_true")
    ARGS = PARSER.parse_args()
    DB = MovieDatabase()
    if ARGS.movie not in DB:
        pfcs(f"w[{ARGS.movie}] not in movie database")
        exit(1)
    if DB.is_removed(ARGS.movie):
        pfcs(f"w[{ARGS.movie}] is marked removed, not processing")
        exit(1)
    pfcs(f"processing g[{ARGS.movie}]")
    if ARGS.setimdb:
        if not util_movie.exists(ARGS.movie):
            pfcs(f"could not find w[{ARGS.movie}] on disk!")
            exit(1)
        util_movie.create_movie_nfo(
            ARGS.movie, ARGS.setimdb, debug_print=True)
    NEED_SAVE = False
    if ARGS.rescan:
        from scan import process_new_movie  # prevents circular import...
        pfcs(f"rescanning omdb-data for g[{ARGS.movie}]")
        DATA = process_new_movie(ARGS.movie)
        for key in ['title', 'year', 'imdb']:
            if key in DATA:
                if DB.update(ARGS.movie, key, DATA[key]):
                    pfcs(f"set b[{key}] = {DATA[key]}")
                    NEED_SAVE = True
    if NEED_SAVE:
        DB.save()
