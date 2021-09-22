#!/usr/bin/python3.8

"Rip things from various websites, call script with URL"

import argparse
import json
import os
import queue
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from urllib.request import urlopen

import printout
import rename
import run
from config import ConfigurationManager
from printout import cstr, fcs, pfcs
from ripper_helpers import EpisodeLister, SessionSingleton

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

    @staticmethod
    def preferred_format(url):
        if any(x in url for x in ["discoveryplus", "viafree"]):
            return YoutubeDLFormats.BestMP4M4A
        return YoutubeDLFormats.Best


class SubRipper():
    SIM_STR = f"i[{SIM_STR}] o[SUBDL]"
    LOG_PREFIX = "SUBRIP"

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
        self.srt_index = 1

    @staticmethod
    def vid_file_has_subs(video_file_path):
        video_file_path = Path(video_file_path)
        for ext in [".vtt", ".srt"]:
            if video_file_path.with_suffix(ext).is_file():
                return video_file_path.with_suffix(ext)
        return False

    def determine_file_name(self):
        dest_path = Path(self.video_file_path)
        file_ext = dest_path.suffix
        if "vtt" in self.url:
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
        if self.simulate:
            pfcs(f"{self.SIM_STR} downloading")
            pfcs(f"{self.SIM_STR} dest: {self.get_dest_path()}")
            self.download_succeeded = True
            pfcs(f"{self.SIM_STR} setting download succeded: "
                 f"{self.download_succeeded}")
            return str(self.get_dest_path())
        if isinstance(self.url, list):
            self.download_vtt_fragments_as_srt()
        elif self.url.endswith(".vtt"):
            self.download_with_curl()
        elif "vtt" in self.url:
            self.download_single_vtt()
        else:
            self.download_with_svtplaydl()
        if self.get_dest_path().is_file():
            self.download_succeeded = True
            print(
                f"downloaded subtitle: {CSTR(f'{self.get_dest_path()}', 'lblue')}")
            return self.get_dest_path()
        else:
            self.log(fcs("subtitle download e[failed]!"))
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

    def download_with_curl(self):
        command = f"curl {self.url} > {self.get_dest_path()}"
        self.log(f"running: {cstr(command, 'lgreen')}")
        if not run.local_command(command, hide_output=True, print_info=False):
            self.download_succeeded = False

    def log(self, info_str, info_str_line2="", repeat=False):
        if not self.print_log:
            return
        if repeat:
            print(fcs(f"\ri[({self.LOG_PREFIX})]"), info_str, end="")
        else:
            print(fcs(f"i[({self.LOG_PREFIX})]"), info_str)
        # TODO: fix repeat with line 2
        if info_str_line2:
            spaces = " " * len(f"({self.LOG_PREFIX}) ")
            print(f"{spaces}{info_str_line2}")

    def _convert_vtt_seg_to_srt(self, text):
        lines = text.splitlines()
        # example X-TIMESTAMP-MAP=MPEGTS:1260000,LOCAL:00:00:00.000
        rgx = r"\:(?P<start_time>\d{1,20})\,"
        match = re.search(rgx, lines[1])
        if not match:
            return None
        mpegts = int(match.groupdict().get("start_time", 0))
        # example: 00:00:01.280 --> 00:00:02.960
        line_index = 3
        merged = ""
        while True:
            try:
                start, end = lines[line_index].split(" --> ")
            except IndexError:
                break
            except ValueError:
                line_index += 1
                continue
            # 90000 is default MPEG-TS timescale, allegedly,
            # and tv4 has a 10s offset for some reason...
            delta = timedelta(seconds=mpegts / 90000 - 10)
            start = datetime.strptime(start, r"%H:%M:%S.%f") + delta
            end = datetime.strptime(end, r"%H:%M:%S.%f") + delta
            srt_dur = f'{start.strftime(r"%H:%M:%S,%f")[:-3]}'
            srt_dur += f' --> {end.strftime(r"%H:%M:%S,%f")[:-3]}'
            if merged != "":
                merged += "\n" * 2
            merged += str(self.srt_index) + "\n" + \
                srt_dur + "\n" + lines[line_index+1]
            self.log(f"added srt index {self.srt_index}", repeat=True)
            self.srt_index += 1
            try:
                if lines[line_index+2] != "":
                    merged += "\n" + lines[line_index+2]
            except IndexError:
                break
            line_index += 1
        return merged + "\n\n"

    def download_vtt_fragments_as_srt(self):
        if not isinstance(self.url, list) or not self.url:
            print("cannot download subtitle!")
            return False
        self.log("attempting to download and merge webvtt subtitle fragments",
                 f"number of fragments={len(self.url)}")
        sub_contents = ""
        for url in self.url:
            fragment_text = SessionSingleton().get(url).text
            edited = self._convert_vtt_seg_to_srt(fragment_text)
            if edited is None:
                if self.print_log:
                    print()
                self.log("failed to merge vtt subtitles, aborting")
                return False
            if edited != "":
                sub_contents += edited
        if self.print_log:
            print()
        sub_contents = sub_contents.encode(
            "latin-1").decode("utf-8", errors="ignore").replace("\n" * 3, "\n" * 2)
        with open(self.get_dest_path(), "wb") as sub_output_file:
            sub_output_file.write(sub_contents.encode("utf-8"))
        return True

    def download_single_vtt(self):
        sub_contents = SessionSingleton().get(self.url).text
        sub_contents = sub_contents.encode("latin-1").decode("utf-8")
        with open(self.get_dest_path(), "wb") as sub_output_file:
            sub_output_file.write(sub_contents.encode("utf-8"))


