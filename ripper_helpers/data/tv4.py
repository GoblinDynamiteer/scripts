

from datetime import datetime

from urllib.parse import quote

from ..lister.session import SessionSingleton
from .episode_data import EpisodeData
from printout import fcs


class Tv4PlayEpisodeData(EpisodeData):
    def __init__(self, episode_data=None, verbose=False):
        super().__init__(episode_data, verbose)
        if episode_data is None:
            episode_data = {}
        self.set_log_prefix("TV4PLAY_DATA")
        self._set(self.Keys.SeasonNumber, episode_data.get("season", None))
        self._set(self.Keys.EpisodeNumber, episode_data.get("episode", None))
        self._set(self.Keys.Id, episode_data.get("id", None))
        self._set(self.Keys.EpisodeName, episode_data.get("title", None))
        self._set(self.Keys.ShowName, episode_data.get("program_nid", None))
        self._set(self.Keys.Url, episode_data.get("url", None))
        self._parse_date(episode_data)
        self.sub_url_list = []
        self.sub_m3u_url = ""

    def __str__(self):
        return ""

    def _parse_date(self, ep_data: dict):
        if not ep_data:
            return
        _date_str = ep_data.get("published_date_time", "")
        if not _date_str:
            return
        if _date_str.endswith("Z"):
            _date_str = _date_str[:-1]
        try:
            _date = datetime.fromisoformat(_date_str)
            self._set(self.Keys.DateAired, _date)
        except ValueError as _:
            pass

    def url(self):
        return f"https://www.tv4play.se/program/{quote(self.show)}/{self.id}"

    def subtitle_url(self) -> list:
        if self.sub_url_list:
            self.log("already retrieved/gotten subtitle url")
            return self.sub_url_list
        if self.id == 0:
            self.log("show id is 0, cannot retrieve subtitle url")
            return []
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