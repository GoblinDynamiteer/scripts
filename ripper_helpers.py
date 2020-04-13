#!/usr/bin/python3.8

import hashlib
import json
import random
import re
import sys

from urllib.request import urlopen
from urllib.parse import urlparse, quote

from datetime import datetime
from requests import Session

VALID_FILTER_KEYS = ["season", "episode", "title", "date"]


def apply_filter(ep_list: list, filter_type: str, filter_val: str):
    "Just for Tv4PlayEpisodeData for now"
    filtered_list = []
    for ep_item in ep_list:
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


class SVTPlayEpisodeData():
    URL_PREFIX = r"https://www.svtplay.se"

    def __init__(self):
        self.season_num = 0
        self.episode_num = 0
        self.title = "N/A"
        self.id = 0
        self.show = "N/A"
        self.url_suffix = ""

    def __str__(self):
        return f"{self.show} S{self.season_num}E{self.episode_num} " \
               f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"

    def set_data(self, **key_val_data):
        if "season_num" in key_val_data:
            self.season_num = key_val_data["season_num"]
        if "episode_num" in key_val_data:
            self.episode_num = key_val_data["episode_num"]
        if "id" in key_val_data:
            self.id = key_val_data["id"]
        if "show" in key_val_data:
            self.show = key_val_data["show"]
        if "title" in key_val_data:
            self.title = key_val_data["title"]
        if "url" in key_val_data:
            self.url_suffix = key_val_data["url"]

    def url(self):
        return f"{self.URL_PREFIX}{self.url_suffix}"


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
               f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"

    def url(self):
        return f"{self.URL_PREFIX}{quote(self.show)}/{self.id}"


class DPlayEpisodeData():
    URL_PREFIX = r"https://www.dplay.se"

    def __init__(self, episode_data: dict, show_data: dict):
        self.raw_data = episode_data
        attr = episode_data.get("attributes", {})
        self.episode_path = attr.get("path", "")
        self.season_num = attr.get("seasonNumber", 0)
        self.episode_num = attr.get("episodeNumber", 0)
        self.title = attr.get("name", "N/A")
        self.show = "N/A"
        self.id = 0
        try:
            self.show = show_data["data"]["attributes"]["name"]
        except:
            pass
        try:
            self.id = int(self.raw_data.get("id"), 0)
        except:
            pass

    def __str__(self):
        return f"{self.show} S{self.season_num}E{self.episode_num} " \
               f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"

    def url(self):
        return f"{self.URL_PREFIX}/videos/{self.episode_path}"


class ViafreeEpisodeData():
    URL_PREFIX = r"https://www.viafree.se"

    def __init__(self, episode_data: dict):
        self.raw_data = episode_data
        self.episode_path = episode_data.get("publicPath", "")
        episode_info = episode_data.get("episode", {})
        self.season_num = episode_info.get("seasonNumber", 0)
        self.episode_num = episode_info.get("episodeNumber", 0)
        self.title = episode_data.get("title", "N/A")
        self.show = episode_info.get("seriesTitle", 0)
        self.id = episode_data.get("guid", "N/A")

    def __str__(self):
        return f"{self.show} S{self.season_num}E{self.episode_num} " \
               f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"

    def url(self):
        return f"{self.URL_PREFIX}{self.episode_path}"


