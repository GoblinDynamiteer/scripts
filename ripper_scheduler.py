#!/usr/bin/python3.8

import argparse
import json
import os
import sys
from time import sleep
from datetime import datetime, timedelta, tzinfo
from enum import Enum
from pathlib import Path
from threading import Thread
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from util import Singleton

import config

from ripper import PlayRipperYoutubeDl
from ripper import SubRipper
from ripper import retrive_sub_url
from ripper_helpers import EpisodeLister
from printing import cstr, pfcs, fcs

JSON_SCHEDULE_FILE = r"ripper_schedule.json"
WEEK_IN_SECONDS = 60 * 60 * 24 * 7

CFG = config.ConfigurationManager()

fast_api_app = FastAPI()


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
    if not path.exists() or not path.is_file():
        print(f"warning: could not write to log: {str(path)}")
        return
    with open(path, "a+") as log_file:
        log_file.write(f"{get_now_str()} : {show_str} {file_str}\n")


def today_weekday():
    now = get_now()
    return now.weekday()


class Airtime:
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


def print_separator():
    pfcs(f"d[{'=' * 60}]")


class DownloaderStatus(Enum):
    Init = "init"
    Sleeping = "sleeping"
    Downloading = "downloading"
    DownloadingSubtitles = "downloadingSubs"
    ProcessingShow = "processingShow"


class SharedData(metaclass=Singleton):
    _run = True
    _downloader_info = {}

    @property
    def run(self):
        return self._run

    @run.setter
    def run(self, state: bool):
        if state == self._run:
            return
        log(f"setting run state to: {state}")
        self._run = state

    def add_downloaded_item(self, item):
        if "downloaded_items" not in self._downloader_info:
            self._downloader_info["downloaded_items"] = []
        self._downloader_info["downloaded_items"].append(item)

    def add_error(self, error_str):
        if "errors" not in self._downloader_info:
            self._downloader_info["errors"] = []
        self._downloader_info["errors"].append({"date": get_now(), "error": error_str})

    def get_info(self, key=None, default=None):
        if "last_update" in self._downloader_info:
            last = self._downloader_info["last_update"]
            try:
                seconds = (get_now() - last).seconds
                self._downloader_info["last_update_secs_since"] = seconds
            except Exception as _:
                pass
        if key is None:
            return self._downloader_info
        return self._downloader_info.get(key, default)

    def set_info(self, key, value):
        if isinstance(value, DownloaderStatus):
            self._downloader_info[key] = value.value
        else:
            self._downloader_info[key] = value
        self._downloader_info["last_update"] = get_now()


class ScheduledShow:
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

    def download(self, force=False, simulate=False):
        if not force and not self.should_download():
            return False
        log(fcs(f"trying to download episodes for i[{self.name}]"))
        for obj in self.get_url_objects():
            SharedData().set_info("status", DownloaderStatus.ProcessingShow)
            ripper = PlayRipperYoutubeDl(obj.url(),
                                         sim=simulate,
                                         dest=self.dest_path,
                                         ep_data=obj,
                                         verbose=True,
                                         use_title=self.use_title)
            if not ripper.file_already_exists():
                try:
                    SharedData().set_info("status", DownloaderStatus.Downloading)
                    SharedData().set_info("file_name", ripper.filename or "None")
                    file_path = ripper.download()
                    SharedData().set_info("status", DownloaderStatus.ProcessingShow)
                except Exception as error:
                    log(fcs(f"e[got exception] when trying to download {self.name}"))
                    SharedData().add_error(str(error))
                    return False
                if file_path and ripper.download_succeeded:
                    SharedData().add_downloaded_item(file_path)
                    log(fcs(f"downloaded: i[{str(file_path)}]"))
                    self.downloaded_today = True
                    if not simulate:
                        write_to_log(self.name, str(file_path))
            else:
                file_path = ripper.get_dest_path()
                log(fcs(f"i[{file_path.name}] already exists, skipping dl..."))
            if file_path and not self.skip_sub and not simulate:
                existing = SubRipper.vid_file_has_subs(file_path)
                if existing is not False:
                    log(fcs(f"i[{existing.name}] already exists, skipping sub dl..."))
                    print_separator()
                    continue
                sub_rip = SubRipper(retrive_sub_url(obj), str(file_path), verbose=True)
                if not sub_rip.file_already_exists():
                    log(fcs(f"trying to download subtitles: i[{sub_rip.filename}]"))
                    try:
                        SharedData().set_info("status", DownloaderStatus.DownloadingSubtitles)
                        SharedData().set_info("file_name", sub_rip.filename)
                        sub_rip.download()
                        SharedData().set_info("status", DownloaderStatus.ProcessingShow)
                    except Exception as error:
                        log(fcs(f"e[got exception] when trying to download subs for {self.name}"))
                        SharedData().add_error(str(error))
                else:
                    log(fcs(f"i[{sub_rip.filename}] already exists, skipping sub dl..."))
            elif self.skip_sub:
                log(fcs(f"skipping subtitle download for i[{self.name}]"))
            print_separator()
        return True

    def reset_downloaded_today(self):
        self.downloaded_today = False

    def should_download(self, print_to_log=True):
        if self.downloaded_today:
            return False
        sec_to = self.shortest_airtime()
        if sec_to > 0:
            delta = timedelta(seconds=sec_to)
            if print_to_log:
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
        return lister.get_episodes(revered_order=True, limit=5)

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


