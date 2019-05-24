#!/usr/bin/env python3

import argparse
from pathlib import Path

import run
from printing import cstr

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
    if file_path.suffix.endswith('zip'):
        srt_filename = find_srt_filename_in_zip(file_path)
        command = f"unzip -oj {file_path} {srt_filename}"
        if run.local_command(command, print_info=False):
            print(f"extracted {cstr(srt_filename, 154)}!")
    #TODO: move srt to corret location
    #TODO: match movie/episode
        