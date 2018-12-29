#!/usr/bin/env python3.6

'''JSON Database handler'''

import json
import os
import shutil

import printing
import util
from config import ConfigurationManager

CSTR = printing.to_color_str
CFG = ConfigurationManager()


class JSONDatabase(object):
    ''' A simple json database '''

    def __init__(self, database_file_path):
        self.json = None
        self.db_file_path = database_file_path
        self._load_database_file()
        self.valid_keys = []
        self.primary_key = None
        self.key_types = {}

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

    def _backup(self):
        ''' Backup json file '''
        timestamp = util.now_timestamp()
        backup_path = CFG.get('path_backup')
        db_filename = util.filename_of_path(self.db_file_path)
        destination = os.path.join(
            backup_path, 'databases', f'{db_filename}_{timestamp}')
        try:
            shutil.copy(self.db_file_path, destination)
        except PermissionError:
            shutil.copyfile(self.db_file_path, destination)
        print(f'backed up to {CSTR(destination, "green")}')

    def save(self):
        ''' Save database file '''
        self._backup()
        self._save_database_file()

    def set_valid_keys(self, key_list):
        ''' Sets allowed keys '''
        self.valid_keys = key_list
        self.primary_key = key_list[0]
        for key in key_list:
            self.key_types[key] = None

    def set_key_type(self, key, data_type):
        ''' Constrict key data type '''
        if key not in self.valid_keys:
            print(f'{CSTR(key, "red")} is not a valid key!')
            return False
        if data_type not in [int, str, float, list, dict]:
            print(f'{CSTR(str(data_type), "red")} is not a valid data type!')
            return False
        self.key_types[key] = data_type

    def update(self, primary_key, data, value):
        ''' Updates data for an entry '''
        if primary_key not in self.json:
            print(
                f'can\'t update {CSTR(f"{primary_key}", "orange")} not in db')
            return False
        if data not in self.valid_keys:
            print(f'{CSTR(data, "red")} is not a valid key!')
            return False
        self.json[primary_key][data] = value
        return True

    def sorted(self, sort_by_key, reversed_sort=False):
        unsorted_list = []
        for primary_key in self.json:
            unsorted_list.append(
                (primary_key, self.json[primary_key][sort_by_key]))
        sorted_list = sorted(
            unsorted_list, key=lambda tuple_item: tuple_item[1], reverse=reversed_sort)
        sorted_dict = {}
        for item in sorted_list:
            sorted_dict[item[0]] = self.json[item[0]]
        return sorted_dict

    def get(self, primary_key, data):
        ''' Retrieve data '''
        try:
            return self.json[primary_key][data]
        except KeyError:
            print(f'could not retrieve data for {CSTR(primary_key, "red")}')
            return None

    def exists(self, primary_key):
        ''' Check if key exists in database '''
        return primary_key in self.json

    def __contains__(self, primary_key):
        return self.exists(primary_key)

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
        if primary in self.json:
            print(f'{CSTR(primary, "red")} already in database, use update instead!')
            return False
        data.pop(self.primary_key)
        self.json[primary] = data
        return True
