#!/usr/bin/env python3

import argparse
from enum import IntEnum
from pathlib import Path

import run
import util_movie
import util_tv
import util
from printing import cstr, pcstr
import config


class SubtitleMediaType(IntEnum):
    Episode = 0
    Movie = 1
    Unknown = 2


class Language(IntEnum):
    English = 0
    Swedish = 1
    Unknown = 2


class Subtitle():
    def __init__(self, path):
        self.path = path
        self.filename = util.filename_of_path(path)
        self.type = SubtitleMediaType.Unknown
        self.matching_media = []
        self.language = Language.Unknown
        self.contents = []

        with open(self.filename, encoding='latin1', errors='replace') as subtitle_file:
            self.contents = subtitle_file.read()

        self._determine_type()
        self._determine_language()
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
                guessed_movie_name = util_movie.determine_title(self.filename)
                value = util.check_string_similarity(mov_name, self.filename)
                if guessed_movie_name and guessed_movie_name.replace(" ", ".") in mov_name:
                    value += 0.5
                matches.append((value, mov_name))
        if self.type in [SubtitleMediaType.Episode, SubtitleMediaType.Unknown]:
            guessed_show = util_tv.guess_show_name_from_episode_name(
                self.filename)
            for path, ep_name in util_tv.list_all_episodes():
                if guessed_show and guessed_show.lower() not in str(path).lower():
                    continue
                value = util.check_string_similarity(ep_name, self.filename)
                se_str = util_tv.parse_season_episode_str(self.filename)
                if se_str and se_str.lower() in ep_name.lower():
                    value += 0.5
                matches.append((value, ep_name))
        if matches:
            self.matching_media = sorted(
                matches, key=lambda tup: tup[0], reverse=True)[0:10]

    def _determine_language(self):
        cfg = config.ConfigurationManager()
        path_txt = Path(cfg.get('path_scripts')) / 'txt'
        langs = {'en': {'points': 0}, 'sv': {'points': 0}}
        for lang in langs:
            with open(path_txt / f'sub_words_{lang}.txt', encoding='utf-8') as word_file:
                for word in word_file.read().split('\n'):
                    langs[lang]['points'] += self.contents.count(f' {word} ')
        self.language = Language.English if langs['en']['points'] > langs['sv']['points'] else Language.Swedish

    def best_match(self):
        return self.matching_media[0][1]


def find_srt_filenames_in_zip(zip_file_path):
    command = f"unzip -l {zip_file_path}"
    srt_files = []
    for line in run.local_command_get_output(command).split('\n'):
        if line.endswith('.srt'):
            srt_files.append(line.split(' ')[-1])
    return srt_files


def handle_srt(srt_file):
    subtitle = Subtitle(srt_file)
    print(f"processed file: {cstr(subtitle.filename, 154)}")
    print(f" - guessed match: {cstr(subtitle.best_match(), 'lgreen')}")
    print(f" - guessed language: {cstr(subtitle.language, 'lgreen')}")
    print(f" - guessed type: {cstr(subtitle.type.name, 'lgreen')}")
    lang_str = 'en' if subtitle.language == Language.English else 'sv'
    subtitle_dest = None
    if subtitle.type == SubtitleMediaType.Episode:
        episode_file = util_tv.get_full_path_of_episode_filename(
            subtitle.matching_media[0][1])
        subtitle_dest = episode_file.replace('.mkv', f'.{lang_str}.srt')
    # Handle unknown type as movie, TODO: check both tv/mov
    elif subtitle.type == SubtitleMediaType.Movie or subtitle.type == SubtitleMediaType.Unknown:
        movie_file = util_movie.get_full_path_to_movie_filename(
            subtitle.matching_media[0][1])
        subtitle_dest = movie_file.replace('.mkv', f'.{lang_str}.srt')
    if not subtitle_dest:
        pcstr("could not determine destination!", "red")
        return
    print(f" - destination:\n   {cstr(subtitle_dest, 'purple')}")
    if input("move file to destination?: ").lower() not in ['y', 'yes']:
        return
    if not run.rename_file(srt_file, subtitle_dest):
        pcstr("failed to move file", 'red')
        return
    pcstr("moved file!", 'lgreen')


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("file")
    ARGS = PARSER.parse_args()
    file_path = Path(ARGS.file)
    if not file_path.exists():
        print("passed file does not exists")
        exit()
    srt_filenames = []
    if file_path.suffix.endswith('zip'):
        srt_filenames = find_srt_filenames_in_zip(file_path)
        if not srt_filenames:
            print("could not find srt in zip file!")
            exit()
        for srt_filename in srt_filenames:
            command = f"unzip -oj {file_path} {srt_filename}"
            if run.local_command(command, print_info=False):
                print(f"extracted {cstr(srt_filename, 154)}!")
    elif file_path.suffix.endswith('srt'):
        srt_filenames = [file_path.name]
    else:
        print("no subtitle file to process..")
        exit()
    [handle_srt(srt) for srt in srt_filenames]
