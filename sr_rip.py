#!/usr/bin/python3.6

import subprocess
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import rename


URL_ROOT = "https://sverigesradio.se"
URL = f"{URL_ROOT}/snedtanktmedkallelind"
PAGE = urlopen(URL).read()
SOUP = bs(PAGE, "lxml")

LINKS = [(a.get('href'), a.text)
         for a in SOUP.find_all('a', href=True, text=True)]


def filter_episodes_from_linklist(links):
    ''' Filter out episodes '''
    return [(f"{URL_ROOT}{link}", title) for link, title in links if "avsnitt" in link]


for link, title in filter_episodes_from_linklist(LINKS):
    episode_page = urlopen(link).read()
    episode_soup = bs(episode_page, "lxml")
    episode_links = [a.get('href')
                     for a in episode_soup.find_all('a', href=True)]
    for episode_link in episode_links:
        if episode_link.endswith(".mp3"):
            file_name = f"{rename.rename_string(title)}.mp3"
            subprocess.run(
                f"wget -O $HOME/Downloads/{file_name} https:{episode_link}", shell=True)
            break
