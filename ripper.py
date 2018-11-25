#!/usr/bin/python3.6

" Rip things from various websites, call script with URL"

import argparse
import subprocess
from urllib.request import urlopen

from bs4 import BeautifulSoup as bs

import rename


def _make_soup(url: str):
    page = urlopen(url).read()
    soup = bs(page, "lxml")
    return soup


def _sveriges_radio(url: str):
    print(f"trying to download sr episodes at {url}")
    soup = _make_soup(url)
    links = [(a.get('href'), a.text)
             for a in soup.find_all('a', href=True, text=True)]

    episodes = [(f"https://sverigesradio.se{link}", title)
                for link, title in links if "avsnitt" in link]

    for link, title in episodes:
        print(f"{link}")
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


if __name__ == "__main__":
    METHODS = [('sverigesradio', _sveriges_radio)]

    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('url', type=str, help='URL')
    ARGS = PARSER.parse_args()

    for hit, method in METHODS:
        if hit in ARGS.url:
            method(ARGS.url)
