#!/usr/bin/env python3.6

'''Scan for new movies'''

import os
import datetime
import filetools as ftool
import movie as MOVIE
import db_mov
import printing

PRINT = printing.PrintClass(os.path.basename(__file__))

DB_MOV = db_mov.database()
if not DB_MOV.load_success():
    quit()

ROOT = MOVIE.root_path()
SUB_FOLDERS = os.listdir(ROOT)


def new_movie(mov_dir_letter, movie_dir_name):
    """ Add a new movie to the database """
    file_path = os.path.join(ROOT, mov_dir_letter, movie_dir_name)
    mov = {'letter': mov_dir_letter, 'folder': movie_dir_name}
    date = ftool.get_creation_date(file_path, convert=True)
    mov['date_created'] = date.strftime(
        "%d %b %Y") if date is not None else None
    mov['date_scanned'] = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    mov['nfo'] = MOVIE.has_nfo(file_path)
    mov['imdb'] = MOVIE.nfo_to_imdb(file_path)
    mov['omdb'] = MOVIE.omdb_search(mov)
    mov['subs'] = {
        'sv': MOVIE.has_subtitle(file_path, "sv"),
        'en': MOVIE.has_subtitle(file_path, "en")}
    mov['video'] = MOVIE.get_vid_file(file_path)
    mov['status'] = "ok"
    PRINT.info(f"added [{movie_dir_name}] to database!")
    DB_MOV.add(mov)


NEW_COUNT = 0
for letter in SUB_FOLDERS:
    if letter in MOVIE.vaild_letters():
        PRINT.info(f"scanning {letter}")
        movies = os.listdir(os.path.join(ROOT, letter))
        movies.sort()
        for movie in movies:
            if movie.startswith("@"):
                continue  # NAS special dir
            if not DB_MOV.exists(movie):
                new_movie(letter, movie)
                NEW_COUNT += 1
    else:
        continue

PRINT.info(f"done scanning. found ({NEW_COUNT}) new movies.")
if NEW_COUNT > 0:
    DB_MOV.save()
    ftool.copy_dbs_to_webserver("movie")
