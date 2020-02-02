#!/usr/bin/python3.8

import argparse
import json
import os
import sys
from time import sleep
from datetime import datetime, timedelta, tzinfo
from enum import Enum
from pathlib import Path

import config

from ripper import _youtube_dl as rip
from ripper import _subtitle_dl as subrip
from ripper_helpers import Tv4PlayEpisodeLister, DPlayEpisodeLister
from printing import cstr, pfcs

JSON_SCHEDULE_FILE = r"ripper_schedule.json"

CFG = config.ConfigurationManager()


class TimeZoneInfo(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=+1)

    def dst(self, dt):
        return timedelta(hours=+1)


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


def date_to_full_str(datetime_obj: datetime):
    return datetime_obj.strftime(r"%Y-%m-%d %T")


def date_to_time_str(datetime_obj: datetime):
    return datetime_obj.strftime(r"%T")


def get_now():
    return datetime.now(tz=TimeZoneInfo())


def get_now_str():
    dt = datetime.now(tz=TimeZoneInfo())
    return date_to_full_str(dt)


def write_to_log(show_str, file_str):
    path = Path(CFG.path("ripper_log"))
    if not path.is_file():
        print(f"warning: could not write to log: {str(path)}")
        return
    with open(path, "a+") as log_file:
        log_file.write(f"{get_now_str()} : {show_str} {file_str}\n")


def today_weekday():
    now = get_now()
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
        airdate = get_now() + timedelta(days=days_to)
        return airdate.replace(hour=self.hour,
                               minute=self.min,
                               second=0,
                               microsecond=0)

    def seconds_to(self):
        return int((self.next_airdate() - get_now()).total_seconds())


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

        pfcs(f"added show i[{self.name}]")
        for day, time in data["airtime"].items():
            self.airtimes.append(Airtime(day, time))

    def download(self, force=False):
        if not force and not self.should_download():
            return False
        pfcs(f"trying to download i[{self.name}]")
        for obj in self.get_url_objects():
            filename = rip(url=obj.url(),
                           dl_loc=str(self.dest_path),
                           use_title=self.use_title)
            if filename:
                pfcs(f"downloaded: i[{filename}]")
                self.downloaded_today = True
                write_to_log(self.name, filename)
                subrip(self.url, filename)
        return True

    def reset_downloaded_today(self):
        self.downloaded_today = False

    def should_download(self):
        if self.downloaded_today:
            return False
        sec_to = self.shortest_airtime()
        if sec_to > 0:
            delta = timedelta(seconds=sec_to)
            pfcs(f"b[{self.name}] airs in i[{delta}]...")
        return sec_to < 0

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
                                        limit=2,
                                        objects=True)

    def get_url_list(self):
        return [obj.url() for obj in self.get_url_objects()]


def parse_json_schedule():
    file_path = Path(os.path.realpath(__file__)).parent / JSON_SCHEDULE_FILE
    if not file_path.exists():
        pfcs(f"could not find file: e[{str(file_path)}]")
        sys.exit(1)
    try:
        with open(file_path) as json_file:
            data = json.load(json_file)
    except:
        pfcs(f"could parse json from file: e[{str(file_path)}]")
        sys.exit(1)
    return data


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--force",
                        "-f",
                        dest="force_download",
                        action="store_true",
                        help="force check/download all shows")
    ARGS = PARSER.parse_args()
    schedule_data = parse_json_schedule()
    sheduled_shows = []
    for show_data in schedule_data:
        sheduled_shows.append(ScheduledShow(show_data))
    if not sheduled_shows:
        print("no shows to process.. exiting.")
        sys.exit(1)
    if ARGS.force_download:
        for show in sheduled_shows:
            show.download(force=True)
    weekday = today_weekday()
    pfcs(f"today is b[{Day(weekday).name}]")
    while True:
        if weekday != today_weekday():
            print("new day, resetting all show \"downloaded\" flags")
            for show in sheduled_shows:
                show.reset_downloaded_today()
            weekday = today_weekday()
            pfcs(f"today is b[{Day(weekday).name}]")
        print(f"{get_now_str()}: checking shows...")
        for show in sheduled_shows:
            show.download()
        sleep_time = None
        name = None
        for show in sheduled_shows:
            if sleep_time is None:
                sleep_time = show.shortest_airtime()
                name = show.name
            else:
                airtime = show.shortest_airtime()
                if sleep_time > airtime:
                    sleep_time = airtime
                    name = show.name
        sleep_time += 10
        sleep_time_delta = timedelta(seconds=sleep_time)
        wake_date = get_now() + sleep_time_delta
        wake_date_str = date_to_time_str(wake_date)
        if wake_date.weekday() != weekday:
            wake_date_str = date_to_full_str(wake_date)
        pfcs(f"d[{'=' * 50}]")
        pfcs(f"sleeping p[{sleep_time_delta}] (to {wake_date_str}), "
             f"next show is p[{name}]")
        sleep(sleep_time)
