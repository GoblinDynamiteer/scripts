from .episode_data import EpisodeData
from printout import fcs

from ..lister.session import SessionSingleton

class ViafreeEpisodeData(EpisodeData):
    URL_PREFIX = r"https://www.viafree.se"
    CONT_URL_PREFIX = r"https://viafree-content.mtg-api.com/viafree-content/v1/se/path/"

    def __init__(self, episode_data=None, verbose=False):
        super().__init__(episode_data, verbose)
        if episode_data is None:
            episode_data = {}
        self.set_log_prefix("VIAFREE_DATA")
        self.episode_path = episode_data.get("publicPath", "")
        episode_info = episode_data.get("episode", {})
        self._set(self.Keys.SeasonNumber, episode_data.get("seasonNumber", None))
        self._set(self.Keys.EpisodeNumber, episode_data.get("episodeNumber", None))
        self._set(self.Keys.Id, episode_data.get("guid", None))
        self._set(self.Keys.EpisodeName, episode_data.get("title", None))
        self._set(self.Keys.ShowName, episode_data.get("seriesTitle", None))
        self.sub_url = ""

    def __str__(self):
        return f"{self.show} S{self.s}E{self.e} " \
               f"\"{self.name}\" -- id:{self.id} -- url:{self.url()}"

    def url(self):
        return f"{self.URL_PREFIX}{self.episode_path}"

    def subtitle_url(self):
        if self.sub_url:
            self.log("already retrieved/gotten subtitle url")
            return self.sub_url
        content_url = f"{self.CONT_URL_PREFIX}{self.episode_path}"
        res = SessionSingleton().get(content_url)
        try:
            stream_url = res.json()[
                '_embedded']['viafreeBlocks'][0]['_embedded']['program']['_links']['streamLink']['href']
            self.log(fcs("got stream url"), fcs(f"i[{stream_url}]"))
        except KeyError as _:
            self.log(fcs("failed to retrieve stream url from:"),
                     fcs(f"o[{content_url}]"))
            return ""
        res = SessionSingleton().get(stream_url)
        try:
            sub_url = self._find_sv_sub(res.json())
            if not sub_url:
                raise ValueError()
            self.log(fcs("got sv subtitle url"), fcs(f"i[{sub_url}]"))
            self.sub_url = sub_url
        except (KeyError, IndexError, ValueError) as _:
            self.log(fcs("failed to retrieve subtitle url from:"),
                     fcs(f"o[{stream_url}]"))
            return ""
        return self.sub_url

    def _find_sv_sub(self, data: dict):
        try:
            _list = data["embedded"]["subtitles"]
        except IndexError as error:
            self.warn("could not find subtitle list for episode!")
            return None
        if not isinstance(_list, list):
            self.warn('data["embedded"]["subtitles"] was not a list!')
            return None
        sv_url = None
        for _sub_data in _list:
            data = _sub_data.get("data", {})
            lang = data.get("language", None)
            if lang:
                self.log(fcs(f"found sub for language: i[{lang}]"))
            if lang == "sv":
                sv_url = _sub_data.get("link", {}).get("href", None)
        return sv_url
