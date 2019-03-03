#!/usr/bin/python3.6

'Extract/move releases'

import argparse
import os
import shutil

import config
import run
import util
import util_movie
import util_tv
from printing import to_color_str as CSTR

OPJ = os.path.join
CFG = config.ConfigurationManager()


def _find_rar(source_dir):
    rar_file = [f for f in os.listdir(
        source_dir) if f.endswith('.rar')]
    if len(rar_file) > 1:
        print("more than 1 rar!")
        return None
    full_path = OPJ(os.getcwd(), ARGS.source, rar_file[0])
    if util.is_file(full_path):
        return full_path
    return None


def _movie_dest(source_dir):
    letter = util_movie.determine_letter(source_dir)
    return OPJ(CFG.get('path_film'), letter, source_dir)


def _episode_dest(source_dir):
    show = util_tv.determine_show_from_episode_name(source_dir)
    if not show:
        return None
    path = OPJ(CFG.get('path_tv'), show)
    if not os.path.exists(path):
        print(path)
        return None
    season = util_tv.parse_season(source_dir)
    if not season:
        return None
    return OPJ(path, f'{season:02d}')


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='extractor')
    PARSER.add_argument('source', type=str, help='item to process')
    ARGS = PARSER.parse_args()

    if util_movie.is_movie(ARGS.source):
        if util.is_dir(ARGS.source):
            REMOVE_DIR = run.extract(_find_rar(ARGS.source), _movie_dest(
                ARGS.source), create_dirs=True)
            if REMOVE_DIR:
                shutil.rmtree(ARGS.source)
                print(f'removed {CSTR(ARGS.source, "orange")}')
        else:
            print(f'{CSTR("move movie file unimplemented", "orange")}')
    elif util_tv.is_episode(ARGS.source):
        if util.is_dir(ARGS.source):
            print(f'{CSTR("episode dir ops unimplemented", "orange")}')
        else:
            run.move_file(ARGS.source, _episode_dest(ARGS.source))
    else:
        print(f'{CSTR("unkown type!", "orange")}')