class PlayRipperYoutubeDl():
    SIM_STR = f"i[{SIM_STR}] p[YTDL]"
    LOG_PREFIX = fcs("i[(YTDL)]")

    def __init__(self, url, ep_data=None, dest=None, use_title=False, sim=False, verbose=False):
        self.ep_data = ep_data
        self.print_log = verbose
        self.url = url
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

        if "discoveryplus" in self.url:
            file_path = ConfigurationManager().path("cookies_txt")
            if not Path(file_path).exists():
                file_path = Path(__file__).resolve().parent / "cookies.txt"
            if not Path(file_path).exists():
                self.log(fcs("e[error]: could not load cookies for discoveryplus"))
            else:
                self.log(fcs("loading o[cookie.txt] for discoveryplus"))
                self.options["cookiefile"] = str(file_path)

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
            retries = 0
            while retries < 4:
                if retries:
                    self.log(fcs(f"retry attempt w[{retries}]"))
                    print("retrying...")
                    time.sleep(1)
                try:
                    with youtube_dl.YoutubeDL(self.options) as ydl:
                        ydl.params["outtmpl"] = str(self.get_dest_path())
                        ydl.download([self.url])
                        if self.file_already_exists():
                            self.download_succeeded = True
                        return str(self.get_dest_path())
                except youtube_dl.utils.DownloadError as error:
                    print("\ngot error during download attempt:\n", error)
                except KeyboardInterrupt:
                    print("user cancelled...")
                    return None
                retries += 1
            self.log(fcs("e[failed download!]"))
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
        formats = [f for f in YoutubeDLFormats]
        preferred = YoutubeDLFormats.preferred_format(self.url)
        if preferred is not None:
            self.log(
                fcs(f"trying preferred format first: p<{preferred.value}>",
                    format_chars=["<", ">"]))
            formats.remove(preferred)
            formats.insert(0, preferred)
        for vid_format in formats:
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


CSTR = printout.to_color_str
MAIN_LOG_PREFIX = fcs("i[(MAIN)]")


def log_main(info_str):
    print(MAIN_LOG_PREFIX, info_str)


def retrive_sub_url(data_obj, verbose=False):
    count = 0
    sub_url = ""
    while not sub_url:
        sub_url = data_obj.subtitle_url()
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
                # Could be done in bg when processing others
                log_main("sleeping 10 seconds...")
            time.sleep(10)


def get_args():
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
    return parser.parse_args()


def download_episodes(episode_list, cli_args):
    first = True
    for ep in episode_list:
        if not first:
            print("=" * 100)
        first = False
        if isinstance(ep, str):
            url = ep
            data = None
        else:
            url = ep.url()
            data = ep
        ripper = PlayRipperYoutubeDl(
            url,
            dest=cli_args.dir,
            ep_data=data,
            sim=cli_args.simulate,
            use_title=cli_args.use_title,
            verbose=cli_args.verb)
        ripper.print_info()
        file_name = ""
        get_subs = False
        if not cli_args.sub_only:
            file_name = ripper.download()
            if file_name and ripper.download_succeeded:
                get_subs = True
            elif not file_name and ripper.file_already_exists():
                file_name = ripper.get_dest_path()
                get_subs = True
        if get_subs or cli_args.sub_only:
            if not file_name:
                file_name = ripper.get_dest_path()
            subtitle_url = url if isinstance(
                ep, str) else retrive_sub_url(ep, cli_args.verb)
            if cli_args.verb:
                if isinstance(subtitle_url, list) and subtitle_url != []:
                    log_main(
                        fcs(f"using url(s) for subtitles: o[{subtitle_url[0]}]..."))
                else:
                    log_main(
                        fcs(f"using url for subtitles: o[{subtitle_url}]"))
            sub_ripper = SubRipper(
                subtitle_url,
                str(file_name),
                sim=cli_args.simulate,
                verbose=cli_args.verb)
            if sub_ripper.file_already_exists():
                if cli_args.verb:
                    log_main(
                        fcs(f"subtitle already exists: i[{sub_ripper.get_dest_path()}]"))
                continue
            sub_ripper.download()


def main():
    pfcs(f"p[======= RIPPER =======]")
    args = get_args()
    if args.sub_only:
        print("Only downloading subtitles")
    if args.simulate:
        print("Running simulation, not downloading...")
    pfcs(f"saving files to: i[{args.dir}]")
    urls = args.url.split(",")
    if args.get_last:
        if len(urls) > 1:
            pfcs(
                f"w[warning] multiple urls unsupported with --get-last, using only: {urls[0]}")
        filter_dict = {}
        if args.filter:
            try:
                filter_dict = json.loads(args.filter)
            except:
                print(f"invalid json for filter: {args.filter}, quitting...")
                sys.exit(1)
        wanted_last = int(args.get_last)
        try:
            lister = EpisodeLister.get_lister(
                urls[0], verbose_logging=args.verb)
            if filter_dict:
                lister.set_filter(**filter_dict)
            episodes = lister.get_episodes(
                revered_order=True, limit=wanted_last)
        except ValueError as error:
            pfcs("e[failed] to list episodes")
            pfcs(f"e[error]: {error}")
            sys.exit(1)
        if len(episodes) >= wanted_last:
            episodes = episodes[-1 * wanted_last:]
        if args.use_ep_order:
            episodes.reverse()
        print(f"will download {len(episodes)} episode(s):")
        for episode in episodes:
            pfcs(f"b[{episode.url()}]")
        download_episodes(episodes, args)
    else:
        download_episodes(urls, args)


if __name__ == "__main__":
    main()
