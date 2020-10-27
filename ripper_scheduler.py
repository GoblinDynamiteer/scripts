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

from ripper import PlayRipperYoutubeDl as youtube_ripper
from ripper import SubRipper as subrip
from ripper import retrive_sub_url
from ripper_helpers import EpisodeLister
from printing import cstr, pfcs, fcs

JSON_SCHEDULE_FILE = r"ripper_schedule.json"
WEEK_IN_SECONDS = 60 * 60 * 24 * 7

CFG = config.ConfigurationManager()


class TimeZoneInfo(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=+2)

    def dst(self, dt):
        return timedelta(hours=+2)


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


def date_to_full_color_str(datetime_obj: datetime):
    date_str = datetime_obj.strftime(r"%Y-%m-%d")
    time_str = datetime_obj.strftime(r"%T")
    return cstr(date_str, 166) + " " + cstr(time_str, 170)


def date_to_time_str(datetime_obj: datetime):
    return datetime_obj.strftime(r"%T")


def get_now():
    return datetime.now(tz=TimeZoneInfo())


def get_now_str():
    dt = datetime.now(tz=TimeZoneInfo())
    return date_to_full_str(dt)


def get_now_color_str():
    dt = datetime.now(tz=TimeZoneInfo())
    return date_to_full_color_str(dt)


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


def log(info_str, info_str_line2=""):
    log_prefix = "SCHEDULER"
    print(fcs(f"i[({log_prefix})]"),
          f"{get_now_color_str()}:", info_str)
    if info_str_line2:
        spaces = " " * len(f"({log_prefix}) ")
        print(f"{spaces}{info_str_line2}")


def print_seperator():
    pfcs(f"d[{'=' * 60}]")


class ScheduledShow():
    def __init__(self, data: dict):
        self.raw_data = data
        self.name = data["name"]
        self.dest_path = Path(data["dest"])
        self.filter_dict = data.get("filter", {})
        self.url = data["url"]
        self.use_title = data.get("use_title", False)
        self.disabled = data.get("disabled", False)
        self.skip_sub = data.get("skip_sub", False)
        self.downloaded_today = False
        self.airtimes = []

        pfcs(f"added show i[{self.name}]")
        for day, time in data["airtime"].items():
            self.airtimes.append(Airtime(day, time))

    def download(self, force=False):
        if not force and not self.should_download():
            return False
        log(fcs(f"trying to download episodes for i[{self.name}]"))
        for obj in self.get_url_objects():
            rip = youtube_ripper(obj.url(),
                                 dest=self.dest_path,
                                 ep_data=obj,
                                 verbose=True,
                                 use_title=self.use_title)
            file_path = None
            if not rip.file_already_exists():
                file_path = rip.download()
                if file_path and rip.download_succeeded:
                    log(fcs(f"downloaded: i[{str(file_path)}]"))
                    self.downloaded_today = True
                    write_to_log(self.name, str(file_path))
            else:
                file_path = rip.get_dest_path()
                log(
                    fcs(f"i[{file_path.name}] already exists, skipping dl..."))
            if file_path and not self.skip_sub:
                existing = subrip.vid_file_has_subs(file_path)
                if existing is not False:
                    log(
                        fcs(f"i[{existing.name}] already exists, skipping sub dl..."))
                    print_seperator()
                    continue
                srip = subrip(retrive_sub_url(obj),
                              str(file_path), verbose=True)
                if not srip.file_already_exists():
                    log(
                        fcs(f"trying to download subtitles: i[{srip.filename}]"))
                    srip.download()
                else:
                    log(
                        fcs(f"i[{srip.filename}] already exists, skipping sub dl..."))
            elif self.skip_sub:
                log(fcs(f"skipping subtitle download for i[{self.name}]"))
            print_seperator()
        return True

    def reset_downloaded_today(self):
        self.downloaded_today = False

    def should_download(self, show=True):
        if self.downloaded_today:
            return False
        sec_to = self.shortest_airtime()
        if sec_to > 0:
            delta = timedelta(seconds=sec_to)
            if show:
                log(fcs(f"b[{self.name}] airs in i[{delta}]..."))
        return sec_to < 0

    def shortest_airtime(self):
        if not self.downloaded_today:
            return min([at.seconds_to() for at in self.airtimes])
        at_list = []
        for at in self.airtimes:
            sec = at.seconds_to()
            if sec >= 0:
                at_list.append(sec)
        return min(at_list) if at_list else WEEK_IN_SECONDS

    def get_url_objects(self):
        lister = EpisodeLister.get_lister(self.url, verbose_logging=True)
        if self.filter_dict:
            lister.set_filter(**self.filter_dict)
        return lister.get_episodes(revered_order=True,
                                   limit=5,
                                   )

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
    except Exception as error:
        print(error)
        pfcs(f"could parse json from file: e[{str(file_path)}]")
        sys.exit(1)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force",
                        "-f",
                        dest="force_download",
                        action="store_true",
                        help="force check/download all shows")
    parser.add_argument("--set-all-downloaded",
                        "-s",
                        dest="set_all_dl",
                        action="store_true",
                        help="sets all shows as downloaded today")
    args = parser.parse_args()
    schedule_data = parse_json_schedule()
    sheduled_shows = []
    for show_data in schedule_data:
        sheduled_show = ScheduledShow(show_data)
        if not sheduled_show.disabled:
            sheduled_shows.append(sheduled_show)
        else:
            log(fcs(f"show o[{sheduled_show.name}] is disabled, skipping..."))
    if not sheduled_shows:
        print("no shows to process.. exiting.")
        sys.exit(1)
    if args.set_all_dl:
        for show in sheduled_shows:
            if show.should_download(show=False):
                show.downloaded_today = True
                log(fcs(f"setting i[{show.name}] as downloaded today"))
    if args.force_download:
        for show in sheduled_shows:
            show.download(force=True)
    weekday = today_weekday()
    log(fcs(f"today is b[{Day(weekday).name}]"))
    while True:
        if weekday != today_weekday():
            log("new day, resetting all show \"downloaded\" flags")
            for show in sheduled_shows:
                show.reset_downloaded_today()
            weekday = today_weekday()
            log(fcs(f"today is b[{Day(weekday).name}]"))
        log("checking shows...")
        sleep_to_next_airdate = True
        for show in sheduled_shows:
            show.download()
            if show.should_download(show=False):
                sleep_to_next_airdate = False
        sleep_time = None
        name = None
        sleep_time_delta = None
        print_seperator()
        if sleep_to_next_airdate:
            for show in sheduled_shows:
                airtime = show.shortest_airtime()
                if airtime < 0:
                    if show.should_download():
                        log(fcs(f"w[warning] {show.name} seems has not "
                                f"been flagged as downloaded today.."))
                    continue
                elif sleep_time is None:
                    sleep_time = airtime
                    name = show.name
                else:
                    if sleep_time > airtime:
                        sleep_time = airtime
                        name = show.name
            sleep_time += 10
            sleep_time_delta = timedelta(seconds=sleep_time)
            wake_date = get_now() + sleep_time_delta
            wake_date_str = date_to_time_str(wake_date)
            if wake_date.weekday() != weekday:
                wake_date_str = date_to_full_str(wake_date)
            log(fcs(f"sleeping p[{sleep_time_delta}] (to {wake_date_str})",
                    f"next show is b[{name}]"))
        else:
            sleep_time = 60 * 5  # try again in 5 minutes, show has failed dl
            sleep_time_delta = timedelta(seconds=sleep_time)
            log(fcs(f"sleeping p[{sleep_time_delta}]"))
        sleep(sleep_time)


if __name__ == "__main__":
    main()
