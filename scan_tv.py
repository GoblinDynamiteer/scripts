#!/usr/bin/env python3.6

'''Scan for new TV'''

import datetime
import argparse
import os
import sys
import filetools as ftool
import tvshow as tvtool
import db_tv
import printing

PRINT = printing.PrintClass(os.path.basename(__file__))
DB_TV = db_tv.database()
if not DB_TV.load_success():
    sys.exit()

ROOT = tvtool.root_path()
if not ROOT:
    PRINT.error("could not determine tv root path, quitting!")
    sys.exit()

SUB_DIRS = os.listdir(ROOT)

new_count = 0


def new_episode(show, season, ep_file_name):
    episode = {'file': ep_file_name, 'status': "ok"}
    episode['date_scanned'] = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    episode['se'] = tvtool.guess_season_episode(episode['file'])
    episode['subs'] = {
        'sv': tvtool.has_subtitle(show, ep_file_name, "sv"),
        'en': tvtool.has_subtitle(show, ep_file_name, "en")}
    episode['omdb'] = tvtool.omdb_search_episode(show, season, episode['file'])
    episode['tvmaze'] = tvtool.tvmaze_search_episode(
        show, season, episode['file'])
    PRINT.info(f"Adding new episode: {episode['se']} : {episode['file']}")
    return episode


def new_season(show, season):
    season = {'folder': season}
    season['omdb'] = tvtool.omdb_search_season(show, season['folder'])
    season['tvmaze'] = tvtool.tvmaze_search_season(show, season['folder'])
    season['episodes'] = []
    return season


def new_show(folder):
    show = {'folder': folder}
    PRINT.info(f"found new show [{folder}] !")
    fp = os.path.join(ROOT, folder)
    date = ftool.get_creation_date(fp, convert=True)
    show['date_created'] = date.strftime(
        "%d %b %Y") if date is not None else None
    show['date_scanned'] = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    show['status'] = "ok"
    show['seasons'] = []
    show['nfo'] = tvtool.has_nfo(folder)
    show['imdb'] = tvtool.nfo_to_imdb(folder)
    show['omdb'] = tvtool.omdb_search_show(show)
    show['tvmaze'] = tvtool.tvmaze_search_show(show)
    for s in tvtool.get_season_folder_list(folder):
        season = {'folder': s, 'status': "ok"}
        season['omdb'] = tvtool.omdb_search_season(show, season['folder'])
        season['tvmaze'] = tvtool.tvmaze_search_season(show, season['folder'])
        season['episodes'] = []
        show['seasons'].append(season)
        for e in tvtool.get_episodes(folder, s):
            episode = new_episode(show, s, e)
            season['episodes'].append(episode)
    PRINT.info(f"added [{folder}] to database!")
    DB_TV.add(show)


PARSER = argparse.ArgumentParser(description='tv scanner')
PARSER.add_argument('-m', '--max', dest='max', default=None,
                    help='max new shows to scan')
ARGS = PARSER.parse_args()

new_show_count = 0
new_episode_count = 0

try:
    max_scan = int(ARGS.max)
    PRINT.info(f"will scan max {max_scan} new shows")
except:
    max_scan = None


for show_s in SUB_DIRS:
    if show_s.startswith("@"):  # Diskstation
        continue
    if max_scan and new_show_count >= max_scan:
        PRINT.info("max new show scan limit reached! breaking")
        break
    PRINT.info(f"scanning [{show_s}]")
    if not DB_TV.exists(show_s):
        new_show(show_s)
        new_show_count += 1
        continue  # new_show() adds all new eps and seasons
    season_folder_list = tvtool.get_season_folder_list(show_s)
    for season_s in season_folder_list:
        ep_file_list = tvtool.get_episodes(show_s, season_s)
        for episode_s in ep_file_list:
            if not DB_TV.has_ep(show_s, episode_s):
                new_episode_count += 1
                show_d = DB_TV.data(show_s)
                episode_d = new_episode(show_d, season_s, episode_s)
                if not DB_TV.has_season(show_s, season_s):
                    season_d = new_season(show_d, season_s)
                    PRINT.info("found new season!")
                    DB_TV.add_season(show_s, season_d)
                DB_TV.add_ep(show_s, season_s, episode_d)

PRINT.info("done scanning!")
PRINT.info(f"found {new_show_count} new shows.")
PRINT.info(f"found {new_episode_count} new episodes.")
if new_show_count > 0 or new_episode_count > 0:
    DB_TV.save()
