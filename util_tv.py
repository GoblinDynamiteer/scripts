#!/usr/bin/env python3.6

''' Various tv show/episode helper/utility functions '''

import os

from config import ConfigurationManager
import util

CFG = ConfigurationManager()
SHOW_DIR = CFG.get('path_tv')


def list_all_shows() -> list:
    '''Returns a list of all current tv show folders'''
    return [show for show in os.listdir(SHOW_DIR)
            if os.path.isdir(os.path.join(SHOW_DIR, show))]


def list_all_episodes():
    '''Returns a list of all current tv show files'''
    show_paths = [os.path.join(SHOW_DIR, sp) for sp in list_all_shows()]
    season_paths = [os.path.join(show, season)
                    for show in show_paths for season in os.listdir(show) if
                    season.upper().startswith('S')]
    for season_path in season_paths:
        for file_name in os.listdir(season_path):
            if any(file_name.endswith(ext) for ext in util.video_extensions()):
                yield (season_path, file_name) # return full path and filename
