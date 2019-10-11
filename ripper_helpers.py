#!/usr/bin/python3.7

import hashlib
import random
import re

from requests import Session


class DPlayEpisodeLister():
    API_URL = "https://disco-api.dplay.se"
    SITE_URL = "https://www.dplay.se"

    def __init__(self, url):
        if not "dplay.se" in url:
            print("cannot handle non-dplay.se urls!")
        self.url = url
        self.session = Session()
        self.check_token()

    def check_token(self) -> bool:
        deviceid = hashlib.sha256(
            bytes(int(random.random() * 1000))).hexdigest()
        url = f"{self.API_URL}/token?realm=dplayse&deviceId={deviceid}&shortlived=true"
        res = self.session.get(url)
        return res.status_code < 400

    def list_episode_urls(self, revered_order=False, limit=None):
        match = re.search(
            "/(program|programmer|videos|videoer)/([^/]+)", self.url)
        if not match:
            print("failed to determine show path!")
            return
        res = self.session.get(
            f"{self.API_URL}/content/shows/{match.group(2)}")

        show_id = res.json()["data"]["id"]
        season_numbers = res.json()["data"]["attributes"]["seasonNumbers"]

        url_list = []

        for season_number in season_numbers:
            qyerystring = (
                "include=primaryChannel,show&filter[videoType]=EPISODE"
                f"&filter[show.id]={show_id}&filter[seasonNumber]={season_number}"
                "&page[size]=100&sort=seasonNumber,episodeNumber,-earliestPlayableStart"
            )
            res = self.session.get(
                f"{self.API_URL}/content/videos?{qyerystring}")
            for data in res.json()["data"]:
                episode_path = data["attributes"]["path"]
                url_list.append(f"{self.SITE_URL}/videos/{episode_path}")

        if revered_order:
            url_list.reverse()
        if limit:
            return url_list[0:limit]
        return url_list


if __name__ == "__main__":
    # For Testing....
    URL = "https://www.dplay.se/program/alla-mot-alla-med-filip-och-fredrik"
    DPEL = DPlayEpisodeLister(URL)
    EPS = DPEL.list_episode_urls()

    print("ALL EPS")
    for ep in EPS:
        print(ep)

    print("ALL EPS REVERSED")
    EPS = DPEL.list_episode_urls(revered_order=True)
    for ep in EPS:
        print(ep)

    print("FIRST 5 EPS")
    EPS = DPEL.list_episode_urls(revered_order=False, limit=5)
    for ep in EPS:
        print(ep)

    print("LAST 5 EPS")
    EPS = DPEL.list_episode_urls(revered_order=True, limit=5)
    for ep in EPS:
        print(ep)
