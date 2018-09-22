#!/usr/bin/env python3.6

import os
import re
import omdb
import filetools as ftool
import config
import str_o

PRINT = str_o.PrintClass(os.path.basename(__file__))
CONFIG = config.ConfigurationManager()

VALID_LETTERS = {'#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'VW', 'X', 'Y', 'Z'}


def valid_movie_path(path):
    for let in VALID_LETTERS:
        p = os.path.join(path, let)
        if not os.path.exists(p):
            return False
    return True


def vaild_letters():
    return VALID_LETTERS


def root_path():
    path = CONFIG.get_setting("path", "movieroot")
    if not valid_movie_path(path):
        PRINT.warning("Could not find movies root location!")
        quit()
    return path


def has_subtitle(path, lang):
    return ftool.get_file(path, lang + ".srt")


def has_nfo(path):
    return True if ftool.get_file(path, "nfo") is not None else False


def nfo_to_imdb(path):
    if not has_nfo(path):
        return None
    f = open(ftool.get_file(path, "nfo", full_path=True), "r")
    imdb_url = f.readline()
    f.close()
    re_imdb = re.compile("tt\d{1,}")
    imdb_id = re_imdb.search(imdb_url)
    return imdb_id.group(0) if imdb_id else None


def get_vid_file(path):
    for ext in ["mkv", "avi", "mp4"]:
        vid = ftool.get_file(path, ext)
        if vid:
            return vid
    return None


def determine_letter(folder):
    folder = folder.replace(" ", ".")
    let = folder[0:1]
    for prefix in ['The.', 'An.', 'A.']:
        if folder.startswith(prefix):
            let = folder[len(prefix):len(prefix) + 1]
    if let is "V" or let is "W":
        return "VW"
    PRINT.info("guessed letter: {}".format(let))
    return let


def determine_title(folder, replace_dots_with=' '):
    re_title = re.compile(".+?(?=\.(\d{4}|REPACK|720p|1080p|DVD|BluRay))")
    title = re_title.search(folder)
    if title is not None:
        title = re.sub('(REPACK|LiMiTED|EXTENDED|Unrated)',
                       '.', title.group(0))
        title = re.sub('\.', replace_dots_with, title)
        return title
    else:
        PRINT.warning("could not guess title for {}".format(folder))
        return None


def determine_year(folder):
    re_year = re.compile("(19|20)\d{2}")
    year = re_year.search(folder)
    if year is not None:
        return year.group(0)
    else:
        PRINT.warning("could not guess year for {}".format(folder))
        return None


def remove_extras_from_folder(folder):
    extras = ["repack", "limited", "extended", "unrated", "swedish",
              "remastered", "festival", "docu", "rerip", "internal",
              "finnish", "danish", "dc.remastered", "proper", "bluray",
              "jpn", "hybrid", "uncut"]
    rep_string = "\\.({})".format("|".join(extras))
    return re.sub(rep_string, '', folder, flags=re.IGNORECASE)


def omdb_search(movie):
    folder = movie['folder']
    PRINT.info(f"searching OMDb for [{folder}] ", end_line=False)
    if movie['imdb'] is not None:
        PRINT.color_brackets(
            f"as [{movie['imdb']}] >", "green", end_line=False)
        omdb_search = omdb.omdb_search(str(movie['imdb']))
    else:
        title = determine_title(folder, replace_dots_with='+')
        year = determine_year(folder)
        PRINT.color_brackets(f"as [{title}] >", "green", end_line=False)
        omdb_search = omdb.omdb_search(title, type="movie", year=year)
    data = omdb_search.data()
    try:
        if data['Response'] == "False":
            PRINT.color_brackets(" [response false]!", "yellow")
            return None
        PRINT.color_brackets(" [got data]!", "green")
        return data
    except:
        PRINT.color_brackets(" [script error] !", "red")
        return None
