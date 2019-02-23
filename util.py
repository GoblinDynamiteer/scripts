#!/usr/bin/env python3.6

''' Various helper/utility functions '''

import ntpath
import os
import re
import shutil
from datetime import datetime as DateTime
from enum import Enum


class Settings(Enum):
    "Various settings for the utils in this file"
    AUTO_TERMINAL = 0


def home_dir():
    "Full path to home directory"
    return os.path.expanduser("~")


def dirname_of_file(file_path):
    try:
        full_path = os.path.realpath(file_path)
        return os.path.dirname(full_path)
    except:
        return None


def filename_of_path(file_path):
    "Gets just the filename of a full part"
    _, tail = ntpath.split(file_path)
    return tail or None


def parse_imdbid(string):
    "Parse the IMDB-id from a string, if possible"
    match = re.search(r'tt\d{1,}', string)
    if match:
        return match.group()
    return None


def parse_percent(string):
    "Parse a percent value from a string, if possible"
    for regex in [r'\d{1,3}%', r'\d{1,3}.%']:
        match = re.search(regex, string)
        if match:
            return match.group()
    return None


def is_imdbid(string):
    "Return true if string contains an IMDB-id"
    if parse_imdbid(string):
        return True
    return False


def is_valid_year(string, min_value=1800, max_value=2050):
    "Determines if a string / int value is a valid year"
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
    "Current time as a UNIX timestamp"
    return int(DateTime.now().timestamp())


def video_extensions() -> list:
    "Get a list of used video file extensions"
    return ['.mkv', '.avi', '.mp4']


def date_str_to_timestamp(string, date_format=None) -> int:
    "Tries to convert a time/date string to UNIX timestamp"
    formats = [date_format, r'%Y-%m-%dT%H:%M:%S', r'%Y-%m-%dT%H:%M:%S+00:00']
    for form in formats:
        try:
            date_time = DateTime.strptime(string, form)
            return int(date_time.timestamp())
        except:
            pass
    return 0  # could not parse time string


def bytes_to_human_readable(num, suffix='B'):
    "Gets a human readable string of a byte file size value"
    num = int(num)
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def is_dir(string):
    "Returns true if string is an existing directory"
    return os.path.isdir(string) and os.path.exists(string)


def is_file(string):
    "Returns true if string is an existing file"
    return os.path.isfile(string) and os.path.exists(string)


def is_vid_file(string):
    "Returns true if string is an existing vid file"
    return is_file(string) and any(ext in string for ext in video_extensions())


def terminal_width():
    "Returns the current terminal column width"
    try:
        return shutil.get_terminal_size()[0]
    except:
        return 0


def shorten_string(string, size, suffix='...'):
    "Shortens a string and adds ... suffix"
    if isinstance(size, Settings):
        if size == Settings.AUTO_TERMINAL:
            size = terminal_width()
    trim_length = size - len(suffix)
    if trim_length < len(string):
        return string[:trim_length] + suffix
    return string[:trim_length]
