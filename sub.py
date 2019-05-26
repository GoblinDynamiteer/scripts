#!/usr/bin/env python3

import argparse
import difflib
from enum import IntEnum
from pathlib import Path

import run
import util_movie
import util_tv
import util
from printing import cstr


class SubtitleMediaType(IntEnum):
    Episode = 0
    Movie = 1
    Unknown = 2


class Subtitle():
    def __init__(self, path):
        self.path = path
        self.filename = util.filename_of_path(path)
        self.type = SubtitleMediaType.Unknown
        self.matching_media = []

        self._determine_type()
        self._find_matching_media_files()

    def _determine_type(self):
        if util_movie.is_movie(self.filename):
            self.type = SubtitleMediaType.Movie
        elif util_tv.is_episode(self.filename):
            self.type = SubtitleMediaType.Episode
        else:
            self.type = SubtitleMediaType.Unknown

    def _find_matching_media_files(self):
        matches = []
        if self.type in [SubtitleMediaType.Movie, SubtitleMediaType.Unknown]:
            for mov_name in util_movie.list_all():
                value = check_similarity(mov_name, self.filename)
                matches.append((value, mov_name))
        if self.type in [SubtitleMediaType.Episode, SubtitleMediaType.Unknown]:
            for _, ep_name in util_tv.list_all_episodes():
                value = check_similarity(ep_name, self.filename)
                matches.append((value, ep_name))
        if matches:
            self.matching_media = sorted(
                matches, key=lambda tup: tup[0], reverse=True)[0:10]


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
    elif file_path.suffix.endswith('srt'):
        srt_filename = file_path.name
    else:
        print("no subtitle file to process..")
        exit()
    subtitle = Subtitle(srt_filename)
    print(subtitle.filename)
    print(subtitle.matching_media)
    # TODO: move srt to corret location
    # TODO: match movie/episode
