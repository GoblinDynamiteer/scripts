#!/usr/bin/env python3.6

'''TV Episode/Show Database handler'''

import os
from datetime import datetime

import config
import db_json
import printing

CFG = config.ConfigurationManager()
EPISODE_DATABASE_PATH = CFG.get('path_epdb')
SHOW_DATABASE_PATH = CFG.get('path_showdb')
CSTR = printing.to_color_str


def _to_text(movie_folder, movie_data):
    scanned_hr = datetime.fromtimestamp(
        movie_data['scanned']).strftime('%Y-%m-%d')
    return f'[{scanned_hr}] [{movie_data["year"]}] [{movie_data["title"]}] [{movie_folder}]\n'


class ShowDatabase(db_json.JSONDatabase):
    ''' TV/Show Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, SHOW_DATABASE_PATH)
        self.set_valid_keys(['folder', 'title', 'year', 'imdb', 'tvmaze'])
        self.set_key_type('folder', str)
        self.set_key_type('title', str)
        self.set_key_type('year', int)
        self.set_key_type('imdb', str)
        self.set_key_type('tvmaze', int)


class EpisodeDatabase(db_json.JSONDatabase):
    ''' TV/Episode Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, EPISODE_DATABASE_PATH)
        self.set_valid_keys(['filename', 'season_number', 'released', 'tvshow',
                             'episode_number', 'tvmaze', 'scanned'])
        self.set_key_type('filename', str)
        self.set_key_type('tvshow', str)
        self.set_key_type('season_number', int)
        self.set_key_type('episode_number', int)
        self.set_key_type('released', int)  # unix timestamp
        self.set_key_type('tvmaze', int)
        self.set_key_type('scanned', int)  # unix timestamp

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

    def export_last_added(self, target=os.path.join(CFG.get('path_tv'), 'latest.txt')):
        ''' Exports the latest added episodes to text file '''
        last_added = self.last_added(num=100)
        last_added_text = [_to_text(m, last_added[m]) for m in last_added]
        try:
            with open(target, 'w') as last_added_file:
                last_added_file.writelines(last_added_text)
            print(f'wrote to {CSTR(target, "green")}')
        except:
            print(CSTR('could not save latest.txt', 'red'))
