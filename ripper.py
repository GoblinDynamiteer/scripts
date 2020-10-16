#!/usr/bin/python3.8

"Rip things from various websites, call script with URL"

import argparse
import json
import os
import queue
import re
import shlex
import subprocess
import time
import sys
from enum import Enum
from pathlib import Path
from urllib.request import urlopen

import printing
import rename
import run
from config import ConfigurationManager
from printing import cstr, pfcs, fcs
from ripper_helpers import (DPlayEpisodeData, DPlayEpisodeLister,
                            SVTPlayEpisodeData, SVTPlayEpisodeLister, ViafreeEpisodeData,
                            Tv4PlayEpisodeLister, ViafreeEpisodeLister, Tv4PlayEpisodeData)

SIM_STR = r"(SIMULATE)"

try:
    import youtube_dl
except ImportError:
    print("youtube-dl lib is required ")
    sys.exit(1)


if run.program_exists("svtplay-dl"):
    SVTPLAY_DL_AVAILABLE = True
else:
    SVTPLAY_DL_AVAILABLE = False


class YoutubeDLFormats(Enum):
    Best = "best"
    BestFLV = "best[ext=flv]"
    BestMP4M4A = "bestvideo[ext=mp4]+bestaudio" \
                 "[ext=m4a]/bestvideo+bestaudio"
    BestMP4 = "best[ext=mp4]"
    MP4 = "mp4"
    FLV = "flv"
    HLS6543 = "hls-6543"
    WorstVideo = "worstvideo"
    BestViaplay = "bestvideo+bestaudio/best"


class SubRipper():
    SIM_STR = f"i[{SIM_STR}] o[SUBDL]"
    LOG_PREFIX = fcs("i[(SUBDL)]")

    def __init__(self, sub_url, video_file_path, sim=False, verbose=False):
        self.url = sub_url
        self.print_log = verbose
        self.video_file_path = video_file_path
        self.simulate = sim
        if sim:
            pfcs(f"{self.SIM_STR} init")
        self.filename = self.determine_file_name()
        self.dest_path = Path(self.video_file_path).parent
        self.download_succeeded = False
        self.data_obj = None
        self.log(fcs(f"using filename p[{self.filename}]"))

    def determine_file_name(self):
        dest_path = Path(self.video_file_path)
        file_ext = dest_path.suffix
        if "viafree" in self.url or "dplay" in self.url:
            srt_file_name = dest_path.name.replace(file_ext, r".vtt")
        else:
            srt_file_name = dest_path.name.replace(file_ext, r".srt")
        return srt_file_name

    def print_info(self):
        pass

    def file_already_exists(self):
        path = self.get_dest_path()
        if not path:
            return False
        return path.is_file()

    def get_dest_path(self):
        if not self.filename:
            return None
        return Path(self.dest_path) / self.filename

    def download(self, destination_path=None):
        if destination_path:
            self.dest_path = destination_path
        if self.file_already_exists():
            pfcs(f"subtitle already exists: o[{self.filename}], skipping")
            return None
        if not self.simulate:
            if any(via in self.url for via in ["viafree", "viaplay"]):
                self.log("using viafree workaround")
                self.download_viafree()
            elif "dplay" in self.url:
                self.log("using dplay workaround")
                self.download_dplay()
            elif isinstance(self.url, list) and "cmore" in self.url[0]:
                self.log("using tv4play workaround")
                self.download_tv4lay()
            else:
                self.download_with_svtplaydl()
            if self.get_dest_path().is_file():
                self.download_succeeded = True
                print(
                    f"downloaded subtitle: {CSTR(f'{self.get_dest_path()}', 'lblue')}")
                return self.get_dest_path()
            else:
                self.log(fcs("subtitle download e[failed]!"))
        else:
            pfcs(f"{self.SIM_STR} downloading")
            pfcs(f"{self.SIM_STR} dest: {self.get_dest_path()}")
            self.download_succeeded = True
            pfcs(f"{self.SIM_STR} setting download succeded: "
                 f"{self.download_succeeded}")
            return str(self.get_dest_path())
        return None

    def download_with_svtplaydl(self):
        command = f'svtplay-dl -S --force-subtitle -o "{self.get_dest_path()}" {self.url}'
        dual_srt_filename = self.get_dest_path().name + ".srt"
        dual_srt_extension_path = Path(self.dest_path) / dual_srt_filename
        if dual_srt_extension_path.exists():  # svtplay-dl might add ext.
            pass
        elif not run.local_command(command, hide_output=True, print_info=False):
            self.download_succeeded = False
        if dual_srt_extension_path.exists():  # svtplay-dl adds srt extension?
            dual_srt_extension_path.rename(self.get_dest_path())

    def download_viafree(self):
        if not self.data_obj:
            self.log("missing viafree data object!")
            return
        self.curl(self.data_obj.retrieve_sub_url())

    def download_dplay(self):
        if not self.data_obj:
            self.log("missing dplay data object!")
            return
        self.data_obj.download_sub(self.filename, self.url)

    def download_tv4lay(self):
        if not self.data_obj:
            self.log("missing tv4play data object!")
            return
        self.data_obj.download_sub(self.filename, self.url)

    def curl(self, sub_url):
        command = f"curl {sub_url} > {self.get_dest_path()}"
        self.log(f"running: {cstr(command, 'lgreen')}")
        if not run.local_command(command, hide_output=True, print_info=False):
            self.download_succeeded = False

    def log(self, info_str):
        if not self.print_log:
            return
        print(self.LOG_PREFIX, info_str)


