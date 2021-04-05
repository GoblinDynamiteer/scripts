#!/usr/bin/python3.8

import argparse
import json
import sys
from time import sleep
from datetime import datetime, timedelta, tzinfo
from enum import Enum
from pathlib import Path
from threading import Thread
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from util import Singleton
from util import BaseLog

import config

from ripper import PlayRipperYoutubeDl
from ripper import SubRipper
from ripper import retrive_sub_url
from ripper_helpers import EpisodeLister
from printing import cstr, pfcs, fcs

WEEK_IN_SECONDS = 60 * 60 * 24 * 7

CFG = config.ConfigurationManager()

fast_api_app = FastAPI()
templates = Jinja2Templates(directory="files/fast_api/templates")
fast_api_app.mount("/static", StaticFiles(directory="files/fast_api/css"), name="static")


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

    def next_airdate(self) -> datetime:
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

    def seconds_to(self) -> int:
        return int((self.next_airdate() - get_now()).total_seconds())


class ScheduledShow(BaseLog):
    def __init__(self, data: dict, cli_args):
        super().__init__(cli_args.verbose)
        self.raw_data = data
        self.name = data["name"]
        self.dest_path = self._parse_dest_path(data["dest"])
        self.log(f"set dest path: {self.dest_path}")
        self.filter_dict = data.get("filter", {})
        self.url = data["url"]
        self.use_title = data.get("use_title", False)
        if data.get("process", False):
            self.disabled = False
        else:
            self.disabled = True
        self.skip_sub = data.get("skip_sub", False)
        self.downloaded_today = False
        self.airtimes = []
        self.set_log_prefix(f"show_{self.name}".replace(" ", "_").upper())
        self.log("init")
        pfcs(f"added show i[{self.name}]")
        for day, time in data["airtime"].items():
            self.airtimes.append(Airtime(day, time))
        if not self.disabled:
            self._validate()

    def _parse_dest_path(self, path_str):
        if "$TV_TEMP" in path_str:
            tv_temp_path = Path(CFG.path("misc")) / "tv_temp"
            return Path(path_str.replace("$TV_TEMP", str(tv_temp_path)))
        if "$TV" in path_str:
            return Path(path_str.replace("$TV", str(CFG.path("tv"))))
        return Path(path_str)

    def _validate(self):
        if not self.dest_path.exists():
            self.warn(fcs(f"no such destination dir: w[{self.dest_path}] : ({self.name})"))

    def download(self, force=False, simulate=False):
        if not force and not self.should_download():
            return False
        self.log(fcs(f"trying to download episodes for i[{self.name}]"))
        objects = self.get_url_objects()
        if not objects:
            self.warn(fcs(f"failed to retrieve urls for i[{self.name}], setting as downloaded..."))
            self.downloaded_today = True
            return False
        for obj in objects:
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
                    self.error(fcs(f"got exception when trying to download {self.name}"))
                    SharedData().add_error(str(error))
                    return False
                if file_path and ripper.download_succeeded:
                    SharedData().add_downloaded_item(file_path)
                    self.log(fcs(f"downloaded: i[{str(file_path)}]"))
                    self.downloaded_today = True
                    if not simulate:
                        write_to_log(self.name, str(file_path))
            else:
                file_path = ripper.get_dest_path()
                self.log(fcs(f"i[{file_path.name}] already exists, skipping dl..."))
            if file_path and not self.skip_sub and not simulate:
                existing = SubRipper.vid_file_has_subs(file_path)
                if existing is not False:
                    self.log(fcs(f"i[{existing.name}] already exists, skipping sub dl..."))
                    print_separator()
                    continue
                sub_rip = SubRipper(retrive_sub_url(obj), str(file_path), verbose=True)
                if not sub_rip.file_already_exists():
                    self.log(fcs(f"trying to download subtitles: i[{sub_rip.filename}]"))
                    try:
                        SharedData().set_info("status", DownloaderStatus.DownloadingSubtitles)
                        SharedData().set_info("file_name", sub_rip.filename)
                        sub_rip.download()
                        SharedData().set_info("status", DownloaderStatus.ProcessingShow)
                    except Exception as error:
                        self.error(fcs(f"got exception when trying to download subs for {self.name}"))
                        SharedData().add_error(str(error))
                else:
                    self.log(fcs(f"i[{sub_rip.filename}] already exists, skipping sub dl..."))
            elif self.skip_sub:
                self.log(fcs(f"skipping subtitle download for i[{self.name}]"))
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
                self.log(fcs(f"b[{self.name}] airs in i[{delta}]..."))
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


