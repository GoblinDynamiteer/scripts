#!/usr/bin/env python3

import argparse
import sys
from enum import IntEnum, Enum
from pathlib import Path
import operator
import tempfile
import zipfile

import requests
from bs4 import BeautifulSoup

import config
import run
import util
import util_movie
import util_tv
from printing import cstr, pcstr, pfcs, print_line, fcs


class SubtitleMediaType(IntEnum):
    Episode = 0
    Movie = 1
    Unknown = 2


class Language(IntEnum):
    English = 0
    Swedish = 1
    Unknown = 2
    Other = 3


class Subtitle():
    def __init__(self, path):
        self.path = path
        self.filename = util.filename_of_path(path)
        self.type = SubtitleMediaType.Unknown
        self.matching_media = []
        self.language = Language.Unknown
        self.contents = []

        with open(self.path, encoding='latin1', errors='replace') as subtitle_file:
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


class SubSceneSubtitle(util.BaseLog):
    BASE_URL = r"https://subscene.com"

    class SpanIndex(Enum):
        Language = 0
        Title = 1

    def __init__(self, soup, release_str, verbose=False):
        super().__init__(verbose)
        self.set_log_prefix("SUB_RESULT")
        self.soup = soup
        self.release = release_str
        self.verbose = verbose
        self.title = None
        self.url = None
        self.url_zip = None
        self.language = Language.Unknown
        self.parse_ok = True
        self.similarity = None
        self.hearing_impaired = False
        try:
            self._parse()
            title = self.title.replace(" ", ".")
            self.similarity = util.check_string_similarity(release_str, title)
            if release_str in title:
                self.similarity += 0.2  # boost
        except Exception as error:
            self.warn("parsing failed!")
            self.parse_ok = False

    def _parse(self):
        spans = self.soup.find("td", "a1").a.find_all("span")
        self.title = spans[self.SpanIndex.Title.value].text.strip()
        lang_str = spans[self.SpanIndex.Language.value].text.strip()
        if lang_str.lower() in ["english", "swedish"]:
            self.language = Language.Swedish if "swedish" in lang_str.lower() else Language.English
        else:
            self.language = Language.Other
        self.url = self.BASE_URL + self.soup.find("td", "a1").a.get("href")
        if self.language == Language.English:
            self.hearing_impaired = self.soup.find("td", "a41") is not None

    def download_and_unzip(self, file_dest=None):
        if file_dest is None:
            if self.language == Language.Swedish:
                ext = ".sv.zip"
            elif self.language == Language.English:
                ext = ".en.zip"
            else:
                ext = ".zip"
            file_dest = Path(tempfile.gettempdir()) / (self.release + ext)
        res = requests.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")
        zip_url = soup.find("div", "download").a.get("href")
        if self.url_zip is None:
            self.url_zip = self.BASE_URL + zip_url
        self.log("downloading", info_str_line2=cstr(self.url_zip, "orange"))
        if not run.wget(self.url_zip, file_dest, debug_print=self.verbose):
            self.error("download failed!")
            return None
        self.log("downloaded to", cstr(file_dest, "lgreen"))
        extracted_srts = []
        with zipfile.ZipFile(file_dest) as zf:
            for i in zf.infolist():
                if i.filename.endswith(".srt"):
                    extracted_srts.append(zf.extract(
                        i, path=tempfile.gettempdir()))
        if len(extracted_srts) > 1:
            self.warn("found more than one srt in zip! using first")
        elif not extracted_srts:
            self.warn("could not extract any srt files!")
            return None
        extracted = Path(extracted_srts[0])
        self.log(f"extracted file:", cstr(extracted, "lgreen"))
        dest = file_dest.with_suffix(".srt")
        if not run.rename_file(extracted, dest):
            self.error("failed to rename extracted file!")
        self.log(f"renamed to:", cstr(dest, "lgreen"))
        return dest

    def print(self):
        print("Title:", cstr(self.title, "lgreen"))
        print("Lang:", cstr(self.language.name, "lgreen"))
        print("URL: ", cstr(self.url, "lgreen"))
        sim_color = "lgreen"
        if self.similarity < 1:
            sim_color = "lyellow"
        elif self.similarity < 0.7:
            sim_color = "orange"
        elif self.similarity < 0.5:
            sim_color = "red"
        print("Similarity:", cstr(self.similarity, sim_color))


