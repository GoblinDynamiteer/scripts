#!/usr/bin/env python3

"Various movie helper/utility functions"

import os
import re
from pathlib import Path

import db_mov
import util
import util_tv
from cache import MovieCache
from config import ConfigurationManager

from printing import pfcs

VALID_LETTERS = {'#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'VW', 'X', 'Y', 'Z'}


CFG = ConfigurationManager()
MOVIE_DIR = CFG.get('path_film')


def parse_year(movie_dir_name):
    ''' Determines the movie year from dir '''
    re_year = re.compile(r'(19|20)\d{2}')
    year = re_year.search(movie_dir_name)
    if year:
        return year.group()
    return None


def determine_letter(movie_dir):
    "Determines the letter dir"
    if isinstance(movie_dir, Path):
        movie_dir = movie_dir.name
    folder = movie_dir.replace(' ', '.')
    letter = folder[0:1].upper()
    for prefix in ['The.', 'An.', 'A.']:
        if folder.startswith(prefix):
            letter = movie_dir[len(prefix):len(prefix) + 1].upper()
            break
    if str.isdigit(letter):
        return '#'
    if letter in ['V', 'W']:
        return 'VW'
    return letter


def list_all_movie_files():
    for movie_dir in list_all(full_path=True):
        for file_name in os.listdir(movie_dir):
            if any(file_name.endswith(ext) for ext in util.video_extensions()):
                yield (movie_dir, file_name)  # return full path and filename


def get_full_path_of_movie_filename(file_name: str, use_cache=True):
    "Returns the full path of an episode, if found"
    if use_cache:
        letter = determine_letter(file_name)
        for path in MovieCache().get_file_path_list(letter):
            if file_name in path:
                return path
        else:
            return None
    for path, filename in list_all_movie_files():
        if filename in file_name:
            return os.path.join(path, filename)
    return None


def get_full_path_to_movie_filename(folder: str, use_cache=True):
    "Returns the full path of movie, if found"
    if use_cache:
        letter = determine_letter(folder)
        for path in MovieCache().get_file_path_list(letter):
            if folder in path:
                return path
        else:
            return None
    for path, filename in list_all_movie_files():
        if folder in path:
            return os.path.join(path, filename)
    return None


def list_all(full_path=False) -> list:
    '''Returns a list of all current movies'''
    letters_dirs = [os.path.join(MOVIE_DIR, letter)
                    for letter in os.listdir(MOVIE_DIR)
                    if os.path.isdir(os.path.join(MOVIE_DIR, letter))]
    if full_path:
        return [os.path.join(letter, movie) for letter in letters_dirs for movie in os.listdir(letter)]
    return [movie for letter in letters_dirs for movie in os.listdir(letter)]


def determine_title(folder):
    ''' Determine the movie title from dir '''
    re_title = re.compile(
        r'.+?(?=\.(\d{4}|REPACK|720p|1080p|2160|DVD|BluRay))')
    title = re_title.search(folder)
    if title:
        title = re.sub('(REPACK|LiMiTED|EXTENDED|Unrated)',
                       '.', title.group(0))
        return re.sub(r'\.', ' ', title)
    return None


def remove_extras_from_folder(folder):
    extras = ["repack", "limited", "extended", "unrated", "swedish",
              "remastered", "festival", "docu", "rerip", "internal",
              "finnish", "danish", "dc.remastered", "proper", "bluray",
              "jpn", "hybrid", "uncut"]
    rep_string = "\\.({})".format("|".join(extras))
    return re.sub(rep_string, '', folder, flags=re.IGNORECASE)


def is_movie(string: str):
    "Try to determine if a string is movie name"
    if util_tv.is_episode(string) or util_tv.is_season(string):
        return False
    has_year = parse_year(string) != None
    parsed_title = determine_title(string) != None
    can_determine_title = parsed_title and parsed_title != string
    return has_year or can_determine_title


def exists(movie_dir_name: str):
    return util.is_dir(movie_path(movie_dir_name))


def movie_path(movie_dir_name: str):
    return Path(MOVIE_DIR) / determine_letter(movie_dir_name) / movie_dir_name


def find_deleted_movies():
    db = db_mov.MovieDatabase()
    for m in db.all():
        if not exists(m):
            yield m


def create_movie_nfo(movie_dir: str, imdb_id: str, debug_print=False):
    mstr = __name__ + ".create_movie_nfo"
    imdb_id = util.parse_imdbid(imdb_id)
    if not imdb_id:
        pfcs(
            f"o[{mstr}] could not parse imdb-id from e[{imdb_id}]", show=debug_print)
        return None
    if not util.is_dir(movie_dir) and exists(movie_dir):
        movie_dir = movie_path(movie_dir)
    if not util.is_dir(movie_dir):
        pfcs(
            f"o[{mstr}] could not determine location of e[{Path(movie_dir).name}]", show=debug_print)
        return None
    previous_imdb = get_movie_nfo_imdb_id(movie_dir, debug_print=debug_print)
    file_loc = Path(movie_dir) / 'movie.nfo'
    with open(file_loc, 'w') as file_item:
        file_item.write(f'https://www.imdb.com/title/{imdb_id}')
    if debug_print:
        prev_str = ""
        if previous_imdb:
            prev_str = f" previous id was o[{previous_imdb}]"
        pfcs(
            f"o[{mstr}] wrote g[{imdb_id}] to movie.nfo for g[{Path(movie_dir).name}]{prev_str}")


def get_movie_nfo_imdb_id(movie_dir: str, debug_print=False):
    "Get the imdb-id from a movie.nfo in the movie folder location"
    mstr = __name__ + ".get_movie_nfo_imdb_id"
    if not util.is_dir(movie_dir) and exists(movie_dir):
        movie_dir = movie_path(movie_dir)
    path = Path(movie_dir) / 'movie.nfo'
    if not path.is_file():
        pfcs(
            f"o[{mstr}] movie.nfo file does not exist in w[{movie_dir}]", show=debug_print)
        return None
    with open(path, 'r') as file_item:
        return util.parse_imdbid(file_item.readline())


def movie_root_dir():
    'Get the root path to movie location'
    return MOVIE_DIR


def valid_letters():
    'Get all valid subdirs for storing movies'
    return VALID_LETTERS
