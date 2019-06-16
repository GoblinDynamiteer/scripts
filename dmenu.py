#!/usr/bin/env python3

import argparse
from tempfile import NamedTemporaryFile

import db_mov
import run
import util_movie
import util_tv
from config import ConfigurationManager

CFG = ConfigurationManager()
TV_HOME = CFG.get('path_tv')
MOV_HOME = CFG.get('path_film')

DMENU_COMMAND = (r"dmenu -i -fn 'Ubuntu Mono:bold:pixelsize=28' -nb '#1e1e1e' "
                 r"-sf '#1e1e1e' -sb '#C54500' -nf '#F4800d'")

MOVIE_PLAYER = 'mpv --fs'


def get_dmenu_selection(dmenu_items: list, lines=20):
    command = DMENU_COMMAND + f' -l {lines}' if lines else DMENU_COMMAND
    temp_file = NamedTemporaryFile()
    with open(temp_file.name, 'w') as dmenu_file:
        dmenu_file.write('\n'.join(dmenu_items))
    return run.local_command_get_output(
        f'cat {dmenu_file.name} | {command}')


def dmenu_play_episode():
    print('generating dmenu options...')
    files = []
    for _, _file in util_tv.list_all_episodes():
        files.append(_file)
    selection = get_dmenu_selection(files).replace('\n', '')
    print(f"starting tv episode {selection}, please wait...")
    file_path = util_tv.get_full_path_of_episode_filename(selection)
    if file_path:
        run.local_command(f'{MOVIE_PLAYER} "{file_path}"')


def dmenu_play_movie():
    mov_items = list(db_mov.MovieDatabase().all_movies())
    selection = get_dmenu_selection(mov_items).replace('\n', '')
    file_path = util_movie.get_full_path_of_movie_filename(selection)
    if file_path:
        run.local_command(f'{MOVIE_PLAYER} "{file_path}"')


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='dmenu generator')
    PARSER.add_argument('dmenu_op', type=str,
                        help='dmenu operation', choices=['play_ep', 'play_movie'])
    ARGS = PARSER.parse_args()
    if ARGS.dmenu_op == 'play_ep':
        dmenu_play_episode()
    elif ARGS.dmenu_op == 'play_movie':
        dmenu_play_movie()
