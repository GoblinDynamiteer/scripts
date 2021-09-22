
import re
import json
from datetime import datetime

from .episode_lister import EpisodeLister
from requests import Session

from ..data.tv4 import Tv4PlayEpisodeData


class Tv4PlayEpisodeLister(EpisodeLister):
    REGEXES = [r"application\/json\">(.*\})<\/script><script ",
               r"application\/json\">(.*\}\})<\/script><script "]

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self.set_log_prefix("TV4PLAY_LISTER")
        if not self.supports_url(url):
            print("cannot handle non-tv4play.se urls!")
        self.session = Session()

    @staticmethod
    def supports_url(url_str: str) -> bool:
        return "tv4play.se" in url_str

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
        if self._save_json_data:
            filename = f"tv4_json_output_{datetime.now()}.json"
            with open(filename, "w") as _file:
                json.dump(json_data, _file, sort_keys=True, indent=4)
                print(f"dumped json data to {filename:}")
        try:
            program_data = json_data["props"]["pageProps"]["initialApolloState"]
        except KeyError:
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
            if "VideoAsset:" not in key:
                continue
            video_data = program_data[key]
            if "id" not in video_data:
                continue
            if "clip" in video_data and video_data["clip"] is True:
                if not self._download_clips:
                    continue
            self.ep_list.append(Tv4PlayEpisodeData(video_data, verbose=self.print_log))
        return super().get_episodes(revered_order, limit)
