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
from ripper_helpers import DPlayEpisodeLister, Tv4PlayEpisodeLister

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

        self.retrieve_info()

    def download(self, destination_path = None):
        if destination_path:
            self.dest_path = destination_path
        if self.file_already_exists():
            pfcs(f"file already exists: o[{self.filename}], skipping")
            return None
        try:
            with youtube_dl.YoutubeDL(self.options) as ydl:
                    ydl.params["outtmpl"] = str(self.get_dest_path())
                    ydl.download([self.url])
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

    class Logger(object):
        "Logger for youtube-dl"

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            pass


class Logger(object):
    "Logger for youtube-dl"

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def _youtube_dl(url: str, dl_loc: str, use_title=False) -> str:
    for index, dl_format in enumerate(FORMATS):
        YDL_OPTS["format"] = dl_format
        try:
            with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)
                file_name = _youtube_dl_generate_filename(
                    info, use_title=use_title)
                full_dl_path = Path(os.path.join(dl_loc, file_name))
                if full_dl_path.exists():
                    print(
                        f"file already exists: {CSTR(full_dl_path.name, 'orange')}, skipping")
                    return None
                ydl.params["outtmpl"] = str(full_dl_path)
                if not SKIP_VIDEO_DOWNLOAD:
                    ydl.download([url])
                return str(full_dl_path)
        except youtube_dl.utils.DownloadError:
            pass
    print(LANG_OUTPUT["dl_failed"][LANGUAGE].format(CSTR(url, "orange")))
    return None


def _youtube_dl_generate_filename(info: dict, use_title=False) -> str:
    series = info.get("series", None)
    title = info.get("title", None)
    season_number = info.get("season_number", None)
    episode_number = info.get("episode_number", None)
    ext = info.get("ext", None)
    ident = info.get("id", None)

    if not ext:
        ext = "mp4"

    file_name = ""
    if series and season_number and episode_number:
        file_name = f"{series}.s{season_number:02d}e{episode_number:02d}"
        if (USE_TITLE_IN_FILENAME or use_title) and title:
            file_name = f"{file_name}.{title}"

    if not file_name:
        for possible_filename in [title, ident, "UnknownFile"]:
            if possible_filename:
                file_name = possible_filename
                break

    file_name += f".{ext}"

    return rename.rename_string(file_name, space_replace_char=".")


def _ytdl_hooks(event):
    if event["status"] == "finished":
        print("\n" + LANG_OUTPUT["dl_done"][LANGUAGE])
    if event["status"] == "downloading":
        percentage = CSTR(event["_percent_str"].lstrip(), "lgreen")
        file_name = CSTR(Path(event["filename"]).name, "lblue")
        info_str = LANG_OUTPUT["dl_progress"][LANGUAGE].format(
            file_name, percentage, event["_eta_str"]
        )
        print("\r" + info_str, end="")


def _rip_with_youtube_dl(url: str, dl_loc: str, site: str, use_title=False):
    if not SKIP_VIDEO_DOWNLOAD:
        print(LANG_OUTPUT["dl_init"][LANGUAGE].format(CSTR(site, "lgreen")))
    downloaded_file = _youtube_dl(url, dl_loc, use_title=use_title)
    if SVTPLAY_DL_AVAILABLE:
        _subtitle_dl(url, downloaded_file)


def _unknown_site(url: str, dl_loc: str, site: str):
    print(LANG_OUTPUT["dl_init"][LANGUAGE].format(CSTR(site, "orange")))
    print(LANG_OUTPUT["using"][LANGUAGE].format(CSTR("youtube-dl", "lgreen")))
    _youtube_dl(url, dl_loc)


def svtplay_dl_get_all_links(url: str) -> list:
    if not SVTPLAY_DL_AVAILABLE:
        return []
    print("getting links using svtplay-dl...")
    found_urls = []
    command = shlex.split(f"svtplay-dl -A -g {url}")
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1
    )
    while process.poll() is None:
        byte_line = process.stderr.readline()
        line = byte_line.decode()
        if line.startswith("INFO: Url: "):
            found_url_str = line.replace("INFO: Url: ", "").replace("\n", "")
            print(f"got url: {found_url_str}")
            found_urls.append(found_url_str)
    return found_urls


def _subtitle_dl(url: str, output_file: str):
    if not output_file:
        return
    if not any(output_file.endswith(ext) for ext in [".mp4", ".flv"]):
        return
    sub_file_path = f"{output_file[0:-4]}"
    if "viafree" in url.lower():
        sub_file_path += ".vtt"
        sub_url = _viafree_subtitle_link(ORIGINAL_URL)
        if not sub_url:
            print(CSTR(f'{LANG_OUTPUT["no_sub"][LANGUAGE]}', "orange"))
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
        print(LANG_OUTPUT["dl_sub"][LANGUAGE].format(
            CSTR(f"{sub_file_path}", "lblue")))
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


def _viafree_workaround_dl(url: str, dl_loc: str, site: str):
    if not "avsnitt" in url:
        _rip_with_youtube_dl(url, dl_loc, site)
        return
    page_contents = urlopen(url).read()
    match = re.search(r"\"product[Gg]uid\"\:\"\d{1,10}\"", str(page_contents))
    if not match:
        print(LANG_OUTPUT["viafree_fail"][LANGUAGE])
        return
    vid_id = match.group(0).replace(r'"productGuid":"', "")
    vid_id = vid_id.replace(r'"', "")
    new_url = re.sub(r"avsnitt-\d{1,2}", vid_id, url)
    print(LANG_OUTPUT["viafree_new_url"]
          [LANGUAGE].format(CSTR(f"{new_url}", "lblue")))

    _rip_with_youtube_dl(new_url, dl_loc, site)


