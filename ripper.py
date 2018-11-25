#!/usr/bin/python3.6

'Rip things from various websites, call script with URL'

import argparse
import os
import subprocess
from urllib.request import urlopen

import youtube_dl
from bs4 import BeautifulSoup as bs

import rename


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
        for possible_filename in [title, ident]:
            if possible_filename:
                file_name = possible_filename
                break

    return rename.rename_string(file_name, space_replace_char='.')


def _ytdl_hooks(event):
    if event['status'] == 'finished':
        print('\n' + LANG_OUTPUT['dl_done'][LANGUAGE])
    if event['status'] == 'downloading':
        info_str = LANG_OUTPUT['dl_progress'][LANGUAGE].format(
            event['filename'], event['_percent_str'].lstrip(), event['_eta_str'])
        print('\r' + info_str, end='')


def _sveriges_radio(url: str, dl_loc: str):
    print(f'trying to download sr episodes at {url}')
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


def _tv4play(url: str, dl_loc: str):
    _youtube_dl(url, dl_loc)


def _dplay(url: str, dl_loc: str):
    _youtube_dl(url, dl_loc)


YDL_OPTS = {
    'logger': Logger(),
    'progress_hooks': [_ytdl_hooks],
    'simulate': False,
    'quiet': True
}

LANGUAGE = 'en'

LANG_OUTPUT = {'dl_done': {'sv': 'Nedladdning klar! Konverterar fil.',
                           'en': 'Done downloading! Now converting.'},
               'dl_progress': {'sv': 'Laddar ner: {} ({} - {})',
                               'en': 'Downloading: {} ({} - {})'}}


if __name__ == '__main__':
    METHODS = [('sverigesradio', _sveriges_radio),
               ('tv4play', _tv4play), ('dplay', _dplay)]

    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('url', type=str, help='URL')
    PARSER.add_argument('--lang', type=str, default='en')
    ARGS = PARSER.parse_args()

    HOME = os.path.expanduser('~')
    DEFAULT_DL = os.path.join(HOME, 'Downloads')

    if ARGS.lang == 'sv':
        LANGUAGE = 'sv'

    for hit, method in METHODS:
        if hit in ARGS.url:
            method(ARGS.url, DEFAULT_DL)
