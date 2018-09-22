#!/usr/bin/env python3.6

'''Scan for new movies'''

import os
import datetime
import filetools as ftool
import movie
import db_mov
import str_o

PRINT = str_o.PrintClass(os.path.basename(__file__))

DB_MOV = db_mov.database()
if not DB_MOV.load_success():
    quit()

ROOT = movie.root_path()
SUB_FOLDERS = os.listdir(ROOT).sort()


def new_movie(letter, movie):
    fp = os.path.join(ROOT, letter, movie)
    mov = {'letter': letter, 'folder': movie}
    date = ftool.get_creation_date(fp, convert=True)
    mov['date_created'] = date.strftime(
        "%d %b %Y") if date is not None else None
    mov['date_scanned'] = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    mov['nfo'] = movie.has_nfo(fp)
    mov['imdb'] = movie.nfo_to_imdb(fp)
    mov['omdb'] = movie.omdb_search(mov)
    mov['subs'] = {
        'sv': movie.has_subtitle(fp, "sv"),
        'en': movie.has_subtitle(fp, "en")}
    mov['video'] = movie.get_vid_file(fp)
    mov['status'] = "ok"
    PRINT.info(f"added [{movie}] to database!")
    DB_MOV.add(mov)


NEW_COUNT = 0
for letter in SUB_FOLDERS:
    if letter in movie.vaild_letters():
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
