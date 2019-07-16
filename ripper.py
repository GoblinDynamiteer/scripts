#!/usr/bin/python3.6

'Rip things from various websites, call script with URL'

import argparse
import os
import queue
import re
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

import printing
import rename
import run

LIB_AVAILABLE = {'youtube_dl': True, 'BeautifulSoup': True, 'pyperclip': True}

try:
    import youtube_dl
except ImportError:
    LIB_AVAILABLE['youtube_dl'] = False

try:
    from bs4 import BeautifulSoup as bs
except ImportError:
    LIB_AVAILABLE['BeautifulSoup'] = False

try:
    import pyperclip
except ImportError:
    LIB_AVAILABLE['pyperclip'] = False


if run.program_exists('svtplay-dl'):
    LIB_AVAILABLE['svtplay_dl'] = True
else:
    LIB_AVAILABLE['svtplay_dl'] = False


class Logger(object):
    'Logger for youtube-dl'

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def _make_soup(url: str):
    page = urlopen(url).read()
    soup = bs(page, 'lxml')
    return soup


def _youtube_dl(url: str, dl_loc: str) -> str:
    if not LIB_AVAILABLE['youtube_dl']:
        lib = CSTR('youtube_dl', 'red')
        print(LANG_OUTPUT['lib_missing'][LANGUAGE].format(lib))
        sys.exit()

    for index, dl_format in enumerate(FORMATS):
        YDL_OPTS['format'] = dl_format
        try:
            with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)
                file_name = _youtube_dl_generate_filename(info)
                full_dl_path = os.path.join(dl_loc, file_name)
                ydl.params["outtmpl"] = full_dl_path
                if not SKIP_VIDEO_DOWNLOAD:
                    ydl.download([url])
                return full_dl_path
        except youtube_dl.utils.DownloadError:
            pass
    print(LANG_OUTPUT['dl_failed'][LANGUAGE].format(CSTR(url, 'orange')))
    return None


def _youtube_dl_generate_filename(info: dict) -> str:
    series = info.get('series', None)
    title = info.get('title', None)
    season_number = info.get('season_number', None)
    episode_number = info.get('episode_number', None)
    ext = info.get('ext', None)
    ident = info.get('id', None)

    if not ext:
        ext = 'mp4'

    file_name = ""
    if series and season_number and episode_number:
        file_name = f'{series}.s{season_number:02d}e{episode_number:02d}'
        if USE_TITLE_IN_FILENAME and title:
            file_name = f'{file_name}.{title}'

    if not file_name:
        for possible_filename in [title, ident, 'UnknownFile']:
            if possible_filename:
                file_name = possible_filename
                break

    file_name += f'.{ext}'

    return rename.rename_string(file_name, space_replace_char='.')


def _ytdl_hooks(event):
    if event['status'] == 'finished':
        print('\n' + LANG_OUTPUT['dl_done'][LANGUAGE])
    if event['status'] == 'downloading':
        percentage = CSTR(event['_percent_str'].lstrip(), 'lgreen')
        file_path = CSTR(event['filename'], 'lblue')
        info_str = LANG_OUTPUT['dl_progress'][LANGUAGE].format(
            file_path, percentage, event['_eta_str'])
        print('\r' + info_str, end='')


def _sveriges_radio(url: str, dl_loc: str, site: str):
    del site  # Unused variable
    print(LANG_OUTPUT['dl_init'][LANGUAGE].format(
        CSTR('Sveriges Radio', 'lgreen')))
    if not LIB_AVAILABLE['BeautifulSoup']:
        lib = CSTR('BeautifulSoup', 'red')
        print(LANG_OUTPUT['lib_missing'][LANGUAGE].format(lib))
        sys.exit()

    soup = _make_soup(url)
    links = [(a.get('href'), a.text)
             for a in soup.find_all('a', href=True, text=True)]

    episodes = [(f'https://sverigesradio.se{link}', title)
                for link, title in links if 'avsnitt' in link]

    for link, title in episodes:
        print(f'{link}')
        episode_page = urlopen(link).read()
        episode_soup = bs(episode_page, 'lxml')
        episode_links = [a.get('href')
                         for a in episode_soup.find_all('a', href=True)]
        for episode_link in episode_links:
            if episode_link.endswith('.mp3'):
                file_name = f'{rename.rename_string(title)}.mp3'
                subprocess.run(
                    f'wget -O {dl_loc}/{file_name} https:{episode_link}', shell=True)
                break


