#!/usr/bin/env python3.6

''' Various helper/utility functions '''

import os
import re
import ntpath
from datetime import datetime as DateTime


def home_dir():
    ''' Full path to home directory '''
    return os.path.expanduser("~")


def dirname_of_file(file_path):
    try:
        full_path = os.path.realpath(file_path)
        return os.path.dirname(full_path)
    except:
        return None


def filename_of_path(file_path):
    ''' Gets just the filename of a full part'''
    _, tail = ntpath.split(file_path)
    return tail or None


def parse_imdbid(string):
    ''' Parse the IMDB-id from a string, if possible '''
    match = re.search(r'tt\d{1,}', string)
    if match:
        return match.group()
    return None


def is_imdbid(string):
    ''' Return true if string contains an IMDB-id '''
    if parse_imdbid(string):
        return True
    return False


def is_valid_year(string, min_value=1800, max_value=2050):
    ''' Determines if a string / int value is a valid year '''
    year = 0
    try:
        year = int(string)
    except ValueError:
        return False
    except TypeError:
        return False
    if min_value < year < max_value:
        return True
    return False


def now_timestamp() -> int:
    ''' Current time as a UNIX timestamp '''
    return int(DateTime.now().timestamp())


def video_extensions() -> list:
    ''' Get a list of used video file extensions '''
    return ['.mkv', '.avi', '.mp4']
