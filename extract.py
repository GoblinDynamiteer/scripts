#!/usr/bin/python3.6

'Extract/move releases'

import argparse
import glob
import os
import shutil
from pathlib import Path

import config
import run
import util
import util_movie
import util_tv
from printing import cstr

OPJ = os.path.join
CFG = config.ConfigurationManager()


def _find_rar(source_dir):
    rar_files = [f for f in os.listdir(
        source_dir) if f.endswith('.rar')]
    if len(rar_files) > 1:
        for rar_file in rar_files:
            if '01.rar' in rar_file:
                rar_files = [rar_file]
                break
    if len(rar_files) > 1:
        print("more than 1 rar!")
        return None
    full_path = OPJ(os.getcwd(), source_dir, rar_files[0])
    if util.is_file(full_path):
        return full_path
    return None


def _find_nfo(source_dir):
    nfo_files = [f for f in os.listdir(
        source_dir) if f.endswith('.nfo')]
    full_path = OPJ(os.getcwd(), ARGS.source, nfo_files[0])
    if util.is_file(full_path):
        return full_path
    return None


def _movie_dest(source_dir):
    letter = util_movie.determine_letter(source_dir)
    return OPJ(CFG.get('path_film'), letter, source_dir)


def _episode_dest(source_dir):
    show = util_tv.determine_show_from_episode_name(source_dir)
    if not show:
        print(f"could not determine show for {cstr(source_dir, 'lblue')}")
        show = util_tv.guess_show_name_from_episode_name(source_dir)
        if not show:
            return None
        print(f"guessing: {cstr(show, 'orange')}")
    path = OPJ(CFG.get('path_tv'), show)
    if not os.path.exists(path):
        print(f"{cstr(path, 'orange')} does not exist! will create")
        return None
    season = util_tv.parse_season(source_dir)
    if not season:
        print(f"could not determine season of {cstr(source_dir, 'orange')}")
        return None
    return OPJ(path, f'S{season:02d}')


def _handle_item(source_item):
    print(source_item)
    if util_movie.is_movie(source_item):
        if util.is_dir(source_item):
            nfo_loc = _find_nfo(source_item)
            rar_loc = _find_rar(source_item)
            if not rar_loc:
                exit()
            dest = _movie_dest(source_item)
            if not run.extract(rar_loc, dest, create_dirs=True):
                return  # extract failed
            if nfo_loc:
                util_movie.create_movie_nfo(
                    dest, util.parse_imdbid_from_file(nfo_loc))
            shutil.rmtree(source_item)
            print(f'removed {cstr(source_item, "orange")}')
        else:
            print(f'{cstr("move movie file unimplemented", "orange")}')
    elif util_tv.is_episode(source_item):
        if util.is_dir(source_item):
            rar_loc = _find_rar(source_item)
            dest = _episode_dest(source_item)
            if not dest:
                print(f"could not determine destination for {source_item}")
                return
            if not run.extract(rar_loc, dest, create_dirs=True):
                return  # extract failed
        else:
            run.move_file(source_item, _episode_dest(
                source_item), create_dirs=True)
    elif util_tv.is_season(source_item):
        if util.is_dir(source_item):
            os.chdir(source_item)
            for item in os.listdir('.'):
                _handle_item(str(item))
            print(
                f'done! please manually remove {cstr(source_item, "orange")}')
    else:
        print(f'{cstr("unkown type!", "orange")}')


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='extractor')
    PARSER.add_argument('source', type=str, help='item(s) to process')
    ARGS, _ = PARSER.parse_known_args()

    if '*' in ARGS.source:
        items = glob.glob(ARGS.source)
        [_handle_item(i) for i in items]
    else:
        _handle_item(ARGS.source)