def _rip_with_youtube_dl(url: str, dl_loc: str, site: str):
    if not SKIP_VIDEO_DOWNLOAD:
        print(LANG_OUTPUT['dl_init'][LANGUAGE].format(
            CSTR(site, 'lgreen')))
    downloaded_file = _youtube_dl(url, dl_loc)
    if LIB_AVAILABLE['svtplay_dl']:
        _subtitle_dl(url, downloaded_file)


def _unknown_site(url: str, dl_loc: str, site: str):
    print(LANG_OUTPUT['dl_init'][LANGUAGE].format(
        CSTR(site, 'orange')))
    print(LANG_OUTPUT['using'][LANGUAGE].format(
        CSTR('youtube-dl', 'lgreen')))
    _youtube_dl(url, dl_loc)


def _subtitle_dl(url: str, output_file: str):
    if not any(output_file.endswith(ext) for ext in ['.mp4', '.flv']):
        return
    srt_file_path = f"{output_file[0:-4]}"
    ext_str = 'srt'
    if 'viafree' in url.lower():
        sub_url = _viafree_subtitle_link(ORIGINAL_URL)
        if not sub_url:
            print(CSTR(f'{LANG_OUTPUT["no_sub"][LANGUAGE]}', 'orange'))
            return
        command = f"curl {sub_url} > {srt_file_path}.vtt"
        ext_str = 'vtt'
    else:
        command = f'svtplay-dl -S --force-subtitle -o {srt_file_path} {url}'
    if run.local_command(command, hide_output=True, print_info=False):
        print(LANG_OUTPUT['dl_sub'][LANGUAGE].format(
            CSTR(f'{srt_file_path}.{ext_str}', 'lblue')))


def _viafree_subtitle_link(url: str):
    page_contents = urlopen(url).read()
    if not page_contents:
        return None
    match = re.search(
        r'\"subtitlesWebvtt\"\:\"https.+[cdn\-subtitles].+\_sv\.vtt', str(page_contents))
    if not match:
        return None
    sub_url = match.group(0).replace(r'"subtitlesWebvtt":"', '')
    return sub_url.replace(r'\\u002F', '/')


def _viafree_workaround_dl(url: str, dl_loc: str, site: str):
    if not 'avsnitt' in url:
        _rip_with_youtube_dl(url, dl_loc, site)
        return
    page_contents = urlopen(url).read()
    match = re.search(r'\"product[Gg]uid\"\:\"\d{1,10}\"', str(page_contents))
    if not match:
        print(LANG_OUTPUT['viafree_fail'][LANGUAGE])
        return
    vid_id = match.group(0).replace(r'"productGuid":"', '')
    vid_id = vid_id.replace(r'"', '')
    new_url = re.sub(r'avsnitt-\d{1,2}', vid_id, url)
    print(LANG_OUTPUT['viafree_new_url'][LANGUAGE].format(
        CSTR(f'{new_url}', 'lblue')))

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
                      LANG_OUTPUT['url_unknown_site'][LANGUAGE])


class ClipboardCatcher():
    def __init__(self, interval=1):
        self.interval = interval
        if not LIB_AVAILABLE['pyperclip']:
            print("no papyrclip lib, cannot start..")
            return
        watcher_thread = threading.Thread(target=self.watcher, args=())
        downloader_thread = threading.Thread(target=self.downloader, args=())
        self.current_clipboard = ''
        valid_sites = []
        for site, _ in METHODS:
            valid_sites.append(site)
        self.print_listen_message = True
        self.queue = queue.Queue()
        self.dl_running = False
        watcher_thread.start()
        downloader_thread.start()

    def watcher(self):
        current_clipboard = ''
        valid_sites = []
        for site, _ in METHODS:
            valid_sites.append(site)
        print_listen_message = True
        while True:
            contents = pyperclip.paste()
            if print_listen_message:
                if self.dl_running:
                    print()  # download info prints on same line
                    print(LANG_OUTPUT['listen_info_queue'][LANGUAGE])
                else:
                    print(LANG_OUTPUT['listen_info'][LANGUAGE])
                print_listen_message = False
            if current_clipboard != contents:
                for site in valid_sites:
                    if site.lower() in contents.lower():
                        if self.dl_running:
                            print()  # download info prints on same line
                        print(LANG_OUTPUT['listen_got_url'][LANGUAGE].format(
                            CSTR(f'{contents}', 'lblue')))
                        self.queue.put(contents)
                        print_listen_message = True
                current_clipboard = contents
            time.sleep(0.5)

    def downloader(self):
        while True:
            url = self.queue.get()
            self.dl_running = True
            _handle_url(url)
            self.dl_running = False
            time.sleep(1)