def determine_sleep_time(scheduled_shows: list):
    sleep_time = None
    name = None
    for show in scheduled_shows:
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
    return name, sleep_time


def get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate",
                        action="store_true")
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
    parser.add_argument("--web",
                        dest="use_fast_api",
                        action="store_true")
    args = parser.parse_args()
    return args


def get_show_list_from_json():
    scheduled_shows = []
    schedule_data = parse_json_schedule()
    for show_data in schedule_data:
        scheduled_show = ScheduledShow(show_data)
        if not scheduled_show.disabled:
            scheduled_shows.append(scheduled_show)
        else:
            log(fcs(f"show o[{scheduled_show.name}] is disabled, skipping..."))
    return scheduled_shows


@fast_api_app.get("/", response_class=HTMLResponse)
def root():
    data = SharedData()
    resp_html_head = f"<head><title>{Path(__file__).name.upper()} WebInfo</title></head>"
    resp_content = f"status: {data.get_info('status') or 'Unknown'}<br>"
    file_item = data.get_info("file_name")
    if file_item and file_item != "None":
        resp_content += f"file being processed: {file_item}<br>"
    secs_since = data.get_info("last_update_secs_since", default="Unknown")
    resp_content += f"seconds since update: {secs_since}<br>"
    next_timedelta = timedelta(seconds=data.get_info("next_show_seconds_until", default=0))
    resp_content += f"next: {data.get_info('next_show', default='-')} in {next_timedelta}<p>"
    resp_content += "downloaded files:<br>"
    dl_items = data.get_info("downloaded_items", default=[])
    if dl_items:
        resp_content += "<ul>"
        resp_content += "\n".join(f"<li>{dl}</li>" for dl in dl_items)
        resp_content += "</ul>"
    else:
        resp_content += "None"
    return f"<html>{resp_html_head}<body>{resp_content}</body></html>"


def thread_downloader(cli_args):
    SharedData().set_info("status", DownloaderStatus.Init)
    scheduled_shows = get_show_list_from_json()
    if not scheduled_shows:
        print("no shows to process.. exiting.")
        return
    if cli_args.set_all_dl:
        for show in scheduled_shows:
            if show.should_download(print_to_log=False):
                show.downloaded_today = True
                log(fcs(f"setting i[{show.name}] as downloaded today"))
    if cli_args.force_download:
        for show in scheduled_shows:
            show.download(force=True, simulate=cli_args.simulate)
    weekday = today_weekday()
    log(fcs(f"today is b[{Day(weekday).name}]"))
    while True:
        if weekday != today_weekday():
            log("new day, resetting all show \"downloaded\" flags")
            for show in scheduled_shows:
                show.reset_downloaded_today()
            weekday = today_weekday()
            log(fcs(f"today is b[{Day(weekday).name}]"))
        log("checking shows...")
        sleep_to_next_airdate = True
        for show in scheduled_shows:
            show.download()
            SharedData().set_info("file_name", "None")
            if show.should_download(print_to_log=False):
                sleep_to_next_airdate = False
        print_separator()
        if sleep_to_next_airdate:
            name, sleep_time = determine_sleep_time(scheduled_shows)
            sleep_time_delta = timedelta(seconds=sleep_time)
            wake_date = get_now() + sleep_time_delta
            wake_date_str = date_to_time_str(wake_date)
            if wake_date.weekday() != weekday:
                wake_date_str = date_to_full_str(wake_date)
            log(fcs(f"sleeping p[{sleep_time_delta}] (to {wake_date_str}) - "
                    f"next show is b[{name}]"))
            SharedData().set_info("next_show", name)
        else:
            sleep_time = 60 * 5  # try again in 5 minutes, show has failed dl
            sleep_time_delta = timedelta(seconds=sleep_time)
            log(fcs(f"sleeping p[{sleep_time_delta}]"))
        SharedData().set_info("status", DownloaderStatus.Sleeping)
        while sleep_time > 0:
            SharedData().set_info("next_show_seconds_until", sleep_time)
            sleep_time -= 10
            sleep(10)
            if not SharedData().run:
                log("stopping downloader")
                return


def main():
    args = get_cli_args()
    dl_thread = Thread(target=thread_downloader, args=[args])
    dl_thread.daemon = True
    dl_thread.start()
    if args.use_fast_api:
        uvicorn.run(fast_api_app, host="0.0.0.0", port=8000)
        SharedData().run = False
    else:
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt as _:
            SharedData().run = False


if __name__ == "__main__":
    main()