class PlayRipperYoutubeDl():
    SIM_STR = f"i[{SIM_STR}] p[YTDL]"
    LOG_PREFIX = fcs("i[(YTDL)]")

    def __init__(self, url, dest=None, use_title=False, sim=False, verbose=False):
        self.ep_data = None
        self.print_log = verbose
        self.url = url
        if isinstance(url, (SVTPlayEpisodeData, DPlayEpisodeData, Tv4PlayEpisodeData, ViafreeEpisodeData)):
            self.ep_data = url
            self.url = url.url()
        self.dest_path = dest
        self.format = None
        self.simulate = sim
        if sim:
            self.log("using simulation (not downloading)")
            pfcs(f"{self.SIM_STR} init")
        self.options = {
            "format": YoutubeDLFormats.Best.value,
            "logger": self.Logger(),
            "progress_hooks": [self.hooks],
            "simulate": False,
            "quiet": True,
            "nocheckcertificate": True,
        }
        self.use_title = use_title
        self.info = None
        self.filename = ""
        self.download_succeeded = False

        if "dplay" in self.url:
            self.log(fcs("loading o[cookie.txt] for dplay"))
            self.options["cookiefile"] = ConfigurationManager().path(
                "cookies_txt")

        self.log(fcs(f"using url p[{self.url}]"))
        self.retrieve_info()

    def log(self, info_str):
        if not self.print_log:
            return
        print(self.LOG_PREFIX, info_str)

    def download(self, destination_path=None):
        if not self.info:
            print("no video info available, skipping download!")
            return None
        if destination_path:
            self.dest_path = destination_path
        if self.file_already_exists():
            pfcs(f"file already exists: o[{self.filename}], skipping")
            return None
        if not self.simulate:
            self.log(fcs(f"downloading to: p[{self.dest_path}]"))
            try:
                with youtube_dl.YoutubeDL(self.options) as ydl:
                    ydl.params["outtmpl"] = str(self.get_dest_path())
                    ydl.download([self.url])
                    if self.file_already_exists():
                        self.download_succeeded = True
                    return str(self.get_dest_path())
            except youtube_dl.utils.DownloadError as error:
                print(error)
                return None
        else:
            pfcs(f"{self.SIM_STR} downloading")
            pfcs(f"{self.SIM_STR} dest: {self.get_dest_path()}")
            self.download_succeeded = True
            pfcs(f"{self.SIM_STR} setting download succeded: "
                 f"{self.download_succeeded}")
            return str(self.get_dest_path())
        return None

    def file_already_exists(self):
        path = self.get_dest_path()
        if not path:
            return False
        return path.is_file()

    def get_dest_path(self):
        if not self.filename:
            return None
        return Path(self.dest_path) / self.filename

    def print_info(self):
        pass

    def hooks(self, event):
        if event["status"] == "finished":
            print("\nDone downloading! Now converting or downloading audio.")
        if event["status"] == "downloading":
            percentage = cstr(event["_percent_str"].lstrip(), "lgreen")
            file_name = cstr(Path(event["filename"]).name, "lblue")
            print(f"\rDownloading: {file_name} ({percentage} "
                  f"- {event['_eta_str']})    ", end="")

    def retrieve_info(self):
        self.log("attempting to retrieve video info using youtube-dl...")
        for vid_format in YoutubeDLFormats:
            self.log(f"trying format: {vid_format.value}")
            self.options["format"] = vid_format.value
            self.format = vid_format
            try:
                with youtube_dl.YoutubeDL(self.options) as ydl:
                    self.info = ydl.extract_info(self.url, download=False)
                    self.filename = self.generate_filename()
                self.log(
                    fcs(f"i[success!] generated filename: p[{self.filename}]"))
                self.log(
                    fcs(f"i<success!> using format: p<{self.format.value}>",
                        format_chars=["<", ">"]))
                return  # succeeded
            except youtube_dl.utils.DownloadError as error:
                self.log(error)
                pass
            except AttributeError:
                pass
        # did not succeed
        pfcs("e[error] could not retrieve info using youtube-dl!")

    def generate_filename(self):
        if self.ep_data:
            series = self.ep_data.show
            title = self.ep_data.title
            season_number = self.ep_data.season_num
            episode_number = self.ep_data.episode_num
        else:
            series = self.info.get("series", None)
            title = self.info.get("title", None)
            season_number = self.info.get("season_number", None)
            episode_number = self.info.get("episode_number", None)
        ext = self.info.get("ext", None)
        ident = self.info.get("id", None)
        if not ext:
            ext = "mp4"
        file_name = ""
        if series and season_number and episode_number:
            # TODO: replace umlauts in series...
            series = series.replace("é", "e")
            file_name = f"{series}.s{season_number:02d}e{episode_number:02d}"
            if self.use_title and title:
                file_name = f"{file_name}.{title}"
        if not file_name:
            for possible_filename in [title, ident, "UnknownFile"]:
                if possible_filename:
                    file_name = possible_filename
                    break
        file_name += f".{ext}"
        return rename.rename_string(file_name, space_replace_char=".")

    class Logger(object):
        "Logger for youtube-dl"

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            pass


