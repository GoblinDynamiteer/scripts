#!/usr/bin/env python3.6

'''Scan for media'''

from config import ConfigurationManager
from db_mov import MovieDatabase
from omdb import movie_search
import util_movie
import util

from printing import to_color_str as CSTR


DB_MOV = MovieDatabase()
CFG = ConfigurationManager()

if __name__ == '__main__':

    MOVIES_NOT_IN_DB = [
        movie for movie in util_movie.list_all() if not DB_MOV.exists(movie)]

    NEW = len(MOVIES_NOT_IN_DB)
    for new_movie in MOVIES_NOT_IN_DB:
        data = {'folder': new_movie, 'scanned': util.now_timestamp()}
        guessed_title = util_movie.determine_title(new_movie)
        guessed_year = util_movie.parse_year(new_movie)
        json_data = {}
        if guessed_title:
            json_data = movie_search(guessed_title, year=guessed_year)
        if 'Year' in json_data:
            year = json_data['Year']
            if util.is_valid_year(year, min_value=1920, max_value=2019):
                data['year'] = int(year)
        if 'imdbID' in json_data:
            imdb_id = json_data['imdbID']
            imdb_id = util.parse_imdbid(imdb_id)
            if imdb_id:
                data['imdb'] = imdb_id
        if 'Title' in json_data:
            data['title'] = json_data['Title']
        DB_MOV.insert(data)
        print(f'added new movie: {CSTR(new_movie, "green")}')

    if NEW:
        DB_MOV.save()
        DB_MOV.export_last_added()
    else:
        print('found no new movies')
