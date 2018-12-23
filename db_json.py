#!/usr/bin/env python3.6

'''JSON Database handler'''

import json

import printing

CSTR = printing.to_color_str


class JSONDatabase(object):
    ''' A simple json database '''

    def __init__(self, database_file_path):
        self.json = None
        self.db_file_path = database_file_path
        self._load_database_file()
        self.valid_keys = []
        self.primary_key = None

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

    def _save_database_file(self):
        try:
            with open(self.db_file_path, 'w') as database_file:
                json.dump(self.json, database_file)
        except:
            print('could not save database')

    def save(self):
        ''' Save database file '''
        self._save_database_file()

    def set_valid_keys(self, key_list):
        ''' Sets allowed keys '''
        self.valid_keys = key_list
        self.primary_key = key_list[0]

    def update(self, primary_key, data, value):
        if primary_key not in self.json:
            print(
                f'can\'t update {CSTR(f"{primary_key}, not in db", "orange")}')
            return False
        if data not in self.valid_keys:
            print(f'{CSTR(data, "red")} is not a valid key!')
            return False
        self.json[primary_key][data] = value
        return True

    def insert(self, data: dict):
        ''' Insert data '''
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
        return True
