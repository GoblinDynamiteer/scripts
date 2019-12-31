#!/usr/bin/env python3

"Various helper/utility functions"

import difflib
import ntpath
import os
import re
import shutil
from datetime import datetime as DateTime
from enum import Enum
from pathlib import Path


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
    try:
        match = re.search(r'tt\d{1,}', string)
        if match:
            return match.group()
    except TypeError:
        pass
    return None


def get_file_contents(file_loc: str):
    if not is_file(file_loc):
        return None
    encodings = ['utf-8', 'utf-16', 'iso-8859-15']
    for enc in encodings:
        with open(file_loc, 'r', encoding=enc) as file_item:
            try:
                lines = file_item.readlines()
                return lines
            except UnicodeDecodeError:
                pass
            except UnicodeError:
                pass
    return None


def parse_imdbid_from_file(file_loc: str):
    if not is_file(file_loc):
        return None
    lines = get_file_contents(file_loc)
    if not lines:
        return None
    for line in lines:
        imdbid = parse_imdbid(line)
        if imdbid:
            return imdbid
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


def is_dir(path):
    "Returns true if path/str is an existing directory"
    if not path:
        return False
    if isinstance(path, Path):
        return path.is_dir() and path.exists()
    if isinstance(path, str):
        return os.path.isdir(path) and os.path.exists(path)
    return False


def is_file(path):
    "Returns true if path/str is an existing file"
    if not path:
        return False
    if isinstance(path, Path):
        return path.is_file() and path.exists()
    if isinstance(path, str):
        return os.path.isfile(path) and os.path.exists(path)
    return False


def str_is_vid_file(string):
    "Returns true if string looks like a vid file"
    return any(ext in string for ext in video_extensions())


def is_vid_file(string):
    "Returns true if string is an existing vid file"
    return is_file(string) and str_is_vid_file(string)


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


def remove_chars_from_string(string, char_list=[]):
    return string.translate({ord(i): None for i in char_list})


def check_string_similarity(string1, string2, remove_chars=[]):
    if remove_chars:
        string1 = remove_chars_from_string(string1, remove_chars)
        string2 = remove_chars_from_string(string2, remove_chars)
    return difflib.SequenceMatcher(None, string1, string2).ratio()
