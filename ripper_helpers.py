#!/usr/bin/python3.8

import json
import re
import unittest
import warnings
from datetime import datetime, timedelta
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import urlopen
from argparse import ArgumentParser

from requests import Session

from config import ConfigurationManager
from printing import fcs
from util import Singleton

VALID_FILTER_KEYS = ["season", "episode", "title", "date"]


class SessionSingleton(metaclass=Singleton):
    SESSION = None
    GETS = {}

    def init_session(self):
        if self.SESSION is None:
            self.SESSION = Session()

    def load_cookies_txt(self, file_path=None):
        self.init_session()
        if not file_path:
            file_path = ConfigurationManager().path("cookies_txt")
        # NOTE use: https://addons.mozilla.org/en-US/firefox/addon/export-cookies-txt/
        jar = MozillaCookieJar(file_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        self.SESSION.cookies.update(jar)

    def get(self, url):
        self.init_session()
        if url in self.GETS:
            return self.GETS[url]
        self.GETS[url] = self.SESSION.get(url)
        return self.GETS[url]


def apply_filter(ep_list: list, filter_type: str, filter_val: str):
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


class EpisodeData():
    def __init__(self, episode_data={}, verbose=False):
        self.print_log = verbose
        self.raw_data = episode_data
        self.log_prefix = "EPISODE_DATA"

    def set_log_prefix(self, log_prefix: str):
        self.log_prefix = log_prefix.upper()

    def log(self, info_str, info_str_line2=""):
        if not self.print_log:
            return
        print(fcs(f"i[({self.log_prefix})]"), info_str)
        if info_str_line2:
            spaces = " " * len(f"({self.log_prefix}) ")
            print(f"{spaces}{info_str_line2}")

    def url(self):
        raise NotImplementedError()

    def subtitle_url(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    @staticmethod
    def get_availabe_classes():
        return [SVTPlayEpisodeData, DPlayEpisodeData, ViafreeEpisodeData, Tv4PlayEpisodeData]


class SVTPlayEpisodeData(EpisodeData):
    URL_PREFIX = r"https://www.svtplay.se"

    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.set_log_prefix("SVTPLAY_DATA")
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

    def subtitle_url(self):
        return self.url()


class Tv4PlayEpisodeData(EpisodeData):
    URL_PREFIX = r"https://www.tv4play.se/program/"

    def __init__(self, episode_data={}, verbose=False):
        super().__init__(episode_data, verbose)
        self.set_log_prefix("TV4PLAY_DATA")
        self.season_num = episode_data.get("season", 0)
        self.episode_num = episode_data.get("episode", 0)
        self.title = episode_data.get("title", "N/A")
        self.id = episode_data.get("id", 0)
        self.show = episode_data.get("program_nid", "N/A")
        self.sub_url_list = []
        self.sub_m3u_url = ""

    def __str__(self):
        return f"{self.show} S{self.season_num}E{self.episode_num} " \
               f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"

    def url(self):
        return f"{self.URL_PREFIX}{quote(self.show)}/{self.id}"

    def subtitle_url(self) -> list:
        if self.sub_url_list:
            self.log("already retrieved/gotten subtitle url")
            return self.sub_url_list
        if self.id == 0:
            self.log("show id is 0, cannot retrive subtitle url")
            return None
        if self.sub_m3u_url:
            self.log("have already retrieved subtitle m3u url",
                     info_str_line2=fcs(f"p[{self.sub_m3u_url}]"))
        else:
            self.log("attempting to retrieve subtitle url...")
            data_url = f"https://playback-api.b17g.net/media/{self.id}?"\
                f"service=tv4&device=browser&protocol=hls%2Cdash&drm=widevine"
            res = SessionSingleton().get(data_url)
            try:
                hls_url = res.json()[
                    "playbackItem"]["manifestUrl"]
                self.log("got manifest url:",
                         info_str_line2=fcs(f"p[{hls_url}]"))
            except KeyError as key_error:
                self.log("failed to retrieve manifest url from",
                         fcs(f"o[{data_url}]"))
                return []
            hls_data = SessionSingleton().get(hls_url)
            last_path = hls_url.split("/")[-1]
            hls_url_prefix = hls_url.replace(last_path, "")
            self.log("using hls url prefix", hls_url_prefix)
            for line in hls_data.text.splitlines():
                if all([x in line for x in ["TYPE=SUBTITLES", "URI=", 'LANGUAGE="sv"']]):
                    sub_url_suffix = line.split('URI="')[1]
                    sub_url_suffix = sub_url_suffix[:-1]
                    self.sub_m3u_url = hls_url_prefix + "/" + sub_url_suffix
                    break
        if not self.sub_m3u_url:
            self.log("could not retrieve subtitle m3u url")
            return []
        self.log("using subtitle m3u url:",
                 info_str_line2=fcs(f"p[{self.sub_m3u_url}]"))
        res = SessionSingleton().get(self.sub_m3u_url)
        vtt_files = []
        last_path = hls_url.split("/")[-1]
        hls_url_prefix = hls_url.replace(last_path, "")
        for line in res.text.splitlines():
            if ".webvtt" in line:
                vtt_files.append(hls_url_prefix + "/" + line)
        self.sub_url_list = vtt_files
        if self.sub_url_list:
            self.log(f"found {len(self.sub_url_list)} vtt files")
            return self.sub_url_list
        self.log(fcs("w[WARNING] could not find vtt link in subtitle m3u!"))
        self.sub_m3u_url = ""
        return []


class DPlayEpisodeData(EpisodeData):
    URL_PREFIX = r"https://www.discoveryplus.se"
    API_URL = "https://disco-api.discoveryplus.se"

    def __init__(self, episode_data={}, show_data={}, premium=False, verbose=False):
        super().__init__(episode_data, verbose)
        self.set_log_prefix("DPLAY_DATA")
        attr = episode_data.get("attributes", {})
        self.episode_path = attr.get("path", "")
        self.season_num = attr.get("seasonNumber", 0)
        self.episode_num = attr.get("episodeNumber", 0)
        self.title = attr.get("name", "N/A")
        self.show = "N/A"
        self.id = 0
        self.sub_url = ""
        self.sub_m3u_url = ""
        self.print_log = False
        self.is_premium = premium
        try:
            self.show = show_data["data"]["attributes"]["name"]
        except:
            pass
        try:
            self.id = int(self.raw_data.get("id"), 0)
        except:
            pass

    def __str__(self):
        string = f"{self.show} S{self.season_num}E{self.episode_num} " \
                 f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"
        if self.sub_url:
            return string + f" -- sub_url: {self.sub_url}"
        return string

    def name(self):
        return f"{self.show} S{self.season_num}E{self.episode_num}"

    def subtitle_url(self):
        if self.sub_url:
            self.log("already retrieved/gotten subtitle url")
            return self.sub_url
        if self.id == 0:
            self.log("show id is 0, cannot retrive subtitle url")
            return ""
        SessionSingleton().load_cookies_txt()
        if self.sub_m3u_url:
            self.log("have already retrieved subtitle m3u url",
                     info_str_line2=fcs(f"p[{self.sub_m3u_url}]"))
        else:
            res = SessionSingleton().get(
                f"{self.API_URL}/playback/videoPlaybackInfo/{self.id}")
            try:
                hls_url = res.json()[
                    "data"]["attributes"]["streaming"]["hls"]["url"]
                self.log("got HLS url:",
                         info_str_line2=fcs(f"p[{hls_url}]"))
            except KeyError as key_error:
                self.log("failed to retrieve HLS url from videoPlaybackInfo")
                return ""
            hls_data = SessionSingleton().get(hls_url)
            hls_url_prefix = hls_url.split("playlist.m3u8")[0]
            self.log("using hls url prefix", hls_url_prefix)
            for line in hls_data.text.splitlines():
                if all([x in line for x in ["TYPE=SUBTITLES", "URI=", 'LANGUAGE="sv"']]):
                    sub_url_suffix = line.split('URI="')[1]
                    sub_url_suffix = sub_url_suffix[:-1]
                    self.sub_m3u_url = hls_url_prefix + "/" + sub_url_suffix
                    break
        if not self.sub_m3u_url:
            self.log("could not retrieve subtitle m3u url")
            return ""
        self.log("using subtitle m3u url:",
                 info_str_line2=fcs(f"p[{self.sub_m3u_url}]"))
        res = SessionSingleton().get(self.sub_m3u_url)
        for line in res.text.splitlines():
            if ".vtt" in line:
                hls_url_prefix = hls_url.split("playlist.m3u8")[0]
                sub_url = hls_url_prefix + "/" + line
                self.sub_url = sub_url
                return self.sub_url
        self.log(fcs("w[WARNING] could not find vtt link in subtitle m3u!"))
        self.sub_m3u_url = ""
        return ""

    def url(self):
        return f"{self.URL_PREFIX}/videos/{self.episode_path}"


class ViafreeEpisodeData(EpisodeData):
    URL_PREFIX = r"https://www.viafree.se"
    CONT_URL_PREFIX = r"https://viafree-content.mtg-api.com/viafree-content/v1/se/path/"

    def __init__(self, episode_data={}, verbose=False):
        super().__init__(episode_data, verbose)
        self.set_log_prefix("VIAFREE_DATA")
        self.episode_path = episode_data.get("publicPath", "")
        episode_info = episode_data.get("episode", {})
        self.season_num = episode_info.get("seasonNumber", 0)
        self.episode_num = episode_info.get("episodeNumber", 0)
        self.title = episode_data.get("title", "N/A")
        self.show = episode_info.get("seriesTitle", 0)
        self.id = episode_data.get("guid", "N/A")
        self.sub_url = ""

    def __str__(self):
        return f"{self.show} S{self.season_num}E{self.episode_num} " \
               f"\"{self.title}\" -- id:{self.id} -- url:{self.url()}"

    def url(self):
        return f"{self.URL_PREFIX}{self.episode_path}"

    def subtitle_url(self):
        if self.sub_url:
            self.log("already retrieved/gotten subtitle url")
            return self.sub_url
        content_url = f"{self.CONT_URL_PREFIX}{self.episode_path}"
        res = SessionSingleton().get(content_url)
        stream_url = ""
        try:
            stream_url = res.json()[
                '_embedded']['viafreeBlocks'][0]['_embedded']['program']['_links']['streamLink']['href']
            self.log(fcs("got stream url"), fcs(f"i[{stream_url}]"))
        except KeyError as error:
            self.log(fcs("failed to retrieve stream url from:"),
                     fcs(f"o[{content_url}]"))
            return ""
        res = SessionSingleton().get(stream_url)
        try:
            sub_url = res.json()["embedded"]["subtitles"][0]["link"]["href"]
            self.log(fcs("got subtitle url"), fcs(f"i[{sub_url}]"))
            self.sub_url = sub_url
        except (KeyError, IndexError) as error:
            self.log(fcs("failed to retrieve subtitle url from:"),
                     fcs(f"o[{stream_url}]"))
            return ""
        return self.sub_url


class EpisodeLister():
    def __init__(self, url, verbose=False):
        self.url = url
        self.ep_list = []
        self.filter = {}
        self.print_log = verbose
        self.log_prefix = "EPISODE_LISTER"

    def set_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key not in VALID_FILTER_KEYS:
                print(f"invalid filter: {key}={val}")
            else:
                self.filter[key] = val

    def set_log_prefix(self, log_prefix: str):
        self.log_prefix = log_prefix.upper()

    def log(self, info_str, info_str_line2=""):
        if not self.print_log:
            return
        print(fcs(f"i[({self.log_prefix})]"), info_str)
        if info_str_line2:
            spaces = " " * len(f"({self.log_prefix}) ")
            print(f"{spaces}{info_str_line2}")

    def get_episodes(self, revered_order=False, limit=None):
        for filter_key, filter_val in self.filter.items():
            self.ep_list = apply_filter(self.ep_list, filter_key, filter_val)
        self.ep_list.sort(key=lambda x: (x.season_num, x.episode_num),
                          reverse=revered_order)
        if limit is not None:
            return self.ep_list[0:limit]
        return self.ep_list

    @staticmethod
    def get_lister(url, verbose_logging=False):
        matches = {"viafree.se": ViafreeEpisodeLister,
                   "tv4play.se": Tv4PlayEpisodeLister,
                   "discoveryplus.se": DPlayEpisodeLister,
                   "svtplay.se": SVTPlayEpisodeLister}
        for site, lister in matches.items():
            if site in url:
                return lister(url, verbose=verbose_logging)
        raise ValueError(f"unsupported site: {url}")


class SVTPlayEpisodeLister(EpisodeLister):
    REGEX = r"application\/json\">(.*\}\})<\/script><script "

    def __init__(self, url, verbose=False):
        super().__init__(url, verbose)
        self.set_log_prefix("SVTPLAY_LISTER")
        if not "svtplay.se" in url:
            print("cannot handle non-svtplay.se urls!")

    def get_episodes(self, revered_order=False, limit=None):
        if self.ep_list:
            return super().get_episodes(revered_order, limit)
        res = SessionSingleton().get(f"{self.url}")
        match = re.search(r"__svtplay_apollo'] = ({.*});", res.text)
        if not match:
            print("could not parse data!")
            return []
        json_data = json.loads(match.group(1))
        season_slug = ""
        show_name = ""
        self.log("processing json data...")
        for key in json_data.keys():
            slug = json_data[key].get("slug", "")
            if slug and slug in self.url:
                season_slug = slug
                self.log(f"got slug: {season_slug}")
                show_name = json_data[key].get("name", "")
                if show_name:
                    self.log(f"got show name: \"{show_name}\"")
                else:
                    self.log(fcs(f"w[warning] failed to get show name!"))
                break
        episode_keys = self.find_episode_keys(json_data, season_slug)
        for ep_key in episode_keys:
            obj = self.key_to_obj(json_data, ep_key)
            if obj is not None:
                obj.set_data(show=show_name)
                self.ep_list.append(obj)
        return super().get_episodes(revered_order, limit)

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
        if determined_ep_number is None:
            self.log(fcs(f"w[warning] failed to get ep_num for key {key}!"))
        url_key = ep_data["urls"]["id"]
        url_str = json_data.get(url_key, {}).get("svtplay", "")
        if not url_str:
            self.log(fcs(f"w[warning] failed to get url for ep key {key}!"))
            return None
        match = re.search(re_url, url_str)
        ep_id = None
        if match:
            determined_season_number = int(
                match.groupdict().get("season_num", None))
            ep_id = int(match.groupdict().get("ep_id", None))
        if determined_season_number is None:
            self.log(
                fcs(
                    f"w[warning] failed to get season_num for url w[{url_str}]!"),
                "--> setting to \"S01\"")
            determined_season_number = 1
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
        if not found_episodes:
            self.log("failed to find any episode keys!")
        return found_episodes


class Tv4PlayEpisodeLister(EpisodeLister):
    REGEXES = [r"application\/json\">(.*\})<\/script><script ",
               r"application\/json\">(.*\}\})<\/script><script "]

    def __init__(self, url, verbose=False):
        super().__init__(url, verbose)
        self.set_log_prefix("TV4PLAY_LISTER")
        if not "tv4play.se" in url:
            print("cannot handle non-tv4play.se urls!")
        self.url = url
        self.session = Session()
        self.filter = {}

    def get_episodes(self, revered_order=False, limit=None):
        if self.ep_list:
            return super().get_episodes(revered_order, limit)
        res = self.session.get(f"{self.url}")
        for regex_str in self.REGEXES:
            match = re.search(regex_str, res.text)
            if match:
                break
            else:
                self.log(f"failed regex match using: {regex_str}")
        else:
            print(f"can't find episodes @ {self.url}")
            return []
        json_data = json.loads(match.group(1))
        program_data = None
        try:
            program_data = json_data["props"]["pageProps"]["initialApolloState"]
        except KeyError:
            program_data = None
            self.log("[props][pageProps][initialApolloState] not present in json")
            try:
                program_data = json_data["props"]["apolloState"]
            except KeyError:
                self.log("[props][apolloState] not present in json")
                program_data = None
        if program_data is None:
            print(f"can't parse episodes data @ {self.url}")
            return []
        for key in program_data:
            if not "VideoAsset:" in key:
                continue
            video_data = program_data[key]
            if "clip" in video_data and video_data["clip"]:  # skip clips
                continue
            elif "id" not in video_data:
                continue
            self.ep_list.append(Tv4PlayEpisodeData(
                video_data, verbose=self.print_log))
        return super().get_episodes(revered_order, limit)


class DPlayEpisodeLister(EpisodeLister):
    API_URL = "https://disco-api.discoveryplus.se"

    def __init__(self, url, verbose=False):
        super().__init__(url, verbose)
        self.set_log_prefix("DPLAY_LISTER")
        if not "discoveryplus.se" in url:
            print("cannot handle non discoveryplus.se urls!")
        if not self.check_token():
            print("failed to get session for dplay")
        else:
            self.log("successfully got session")

    def check_token(self) -> bool:
        url = f"{self.API_URL}/users/me/favorites?include=default"
        SessionSingleton().load_cookies_txt()
        res = SessionSingleton().get(url)
        self.log(f"got ret code: {res.status_code} for url", url)
        return res.status_code < 400

    def is_episode_data_premium(self, data):
        "Check if a free account can see/download episode"
        has_free = False
        free_datetime = None
        for availability_window in data.get("availabilityWindows", []):
            if availability_window.get("package", "None") == "Registered":
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

    def get_episodes(self, revered_order=False, limit=None):
        if self.ep_list:
            return super().get_episodes(revered_order, limit)
        match = re.search(
            "/(program|programmer|videos|videoer)/([^/]+)", self.url)
        if not match:
            print("failed to determine show path!")
            return
        res = SessionSingleton().get(
            f"{self.API_URL}/content/shows/{match.group(2)}")
        show_data = res.json()
        show_id = res.json()["data"]["id"]
        season_numbers = res.json()["data"]["attributes"]["seasonNumbers"]
        for season_number in season_numbers:
            qyerystring = (
                "include=primaryChannel,show&filter[videoType]=EPISODE"
                f"&filter[show.id]={show_id}&filter[seasonNumber]={season_number}"
                "&page[size]=100&sort=seasonNumber,episodeNumber,-earliestPlayableStart"
            )
            res = SessionSingleton().get(
                f"{self.API_URL}/content/videos?{qyerystring}")
            for data in res.json()["data"]:
                is_premium = self.is_episode_data_premium(
                    data.get("attributes", {}))
                obj = DPlayEpisodeData(data, show_data, premium=is_premium)
                self.ep_list.append(obj)
        return super().get_episodes(revered_order, limit)


class ViafreeEpisodeLister(EpisodeLister):
    def __init__(self, url, verbose=False):
        super().__init__(url, verbose)
        self.set_log_prefix("VIAFREE_LISTER")
        if not "viafree" in url:
            print("cannot handle non-viafree.se urls!")
        self.url = url
        self.session = Session()
        self.filter = {}

    def get_episodes(self, revered_order=False, limit=None):
        if self.ep_list:
            return super().get_episodes(revered_order, limit)
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
        except Exception as error:
            self.log(fcs("e[error]"), error)
            return []
        if not candidates:
            self.log("failed to retrieve episodes!")
            return []
        json_data = self.candidates_to_json(candidates)
        if not json_data:
            self.log("failed to retrieve episodes!")
            return []
        for episode_data in json_data:
            self.ep_list.append(ViafreeEpisodeData(
                episode_data, verbose=self.print_log))
        return super().get_episodes(revered_order, limit)

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


class TestEpisodeLister(unittest.TestCase):
    URL_TV4 = r"https://www.tv4play.se/program/idol"
    URL_VIAFREE = r"https://www.viafree.se/program/livsstil/lyxfallan"
    URL_SVTPLAY = r"https://www.svtplay.se/skavlan"
    URL_INVALID = r"http://www.somerandomsite.se/tvshow/"
    URL_DPLAY = r"https://www.dplay.se/program/alla-mot-alla-med-filip-och-fredrik"

    def setUp(self):
        warnings.simplefilter("ignore", category=ResourceWarning)

    def test_get_lister_viafree(self):
        lister = EpisodeLister.get_lister(self.URL_VIAFREE)
        self.assertTrue(isinstance(lister, ViafreeEpisodeLister))

    def test_get_lister_tv4play(self):
        lister = EpisodeLister.get_lister(self.URL_TV4)
        self.assertTrue(isinstance(lister, Tv4PlayEpisodeLister))

    def test_get_lister_dplay(self):
        lister = EpisodeLister.get_lister(self.URL_DPLAY)
        self.assertTrue(isinstance(lister, DPlayEpisodeLister))

    def test_get_lister_svtplay(self):
        lister = EpisodeLister.get_lister(self.URL_SVTPLAY)
        self.assertTrue(isinstance(lister, SVTPlayEpisodeLister))

    def test_get_lister_unsupported(self):
        with self.assertRaises(Exception):
            EpisodeLister.get_lister(self.URL_INVALID)

    def test_get_episodes_svtplay(self):
        lister = EpisodeLister.get_lister(self.URL_SVTPLAY)
        self.assertGreater(len(lister.get_episodes()), 0)

    def test_get_episodes_viafree(self):
        lister = EpisodeLister.get_lister(self.URL_VIAFREE)
        self.assertGreater(len(lister.get_episodes()), 0)

    def test_get_episodes_tv4play(self):
        lister = EpisodeLister.get_lister(self.URL_TV4)
        self.assertGreater(len(lister.get_episodes()), 0)

    def test_get_episodes_dplay(self):
        lister = EpisodeLister.get_lister(self.URL_DPLAY)
        self.assertGreater(len(lister.get_episodes()), 0)


class TestEpisodeData(unittest.TestCase):
    def test_subtitle_url_implemented(self):
        for data_class in EpisodeData.get_availabe_classes():
            data = data_class()
            try:
                data.subtitle_url()
            except NotImplementedError:
                self.fail(
                    f"{data.__class__.__name__} has not implemented subtitle_url")


def get_args():
    parser = ArgumentParser("ripper helper")
    parser.add_argument("--test", dest="run_tests", action="store_true")
    parser.add_argument("--url", type=str)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main():
    args = get_args()
    if args.run_tests:
        print("running unit tests")
        unittest.main(argv=[__file__])
    if args.url:
        lister = EpisodeLister.get_lister(args.url, args.verbose)
        for episode in lister.get_episodes():
            print("vid url", episode.url())
            print("sub url", episode.subtitle_url())


if __name__ == "__main__":
    main()
