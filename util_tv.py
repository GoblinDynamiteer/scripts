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
    match = re.search(r'[Ss]\d{1,2}', episode_filename)
    if match:
        s_string = match.group().lower().replace('s', '')
        return (int(s_string), None)
    return (None, None)


def parse_season(episode_filename: str):
    season, _ = parse_season_episode(episode_filename)
    return season


def is_episode(string: str):
    "Try to determine if a string is an episode name"
    season, episode = parse_season_episode(string)
    return season is not None and episode is not None


def is_season(string: str):
    "Try to determine if a string is a season folder"
    season, episode = parse_season_episode(string)
    return season is not None and episode is None


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


def season_num_to_str(season, upper_case=True) -> str:
    'return the str rep of a season number, eg 3 -> S03'
    ret_str = ''
    if isinstance(season, int):
        if season < 0:
            return ret_str
        ret_str = f's{season:02d}'
    if isinstance(season, str):
        if season.isnumeric():
            ret_str = f's{int(season):02d}'
    if upper_case:
        return ret_str.upper()
    return ret_str.lower()


def episode_num_to_str(episode, upper_case=True) -> str:
    'return the str rep of a episode number, eg 12 -> E12'
    ret_str = season_num_to_str(episode).lower().replace('s', 'e')
    if upper_case:
        return ret_str.upper()
    return ret_str.lower()


def season_episode_str_list(season, episode_start, episode_end) -> list:
    'returns a list of SXXEXX strings'
    season_str, ep_start_str, ep_end_str = (season_num_to_str(season), episode_num_to_str(
        episode_start), episode_num_to_str(episode_end))
    if not season_str or not ep_start_str or not ep_end_str:
        return []
    steps = -1 if int(episode_end) < int(episode_start) else 1
    return [f'{season_str}E{e:02d}' for e in range(episode_start, episode_end+steps, steps)]
