#!/usr/bin/python3

from enum import IntEnum

import util
import util_movie
import util_tv

EDU_SITES = ['packt', 'pluralsight', 'linkedin', 'technics']


class ReleaseType(IntEnum):
    TvShowEpisodeFile = 0
    TvShowEpisodeDir = 1
    MovieFile = 2
    MovieDir = 3
    TvShowSeasonPackDir = 4
    Education = 5
    AnimeEpisodeFile = 6
    AnimeEpisodeDir = 7
    SubPack = 8
    Unknown = 999

    @property
    def strshort(self):
        rt = ReleaseType(self.value)
        if rt == ReleaseType.TvShowEpisodeFile:
            return 'TvEpF'
        if rt == ReleaseType.TvShowEpisodeDir:
            return 'TvEpD'
        if rt == ReleaseType.TvShowSeasonPackDir:
            return 'TvSea'
        if rt == ReleaseType.MovieDir:
            return "MoviD"
        if rt == ReleaseType.MovieFile:
            return "MoviF"
        if rt == ReleaseType.Education:
            return "Educa"
        if rt == ReleaseType.SubPack:
            return "SubPk"
        return "Unkwn"


def determine_release_type(release_name: str) -> ReleaseType:
    if "subpack" in release_name.lower():
        return ReleaseType.SubPack
    if any(release_name.lower().startswith(edu_site) for edu_site in EDU_SITES):
        return ReleaseType.Education
    if util_tv.is_episode(release_name):
        if util.str_is_vid_file(release_name):
            return ReleaseType.TvShowEpisodeFile
        return ReleaseType.TvShowEpisodeDir
    if util_tv.is_season(release_name):
        return ReleaseType.TvShowSeasonPackDir
    if util_movie.is_movie(release_name):
        if util.str_is_vid_file(release_name):
            return ReleaseType.MovieFile
        return ReleaseType.MovieDir
    return ReleaseType.Unknown