class SVTPlayEpisodeLister():
    REGEX = r"application\/json\">(.*\}\})<\/script><script "

    def __init__(self, url):
        if not "svtplay.se" in url:
            print("cannot handle non-svtplay.se urls!")
        self.url = url
        self.session = Session()
        self.filter = {}

    def set_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key not in VALID_FILTER_KEYS:
                print(f"invalid filter: {key}={val}")
            else:
                self.filter[key] = val

    def list_episode_urls(self, revered_order=False, limit=None, objects=False):
        res = self.session.get(f"{self.url}")
        match = re.search(r"__svtplay_apollo'] = ({.*});", res.text)
        if not match:
            print("could not parse data!")
            return []
        json_data = json.loads(match.group(1))
        season_slug = ""
        show_name = ""
        for key in json_data.keys():
            slug = json_data[key].get("slug", "")
            if slug and slug in self.url:
                season_slug = slug
                show_name = json_data[key].get("name", "")
                break
        episode_keys = self.find_episode_keys(json_data, season_slug)
        ep_list = []
        for ep_key in episode_keys:
            obj = self.key_to_obj(json_data, ep_key)
            if obj is not None:
                obj.set_data(show=show_name)
                ep_list.append(obj)
        for filter_key, filter_val in self.filter.items():
            ep_list = apply_filter(ep_list, filter_key, filter_val)
        ep_list.sort(key=lambda x: (x.season_num, x.episode_num),
                     reverse=revered_order)
        if limit:
            return [ep if objects else ep.url() for ep in ep_list[0:limit]]
        return [ep if objects else ep.url() for ep in ep_list]

    def key_to_obj(self, json_data: dict, key: str):
        re_ix = r"\d{3}$"
        re_part = r"[dD]el+\s(?P<ep_num>\d+)\sav\s\d+"
        re_url = r"\/(?P<ep_id>\d+).+sasong\-(?P<season_num>\d+)"
        ep_data = json_data.get(key, {})
        if not ep_data:
            return None
        determined_ep_number = None
        determined_season_number = None
        match = re.search(re_ix, ep_data.get("id", ""))
        if match:
            determined_ep_number = int(match.group(0))
        match = re.search(re_part, ep_data.get("longDescription", ""))
        if match:
            part_num = int(match.groupdict().get("ep_num", None))
            if determined_ep_number is not None:
                if part_num != determined_ep_number:
                    print(f"found several ep numbers for{key}!")
            determined_ep_number = part_num
        url_key = ep_data["urls"]["id"]
        url_str = json_data.get(url_key, {}).get("svtplay", "")
        if not url_str:
            return None
        match = re.search(re_url, url_str)
        ep_id = None
        if match:
            determined_season_number = int(
                match.groupdict().get("season_num", None))
            ep_id = int(match.groupdict().get("ep_id", None))
        obj = SVTPlayEpisodeData()
        obj.set_data(id=ep_id,
                     title=ep_data.get("name", "N/A"),
                     url=url_str,
                     season_num=determined_season_number,
                     episode_num=determined_ep_number)
        return obj

    def find_episode_keys(self, json_data, show_slug):
        found_episodes = []
        if not show_slug:
            return found_episodes
        for key, val in json_data.items():
            if key in found_episodes:
                continue
            if not key.lower().startswith("episode"):
                continue
            url_key = ""
            try:
                url_key = val["urls"]["id"]
            except KeyError:
                continue
            url_str = json_data.get(url_key, {}).get("svtplay", "")
            if show_slug in url_str:
                found_episodes.append(key)
        return found_episodes


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

    def list_episode_urls(self, revered_order=False, limit=None, objects=False):
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
            if "clip" in video_data and video_data["clip"]:  # skip clips
                continue
            elif "id" not in video_data:
                continue
            ep_list.append(Tv4PlayEpisodeData(video_data))
        for filter_key, filter_val in self.filter.items():
            ep_list = apply_filter(ep_list, filter_key, filter_val)
        ep_list.sort(key=lambda x: (x.season_num, x.episode_num),
                     reverse=revered_order)
        if limit:
            return [ep if objects else ep.url() for ep in ep_list[0:limit]]
        return [ep if objects else ep.url() for ep in ep_list]


