#!/usr/bin/env python3.6

import json
import os
from pathlib import Path
from threading import Lock, Thread

import db_json
import util
from config import ConfigurationManager
from printing import cstr

CACHE_DB_MOV_PATH = ConfigurationManager().get('path_mov_cachedb')
CACHE_DB_TV_PATH = ConfigurationManager().get('path_tv_cachedb')
SHOW_DIR = ConfigurationManager().get('path_tv')
MOVIE_DIR = ConfigurationManager().get('path_film')
VALID_MOV_SUBDIR_LETTERS = {'#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                            'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'VW', 'X', 'Y', 'Z'}


def list_all_shows() -> list:
    '''Returns a list of all current tv show folders'''
    return [show for show in os.listdir(SHOW_DIR)
            if os.path.isdir(os.path.join(SHOW_DIR, show))]


class TvCache(db_json.JSONDatabase):
    ''' Cached tv paths Database '''

    def __init__(self, debug_print: bool = False):
        db_json.JSONDatabase.__init__(
            self, CACHE_DB_TV_PATH, debug_print=debug_print)
        self.set_valid_keys(
            ['season_dir', 'modified', 'files'])
        self.set_key_type('season_dir', str)  # ShowName/S##
        self.set_key_type('modified', int)  # unix timestamp
        self.set_key_type('files', list)
        self.cache_update_lock = Lock()
        Thread(target=self.update_paths).start()

    def update_paths(self):
        self.cache_update_lock.acquire()
        need_save = False

        for show in list_all_shows():
            show_path = Path(SHOW_DIR) / show
            season_paths = [
                Path(show_path) / sp for sp in os.listdir(show_path)]
            for sp in season_paths:
                if sp.is_dir():
                    mtime = int(sp.stat().st_mtime)
                    show, season = sp.parts[-2:]
                    season_dir = f"{show}/{season}"
                    if season_dir not in self:
                        self.insert({'season_dir': season_dir,
                                     'modified': mtime,
                                     'files': []})
                        self.update_season_files(season_dir)
                        need_save = True
                    elif self.get(season_dir, 'modified') < mtime:
                        self.update(season_dir, 'modified', mtime)
                        self.update_season_files(season_dir)
                        need_save = True
        if need_save:
            self.save()
        elif self.debug:
            print('no new tv show files found')
        self.cache_update_lock.release()

    def update_season_files(self, season_dir):
        root_path = Path(SHOW_DIR) / season_dir
        episode_files = []
        for root, _, files in os.walk(root_path):
            for file_ in files:
                full_path = Path(root) / file_
                file_name = full_path.parts[-1]
                if any(file_name.endswith(ext) for ext in util.video_extensions()):
                    episode_files.append(str(file_name))
                    if self.debug:
                        print(
                            f'added to tv cache: {cstr(file_name, "lgreen")}')
        self.update(season_dir, 'files', episode_files)

    def get_file_path_list(self, only_show=None):
        with self.cache_update_lock:
            for path in self:
                if only_show and only_show not in path:
                    continue
                for file_path in self.get(path, 'files'):
                    full_path = Path(SHOW_DIR) / path / file_path
                    yield str(full_path)
        return []


class MovieCache(db_json.JSONDatabase):

    def __init__(self, debug_print: bool = False):
        db_json.JSONDatabase.__init__(
            self, CACHE_DB_MOV_PATH, debug_print=debug_print)
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
        for letter in os.listdir(MOVIE_DIR):
            if letter in VALID_MOV_SUBDIR_LETTERS:
                letter_path = Path(MOVIE_DIR) / letter
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
        elif self.debug:
            print('no new movie files found')
        self.cache_update_lock.release()

    def update_letter_files(self, letter):
        root_path = Path(MOVIE_DIR) / letter
        letter_files = []
        for root, _, files in os.walk(root_path):
            for file_ in files:
                full_path = Path(root) / file_
                movie_dir, file_name = full_path.parts[-2:]
                if any(file_name.endswith(ext) for ext in util.video_extensions()):
                    sub_path = Path(movie_dir) / file_name
                    letter_files.append(str(sub_path))
                    if self.debug:
                        print(
                            f'added to mov cache: {cstr(sub_path, "lgreen")}')
        self.update(letter, 'files', letter_files)

    def get_file_path_list(self, only_letter=None):
        with self.cache_update_lock:
            for letter in self:
                if only_letter and only_letter != letter:
                    continue
                for file_path in self.get(letter, 'files'):
                    full_path = Path(MOVIE_DIR) / letter / file_path
                    yield str(full_path)
        return []


if __name__ == "__main__":
    mov_cache = MovieCache(debug_print=True)
    tv_cache = TvCache(debug_print=True)
