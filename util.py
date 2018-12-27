#!/usr/bin/env python3.6

''' Various helper/utility functions '''

import os
import re


def home_dir():
    ''' Full path to home directory '''
    return os.path.expanduser("~")


def dirname_of_file(file_path):
    try:
        full_path = os.path.realpath(file_path)
        return os.path.dirname(full_path)
    except:
        return None


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
