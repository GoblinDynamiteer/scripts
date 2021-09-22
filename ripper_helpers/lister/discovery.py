
import re
from datetime import datetime

from .episode_lister import EpisodeLister
from .session import SessionSingleton

from ..data.discovery import DPlayEpisodeData


class DPlayEpisodeLister(EpisodeLister):
    API_URL = "https://disco-api.discoveryplus.se"

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self.set_log_prefix("DPLAY_LISTER")
        if not "discoveryplus.se" in url:
            print("cannot handle non discoveryplus.se urls!")
        if not self.check_token():
            print("failed to get session for dplay")
        else:
            self.log("successfully got session")

    @staticmethod
    def supports_url(url_str: str) -> bool:
        return "discoveryplus.se" in url_str

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
        try:
            show_id = res.json()["data"]["id"]
            season_numbers = res.json()["data"]["attributes"]["seasonNumbers"]
        except KeyError:
            self.error(f"could not get data from response for: {self.url}")
            return []
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
                obj = DPlayEpisodeData(data,
                                       show_data,
                                       verbose=self.print_log,
                                       premium=is_premium)
                self.ep_list.append(obj)
        return super().get_episodes(revered_order, limit)