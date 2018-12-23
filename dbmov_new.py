#!/usr/bin/env python3.6

'''Movie Database handler'''

import config
import printing
import db_json

CFG = config.ConfigurationManager()
MOVIE_DATABASE_PATH = CFG.get('movdb_new')
CSTR = printing.to_color_str


class MovieDatabase(db_json.JSONDatabase):
    ''' Movie Database '''

    def __init__(self):
        db_json.JSONDatabase.__init__(self, MOVIE_DATABASE_PATH)
        self.set_valid_keys(['folder', 'title', 'year', 'imdb'])
        self.insert({'folder': 'kalle_f', 'title': 'kalle_t', 'year': 1823})
        if not self.insert({'title': 'kalle_t', 'year': 1823}):
            print('fail')
        if not self.insert({'folder': 'kalle_t', 'year': 1823, 'plot': 'fassss'}):
            print('fail2')
        self.insert({'folder': 'skalle_f', 'title': 'skalle_t',
                     'year': 1553, 'imdb': 'tt123'})
        print(self.json)


MVDB = MovieDatabase()