def _handle_url(url: str):
    match = False
    global ORIGINAL_URL
    ORIGINAL_URL = url
    for site_hit, method in METHODS:
        if site_hit.lower() in url:
            match = True
            method(url, DEFAULT_DL, site_hit)
    if not match:
        _unknown_site(url, DEFAULT_DL,
                      LANG_OUTPUT["url_unknown_site"][LANGUAGE])


YDL_OPTS = {
    "logger": Logger(),
    "progress_hooks": [_ytdl_hooks],
    "simulate": False,
    "quiet": True,
    "nocheckcertificate": True,
}

LANGUAGE = "en"


# TODO: list formats from video instead
FORMATS = [
    "best[ext=flv]",
    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
    "best",
    "mp4",
    "flv",
    "hls-6543",
    "worstvideo",
]

LANG_OUTPUT = {
    "dl_done": {
        "sv": "Nedladdning klar! Konverterar fil eller laddar ner ljudspår.",
        "en": "Done downloading! Now converting or downloading audio.",
    },
    "dl_progress": {
        "sv": "Laddar ner: {} ({} - {})     ",
        "en": "Downloading: {} ({} - {})    ",
    },
    "dl_init": {
        "sv": "Startar nedladdning från {}...",
        "en": "Starting download from {}...",
    },
    "using": {"sv": "Använder {}", "en": "Using {}"},
    "only_sub": {
        "sv": "Laddar endast ner undertexter",
        "en": "Only downloading subtitles",
    },
    "viafree_new_url": {
        "sv": "Viafree fix -> använder URL: {}",
        "en": "Viafree workaround -> using URL: {}",
    },
    "viafree_fail": {
        "sv": "Viafree fix -> kunde inte hitta video id",
        "en": "Viafree workaround -> failed to extract video id",
    },
    "dl_sub": {"sv": "Laddade ner undertext: {}", "en": "Downloaded subtitle: {}"},
    "dest_info": {"sv": "Sparar filer till: {}", "en": "Saving files to: {}"},
    "lib_missing": {"sv": "Saknar {}! Avbryter", "en": "Missing lib {}! Aborting"},
    "no_sub": {"sv": "Hittade ingen undertext!", "en": "Could not download subtitles!"},
    "dl_failed": {"sv": "Kunde inte ladda ner {}", "en": "Could not download {}"},
    "url_unknown_site": {"sv": "okänd sida", "en": "unknown site"},
    "missing_url_arg": {"sv": "ingen länk angiven!", "en": "no url given!"},
    "listen_got_url": {"sv": "fick länk: {}", "en": "got url {}"},
    "listen_info": {
        "sv": "kopiera en länk för att starta nedladdning",
        "en": "copy an url to initiate download",
    },
    "listen_info_queue": {
        "sv": "kopiera en länk för att köa nedladdning",
        "en": "copy an url to queue download",
    },
}

CSTR = printing.to_color_str
USE_TITLE_IN_FILENAME = False
SKIP_VIDEO_DOWNLOAD = False
ORIGINAL_URL = None

if __name__ == "__main__":
    print(CSTR("======= ripper =======".upper(), "purple"))
    HOME = os.path.expanduser("~")
    METHODS = [
        ("TV4Play", _rip_with_youtube_dl),
        ("DPlay", _rip_with_youtube_dl),
        ("SVTPlay", _rip_with_youtube_dl),
        ("Viafree", _viafree_workaround_dl),
    ]

    PARSER = argparse.ArgumentParser(description="ripper")
    PARSER.add_argument("url", type=str, help="URL")
    PARSER.add_argument("--lang", type=str, default="en")
    PARSER.add_argument("--dir", type=str, default=os.getcwd())
    PARSER.add_argument("--title-in-filename",
                        action="store_true", dest="use_title")
    PARSER.add_argument("--sub-only", action="store_true", dest="sub_only")
    PARSER.add_argument("--get-last", default=0, dest="get_last")
    PARSER.add_argument("--filter", "-f", type=str, default="")
    ARGS = PARSER.parse_args()

    DEFAULT_DL = ARGS.dir
    USE_TITLE_IN_FILENAME = ARGS.use_title
    SKIP_VIDEO_DOWNLOAD = ARGS.sub_only

    if SKIP_VIDEO_DOWNLOAD:
        print(LANG_OUTPUT["only_sub"][LANGUAGE])

    if ARGS.lang == "sv":
        LANGUAGE = "sv"

    print(LANG_OUTPUT["dest_info"][LANGUAGE].format(
        CSTR(DEFAULT_DL, "lgreen")))

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
        elif "tv4play" in urls[0]:
            lister = Tv4PlayEpisodeLister(urls[0])
            if filter_dict:
                lister.set_filter(**filter_dict)
            urls = lister.list_episode_urls(
                revered_order=False, limit=wanted_last
            )
        else:
            urls = svtplay_dl_get_all_links(urls[0])
        if len(urls) >= wanted_last:
            urls = urls[-1 * wanted_last:]
        print(f"will download {len(urls)} links:")
        for url in urls:
            print(CSTR(f"  {url}", "lblue"))
    for url in urls:
        ripper = PlayRipperYoutubeDl(url, ARGS.dir)
        # _handle_url(url)
        ripper.print_info()
        ripper.download()
        print("=" * 100)