CSTR = printing.to_color_str
MAIN_LOG_PREFIX = fcs("i[(MAIN)]")


def log_main(info_str):
    print(MAIN_LOG_PREFIX, info_str)


def retrive_sub_url(data_obj, verbose=False):
    count = 0
    sub_url = ""
    while not sub_url:
        sub_url = data_obj.retrieve_sub_url()
        if sub_url:
            if verbose:
                log_main("successfully retrieved subtitle url")
            return sub_url
        else:
            if verbose:
                log_main("failed to retrieve subtitle url")
            count += 1
            if count > 5:
                if verbose:
                    log_main(
                        "could retrieve subtitle url, skipping sub download")
                return ""
            if verbose:
                # Could be done in bg when processing others?
                log_main("sleeping 10 seconds...")
            time.sleep(10)


def main():
    print(CSTR("======= ripper =======".upper(), "purple"))

    parser = argparse.ArgumentParser(description="ripper")
    parser.add_argument("url", type=str, help="URL")
    parser.add_argument("--dir", type=str, default=os.getcwd())
    parser.add_argument("--title-in-filename",
                        action="store_true", dest="use_title")
    parser.add_argument("--sub-only", "-s",
                        action="store_true", dest="sub_only")
    parser.add_argument("--get-last", default=0, dest="get_last")
    parser.add_argument("--download-last-first", "-u",
                        action="store_false", dest="use_ep_order")
    parser.add_argument("--filter", "-f", type=str, default="")
    parser.add_argument("--simulate", action="store_true", help="run tests")
    parser.add_argument("--verbose", "-v", action="store_true", dest="verb")
    args = parser.parse_args()

    if args.sub_only:
        print("Only downloading subtitles")

    if args.simulate:
        print("Running simulation, not downloading...")

    print(f"Saving files to: {CSTR(args.dir, 'lgreen')}")

    urls = args.url.split(",")
    if args.get_last:
        filter_dict = {}
        if args.filter:
            try:
                filter_dict = json.loads(args.filter)
            except:
                print(f"invalid json for filter: {args.filter}, quitting...")
                sys.exit(1)
        wanted_last = int(args.get_last)
        if "dplay" in urls[0]:
            lister = DPlayEpisodeLister(urls[0], verbose=args.verb)
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(objects=True,
                                            revered_order=True, limit=wanted_last
                                            )
        elif "viafree" in urls[0]:
            lister = ViafreeEpisodeLister(urls[0], verbose=args.verb)
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(
                revered_order=True, limit=wanted_last, objects=True
            )
        elif "tv4play" in urls[0]:
            lister = Tv4PlayEpisodeLister(urls[0], verbose=args.verb)
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(
                revered_order=True, limit=wanted_last, objects=True
            )
        elif "svtplay" in urls[0]:
            lister = SVTPlayEpisodeLister(urls[0], verbose=args.verb)
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(objects=True,
                                            revered_order=True, limit=wanted_last
                                            )
        else:
            print("cannot list episodes..")
            sys.exit(1)
        if len(urls) >= wanted_last:
            urls = urls[-1 * wanted_last:]
        if args.use_ep_order:
            urls.reverse()
        print(f"will download {len(urls)} link(s):")
        for url in urls:
            if isinstance(url, (SVTPlayEpisodeData, DPlayEpisodeData, Tv4PlayEpisodeData, ViafreeEpisodeData)):
                url_str = url.url()
            else:
                url_str = url
            print(CSTR(f"  {url_str}", "lblue"))
    # TODO: refactor and do major cleanups! always get objects instead of url strings....
    for url in urls:
        ripper = PlayRipperYoutubeDl(
            url, args.dir, sim=args.simulate, use_title=args.use_title, verbose=args.verb)
        ripper.print_info()
        if isinstance(url, SVTPlayEpisodeData):
            subtitle_url = url.url()
        elif isinstance(url, ViafreeEpisodeData):
            subtitle_url = "viafree_placeholder_url"
        elif isinstance(url, DPlayEpisodeData):
            url.set_logging(args.verb)
            subtitle_url = "dplay_placeholder_url"
        elif isinstance(url, Tv4PlayEpisodeData):
            subtitle_url = "tv4_placeholder_url"
        else:
            subtitle_url = url
        if args.verb:
            log_main(fcs(f"using url for subtitles: o[{subtitle_url}]"))
        if args.sub_only:
            file_name = ripper.get_dest_path()
            sub_ripper = SubRipper(
                subtitle_url, str(file_name), sim=args.simulate, verbose=args.verb)
            if not sub_ripper.file_already_exists():
                if isinstance(url, (DPlayEpisodeData, Tv4PlayEpisodeData, ViafreeEpisodeData)):
                    retrieved_url = retrive_sub_url(url, args.verb)
                    if retrieved_url:
                        sub_ripper.url = retrieved_url
                        sub_ripper.data_obj = url
                if "placeholder" not in sub_ripper.url:
                    sub_ripper.download()
        else:
            get_subs = False
            file_name = ripper.download()
            if file_name and ripper.download_succeeded:
                get_subs = True
            elif not file_name and ripper.file_already_exists():
                file_name = ripper.get_dest_path()
                get_subs = True
            if get_subs:
                if args.verb:
                    log_main("preparing to download subtitles if needed")
                sub_ripper = SubRipper(
                    subtitle_url, str(file_name), sim=args.simulate, verbose=args.verb)
                sub_ripper.print_info()
                if not sub_ripper.file_already_exists():
                    if isinstance(url, (DPlayEpisodeData, Tv4PlayEpisodeData, ViafreeEpisodeData)):
                        retrieved_url = retrive_sub_url(url, args.verb)
                        if retrieved_url:
                            sub_ripper.url = retrieved_url
                            sub_ripper.data_obj = url
                    if "placeholder" not in sub_ripper.url:
                        sub_ripper.download()
                elif args.verb:
                    log_main("subtitle file already exists, skipping")

        print("=" * 100)


if __name__ == "__main__":
    main()
