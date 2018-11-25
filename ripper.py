#!/usr/bin/python3.6

'Rip things from various websites, call script with URL'

import argparse
import os
import subprocess
import sys
from urllib.request import urlopen

import rename
import str_o

LIB_AVAILABLE = {'youtube_dl': True, 'BeautifulSoup': True}

try:
    import youtube_dl
except ImportError:
    LIB_AVAILABLE['youtube_dl'] = False

try:
    from bs4 import BeautifulSoup as bs
except ImportError:
    LIB_AVAILABLE['BeautifulSoup'] = False


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


def _youtube_dl(url: str, dl_loc: str):
    if not LIB_AVAILABLE['youtube_dl']:
        lib = CSTR('youtube_dl', 'red')
        print(LANG_OUTPUT['lib_missing'][LANGUAGE].format(lib))
        sys.exit()

    with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        file_name = _youtube_dl_generate_filename(info)
        full_dl_path = os.path.join(dl_loc, file_name)
        ydl.params["outtmpl"] = full_dl_path
        ydl.download([url])


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
        if title:
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
    print(LANG_OUTPUT['dl_init'][LANGUAGE].format(
        CSTR(site, 'lgreen')))
    _youtube_dl(url, dl_loc)


def _unknown_site(url: str, dl_loc: str, site: str):
    print(LANG_OUTPUT['dl_init'][LANGUAGE].format(
        CSTR(site, 'orange')))
    print(LANG_OUTPUT['using'][LANGUAGE].format(
        CSTR('youtube-dl', 'lgreen')))
    _youtube_dl(url, dl_loc)


YDL_OPTS = {
    'format': 'bestaudio/best',
    'write-sub': True,  # TODO: try to make sub dl work, alt use svtplay-dl
    'logger': Logger(),
    'progress_hooks': [_ytdl_hooks],
    'simulate': False,
    'quiet': True
}

LANGUAGE = 'en'

LANG_OUTPUT = {'dl_done': {'sv': 'Nedladdning klar! Konverterar fil.',
                           'en': 'Done downloading! Now converting.'},
               'dl_progress': {'sv': 'Laddar ner: {} ({} - {})     ',
                               'en': 'Downloading: {} ({} - {})    '},
               'dl_init': {'sv': 'Startar nedladdning från {}...',
                           'en': 'Starting download from {}...'},
               'using': {'sv': 'Använder {}',
                         'en': 'Using {}'},
               'dest_info': {'sv': 'Sparar filer till: {}',
                             'en': 'Saving files to: {}'},
               'lib_missing': {'sv': 'Saknar {}! Avbryter',
                               'en': 'Missing lib {}! Aborting'}}

CSTR = str_o.to_color_str


if __name__ == '__main__':
    print(CSTR('======= ripper ======='.upper(), 'red'))
    HOME = os.path.expanduser('~')
    METHODS = [('sverigesradio', _sveriges_radio),
               ('TV4Play', _rip_with_youtube_dl),
               ('DPlay', _rip_with_youtube_dl),
               ('Viafree', _rip_with_youtube_dl)]

    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('url', type=str, help='URL')
    PARSER.add_argument('--lang', type=str, default='en')
    PARSER.add_argument('--dir', type=str,
                        default=os.path.join(HOME, 'Downloads'))
    ARGS = PARSER.parse_args()

    DEFAULT_DL = ARGS.dir

    print(LANG_OUTPUT['dest_info'][LANGUAGE].format(
        CSTR(DEFAULT_DL, 'lgreen')))

    if ARGS.lang == 'sv':
        LANGUAGE = 'sv'

    MATCH = False
    for site_hit, method in METHODS:
        if site_hit.lower() in ARGS.url:
            MATCH = True
            method(ARGS.url, DEFAULT_DL, site_hit)
    if not MATCH:
        UNKOWN_SITE_STR = 'Unkown Site' if LANGUAGE == 'en' else "Okänd sida"
        _unknown_site(ARGS.url, DEFAULT_DL, UNKOWN_SITE_STR)