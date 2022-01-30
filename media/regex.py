#!/usr/bin/env python3

from typing import Optional, Tuple, List
import re

MOVIE_REGEX_PATTERN = r"^.+\.(2160p|1080p|720p|dvd|bdrip).+(\-|\.)[a-z0-9]+$"
SEASON_REGEX_PATTERN = r"^.+\.[sS]\d{02}\.+(?:.+)?(2160p|1080p|720p|dvd|bdrip).+\-[a-zA-Z0-9]+"
SEASON_EPISODE_REGEX_PATTERN = r"\.[sS](?P<season_num>\d{2,4})?([Ee](?P<episode_num>\d{2})?\.)?"
YEAR_REGEX_PATTERN = r"(?P<year>(19|20)\d{2})"
RES_REGEX_PATTERN = r"(2160p|1080p|720p|dvd|bdrip)"


def matches_movie_regex(item: str, replace_whitespace: bool = True) -> bool:
    if replace_whitespace:
        item = item.replace(" ", ".")
    return re.search(MOVIE_REGEX_PATTERN, item, re.IGNORECASE) is not None


def matches_season_regex(item: str, replace_whitespace: bool = True) -> bool:
    if replace_whitespace:
        item = item.replace(" ", ".")
    return re.search(SEASON_REGEX_PATTERN, item, re.IGNORECASE) is not None


def parse_season_and_episode(item: str, replace_whitespace: bool = True) -> Tuple[Optional[int], Optional[int]]:
    if replace_whitespace:
        item = item.replace(" ", ".")
    match = re.search(SEASON_EPISODE_REGEX_PATTERN, item)
    if not match:
        return None, None
    _dict = match.groupdict()
    _s = _dict.get("season_num", None)
    _e = _dict.get("episode_num", None)
    return int(_s) if _s is not None else None, int(_e) if _e is not None else None


def parse_year(string: str) -> Optional[int]:
    re_year = re.compile(YEAR_REGEX_PATTERN)
    matches: List[Tuple] = re_year.findall(string)
    if not matches:
        return None
    return int(matches[-1][0])


def parse_quality(string: str) -> Optional[str]:
    re_year = re.compile(RES_REGEX_PATTERN)
    match = re_year.search(string)
    if not match:
        return None
    return match.group()


def main():
    from media.util import MediaPaths
    for movie_dir in MediaPaths().movie_dirs():
        if not matches_movie_regex(movie_dir.name):
            print(f"does not match regex: {movie_dir.name}")


if __name__ == "__main__":
    main()
