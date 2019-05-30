#!/usr/bin/env python3.6

import json
import os
from pathlib import Path

import util
import util_movie
from printing import cstr


class MovieCache():
    def __init__(self):
        self.cache_file = 'mov_cache.json'
        self.mov_file_paths = []
        self.letter_modified = {}
        try:
            with open(self.cache_file, 'r') as json_file:
                json_data = json.load(json_file)
                self.mov_file_paths = json_data['paths']
                self.letter_modified = json_data['mod_dates']
        except FileNotFoundError:
            pass

    def update_paths(self):
        need_save = False
        for item in os.listdir(util_movie.MOVIE_DIR):
            path = Path(util_movie.MOVIE_DIR) / item
            if path.is_dir():
                mod_date = path.stat().st_mtime
                if self.letter_modified.get(item, 0) < mod_date:
                    self.letter_modified[item] = mod_date
                    self.scan_dir(path)
                    need_save = True
        if need_save:
            self.save()

    def scan_dir(self, dir):
        for root, _, files in os.walk(dir):
            for file_ in files:
                if any(file_.endswith(ext) for ext in util.video_extensions()):
                    full_path = Path(root) / file_
                    if str(full_path) not in self.mov_file_paths:
                        self.mov_file_paths.append(str(full_path))
                        print(
                            f'added to mov cache: {cstr(full_path, "lgreen")}')

    def save(self):
        with open(self.cache_file, 'w') as json_file:
            data = {'mod_dates': self.letter_modified,
                    'paths': self.mov_file_paths}
            json.dump(data, json_file)


if __name__ == "__main__":
    mov_cache = MovieCache()
    mov_cache.update_paths()
