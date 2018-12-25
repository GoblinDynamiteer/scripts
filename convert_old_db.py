#!/usr/bin/env python3.6

'''JSON Database handler'''

from datetime import datetime


from dbmov_new import MovieDatabase
from db_mov import database

OLD_DB = database()
NEW_DB = MovieDatabase()

ALL_MOVIES = OLD_DB.list_movies()


def scanned_to_timestamp(scanned_str: str)->int:
    try:
        return int(datetime.strptime(scanned_str, '%d %b %Y').timestamp())
    except ValueError:
        pass
    try:
        return int(datetime.strptime(scanned_str, '%d %b %Y %H:%M').timestamp())
    except ValueError:
        pass


def year_to_int(year_str: str)->int:
    if not year:
        return 0
    if len(year_str) > 4:
        year_str = year_str[0:4]
    return int(year_str)


for movie in ALL_MOVIES:
    folder = movie
    title = OLD_DB.omdb_data(movie, 'Title')
    imdb = OLD_DB.movie_data(movie, 'imdb')
    scanned = OLD_DB.movie_data(movie, 'date_scanned')
    year = OLD_DB.omdb_data(movie, 'Year')
    year = year_to_int(year)
    scanned = scanned_to_timestamp(scanned)
    NEW_DB.insert({'folder': folder, 'title': title,
                   'imdb': imdb, 'year': year, 'scanned': scanned})
NEW_DB.save()

#datetime_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
