#!/usr/bin/env python3.6

''' Personal script for extracting/moving scene releases of
    movies/tv to correct dir '''

import argparse
import os
import re
import shutil
import subprocess
import str_i
import str_o
import movie
import filetools
import tvshow
import config

PRINT = str_o.PrintClass(os.path.basename(__file__))
INPUT = str_i
CONFIG = config.ConfigurationManager()
SCRIPT = os.path.basename(__file__)
PARSER = argparse.ArgumentParser(description='TV/Movie UnRarer')
PARSER.add_argument('dir', type=str, help='Path to movie or tv source')
ARGS = PARSER.parse_args()
CWD = os.getcwd()

if ARGS.dir == "all":
    ITEMS = os.listdir(CWD)
else:
    ITEMS = [ARGS.dir]
ITEM_COUNT = 1


def check_valid_source_folder(source_path):
    if not os.path.exists(source_path):
        PRINT.error(f"[{source_path}] does not exist!")
        return False
    return True


def _generate_mv_command(src, dest):
    return "mv {} {}".format(src.replace(" ", "\\ "), dest)


def move_mov(file_name_s, folder_name=None):
    src = os.path.join(CWD, file_name_s)
    if folder_name:
        folder = folder_name
    else:
        folder = file_name_s.replace(".mkv", "")
    if not check_valid_source_folder(src):
        return
    folder = filetools.fix_invalid_folder_or_file_name(folder)
    file_dest = filetools.fix_invalid_folder_or_file_name(file_name_s)
    dest = os.path.join(movie.root_path(),
                        movie.determine_letter(file_name_s), folder, file_dest)
    PRINT.info(f'move [{file_name_s}]')
    PRINT.info(f'---> [{dest}]')
    if str_i.yes_no("Proceed with move?", script_name=None):
        if not os.path.exists(dest):
            os.makedirs(dest)
        command = _generate_mv_command(src, dest)
        subprocess.call(command, shell=True)
        PRINT.info("File moved!")


def move_ep(file_name_s):
    src = os.path.join(CWD, file_name_s)
    dest = tvshow.show_season_path_from_ep_s(file_name_s)
    PRINT.info(f'move [{file_name_s}]')
    PRINT.info(f'---> [{dest}]')
    if INPUT.yes_no("Proceed with move?", script_name=None):
        os.system("mv {} \"{}\"".format(src, dest))
        PRINT.info("File moved!")


def extract_ep(folder):
    src = os.path.join(CWD, folder)
    dest = tvshow.show_season_path_from_ep_s(folder)
    rar_file = filetools.get_file(src, "rar")
    if rar_file is None:
        PRINT.warning(f"could not find .rar in [{folder}]")
        return
    src_rar = os.path.join(src, rar_file)
    PRINT.info(f"found rar-file: [{rar_file}]")
    PRINT.info(f'extract [{folder}]')
    PRINT.info(f'------> [{dest}]')
    if INPUT.yes_no("proceed with extraction?", script_name=None):
        os.system("unrar e \"{}\" \"{}\"".format(src_rar, dest))
        PRINT.info("done!")


def extract_mov(folder):
    source_path = os.path.join(CWD, folder)
    if not check_valid_source_folder(source_path):
        return
    dest_path = os.path.join(
        movie.root_path(), movie.determine_letter(folder), folder)
    rar_file = filetools.get_file(source_path, "rar")
    nfo_file = filetools.get_file(source_path, "nfo")
    if rar_file is None:
        PRINT.warning(f"could not find .rar in [{folder}]")
        return
    source_file = os.path.join(source_path, rar_file)
    PRINT.info("Found rar-file: [ {} ]".format(os.path.basename(source_file)))
    if INPUT.yes_no("Extract to: [ {} ]".format(dest_path),
                    script_name=os.path.basename(__file__)):
        os.system("unrar e \"{}\" \"{}\"".format(source_file, dest_path))
    else:
        return
    if nfo_file is not None:
        pattern = re.compile("tt\d{2,}")
        nfo_file = os.path.join(source_path, nfo_file)
        with open(nfo_file, 'r', encoding='utf-8', errors='ignore') as nfo:
            for line in nfo:
                match = re.search(pattern, line)
                if match:
                    imdb_id = match[0]
                    PRINT.info(
                        "Found IMDb-id in nfo-file: [ {} ]".format(imdb_id))
                    filetools.create_nfo(dest_path, "http://www.imdb.com/title/{}"
                                         .format(imdb_id), "movie")


