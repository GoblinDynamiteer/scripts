#!/usr/bin/env python3

import argparse
import difflib
from pathlib import Path

import run
import util_movie
from printing import cstr


def check_similarity(string1, string2):
    return difflib.SequenceMatcher(None, string1, string2).ratio()


def find_srt_filename_in_zip(zip_file_path):
    command = f"unzip -l {zip_file_path}"
    for line in run.local_command_get_output(command).split('\n'):
        if line.endswith('.srt'):
            return line.split(' ')[-1]
    return ""


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("file")
    ARGS = PARSER.parse_args()
    file_path = Path(ARGS.file)
    if not file_path.exists():
        print("passed file does not exists")
        exit()
    srt_filename = ""
    if file_path.suffix.endswith('zip'):
        srt_filename = find_srt_filename_in_zip(file_path)
        if not srt_filename:
            print("could not find srt in zip file!")
            exit()
        command = f"unzip -oj {file_path} {srt_filename}"
        if run.local_command(command, print_info=False):
            print(f"extracted {cstr(srt_filename, 154)}!")
    count = 0
    matches = []
    for mov_name in util_movie.list_all():
        value = check_similarity(mov_name, srt_filename)
        matches.append((value, mov_name))
    top_ten = sorted(matches, key=lambda tup: tup[0], reverse=True)[0:10]
    for match in top_ten:
        print(match)
    # TODO: move srt to corret location
    # TODO: match movie/episode
