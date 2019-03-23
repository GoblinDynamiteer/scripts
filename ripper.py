#!/usr/bin/python3.6

'Rip things from various websites, call script with URL'

import argparse
import os
import re
import subprocess
import sys
from urllib.request import urlopen

import printing
import rename
import run

LIB_AVAILABLE = {'youtube_dl': True, 'BeautifulSoup': True}

try:
    import youtube_dl
except ImportError:
    LIB_AVAILABLE['youtube_dl'] = False

try:
    from bs4 import BeautifulSoup as bs
except ImportError:
    LIB_AVAILABLE['BeautifulSoup'] = False


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
    if not output_file.endswith('.mp4') or output_file.endswith('.flv'):
        return
    srt_file_path = f"{output_file[0:-4]}"
    ext_str = 'srt'
    if 'viafree' in url.lower():
        sub_url = _viafree_subtitle_link(ORIGINAL_URL)
        command = f"curl {sub_url} > {srt_file_path}.vtt"
        ext_str = 'vtt'
    else:
        command = f'svtplay-dl -S --force-subtitle -o {srt_file_path} {url}'
    if run.local_command(command, hide_output=True, print_info=False):
        print(LANG_OUTPUT['dl_sub'][LANGUAGE].format(
            CSTR(f'{srt_file_path}.{ext_str}', 'lblue')))


def _viafree_subtitle_link(url: str):
    page_contents = urlopen(url).read()
    match = re.search(r'\"subtitlesWebvtt\"\:\"https.+[cdn\-subbtitles].+\_sv\.vtt', str(page_contents))
    if not match:
        return None
    sub_url = match.group(0).replace(r'"subtitlesWebvtt":"', '')
    return sub_url.replace(r'\\u002F', '/')


def _viafree_workaround_dl(url: str, dl_loc: str, site: str):
    if not 'avsnitt' in url:
        _rip_with_youtube_dl(url, dl_loc, site)
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
               'dl_failed': {'sv': 'Kunde inte ladda ner {}',
                             'en': 'Could not download {}'}}

CSTR = printing.to_color_str
USE_TITLE_IN_FILENAME = True


if __name__ == '__main__':
    print(CSTR('======= ripper ======='.upper(), 'purple'))
    HOME = os.path.expanduser('~')
    METHODS = [('sverigesradio', _sveriges_radio),
               ('TV4Play', _rip_with_youtube_dl),
               ('DPlay', _rip_with_youtube_dl),
               ('SVTPlay', _rip_with_youtube_dl),
               ('Viafree', _viafree_workaround_dl)]

    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('url', type=str, help='URL')
    PARSER.add_argument('--lang', type=str, default='en')
    PARSER.add_argument('--dir', type=str,
                        default=os.getcwd())
    PARSER.add_argument('--title-in-filename',
                        action='store_true', dest='use_title')
    ARGS = PARSER.parse_args()

    DEFAULT_DL = ARGS.dir
    USE_TITLE_IN_FILENAME = ARGS.use_title

    if ARGS.lang == 'sv':
        LANGUAGE = 'sv'

    print(LANG_OUTPUT['dest_info'][LANGUAGE].format(
        CSTR(DEFAULT_DL, 'lgreen')))

    for url in ARGS.url.split(','):
        MATCH = False
        for site_hit, method in METHODS:
            if site_hit.lower() in url:
                MATCH = True
                method(url, DEFAULT_DL, site_hit)
        if not MATCH:
            UNKOWN_SITE_STR = 'Unkown Site' if LANGUAGE == 'en' else "Okänd sida"
            _unknown_site(url, DEFAULT_DL, UNKOWN_SITE_STR)