def extract_season(folder):
    source_path = os.path.join(CWD, folder)
    if not check_valid_source_folder(source_path):
        return
    dest_path = os.path.join(
        tvshow.root_path(), tvshow.guess_ds_folder(folder))
    if os.path.exists(dest_path):
        PRINT.info("[ {} ] exists!".format(dest_path))
    season = tvshow.guess_season(folder)
    PRINT.info("guessed season: {}".format(season))
    dest_path = os.path.join(dest_path, f"S{season:02d}")
    if INPUT.yes_no("Extract to: {}".format(dest_path), script_name=SCRIPT):
        move_subs(source_path, folder)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        print("unrar e -r \"{}*.rar\" \"{}\"".format(source_path, dest_path))
        os.system("unrar e -r \"{}*.rar\" \"{}\"".format(source_path, dest_path))


def move_subs(full_source_path, folder):
    misc_root = CONFIG.get_setting("path", "misc")
    dest_path = os.path.join(misc_root, "Subtitles", folder)
    found_subs = False
    if not os.path.exists(dest_path):
        PRINT.info("Creating {}".format(dest_path))
        os.makedirs(dest_path)
    for root, _, files in os.walk(full_source_path):
        for file in files:
            if file.endswith(".subs.rar") or file.endswith(".subs.sfv"):
                if not found_subs:
                    found_subs = True
                    PRINT.info("Found subtitles - will move before extract")
                file_to_move = os.path.join(root, file)
                PRINT.info("Moving {} to subs storage".format(file))
                shutil.move(file_to_move, dest_path)


for item in ITEMS:
    PRINT.info(f"processing {ITEM_COUNT} of {len(ITEMS)}")
    dir_name = movie.remove_extras_from_folder(item)
    full_path = os.path.join(CWD, item)
    guessed_type = filetools.guess_folder_type(dir_name)
    if guessed_type == 'movie':
        PRINT.info("guessed movie!")
        if filetools.is_existing_file(full_path) and \
            (item.endswith(".mkv") or item.endswith(".mp4") or
             item.endswith(".avi")):
            PRINT.info("is video file (not rared)")
            move_mov(item)
        elif filetools.is_existing_folder(full_path):
            file_path = filetools.get_vid_file(full_path, full_path=True)
            if file_path:
                file_name = filetools.get_vid_file(full_path, full_path=False)
                size_bytes = os.path.getsize(file_path)
                size_mbytes = size_bytes / 1024.0 / 1024.0
                if size_mbytes > 200:
                    os.system(f"mv \"{file_path}\" \"{CWD}\"")
                    PRINT.info("moving to cwd...")
                    move_mov(file_name, folder_name=item)
            else:
                extract_mov(str(item))
    elif guessed_type == 'episode':
        PRINT.info("guessed tv episode!")
        if filetools.is_existing_file(full_path) and \
            (item.endswith(".mkv") or item.endswith(".mp4") or
             item.endswith(".avi")):
            PRINT.info("is video file (not rared)")
            move_ep(item)
        elif filetools.is_existing_folder(full_path):
            file_path = filetools.get_vid_file(full_path, full_path=True)
            if file_path:
                file_name = filetools.get_vid_file(full_path, full_path=False)
                size_bytes = os.path.getsize(file_path)
                size_mbytes = size_bytes / 1024.0 / 1024.0
                if size_mbytes > 200:
                    os.system(f"mv \"{file_path}\" \"{CWD}\"")
                    PRINT.info("moving to cwd...")
                    move_ep(file_name)
            else:
                extract_ep(str(item))
    elif guessed_type == 'season':
        PRINT.info("guessed tv season!")
        extract_season(str(item))
    else:
        PRINT.error(f"Could not determine type of [{item}]")
    ITEM_COUNT += 1
