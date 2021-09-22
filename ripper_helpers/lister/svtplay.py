
import re
import json

from .episode_lister import EpisodeLister
from .session import SessionSingleton
from ..data.svtplay import SVTPlayEpisodeData

from printout import fcs


class SVTPlayEpisodeLister(EpisodeLister):
    REGEX = r"application\/json\">(.*\}\})<\/script><script "

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self.set_log_prefix("SVTPLAY_LISTER")
        if "svtplay.se" not in url:
            print("cannot handle non-svtplay.py.se urls!")

    @staticmethod
    def supports_url(url_str: str) -> bool:
        return "svtplay.se" in url_str

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
        url_str = json_data.get(url_key, {}).get("svtplay.py", "")
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
            url_str = json_data.get(url_key, {}).get("svtplay.py", "")
            if show_slug in url_str:
                found_episodes.append(key)
        if not found_episodes:
            self.log("failed to find any episode keys!")
        return found_episodes




