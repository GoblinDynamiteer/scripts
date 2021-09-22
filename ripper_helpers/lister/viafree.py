
import json
from urllib.parse import urlparse

from requests import Session

from .episode_lister import EpisodeLister
from ..data.viafree import ViafreeEpisodeData

from printout import fcs


class ViafreeEpisodeLister(EpisodeLister):
    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self.set_log_prefix("VIAFREE_LISTER")
        if not self.supports_url(url):
            print("cannot handle non-viafree.se urls!")
        self.url = url
        self.session = Session()
        self.filter = {}

    @staticmethod
    def supports_url(url_str: str) -> bool:
        return "viafree.se" in url_str

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