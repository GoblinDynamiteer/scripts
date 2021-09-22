from .episode_data import EpisodeData


class SVTPlayEpisodeData(EpisodeData):

    def __init__(self, episode_data=None, verbose=False):
        super().__init__(episode_data, verbose)
        self.set_log_prefix("SVTPLAY_DATA")

    def set_data(self, **ep_data):
        self._set(self.Keys.SeasonNumber, ep_data.get("season_num", None))
        self._set(self.Keys.EpisodeNumber, ep_data.get("episode_num", None))
        self._set(self.Keys.Id, ep_data.get("id", None))
        self._set(self.Keys.EpisodeName, ep_data.get("title", None))
        self._set(self.Keys.ShowName, ep_data.get("show", None))
        self._set(self.Keys.Url, ep_data.get("url", None))

    def __str__(self):
        return ""

    def url(self):
        _suffix = self._get(self.Keys.Url, default="")
        return f"https://www.svtplay.se{_suffix}"

    def subtitle_url(self):
        return self.url()
