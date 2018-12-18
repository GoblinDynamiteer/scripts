#!/usr/bin/env python3.6

'''Movie Database handler'''

import json

import config
import printing

CFG = config.ConfigurationManager()
MOVIE_DATABASE_PATH = CFG.get('movdb_new')
CSTR = printing.to_color_str


class JSONDatabase(object):
    def __init__(self, database_file_path):
        self.json = None
        self.db_file_path = database_file_path
        self._load_database_file()
        self.valid_keys = []

    def _load_database_file(self):
        try:
            with open(self.db_file_path, 'r') as database_file:
                self.json = json.load(database_file)
        except FileNotFoundError:
            with open(self.db_file_path, 'w') as database_file:
                database_file.write('')
            self._load_database_file()
        except json.decoder.JSONDecodeError:
            self.json = {}

    def set_valid_keys(self, key_list):
        self.valid_keys = key_list
        self.primary_key = key_list[0]

    def insert(self, data: dict):
        keys = list(data.keys())
        if self.primary_key not in keys:
            print(
                f'missing primary key: {CSTR(f"{self.primary_key}", "orange")}')
            return False
        invalid_keys = [k for k in keys if k not in self.valid_keys]
        if invalid_keys:
            print(
                f'invalid key(s) for database: {CSTR(f"{invalid_keys}", "red")}')
            return False
        primary = data[self.primary_key]
        data.pop(self.primary_key)
        self.json[primary] = data


class MovieDatabase(JSONDatabase):
    def __init__(self):
        JSONDatabase.__init__(self, MOVIE_DATABASE_PATH)
        self.set_valid_keys(['folder', 'title', 'year', 'imdb'])
        self.insert({'folder': 'kalle_f', 'title': 'kalle_t', 'year': 1823})
        if not self.insert({'title': 'kalle_t', 'year': 1823}):
            print('fail')
        if not self.insert({'folder': 'kalle_t', 'year': 1823, 'plot': 'fassss'}):
            print('fail2')
        self.insert({'folder': 'skalle_f', 'title': 'skalle_t',
                     'year': 1553, 'imdb': 'tt123'})
        print(self.json)


mvdb = MovieDatabase()
