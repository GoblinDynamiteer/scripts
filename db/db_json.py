#!/usr/bin/env python3

import json
import os
import shutil

from printout import cstr
import util
from config import ConfigurationManager

CFG = ConfigurationManager()


class JSONDatabase(object):
    def __init__(self, database_file_path, debug_print: bool = False):
        self.json = None
        self.db_file_path = database_file_path
        self._load_database_file()
        self.valid_keys = []
        self.primary_key = None
        self.key_types = {}
        self.debug = debug_print

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
            if self.debug:
                print(f'saved database file {cstr(self.db_file_path, "lblue")}')
        except:
            if self.debug:
                print('could not save database')

    def _backup(self):
        timestamp = util.now_timestamp()
        backup_path = CFG.get('path_backup')
        db_filename = util.filename_of_path(self.db_file_path)
        destination = os.path.join(
            backup_path, 'databases', f'{db_filename}_{timestamp}')
        try:
            shutil.copy(self.db_file_path, destination)
        except PermissionError:
            shutil.copyfile(self.db_file_path, destination)
        if self.debug:
            print(f'backed up to {cstr(destination, "green")}')

    def save(self):
        self._backup()
        self._save_database_file()

    def set_valid_keys(self, key_list):
        self.valid_keys = key_list
        self.primary_key = key_list[0]
        for key in key_list:
            self.key_types[key] = None

    def set_key_type(self, key, data_type):
        if key not in self.valid_keys:
            print(f'{cstr(key, "red")} is not a valid key!')
            return False
        if data_type not in [int, str, float, list, dict, bool]:
            print(f'{cstr(str(data_type), "red")} is not a valid data type!')
            return False
        self.key_types[key] = data_type

    def update(self, primary_key, data, value):
        if primary_key not in self.json:
            print(
                f'can\'t update {cstr(f"{primary_key}", "orange")} not in db')
            return False
        if data not in self.valid_keys:
            print(f'{cstr(data, "red")} is not a valid key!')
            return False
        if self.key_types.get(data, None):
            if not isinstance(value, self.key_types[data]):
                print(
                    f'{cstr(data, "red")} is not of data type {str(self.key_types[data])}!')
                return False
        self.json[primary_key][data] = value
        return True

    def sorted(self, sort_by_key, reversed_sort=False):
        unsorted_list = []
        for primary_key in self.json:
            if not sort_by_key in self.json[primary_key]:
                continue
            unsorted_list.append(
                (primary_key, self.json[primary_key][sort_by_key]))
        sorted_list = sorted(
            unsorted_list, key=lambda tuple_item: tuple_item[1], reverse=reversed_sort)
        sorted_dict = {}
        for item in sorted_list:
            sorted_dict[item[0]] = self.json[item[0]]
        return sorted_dict

    def get(self, primary_key, data):
        try:
            return self.json[primary_key][data]
        except KeyError:
            if self.debug:
                print(
                    f'could not retrieve data [{data}] for {cstr(primary_key, "red")}')
            return None

    def exists(self, primary_key):
        return primary_key in self.json

    def all(self):
        return self.json.keys()

    def __contains__(self, primary_key):
        return self.exists(primary_key)

    def __iter__(self):
        for key in list(self.json.keys()):
            yield key

    def find(self, key, value):
        ret_list = []
        if not key in self.valid_keys:
            return ret_list
        ret_list = [pkey for pkey in self.json if self.json[pkey].get(
            key, None) == value]
        return ret_list

    def find_duplicates(self, key):
        ret_list = []
        if not key in self.valid_keys:
            return ret_list
        all_values = [self.json[pkey][key]
                      for pkey in self.json if key in self.json[pkey]]
        duplicates = {}
        for value in all_values:
            if not value:
                continue
            if all_values.count(value) > 1 and value not in duplicates:
                duplicates[value] = self.find(key, value)
        return duplicates

    def insert(self, data: dict):
        keys = list(data.keys())
        if self.primary_key not in keys:
            print(
                f'missing primary key: {cstr(f"{self.primary_key}", "orange")}')
            return False
        invalid_keys = [k for k in keys if k not in self.valid_keys]
        if invalid_keys:
            print(
                f'invalid key(s) for database: {cstr(f"{invalid_keys}", "red")}')
            return False
        for key in keys:
            if self.key_types.get(key, None):
                if not isinstance(data[key], self.key_types[key]):
                    print(
                        f'{cstr(key, "red")} is not of',
                        f'data type {str(self.key_types[key])}!')
                    return False
        primary = data[self.primary_key]
        if primary in self.json:
            print(f'{cstr(primary, "red")} already in database, use update instead!')
            return False
        data.pop(self.primary_key)
        self.json[primary] = data
        return True
