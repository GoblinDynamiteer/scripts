# -*- coding: utf-8 -*-
import paths
import filetools as ftool
import movie as mtool
import db_mov
import os
import datetime
from printout import print_class as pr

pr = pr(os.path.basename(__file__))
db = db_mov.database()
if not db.load_success():
    quit()

mov_root = mtool.root_path()
letters = os.listdir(mov_root)
letters.sort()
new_count = 0

_valid_letters = { "#", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
    "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "VW", "X", "Y", "Z" }

# Add new movie to database
def new_movie(letter, movie):
    fp = os.path.join(mov_root, letter, movie)
    mov = { 'letter' : letter, 'folder' : movie }
    date = ftool.get_creation_date(fp, convert=True)
    mov['date_created'] = date.strftime("%d %b %Y") if date is not None else None
    mov['date_scanned'] = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    mov['nfo'] = mtool.has_nfo(fp)
    mov['imdb'] = mtool.nfo_to_imdb(fp)
    mov['omdb'] = mtool.omdb_search(mov)
    mov['subs'] = {
        'sv' : mtool.has_subtitle(fp, "sv"),
        'en' : mtool.has_subtitle(fp, "en") }
    mov['video'] = mtool.get_vid_file(fp)
    mov['status'] = "ok"
    pr.info(f"added [{movie}] to database!")
    db.add(mov)

# Scan for new movies...
for letter in letters:
    if letter in _valid_letters:
        pr.info(f"scanning {letter}")
        movies = os.listdir(os.path.join(mov_root, letter))
        movies.sort()
        for movie in movies:
            if movie.startswith("@"): # Diskstation
                continue;
            if not db.exists(movie):
                new_movie(letter, movie)
                new_count += 1
    else:
        continue

pr.info(f"done scanning. found ({new_count}) new movies.")
if new_count > 0:
    db.save()
    ftool.copy_dbs_to_webserver("movie")
