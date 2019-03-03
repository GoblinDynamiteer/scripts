#!/usr/bin/python3.6

'Extract/move releases'

import argparse
import glob
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
    return OPJ(path, f'S{season:02d}')


def _handle_item(source_item):
    if util_movie.is_movie(source_item):
        if util.is_dir(source_item):
            remove_dir = run.extract(_find_rar(source_item), _movie_dest(
                source_item), create_dirs=True)
            if remove_dir:
                shutil.rmtree(source_item)
                print(f'removed {CSTR(source_item, "orange")}')
        else:
            print(f'{CSTR("move movie file unimplemented", "orange")}')
    elif util_tv.is_episode(source_item):
        if util.is_dir(source_item):
            print(f'{CSTR("episode dir ops unimplemented", "orange")}')
        else:
            run.move_file(source_item, _episode_dest(source_item))
    else:
        print(f'{CSTR("unkown type!", "orange")}')


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='extractor')
    PARSER.add_argument('source', type=str, help='item(s) to process')
    ARGS, _ = PARSER.parse_known_args()

    if '*' in ARGS.source:
        items = glob.glob(ARGS.source)
        [_handle_item(i) for i in items]
    else:
        _handle_item(ARGS.source)
