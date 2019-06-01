#!/usr/bin/env python3.6

import json
import os
from pathlib import Path
from threading import Thread, Lock

import db_json
import util
import util_movie
from config import ConfigurationManager
from printing import cstr

CACHE_DB_PATH = ConfigurationManager().get('path_cachedb')


class MovieCache(db_json.JSONDatabase):
    ''' Cached paths Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, CACHE_DB_PATH)
        self.set_valid_keys(
            ['letter_dir', 'modified', 'files'])
        self.set_key_type('letter_dir', str)
        self.set_key_type('modified', int)  # unix timestamp
        self.set_key_type('files', list)
        self.cache_update_lock = Lock()
        Thread(target=self.update_paths).start()

    def update_paths(self):
        self.cache_update_lock.acquire()
        need_save = False
        for letter in os.listdir(util_movie.MOVIE_DIR):
            if letter in util_movie.VALID_LETTERS:
                letter_path = Path(util_movie.MOVIE_DIR) / letter
                mtime = int(letter_path.stat().st_mtime)
                if letter not in self:
                    self.insert({'letter_dir': letter,
                                 'modified': mtime,
                                 'files': []})
                    self.update_letter_files(letter)
                    need_save = True
                elif self.get(letter, 'modified') < mtime:
                    self.update(letter, 'modified', mtime)
                    self.update_letter_files(letter)
                    need_save = True
        if need_save:
            self.save()
        self.cache_update_lock.release() 

    def update_letter_files(self, letter, debug_print=False):
        root_path = Path(util_movie.MOVIE_DIR) / letter
        letter_files = []
        for root, _, files in os.walk(root_path):
            for file_ in files:
                full_path = Path(root) / file_
                movie_dir, file_name = full_path.parts[-2:]
                if any(file_name.endswith(ext) for ext in util.video_extensions()):
                    sub_path = Path(movie_dir) / file_name
                    letter_files.append(str(sub_path))
                    if debug_print:
                        print(
                            f'added to mov cache: {cstr(sub_path, "lgreen")}')
        self.update(letter, 'files', letter_files)

    def get_file_path_list(self, only_letter=None):
        with self.cache_update_lock:
            for letter in self:
                if only_letter and only_letter != letter:
                    continue
                for file_path in self.get(letter, 'files'):
                    full_path = Path(util_movie.MOVIE_DIR) / letter / file_path
                    yield str(full_path)
        return []


if __name__ == "__main__":
    mov_cache = MovieCache()