#!/usr/bin/env python3.6

''' Various movie helper/utility functions '''

import re
import os
import util_tv
import util
import db_mov

from config import ConfigurationManager

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


def determine_letter(movie_dir_name):
    ''' Determines the letter dir '''
    folder = movie_dir_name.replace(' ', '.')
    letter = folder[0:1].upper()
    for prefix in ['The.', 'An.', 'A.']:
        if folder.startswith(prefix):
            letter = movie_dir_name[len(prefix):len(prefix) + 1].upper()
            break
    if str.isdigit(letter):
        return '#'
    if letter in ['V', 'W']:
        return 'VW'
    return letter


def list_all() -> list:
    '''Returns a list of all current movies'''
    letters_dirs = [os.path.join(MOVIE_DIR, letter)
                    for letter in os.listdir(MOVIE_DIR)
                    if os.path.isdir(os.path.join(MOVIE_DIR, letter))]
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
    path = os.path.join(MOVIE_DIR, determine_letter(
        movie_dir_name), movie_dir_name)
    return util.is_dir(path)


def find_deleted_movies():
    db = db_mov.MovieDatabase()
    for m in db.all():
        if not exists(m):
            yield m


def create_movie_nfo(movie_dir: str, imdb_id: str):
    imdb_id = util.parse_imdbid(imdb_id)
    if not util.is_dir(movie_dir) or not imdb_id:
        return
    file_loc = os.path.join(movie_dir, 'movie.nfo')
    with open(file_loc, 'w') as file_item:
        file_item.write(f'https://www.imdb.com/title/{imdb_id}')


def get_movie_nfo_imdb_id(movie_dir: str):
    "Get the imdb-id from a movie.nfo in the movie folder location"
    if not exists(movie_dir):
        return None
    path = os.path.join(MOVIE_DIR, determine_letter(
        movie_dir), movie_dir, 'movie.nfo')
    if not util.is_file(path):
        return None
    with open(path, 'r') as file_item:
        return util.parse_imdbid(file_item.readline())