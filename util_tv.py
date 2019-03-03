#!/usr/bin/env python3.6

''' Various tv show/episode helper/utility functions '''

import os
import re

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


def parse_season_episode(episode_filename: str):
    match = re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', episode_filename)
    if match:
        se_string = match.group().lower()
        se_list = se_string.replace('s', '').split('e')
        season = int(se_list[0])
        episode = int(se_list[1])
        return (season, episode)
    return (None, None)


def parse_season(episode_filename: str):
    season, _ = parse_season_episode(episode_filename)
    return season


def is_episode(string: str):
    "Try to determine if a string is an episode name"
    season, episode = parse_season_episode(string)
    return season and episode


def guess_show_name_from_episode_name(episode_filename: str):
    "Try to determine the Show name from episode name"
    match = re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', episode_filename)
    if match:
        se_string = match.group()
        show_name = episode_filename.split(se_string)[0]
        return show_name.replace('.', ' ').strip()
    return None


def determine_show_from_episode_name(episode_filename: str):
    "Match existing show from episode name"
    guessed_show = guess_show_name_from_episode_name(episode_filename)
    matched_shows = [s for s in list_all_shows() if
                     guessed_show.lower() in s.lower()]
    if len(matched_shows) > 1:
        matched_shows = [
            s for s in matched_shows if guessed_show.lower() == s.lower()]
    try:
        return matched_shows[0]
    except IndexError:
        return None
