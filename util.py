#!/usr/bin/env python3.6

''' Various helper/utility functions '''

import os


def home_dir():
    ''' Full path to home directory '''
    return os.path.expanduser("~")


def dirname_of_file(file_path):
    try:
        full_path = os.path.realpath(file_path)
        return os.path.dirname(full_path)
    except:
        return None
