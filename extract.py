#!/usr/bin/python3


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
from printout import cstr, pfcs

OPJ = os.path.join
CFG = config.ConfigurationManager()


def validate_path(path):
    if isinstance(path, str):
        path = Path(path)
    if not isinstance(path, Path):
        print(f"invalid path: {path}")
        return None
    path = path.resolve()
    if not path.exists():
        print(f"path does not exist: {str(path)}")
        return None
    return path


def find_rar_in_path(path):
    path = validate_path(path)
    if not path:
        return None
    rar_files = list(path.glob("**/*.rar"))
    if len(rar_files) > 1:
        for rar_file in rar_files:
            if rar_file.name.endswith("01.rar"):
                return rar_file
    try:
        return rar_files[0]
    except IndexError:
        return None


def find_mkv_in_path(path):
    path = validate_path(path)
    if not path:
        return None
    skip_list = ["Sample", "sample"]
    found_files = path.glob("**/*.mkv")
    mkv_files = []
    for f in found_files:
        if any([x in str(f) for x in skip_list]):
            continue
        mkv_files.append(f)
    if len(mkv_files) > 1:
        return None  # TODO: determine which file is valid
    try:
        return mkv_files[0]
    except IndexError:
        return None


def find_nfo_file_in_path(path):
    path = validate_path(path)
    if not path:
        return None
    try:
        return list(path.glob("**/*.nfo"))[0]  # TODO: validate nfo file?
    except IndexError:
        return None


def determine_movie_destination(movie_name):
    letter = util_movie.determine_letter(movie_name)
    if isinstance(movie_name, Path):
        movie_name = movie_name.name
    return OPJ(CFG.get('path_film'), letter, movie_name)


def determine_episode_destination(episode_name):
    show = util_tv.determine_show_from_episode_name(episode_name)
    if not show:
        print(f"could not determine show for {cstr(episode_name, 'lblue')}")
        show = util_tv.guess_show_name_from_episode_name(episode_name)
        if not show:
            return None
        print(f"guessing: {cstr(show, 'orange')}")
    path = OPJ(CFG.get('path_tv'), show)
    if not os.path.exists(path):
        print(f"{cstr(path, 'orange')} does not exist! will create")
    season = util_tv.parse_season(episode_name)
    if not season:
        print(f"could not determine season of {cstr(episode_name, 'orange')}")
        return None
    return OPJ(path, f'S{season:02d}')


def process_movie_dir(movie_dir_source: Path):
    name = movie_dir_source.name
    pfcs(f"processing: i[{name}] as type b[movie dir]")
    nfo_loc = find_nfo_file_in_path(movie_dir_source)
    rar_loc = find_rar_in_path(movie_dir_source)
    mkv_loc = find_mkv_in_path(movie_dir_source)
    if not rar_loc and not mkv_loc:
        pfcs(f"could e[not] find item to process in w[{movie_dir_source}]!")
        return
    if rar_loc and mkv_loc:
        pfcs(f"found e[both] rar and mkv in w[{movie_dir_source}]!")
        return
    pfcs(f"found file: i[{mkv_loc or rar_loc}]")
    dest = determine_movie_destination(name)
    pfcs(f"destination: i[{dest}]")
    if rar_loc:
        if not run.extract(rar_loc, dest, create_dirs=True):
            return  # extract failed
    if mkv_loc:
        run.move_file(mkv_loc, dest, create_dirs=True)
    if nfo_loc:
        imdb_id = util.parse_imdbid_from_file(nfo_loc)
        if imdb_id:
            print(
                f"found imdb-id: {cstr(imdb_id, 154)}, will create movie.nfo")
            util_movie.create_movie_nfo(dest, imdb_id)
    shutil.rmtree(movie_dir_source)
    print(f'removed {cstr(movie_dir_source, "orange")}')


def process_movie_file(movie_file_path):
    movie_path = validate_path(movie_file_path)
    if not movie_file_path:
        return
    if not movie_file_path.is_file():
        print(f"path {movie_file_path.name} is not a file!")
        return
    pfcs(f"processing: i[{movie_file_path.name}] as type b[movie file]")
    if not movie_file_path.suffix in util.video_extensions():
        pfcs(f"could not determine destination for w[{movie_file_path.name}]")
        return
    directory = str(movie_file_path.name).replace(movie_file_path.suffix, "")
    dest = determine_movie_destination(directory)
    pfcs(f"destination: i[{dest}]")
    run.move_file(movie_file_path, dest, create_dirs=True)


def process_movie(movie_path: Path):
    movie_path = validate_path(movie_path)
    if not movie_path:
        return
    if movie_path.is_dir():
        process_movie_dir(movie_path)
    else:
        process_movie_file(movie_path)


def process_episode(ep_path: Path):
    ep_path = validate_path(ep_path)
    if not ep_path:
        return
    dest = determine_episode_destination(ep_path.name)
    if not dest:
        pfcs(f"could not determine destination for w[{ep_path}]")
        return
    if ep_path.is_dir():
        pfcs(f"processing: i[{ep_path.name}] as type b[episode dir]")
        rar_loc = find_rar_in_path(ep_path)
        if not run.extract(rar_loc, dest, create_dirs=True):
            return  # extract failed
        return
    pfcs(f"processing: i[{ep_path.name}] as type b[episode file]")
    run.move_file(ep_path, dest, create_dirs=True)


def extract_item(source_item_path):
    source_item_path = validate_path(source_item_path)
    if not source_item_path:
        return
    name = source_item_path.name
    if util_movie.is_movie(name):
        process_movie(source_item_path)
    elif util_tv.is_episode(name):
        process_episode(source_item_path)
    elif util_tv.is_season(name):
        if source_item_path.is_dir():
            pfcs(f"processing: i[{name}] as type b[season dir]")
            for item in source_item_path.iterdir():
                extract_item(item)
            pfcs(f"g[done!] please remove w[{name}] manually.")
    else:
        pfcs(f"could not determine type of w[{name}]")


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='extractor')
    PARSER.add_argument('source', type=str, help='item(s) to process')
    ARGS, _ = PARSER.parse_known_args()
    CURRENT_DIR = Path.cwd()
    if '*' in ARGS.source:
        items = glob.glob(ARGS.source)
        [extract_item(CURRENT_DIR / i) for i in items]
    else:
        extract_item(Path(ARGS.source))
