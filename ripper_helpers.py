#!/usr/bin/python3.8

import hashlib
import json
import random
import re

from requests import Session

VALID_FILTER_KEYS = ["season", "episode", "title", "date"]


def apply_filter(ep_list: list, filter_type: str, filter_val: str):
    "Just for Tv4PlayEpisodeData for now"
    filtered_list = []
    for ep_item in ep_list:
        if not isinstance(ep_item, Tv4PlayEpisodeData):
            continue
        if filter_type == "season":
            try:
                if int(filter_val) == ep_item.season_num:
                    filtered_list.append(ep_item)
            except ValueError:
                continue
        elif filter_type == "episode":
            try:
                if int(filter_val) == ep_item.episode_num:
                    filtered_list.append(ep_item)
            except ValueError:
                continue
        elif filter_type == "title":
            title = ep_item.title.lower()
            if filter_val.startswith("!"):
                if filter_val.replace("!", "").lower() not in title:
                    filtered_list.append(ep_item)
            elif filter_val.lower() in title:
                filtered_list.append(ep_item)
    return filtered_list


class Tv4PlayEpisodeData():
    URL_PREFIX = r"https://www.tv4play.se/program/"

    def __init__(self, episode_data: dict):
        self.raw_data = episode_data
        self.season_num = episode_data.get("season", 0)
        self.episode_num = episode_data.get("episode", 0)
        self.title = episode_data.get("title", "N/A")
        self.id = episode_data.get("id", 0)
        self.show = episode_data.get("program_nid", "N/A")

    def __str__(self):
        return f"{self.show} S{self.season_num}E{self.episode_num} " \
               f"\"{self.title}\" -- {self.id}"

    def url(self):
        return f"{self.URL_PREFIX}{self.show}/{self.id}"


class Tv4PlayEpisodeLister():
    REGEX = r"application\/json\">(.*\}\})<\/script><script "

    def __init__(self, url):
        if not "tv4play.se" in url:
            print("cannot handle non-tv4play.se urls!")
        self.url = url
        self.session = Session()
        self.filter = {}
        # self.check_token()

    def set_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key not in VALID_FILTER_KEYS:
                print(f"invalid filter: {key}={val}")
            else:
                self.filter[key] = val

    def list_episode_urls(self, revered_order=False, limit=None):
        res = self.session.get(f"{self.url}")
        match = re.search(self.REGEX, res.text)
        if not match:
            print(f"can't find episodes @ {self.url}")
            return []
        json_data = json.loads(match.group(1))
        try:
            program_data = json_data["props"]["apolloState"]
        except KeyError:
            print(f"can't parse episodes data @ {self.url}")
            return []
        ep_list = []
        for key in program_data:
            if not "VideoAsset:" in key:
                continue
            video_data = program_data[key]
            if video_data["clip"]:  # skip clips
                continue
            ep_list.append(Tv4PlayEpisodeData(video_data))
        for filter_key, filter_val in self.filter.items():
            ep_list = apply_filter(ep_list, filter_key, filter_val)
        if revered_order:
            ep_list.reverse()
        if limit:
            for ep in ep_list[0:limit]:
                yield ep.url()
        else:
            for ep in ep_list:
                yield ep.url()


class DPlayEpisodeLister():
    API_URL = "https://disco-api.dplay.se"
    SITE_URL = "https://www.dplay.se"

    def __init__(self, url):
        if not "dplay.se" in url:
            print("cannot handle non-dplay.se urls!")
        self.url = url
        self.session = Session()
        self.check_token()

    def check_token(self) -> bool:
        deviceid = hashlib.sha256(
            bytes(int(random.random() * 1000))).hexdigest()
        url = f"{self.API_URL}/token?realm=dplayse&deviceId={deviceid}&shortlived=true"
        res = self.session.get(url)
        return res.status_code < 400

    def list_episode_urls(self, revered_order=False, limit=None):
        match = re.search(
            "/(program|programmer|videos|videoer)/([^/]+)", self.url)
        if not match:
            print("failed to determine show path!")
            return
        res = self.session.get(
            f"{self.API_URL}/content/shows/{match.group(2)}")

        show_id = res.json()["data"]["id"]
        season_numbers = res.json()["data"]["attributes"]["seasonNumbers"]

        url_list = []

        for season_number in season_numbers:
            qyerystring = (
                "include=primaryChannel,show&filter[videoType]=EPISODE"
                f"&filter[show.id]={show_id}&filter[seasonNumber]={season_number}"
                "&page[size]=100&sort=seasonNumber,episodeNumber,-earliestPlayableStart"
            )
            res = self.session.get(
                f"{self.API_URL}/content/videos?{qyerystring}")
            for data in res.json()["data"]:
                episode_path = data["attributes"]["path"]
                url_list.append(f"{self.SITE_URL}/videos/{episode_path}")

        if revered_order:
            url_list.reverse()
        if limit:
            return url_list[0:limit]
        return url_list


def test_dplay():
    prog_url = "https://www.dplay.se/program/alla-mot-alla-med-filip-och-fredrik"
    dpel = DPlayEpisodeLister(prog_url)
    eps = dpel.list_episode_urls()

    print("ALL EPS")
    for ep in eps:
        print(ep)

    print("ALL EPS REVERSED")
    eps = dpel.list_episode_urls(revered_order=True)
    for ep in eps:
        print(ep)

    print("FIRST 5 EPS")
    eps = dpel.list_episode_urls(revered_order=False, limit=5)
    for ep in eps:
        print(ep)

    print("LAST 5 EPS")
    eps = dpel.list_episode_urls(revered_order=True, limit=5)
    for ep in eps:
        print(ep)


def test_tv4play():
    prog_url = "https://www.tv4play.se/program/farmen"
    tfel = Tv4PlayEpisodeLister(prog_url)
    eps = tfel.list_episode_urls()

    print("ALL EPS")
    for ep in eps:
        print(ep)

    print("LAST 5 EPS")  # tv4play shows last first, for last season...
    eps = tfel.list_episode_urls(revered_order=False, limit=5)
    for ep in eps:
        print(ep)

    print("EPS, SEASON 13")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(season="13")
    eps = tfel.list_episode_urls()
    for ep in eps:
        print(ep)

    print("EPS, TORPET")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(title="torpet")
    eps = tfel.list_episode_urls()
    for ep in eps:
        print(ep)

    print("EPS, NOT TORPET, SEASON 13")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(title="!torpet", season="13")
    eps = tfel.list_episode_urls()
    for ep in eps:
        print(ep)


if __name__ == "__main__":
    # For Testing....
    test_tv4play()
    test_dplay()
