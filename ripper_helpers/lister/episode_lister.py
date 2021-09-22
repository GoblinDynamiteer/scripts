import re

from base_log import BaseLog


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
            if isinstance(filter_val, str):
                match = re.search(r"\d{1,3}", filter_val)
                if not match:
                    continue
                if filter_val.startswith(">"):
                    _val = int(match.group(0))
                    if ep_item.episode_num > _val:
                        filtered_list.append(ep_item)
                elif filter_val.startswith("<"):
                    _val = int(match.group(0))
                    if ep_item.episode_num < _val:
                        filtered_list.append(ep_item)
                elif int(filter_val) == ep_item.episode_num:
                    filtered_list.append(ep_item)
            else:
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


class EpisodeLister(BaseLog):
    VALID_FILTER_KEYS = ["season", "episode", "title", "date"]

    def __init__(self, url, verbose=False, save_json_data=False, get_clips=False):
        super().__init__(verbose=verbose)
        self.set_log_prefix("EPISODE_LISTER")
        self.url = url
        self.ep_list = []
        self.filter = {}
        self._save_json_data = save_json_data
        self._download_clips = get_clips
        self._sort_by_date = False
        if self._download_clips:
            self.log("will download clips!")

    @staticmethod
    def supports_url(url_str: str):
        raise NotImplementedError()

    def set_sort_by_date(self, state=True):
        if self._sort_by_date == state:
            return
        self._sort_by_date = state
        self.log(f"setting {self._sort_by_date:}")

    def set_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key not in self.VALID_FILTER_KEYS:
                print(f"invalid filter: {key}={val}")
            else:
                self.filter[key] = val

    def get_episodes(self, revered_order=False, limit=None):
        for filter_key, filter_val in self.filter.items():
            self.ep_list = apply_filter(self.ep_list, filter_key, filter_val)
        if self._sort_by_date:
            self.ep_list.sort(key=lambda x: x.airdate, reverse=revered_order)
        else:
            self.ep_list.sort(key=lambda x: (x.s, x.e), reverse=revered_order)
        if limit is not None:
            return self.ep_list[0:limit]
        return self.ep_list
