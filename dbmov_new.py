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


MVDB = MovieDatabase()
MVDB.insert(
    {'folder': 'Junior.1994.1080p.BluRay.x264-CiNEFiLE', 'imdb': 'tt0110216'})
MVDB.insert(
    {'folder': 'Kill.Bill.Vol.1.2003.RERiP.iNTERNAL.1080p.BluRay.x264-LiBRARiANS', 'year': 2003})
MVDB.update('Kill.Bill.Vol.1.2003.RERiP.iNTERNAL.1080p.BluRay.x264-LiBRARiANS',
            'imdb', 'tt0266697')
MVDB.update('Kick-Ass.2010.720p.BluRay.X264-AMIABLE', 'year', 2010)
MVDB.save()