class SubSceneSearchResult(util.BaseLog):
    BASE_URL = r"https://subscene.com"

    class MatchType(Enum):
        Exact = "Exact"
        TV = "TV-Series"
        Close = "Close"
        Popular = "Popular"

    def __init__(self, result_text, release_str, title, year, verbose=False):
        super().__init__(verbose)
        self.verbose = verbose
        self.set_log_prefix("RESULT")
        self.release = release_str
        self.title = title
        self.year = year
        self.log("init")
        self.soup = BeautifulSoup(result_text, "html.parser")
        self.best_match_url = self._parse_best_match_url()
        self.subs = []
        if not self.best_match_url:
            self.error(f"could not get url for {title}")
        else:
            self.subs = self._parse_subs()

    def get_best(self, language, skip_hi=True):
        for sub in self.subs:
            if sub.hearing_impaired and skip_hi:
                continue
            if sub.language == language:
                return sub
        return None

    def _parse_subs(self):
        url = self.BASE_URL + self.best_match_url
        res = requests.get(url)
        if res.status_code != 200:
            self.error(f"got status code {res.status_code} for {url}")
            return []
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.find("table").tbody.find_all("tr")
        ret = []
        for row in rows:
            if row.td.a is not None:
                sub = SubSceneSubtitle(row, self.release, verbose=self.verbose)
                if not sub.parse_ok:
                    continue
                if sub.language == Language.Swedish or sub.language == Language.English:
                    ret.append(sub)
        if not ret:
            self.warn("no subtitles found!")
            return ret
        if self.verbose:
            for lang in [Language.Swedish, Language.English]:
                count = len([x for x in ret if x.language == lang])
                self.log(f"found {cstr(count, 'lgreen')} subs for {lang.name}")
        ret = sorted(ret, key=operator.attrgetter("similarity"), reverse=True)
        return ret

    def _parse_best_match_url(self):
        match_types = self.soup.find("div", "search-result").find_all("h2")
        for match_type in match_types:
            try:
                mt = self.MatchType(match_type.text)
                self.log(f"got MatchType: {mt.name}")
                if mt == self.MatchType.Exact:
                    items = match_type.findNext("ul").findAll("a")
                    return self._get_best_match_url(items)
            except Exception as error:
                self.log(f"could not parse MatchType:"
                         f" {cstr(match_type.text, 'red')}")
        return None

    def _get_best_match_url(self, items: list):
        url = None
        if not items:
            self.warn("no matches")
            return url
        if len(items) == 1:
            item = items[0]
            url = item.get("href")
            self.log(f"only one match: \"{item.text}\"")
        elif not self.year:
            # TODO: try to match title
            self.warn(f"year is not dermined! "
                      f"using first match: \"{item.text}\"")
            item = items[0]
            url = item.get("href")
        else:
            for item in items:
                if str(self.year) in item.text:
                    url = item.get("href")
                    self.log(f"found year {cstr(self.year, 'lgreen')} "
                             f"in \"{item.text}\"")
                    break
            else:
                item = items[0]
                self.warn(f"could not find {cstr(self.year, 'orange')} in matches! "
                          f"using first: \"{item.text}\"")
        self.log(f"using url: {cstr(url, 'lgreen')}")
        return url


