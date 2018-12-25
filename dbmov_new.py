#!/usr/bin/env python3.6

'''Movie Database handler'''

import config
import printing
import db_json

CFG = config.ConfigurationManager()
MOVIE_DATABASE_PATH = CFG.get('path_movdb_new')
CSTR = printing.to_color_str


class MovieDatabase(db_json.JSONDatabase):
    ''' Movie Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, MOVIE_DATABASE_PATH)
        self.set_valid_keys(['folder', 'title', 'year', 'imdb', 'scanned'])
        self.set_key_type('folder', str)
        self.set_key_type('title', str)
        self.set_key_type('year', int)
        self.set_key_type('imdb', str)
        self.set_key_type('scanned', int)  # unix timestamp
