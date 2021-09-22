from printout import fcs
from .episode_data import EpisodeData
from ..lister.session import SessionSingleton


class DPlayEpisodeData(EpisodeData):
    URL_PREFIX = r"https://www.discoveryplus.se"
    API_URL = "https://disco-api.discoveryplus.se"

    def __init__(self, episode_data=None, show_data=None, premium=False, verbose=False):
        super().__init__(episode_data, verbose)
        if episode_data is None:
            episode_data = {}
        if show_data is None:
            show_data = {}
        self.set_log_prefix("DPLAY_DATA")
        attr = episode_data.get("attributes", {})
        self.episode_path = attr.get("path", "")
        self._set(self.Keys.SeasonNumber, episode_data.get("seasonNumber", None))
        self._set(self.Keys.EpisodeNumber, episode_data.get("episodeNumber", None))
        self._set(self.Keys.EpisodeName, episode_data.get("name", None))
        self.sub_url = ""
        self.sub_m3u_url = ""
        self.is_premium = premium
        try:
            _show_name = show_data["data"]["attributes"]["name"]
            self._set(self.Keys.ShowName, _show_name)
        except KeyError as _:
            pass
        _id = int(self.raw.get("id"), 0)
        self._set(self.Keys.Id, _id)

    def __str__(self):
        string = f"{self.show} S{self.s}E{self.e} " \
                 f"\"{self.name}\" -- id:{self.id} -- url:{self.url()}"
        if self.sub_url:
            return string + f" -- sub_url: {self.sub_url}"
        return string

    def name(self):
        return f"{self.show} S{self.s}E{self.e}"

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