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
        print(f'{CSTR("episode ops unimplemented", "orange")}')
    else:
        print(f'{CSTR("unkown type!", "orange")}')