YDL_OPTS = {
    'logger': Logger(),
    'progress_hooks': [_ytdl_hooks],
    'simulate': False,
    'quiet': True
}

LANGUAGE = 'en'


# TODO: list formats from video instead
FORMATS = ['best[ext=flv]',
           'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio',
           'best', 'mp4', 'flv', 'hls-6543', 'worstvideo']

LANG_OUTPUT = {'dl_done': {'sv': 'Nedladdning klar! Konverterar fil eller laddar ner ljudspår.',
                           'en': 'Done downloading! Now converting or downloading audio.'},
               'dl_progress': {'sv': 'Laddar ner: {} ({} - {})     ',
                               'en': 'Downloading: {} ({} - {})    '},
               'dl_init': {'sv': 'Startar nedladdning från {}...',
                           'en': 'Starting download from {}...'},
               'using': {'sv': 'Använder {}',
                         'en': 'Using {}'},
               'only_sub': {'sv': 'Laddar endast ner undertexter',
                            'en': 'Only downloading subtitles'},
               'viafree_new_url': {'sv': 'Viafree fix -> använder URL: {}',
                                   'en': 'Viafree workaround -> using URL: {}'},
               'viafree_fail': {'sv': 'Viafree fix -> kunde inte hitta video id',
                                'en': 'Viafree workaround -> failed to extract video id'},
               'dl_sub': {'sv': 'Laddade ner undertext: {}',
                          'en': 'Downloaded subtitle: {}'},
               'dest_info': {'sv': 'Sparar filer till: {}',
                             'en': 'Saving files to: {}'},
               'lib_missing': {'sv': 'Saknar {}! Avbryter',
                               'en': 'Missing lib {}! Aborting'},
               'no_sub': {'sv': 'Hittade ingen undertext!',
                          'en': 'Could not download subtitles!'},
               'dl_failed': {'sv': 'Kunde inte ladda ner {}',
                             'en': 'Could not download {}'},
               'url_unknown_site': {'sv': 'okänd sida', 'en': 'unknown site'},
               'missing_url_arg': {'sv': 'ingen länk angiven!', 'en': 'no url given!'},
               'listen_got_url': {'sv': 'fick länk: {}', 'en': 'got url {}'},
               'listen_info': {'sv': 'kopiera en länk för att starta nedladdning',
                               'en': 'copy an url to initiate download'},
               'listen_info_queue': {'sv': 'kopiera en länk för att köa nedladdning',
                                     'en': 'copy an url to queue download'}}

CSTR = printing.to_color_str
USE_TITLE_IN_FILENAME = True
SKIP_VIDEO_DOWNLOAD = False
ORIGINAL_URL = None

if __name__ == '__main__':
    print(CSTR('======= ripper ======='.upper(), 'purple'))
    HOME = os.path.expanduser('~')
    METHODS = [('sverigesradio', _sveriges_radio),
               ('TV4Play', _rip_with_youtube_dl),
               ('DPlay', _rip_with_youtube_dl),
               ('SVTPlay', _rip_with_youtube_dl),
               ('Viafree', _viafree_workaround_dl)]

    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('--url', '-u', type=str, help='URL')
    PARSER.add_argument('--lang', type=str, default='en')
    PARSER.add_argument('--dir', type=str,
                        default=os.getcwd())
    PARSER.add_argument('--title-in-filename',
                        action='store_true', dest='use_title')
    PARSER.add_argument('--sub-only',
                        action='store_true', dest='sub_only')
    PARSER.add_argument('--listen', '-l',
                        action='store_true', dest='listen_mode')
    ARGS = PARSER.parse_args()

    DEFAULT_DL = ARGS.dir
    USE_TITLE_IN_FILENAME = ARGS.use_title
    SKIP_VIDEO_DOWNLOAD = ARGS.sub_only

    if SKIP_VIDEO_DOWNLOAD:
        print(LANG_OUTPUT['only_sub'][LANGUAGE])

    if ARGS.lang == 'sv':
        LANGUAGE = 'sv'

    print(LANG_OUTPUT['dest_info'][LANGUAGE].format(
        CSTR(DEFAULT_DL, 'lgreen')))

    if ARGS.listen_mode:
        listener = ClipboardCatcher()
        # _listen_mode()
    elif not ARGS.url:
        print(LANG_OUTPUT['missing_url_arg']
              [LANGUAGE] + CSTR(' (argument --url [url])', 'orange'))
    else:
        for arg in ARGS.url.split(','):
            _handle_url(arg)
