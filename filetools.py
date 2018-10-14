#!/usr/bin/env python3.6

''' File tools '''

import platform
import os
import re
from datetime import datetime
from shutil import copy2
import movie as movie_tools
import config
import str_o

PRINT = str_o.PrintClass(os.path.basename(__file__))
CONFIG = config.ConfigurationManager()


def get_creation_date(path_to_file_or_folder, convert=False):
    if platform.system() == 'Linux':
        return None
    if platform.system() == 'Windows':
        ret_time = os.path.getctime(path_to_file_or_folder)
        ret_time.replace(microsecond=0)
        return ret_time if convert is False \
            else datetime.fromtimestamp(ret_time)


def create_nfo(full_path, imdb, nfo_type, replace=False):
    if nfo_type == "movie":
        file_string = "movie.nfo"
    elif nfo_type == "tv":
        file_string = "tvshow.nfo"
    else:
        PRINT.error("wrong type for create_nfo: {}".format(type))
    nfo_path = os.path.join(full_path, file_string)
    if not os.path.isfile(nfo_path) or (os.path.isfile(nfo_path) and replace):
        try:
            with open(nfo_path, 'w') as newfile:
                newfile.write(imdb)
            return True
        except:
            PRINT.warning("could not create nfo: {}".format(full_path))
            return False
    else:
        PRINT.warning(
            "nfo already exists: {}, not replacing".format(full_path))
        return True


def is_file_empty(full_path):
    try:
        if os.stat(full_path).st_size is 0:
            return True
    except:
        PRINT.warning(
            "is_file_empty: could not check file {}".format(full_path))
        return False


def backup_file(src_full_path, dest_dir_full_path):
    now = datetime.now().strftime("%Y-%m-%d-%H%M")
    dest = os.path.join(dest_dir_full_path, now)
    try:
        if not os.path.exists(dest):
            os.makedirs(dest)
        copy2(src_full_path, dest)
        return True
    except:
        PRINT.warning(
            "backup_file: could not backup file: {}".format(src_full_path))
        PRINT.warning("backup_file: make sure to run scripts as sudo!")
        return False


def copy_dbs_to_webserver(tv_or_db):
    htdoc_loc = CONFIG.get_setting("path", "webserver")
    db = None
    if tv_or_db == "tv":
        db = CONFIG.get_setting("path", "tvdb")
    if tv_or_db == "movie":
        db = CONFIG.get_setting("path", "movdb")
    if db:
        copy2(db, htdoc_loc)
        PRINT.info("copied  to webserver htdocs: {}".format(db))
    else:
        PRINT.warning("could not copy to htdocs!")


def _type_points(folder):
    folder = folder.replace(' ', '.')
    folder = folder.replace('.-.', '-')
    folder = movie_tools.remove_extras_from_folder(folder)
    regex = {'season': r'\.[Ss]\d{2}\.', 'episode': r"\.[Ss]\d{2}[Ee]\d{2}",
             'movie': r"\.\d{4}\.\d{3,4}p\."}
    points = {'season': 0, 'episode': 0, 'movie': 0}
    for key in regex:
        if _is_regex_match(regex[key], folder):
            points[key] += 1
    return points


def is_existing_folder(path):
    return os.path.isdir(path)


def is_existing_file(path):
    return os.path.isfile(path)


def get_file(path, file_or_extension, full_path=False):
    if not os.path.exists(path):
        PRINT.warning(
            f"{path} does not exist! tried checking: {file_or_extension}")
        return None
    for file in os.listdir(path):
        if file.endswith(file_or_extension):
            return os.path.join(path, str(file)) if full_path else str(file)
    return None


def get_vid_file(path, full_path=False):
    for ext in ["mkv", "avi", "mp4"]:
        vid = get_file(path, ext, full_path=full_path)
        if vid:
            return vid
    return None


def _is_regex_match(regex, string):
    rgx = re.compile(regex)
    match = re.search(rgx, string)
    if match:
        return True
    return False


def guess_folder_type(folder):
    points = _type_points(folder)
    max_key = 0
    winner_key = None
    for key in points:
        if points[key] > max_key:
            max_key = points[key]
            winner_key = key
    return winner_key


def fix_invalid_folder_or_file_name(string):
    string = string.replace(' ', '.')
    string = string.replace('.-.', '-')
    string = re.sub("blu-ray", "BluRay", string, flags=re.I)
    if string.endswith('-'):
        string = string[:-1]
    return string