class ScheduledShowList(BaseLog):
    def __init__(self, cli_args):
        super().__init__(verbose=cli_args.verbose)
        self.set_log_prefix("show_list".upper())
        self._cli_args = cli_args
        self.valid = False
        self._list = self._init_shows()
        self.log(f"processing {len(self._list)} shows")

    def _init_shows(self):
        scheduled_shows = []
        schedule_data = self._parse_json_schedule()
        if schedule_data is None:
            return []
        self.valid = True
        for show_data in schedule_data:
            scheduled_show = ScheduledShow(show_data, self._cli_args)
            if not scheduled_show.disabled:
                scheduled_shows.append(scheduled_show)
            else:
                log(fcs(f"show o[{scheduled_show.name}] is disabled, skipping..."))
        return scheduled_shows

    def _parse_json_schedule(self):
        file_path = self._cli_args.json_file
        if not file_path.exists():
            self.error(f"could not find file: e[{file_path}]")
            return None
        try:
            with open(file_path) as json_file:
                return json.load(json_file)
        except Exception as error:
            print(error)
            self.error(f"could parse json file: e[{file_path}]")
        return None

    def empty(self):
        return False if self._list else True

    def next_show(self) -> [ScheduledShow, None]:
        if not self._list:
            return None
        return sorted(self._list, key=lambda x: x.shortest_airtime())[0]

    def __iter__(self):
        for show in self._list:
            yield show


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


def get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate",
                        action="store_true")
    parser.add_argument("--verbose",
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
    parser.add_argument("--jsonfile",
                        dest="json_file",
                        type=Path,
                        default=Path(Path(__file__)).parent / "ripper_schedule.json")
    args = parser.parse_args()
    return args


@fast_api_app.get("/template", response_class=HTMLResponse)
def template_test(request: Request):
    return templates.TemplateResponse("ripper_info.html", {"request": request, "id": 123})


@fast_api_app.get("/", response_class=HTMLResponse)
def root(request: Request):
    data = SharedData()
    title_str = f"{Path(__file__).name} WebInfo"
    dl_items = data.get_info("downloaded_items", default=[])
    next_timedelta = timedelta(seconds=data.get_info("next_show_seconds_until", default=0))
    return templates.TemplateResponse("ripper_info.html", {"request": request,
                                                           "web_title": title_str,
                                                           "next_show": data.get_info('next_show', default='-'),
                                                           "next_show_timedelta": next_timedelta,
                                                           "dl_items": dl_items,
                                                           "file_processed": data.get_info("file_name"),
                                                           "status": data.get_info('status') or 'Unknown'})

def thread_downloader(cli_args):
    SharedData().set_info("status", DownloaderStatus.Init)
    show_list = ScheduledShowList(cli_args)
    if show_list.empty():
        print("no shows to process.. exiting.")
        return
    if cli_args.simulate:
        log("running simulation..")
    if cli_args.set_all_dl:
        for show in show_list:
            if show.should_download(print_to_log=False):
                show.downloaded_today = True
                log(fcs(f"setting i[{show.name}] as downloaded today"))
    if cli_args.force_download:
        for show in show_list:
            show.download(force=True, simulate=cli_args.simulate)
    weekday = today_weekday()
    log(fcs(f"today is b[{Day(weekday).name}]"))
    while True:
        if weekday != today_weekday():
            log("new day, resetting all show \"downloaded\" flags")
            for show in show_list:
                show.reset_downloaded_today()
            weekday = today_weekday()
            log(fcs(f"today is b[{Day(weekday).name}]"))
        log("checking shows...")
        sleep_to_next_airdate = True
        for show in show_list:
            show.download(simulate=cli_args.simulate)
            SharedData().set_info("file_name", "None")
            if show.should_download(print_to_log=False):
                sleep_to_next_airdate = False
        print_separator()
        if sleep_to_next_airdate:
            show = show_list.next_show()
            sleep_time = show.shortest_airtime()
            wake_date = get_now() + timedelta(seconds=sleep_time)
            wake_date_str = date_to_time_str(wake_date)
            if wake_date.weekday() != weekday:
                wake_date_str = date_to_full_str(wake_date)
            log(fcs(f"sleeping p[{show.shortest_airtime()}] (to {wake_date_str}) - "
                    f"next show is b[{show.name}]"))
            SharedData().set_info("next_show", show.name)
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