class SubScene(util.BaseLog):
    URL_SEARCH = r"https://subscene.com/subtitles/searchbytitle"

    def __init__(self, search_str=None, verbose=False):
        super().__init__(verbose)
        self.set_log_prefix("SUBSCENE")
        self.search_str = search_str
        self.movie_title = util_movie.determine_title(search_str)
        self.movie_year = util_movie.parse_year(search_str)
        self.verbose = verbose
        self.log("init")
        if not util_movie.is_movie(search_str):
            raise ValueError("Search string has to be a movie"
                             "release (for now)")
            # TODO: handle tv episodes...
        self.log(f"parsed title: {self.movie_title}")
        if self.movie_year:
            self.log(f"parsed year: {self.movie_year}")
        else:
            self.log_warn("could not parse year!")
        self.result = None
        if self.search_str is not None:
            self.result = self.search()

    def search(self):
        if not self.search_str:
            self.log("no string set for searching...")
            return []
        self.log(f"searching for: {cstr(self.search_str, 'orange')}")
        return self._search_get_result()

    def _search_get_result(self):
        data = {"query": self.movie_title}
        res = requests.post(self.URL_SEARCH, data=data)
        if res.status_code != 200:
            self.log(f"failed search with query {cstr(data, 'orange')} "
                     f"got response: {cstr(res.status_code, 'red')}")
            return None
        return SubSceneSearchResult(res.text,
                                    self.search_str,
                                    self.movie_title,
                                    self.movie_year,
                                    verbose=self.verbose)


def find_srt_filenames_in_zip(zip_file_path):
    command = f"unzip -l {zip_file_path}"
    srt_files = []
    for line in run.local_command_get_output(command).split('\n'):
        if line.endswith('.srt'):
            srt_files.append(line.split(' ')[-1])
    return srt_files


def handle_srt(srt_file, auto_move=False):
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
    if not auto_move:
        if input("move file to destination?: ").lower() not in ['y', 'yes']:
            return
    if not run.rename_file(srt_file, subtitle_dest):
        pcstr("failed to move file", 'red')
        return
    pcstr("moved file!", 'lgreen')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("file",
                        nargs="?",
                        default="*.srt")
    parser.add_argument("--yes",
                        "-y",
                        action="store_true",
                        dest="auto_move")
    parser.add_argument("--search",
                        "-s",
                        default=None,
                        dest="search_subscene")
    parser.add_argument("--verbose",
                        "-v",
                        action="store_true",
                        dest="verbose")
    parser.add_argument("--language",
                        "-l",
                        "--lang",
                        default=None,
                        choices=["en", "sv"],
                        dest="lang")
    return parser.parse_args()


def main():
    args = get_args()
    srt_filenames = []
    if args.search_subscene is not None:
        if args.verbose:
            print("searching subscene")
        subscene = SubScene(args.search_subscene, verbose=args.verbose)
        for lang in [Language.English, Language.Swedish]:
            if args.lang is not None:
                if args.lang == "en" and lang != Language.English:
                    continue
                if args.lang == "sv" and lang != Language.Swedish:
                    continue
            sub = subscene.result.get_best(lang)
            if sub:
                srt_path = sub.download_and_unzip()
                if srt_path:
                    handle_srt(srt_path)
            else:
                print(f"could not find any subs for language: {lang}")
        return 0
    if "*" in args.file:
        items = list(Path().glob(args.file))
        if items:
            pfcs(f"found i[{len(items)}] item matching i[{args.file}]")
        for num, item in enumerate(items, 1):
            if len(items) > 1:
                pfcs(f"processing item i[{num}] of {len(items)}")
            if item.suffix.endswith("srt"):
                handle_srt(item.name, auto_move=args.auto_move)
            else:
                pfcs(f"skipping item w[{item.name}], not srt")
            print_line()
        print("done!")
        sys.exit(0)
    file_path = Path(args.file)
    if not file_path.exists():
        print("passed file does not exists")
        exit()
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
    [handle_srt(srt, auto_move=args.auto_move) for srt in srt_filenames]


if __name__ == "__main__":
    main()
