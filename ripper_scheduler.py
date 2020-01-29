#!/usr/bin/python3.8

import json
import os
import sys
from time import sleep
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from ripper import _rip_with_youtube_dl as rip
from ripper import _subtitle_dl as subrip

from ripper_helpers import Tv4PlayEpisodeLister, DPlayEpisodeLister

from printing import cstr

JSON_SCHEDULE_FILE = r"ripper_schedule.json"


class Day(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


DAY = {"mon": Day.Monday,
       "tue": Day.Tuesday,
       "wed": Day.Wednesday,
       "thu": Day.Thursday,
       "fri": Day.Friday,
       "sat": Day.Saturday,
       "sun": Day.Sunday}


def today_weekday():
    now = datetime.now()
    return now.weekday()


class Airtime():
    def __init__(self, day_str: str, time_str: str):
        time_list = time_str.split(":")
        self.hour = int(time_list[0])
        self.min = int(time_list[1])
        self.weekday = DAY[day_str]

    def next_airdate(self):
        weekday = today_weekday()
        weekday_air = self.weekday.value
        days_to = 0
        while weekday != weekday_air:
            days_to += 1
            if weekday == Day.Sunday.value:
                weekday = Day.Monday.value
            else:
                weekday += 1
        airdate = datetime.now() + timedelta(days=days_to)
        return airdate.replace(hour=self.hour,
                               minute=self.min,
                               second=0,
                               microsecond=0)

    def seconds_to(self):
        return int((self.next_airdate() - datetime.now()).total_seconds())


class ScheduledShow():
    def __init__(self, data: dict):
        self.raw_data = data
        self.name = data["name"]
        self.dest_path = Path(data["dest"])
        self.filter_dict = data.get("filter", {})
        self.url = data["url"]
        self.use_title = data.get("use_title", False)
        self.site = "TV4Play" if "tv4" in self.url else "DPlay"
        self.downloaded_today = False
        self.airtimes = []

        print(f"added {self.name}")
        for day, time in data["airtime"].items():
            self.airtimes.append(Airtime(day, time))

    def download(self, force=False):
        if not self.should_download() and not force:
            return False
        print(f"trying to download {self.name}")
        for obj in self.get_url_objects():
            filename = rip(obj.url(),
                           str(self.dest_path),
                           self.site,
                           use_title=self.use_title)
            if filename:
                print(f"downloaded: {filename}")
                self.downloaded_today = True
                subrip(filename)
        return True

    def reset_downloaded_today(self):
        self.downloaded_today = False

    def should_download(self):
        if self.downloaded_today:
            return False
        return self.shortest_airtime() < 0

    def shortest_airtime(self):
        return min([at.seconds_to() for at in self.airtimes])

    def get_url_objects(self):
        lister = None
        rev_order = True
        if "dplay" in self.url:
            lister = DPlayEpisodeLister(self.url)
        elif "tv4play" in self.url:
            lister = Tv4PlayEpisodeLister(self.url)
            rev_order = False
        else:
            return []
        if self.filter_dict:
            lister.set_filter(**self.filter_dict)
        return lister.list_episode_urls(revered_order=rev_order,
                                        limit=5,
                                        objects=True)

    def get_url_list(self):
        return [obj.url() for obj in self.get_url_objects()]


def parse_json_schedule():
    file_path = Path(os.path.realpath(__file__)).parent / JSON_SCHEDULE_FILE
    if not file_path.exists():
        print(f"could not find file: {str(file_path)}")
        sys.exit(1)
    try:
        with open(file_path) as json_file:
            data = json.load(json_file)
    except:
        print(f"could parse json from file: {str(file_path)}")
        sys.exit(1)
    return data


if __name__ == "__main__":
    TIME_TO_SLEEP_S = (5 * 60) # 5 minutes
    schedule_data = parse_json_schedule()
    sheduled_shows = []
    for show_data in schedule_data:
        sheduled_shows.append(ScheduledShow(show_data))
    if not sheduled_shows:
        print("no shows to process.. exiting.")
        sys.exit(1)
    weekday = today_weekday()
    print(f"today is {Day(weekday).name}")
    for show in sheduled_shows:
        show.download(force=True)
    while True:
        if weekday != today_weekday():
            print("new day, resetting all show \"downloaded\" flags")
            for show in sheduled_shows:
                show.reset_downloaded_today()
            weekday = today_weekday()
            print(f"today is {Day(weekday).name}")
        print(f"{datetime.now()}: checking shows....")
        show.download()
        print(f"sleeping {TIME_TO_SLEEP_S / 60} minutes...")
        sleep(TIME_TO_SLEEP_S)