class DPlayEpisodeLister():
    API_URL = "https://disco-api.dplay.se"

    def __init__(self, url):
        if not "dplay.se" in url:
            print("cannot handle non-dplay.se urls!")
        self.url = url
        self.filter = {}
        self.session = Session()
        self.check_token()

    def check_token(self) -> bool:
        deviceid = hashlib.sha256(
            bytes(int(random.random() * 1000))).hexdigest()
        url = f"{self.API_URL}/token?realm=dplayse&deviceId={deviceid}&shortlived=true"
        res = self.session.get(url)
        return res.status_code < 400

    def set_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key not in VALID_FILTER_KEYS:
                print(f"invalid filter: {key}={val}")
            else:
                self.filter[key] = val

    def is_episode_data_premium(self, data):
        "Check if a free account can see/download episode"
        has_free = False
        free_datetime = None
        for availability_window in data.get("availabilityWindows", []):
            if availability_window.get("package", "None") == "Free":
                has_free = True
                free_datetime = availability_window.get("playableStart", None)
                break
        if not has_free or not free_datetime:
            return True
        try:
            free_datetime = datetime.strptime(
                free_datetime, r"%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return True  # TODO: might still be free?
        return free_datetime > datetime.now()

    def list_episode_urls(self, revered_order=False, limit=None, objects=False):
        match = re.search(
            "/(program|programmer|videos|videoer)/([^/]+)", self.url)
        if not match:
            print("failed to determine show path!")
            return
        res = self.session.get(
            f"{self.API_URL}/content/shows/{match.group(2)}")

        show_data = res.json()
        show_id = res.json()["data"]["id"]
        season_numbers = res.json()["data"]["attributes"]["seasonNumbers"]

        ep_list = []

        for season_number in season_numbers:
            qyerystring = (
                "include=primaryChannel,show&filter[videoType]=EPISODE"
                f"&filter[show.id]={show_id}&filter[seasonNumber]={season_number}"
                "&page[size]=100&sort=seasonNumber,episodeNumber,-earliestPlayableStart"
            )
            res = self.session.get(
                f"{self.API_URL}/content/videos?{qyerystring}")
            for data in res.json()["data"]:
                if self.is_episode_data_premium(data.get("attributes", {})):
                    continue
                ep_list.append(DPlayEpisodeData(data, show_data))
        for filter_key, filter_val in self.filter.items():
            ep_list = apply_filter(ep_list, filter_key, filter_val)
        ep_list.sort(key=lambda x: (x.season_num, x.episode_num),
                     reverse=revered_order)
        if limit:
            return [ep if objects else ep.url() for ep in ep_list[0:limit]]
        return [ep if objects else ep.url() for ep in ep_list]


class ViafreeUrlHandler():
    APU_URL_VID = r"http://playapi.mtgx.tv/v3/videos/"
    APU_URL_STREAM = r"https://viafree.mtg-api.com/stream-links/viafree/web" \
                     r"/se/clear-media-guids/{}/streams"

    def __init__(self, url):
        if not "viafree" in url:
            print("cannot handle non-viafree.se urls!")
        self.url = url
        self.session = Session()
        self.id = self.parse_id()
        self.mpx_guid = None
        self.stream_url = self.determine_stream_url()

    def parse_id(self):
        if not "avsnitt" in self.url:
            return None
        page_contents = urlopen(self.url).read()
        match = re.search(
            r"\"product[Gg]uid\"\:\"\d{1,10}\"", str(page_contents))
        if not match:
            print("viafree workaround -> failed to extract video id")
            return None
        vid_id = match.group(0).replace(r'"productGuid":"', "")
        vid_id = vid_id.replace(r'"', "")
        try:
            return int(vid_id)
        except:
            return None

    def determine_stream_url(self):
        if self.id is None:
            return ""
        res = self.session.get(f"{self.APU_URL_VID}{self.id}")
        json_data = res.json()
        self.mpx_guid = json_data.get("mpx_guid", None)
        res = self.session.get(self.APU_URL_STREAM.format(self.mpx_guid))
        try:
            stream_url = res.json()[
                "embedded"]["prioritizedStreams"][0]["links"]["stream"]["href"]
        except:
            stream_url = ""
        return stream_url


class ViafreeEpisodeLister():
    def __init__(self, url):
        if not "viafree" in url:
            print("cannot handle non-viafree.se urls!")
        self.url = url
        self.session = Session()
        self.filter = {}

    def set_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key not in VALID_FILTER_KEYS:
                print(f"invalid filter: {key}={val}")
            else:
                self.filter[key] = val

    def list_episode_urls(self, revered_order=False, limit=None, objects=False):
        res = self.session.get(self.url)
        splits = res.text.split("\"programs\":")
        candidates = []
        try:
            for index, string in enumerate(splits, 0):
                if index == 0:
                    continue
                if not string.startswith("["):
                    continue
                index_of_list_end = string.rfind("]")
                candidates.append(string[:index_of_list_end+1])
        except:
            return []
        if not candidates:
            return []
        json_data = self.candidates_to_json(candidates)
        if not json_data:
            return []
        ep_list = []
        for episode_data in json_data:
            ep_list.append(ViafreeEpisodeData(episode_data))
        for filter_key, filter_val in self.filter.items():
            ep_list = apply_filter(ep_list, filter_key, filter_val)
        ep_list.sort(key=lambda x: (x.season_num, x.episode_num),
                     reverse=revered_order)
        if limit:
            return [ep if objects else ep.url() for ep in ep_list[0:limit]]
        return [ep if objects else ep.url() for ep in ep_list]

    def candidates_to_json(self, candidate_list):
        best_data = {}
        best_ep_count = 0
        for cand in candidate_list:
            cand_str = cand
            list_diff = cand_str.count("]") - cand_str.count("[")
            if list_diff < 0:
                continue
            while list_diff > 0:
                cand_str = cand_str[:cand_str.rfind("]")]
                cand_str = cand_str[:cand_str.rfind("]")+1]
                list_diff = cand_str.count("[") - cand_str.count("]")
            json_data = {}
            try:
                json_data = json.loads(cand_str)
            except:
                continue
            url_path = urlparse(self.url).path
            count = 0
            for ep_data in json_data:
                if url_path in ep_data.get("publicPath", ""):
                    count += 1
                if count > best_ep_count:
                    best_ep_count = count
                    best_data = json_data
        return best_data


def test_dplay():
    print("DPLAY")
    prog_url = "https://www.dplay.se/program/alla-mot-alla-med-filip-och-fredrik"
    dpel = DPlayEpisodeLister(prog_url)
    eps = dpel.list_episode_urls(objects=True)

    print("ALL EPS")
    for ep in eps:
        print(ep)

    print("ALL EPS REVERSED")
    eps = dpel.list_episode_urls(revered_order=True, objects=True)
    for ep in eps:
        print(ep)

    print("FIRST 5 EPS")
    eps = dpel.list_episode_urls(revered_order=False, limit=5, objects=True)
    for ep in eps:
        print(ep)

    print("LAST 5 EPS")
    eps = dpel.list_episode_urls(revered_order=True, limit=5, objects=True)
    for ep in eps:
        print(ep)


def test_tv4play():
    print("TV4PLAY")
    prog_url = "https://www.tv4play.se/program/farmen"
    tfel = Tv4PlayEpisodeLister(prog_url)
    eps = tfel.list_episode_urls(objects=True)

    print("ALL EPS")
    for ep in eps:
        print(ep)

    print("LAST 5 EPS")
    eps = tfel.list_episode_urls(revered_order=True, limit=5, objects=True)
    for ep in eps:
        print(ep)

    print("EPS, SEASON 13")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(season="13")
    eps = tfel.list_episode_urls(objects=True)
    for ep in eps:
        print(ep)

    print("EPS, TORPET")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(title="torpet")
    eps = tfel.list_episode_urls(objects=True)
    for ep in eps:
        print(ep)

    print("EPS, TORPET REVERSED")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(title="torpet")
    eps = tfel.list_episode_urls(objects=True, revered_order=True)
    for ep in eps:
        print(ep)

    print("EPS, NOT TORPET, SEASON 13")
    tfel = Tv4PlayEpisodeLister(prog_url)
    tfel.set_filter(title="!torpet", season="13")
    eps = tfel.list_episode_urls(objects=True)
    for ep in eps:
        print(ep)


def test_viafree():
    print("VIAFREE")
    prog_url = "https://www.viafree.se/program/livsstil/lyxfallan/sasong-26"
    vfel = ViafreeEpisodeLister(prog_url)
    eps = vfel.list_episode_urls(objects=True)
    print("LF ALL EPS")
    for ep in eps:
        print(ep)

    print("LF LAST 5 EPS")
    eps = vfel.list_episode_urls(revered_order=True, limit=5, objects=True)
    for ep in eps:
        print(ep)

    print("LF FIRST 5 EPS")
    eps = vfel.list_episode_urls(revered_order=False, limit=5, objects=True)
    for ep in eps:
        print(ep)

    prog_url = "https://www.viafree.se/program/reality/paradise-hotel/"
    vfel = ViafreeEpisodeLister(prog_url)
    eps = vfel.list_episode_urls(objects=True)
    print("PH ALL EPS")
    for ep in eps:
        print(ep)

    print("PH LAST 5 EPS")
    eps = vfel.list_episode_urls(revered_order=True, limit=5, objects=True)
    for ep in eps:
        print(ep)

    print("PH FIRST 5 EPS")
    eps = vfel.list_episode_urls(
        revered_order=False, limit=5, objects=True)
    for ep in eps:
        print(ep)


def test_viafree_url_handler():
    vfurl = ViafreeUrlHandler(
        "https://www.viafree.se/program/reality/paradise-hotel/sasong-12/avsnitt-25")
    print("PH URL ID")
    print(vfurl.id)
    print(vfurl.stream_url)


if __name__ == "__main__":
    # For Testing....
    test_tv4play()
    test_dplay()
    test_viafree()
    test_viafree_url_handler()
