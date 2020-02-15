#!/usr/bin/python3.6

"Rip things from various websites, call script with URL"

import argparse
import json
import os
import queue
import re
import shlex
import subprocess
import sys
from enum import Enum
from pathlib import Path
from urllib.request import urlopen

import printing
import rename
import run
from printing import cstr, pfcs
from ripper_helpers import DPlayEpisodeLister
from ripper_helpers import Tv4PlayEpisodeLister
from ripper_helpers import ViafreeEpisodeLister

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


class PlayRipperYoutubeDl():
    def __init__(self, url, dest=None, use_title=False):
        self.url = url
        self.dest_path = dest
        self.format = None
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

        if "viafree" in self.url:
            self.url = self.viafree_url()
            if not self.url:
                return

        self.retrieve_info()

    def download(self, destination_path=None):
        if destination_path:
            self.dest_path = destination_path
        if self.file_already_exists():
            pfcs(f"file already exists: o[{self.filename}], skipping")
            return None
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
        pfcs(f"url i[{self.url}]")
        pfcs(f"format i[{self.format.value}]")
        pfcs(f"filename i[{self.filename}]")
        pfcs(f"dest i[{self.dest_path}]")
        pfcs(f"full_dest i[{self.get_dest_path()}]")
        pfcs(f"file_exists i[{self.file_already_exists()}]")

    def hooks(self, event):
        if event["status"] == "finished":
            print("\nDone downloading! Now converting or downloading audio.")
        if event["status"] == "downloading":
            percentage = cstr(event["_percent_str"].lstrip(), "lgreen")
            file_name = cstr(Path(event["filename"]).name, "lblue")
            print(f"\rDownloading: {file_name} ({percentage} "
                  f"- {event['_eta_str']})    ", end="")

    def retrieve_info(self):
        for vid_format in YoutubeDLFormats:
            self.options["format"] = vid_format.value
            self.format = vid_format
            try:
                with youtube_dl.YoutubeDL(self.options) as ydl:
                    self.info = ydl.extract_info(self.url, download=False)
                    self.filename = self.generate_filename()
                return  # succeeded
            except youtube_dl.utils.DownloadError as error:
                pass

    def generate_filename(self):
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

    def viafree_url(self):
        if not "avsnitt" in url:
            return self.url
        page_contents = urlopen(self.url).read()
        match = re.search(
            r"\"product[Gg]uid\"\:\"\d{1,10}\"", str(page_contents))
        if not match:
            print("viafree workaround -> failed to extract video id")
            return None
        vid_id = match.group(0).replace(r'"productGuid":"', "")
        vid_id = vid_id.replace(r'"', "")
        return re.sub(r"avsnitt-\d{1,2}", vid_id, self.url)

    class Logger(object):
        "Logger for youtube-dl"

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            pass


def _subtitle_dl(url: str, output_file: str):
    if not output_file:
        return
    if not any(output_file.endswith(ext) for ext in [".mp4", ".flv"]):
        return
    sub_file_path = f"{output_file[0:-4]}"
    if "viafree" in url.lower():
        sub_file_path += ".vtt"
        sub_url = _viafree_subtitle_link(url)
        if not sub_url:
            print(CSTR(f"Could not download subtitles!", "orange"))
            return
        command = f"curl {sub_url} > {sub_file_path}"
    else:
        sub_file_path += ".srt"
        command = f'svtplay-dl -S --force-subtitle -o "{sub_file_path}" {url}'
    if Path(sub_file_path).exists():
        print(f"subtitle already exists: {sub_file_path}, skipping")
        return
    dual_srt_extension_path = Path(sub_file_path + ".srt")
    if dual_srt_extension_path.exists():  # svtplay-dl adds srt extension?
        pass
    elif run.local_command(command, hide_output=True, print_info=False):
        print(f"Downloaded subtitle: {CSTR(f'{sub_file_path}', 'lblue')}")
    if dual_srt_extension_path.exists():  # svtplay-dl adds srt extension?
        dual_srt_extension_path.rename(sub_file_path)


def _viafree_subtitle_link(url: str):
    page_contents = urlopen(url).read()
    if not page_contents:
        return None
    match = re.search(
        r"\"subtitlesWebvtt\"\:\"https.+[cdn\-subtitles].+\_sv\.vtt", str(
            page_contents)
    )
    if not match:
        return None
    sub_url = match.group(0).replace(r'"subtitlesWebvtt":"', "")
    return sub_url.replace(r"\\u002F", "/")


CSTR = printing.to_color_str

if __name__ == "__main__":
    print(CSTR("======= ripper =======".upper(), "purple"))
    HOME = os.path.expanduser("~")

    PARSER = argparse.ArgumentParser(description="ripper")
    PARSER.add_argument("url", type=str, help="URL")
    PARSER.add_argument("--dir", type=str, default=os.getcwd())
    PARSER.add_argument("--title-in-filename",
                        action="store_true", dest="use_title")
    PARSER.add_argument("--sub-only", "-s", action="store_true", dest="sub_only")
    PARSER.add_argument("--get-last", default=0, dest="get_last")
    PARSER.add_argument("--filter", "-f", type=str, default="")
    ARGS = PARSER.parse_args()

    if ARGS.sub_only:
        print("Only downloading subtitles")

    print(f"Saving files to: {CSTR(ARGS.dir, 'lgreen')}")

    urls = ARGS.url.split(",")
    if ARGS.get_last:
        filter_dict = {}
        if ARGS.filter:
            try:
                filter_dict = json.loads(ARGS.filter)
            except:
                print(f"invalid json for filter: {ARGS.filter}, quitting...")
                sys.exit(1)
        wanted_last = int(ARGS.get_last)
        if "dplay" in urls[0]:
            lister = DPlayEpisodeLister(urls[0])
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(
                revered_order=True, limit=wanted_last
            )
        elif "viafree" in urls[0]:
            lister = ViafreeEpisodeLister(urls[0])
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(
                revered_order=True, limit=wanted_last
            )
        elif "tv4play" in urls[0]:
            lister = Tv4PlayEpisodeLister(urls[0])
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(
                revered_order=False, limit=wanted_last
            )
        else:
            print("cannot list episodes..")
            sys.exit(1)
        if len(urls) >= wanted_last:
            urls = urls[-1 * wanted_last:]
        print(f"will download {len(urls)} links:")
        for url in urls:
            print(CSTR(f"  {url}", "lblue"))
    for url in urls:
        ripper = PlayRipperYoutubeDl(url, ARGS.dir)
        ripper.print_info()
        if ARGS.sub_only:
            file_name = ripper.get_dest_path()
            _subtitle_dl(url, str(file_name))
        else:
            file_name = ripper.download()
            if file_name and ripper.download_succeeded:
                _subtitle_dl(url, file_name)
        print("=" * 100)
