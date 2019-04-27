#!/usr/bin/env python3

'''Scan for media'''

import argparse
import os
from pathlib import Path

import tvmaze
import util
import util_movie
import util_tv
from config import ConfigurationManager
from db_mov import MovieDatabase
from db_tv import EpisodeDatabase, ShowDatabase
from diskstation import is_ds_special_dir
from omdb import movie_search
from printing import to_color_str as CSTR

DB_MOV = MovieDatabase()
DB_EP = EpisodeDatabase()
DB_SHOW = ShowDatabase()
CFG = ConfigurationManager()


def _scan_movies():
    movies_not_in_db = [
        movie for movie in util_movie.list_all() if not DB_MOV.exists(movie)]

    new = False
    for new_movie in movies_not_in_db:
        if is_ds_special_dir(new_movie):
            continue
        new = True
        data = {'folder': new_movie, 'scanned': util.now_timestamp()}
        guessed_title = util_movie.determine_title(new_movie)
        guessed_year = util_movie.parse_year(new_movie)
        imdb_id_from_nfo = util_movie.get_movie_nfo_imdb_id(new_movie)
        json_data = {}
        if imdb_id_from_nfo:
            json_data = movie_search(imdb_id_from_nfo)
        elif guessed_title:
            json_data = movie_search(guessed_title, year=guessed_year)
        else:
            print(
                CSTR(f'failed to determine title or imdb-id for {new_movie}', 'red'))
        if 'Year' in json_data:
            year = json_data['Year']
            if util.is_valid_year(year, min_value=1920, max_value=2019):
                data['year'] = int(year)
        if 'imdbID' in json_data:
            imdb_id = json_data['imdbID']
            imdb_id = util.parse_imdbid(imdb_id)
            if imdb_id:
                data['imdb'] = imdb_id
        if 'Title' in json_data:
            data['title'] = json_data['Title']
        DB_MOV.insert(data)
        if imdb_id_from_nfo:
            imdb_id_str = f' -> used imdb-id [{CSTR(imdb_id_from_nfo, "lblue")}]'
        else:
            imdb_id_str = ""
        print(f'added new movie: {CSTR(new_movie, "green")}{imdb_id_str}')

    if new:
        DB_MOV.save()
        DB_MOV.export_last_added()
    else:
        print('found no new movies')


def _scan_new_shows():
    shows_not_in_db = [
        show for show in util_tv.list_all_shows()
        if show not in DB_SHOW and not is_ds_special_dir(show)]

    new = False
    if shows_not_in_db:
        new = True
        for new_show in shows_not_in_db:
            if is_ds_special_dir(new_show):
                continue
            nfo_imdb_id = util_tv.imdb_from_nfo(new_show)
            if nfo_imdb_id:
                maze_data = tvmaze.show_search(nfo_imdb_id)
                if not maze_data:
                    maze_data = tvmaze.show_search(new_show)
            else:
                maze_data = tvmaze.show_search(new_show)
            data = {'folder': new_show}
            print(maze_data)
            if maze_data:
                if 'id' in maze_data:
                    data['tvmaze'] = maze_data['id']
                if 'name' in maze_data:
                    data['title'] = maze_data['name']
                if 'premiered' in maze_data:
                    year_str = maze_data['premiered'][0:4]
                    if util.is_valid_year(year_str):
                        data['year'] = int(year_str)
                if 'externals' in maze_data:
                    ext = maze_data['externals']
                    if 'imdb' in ext and ext['imdb']:
                        data['imdb'] = ext['imdb']
            DB_SHOW.insert(data)
            print(f'added new show: {CSTR(new_show, "green")}')
    if new:
        DB_SHOW.save()
    else:
        print('found no new shows')


def _scan_episodes():
    new = False
    for path, episode in util_tv.list_all_episodes():  # uses yield
        if episode in DB_EP or is_ds_special_dir(episode):
            continue
        new = True
        data = {'filename': episode, 'scanned': util.now_timestamp()}
        season_number, episode_number = util_tv.parse_season_episode(episode)
        data['season_number'] = season_number
        data['episode_number'] = episode_number
        # TODO: use better way to get show
        show_path, _ = os.path.split(path)
        show = os.path.basename(show_path)
        tvmaze_data = None
        if show in DB_SHOW:
            data['tvshow'] = show
            show_id = DB_SHOW.get(show, 'tvmaze')
            tvmaze_data = tvmaze.episode_search(
                show, season_number, episode_number, show_maze_id=show_id)
        if tvmaze_data:
            if 'id' in tvmaze_data:
                data['tvmaze'] = tvmaze_data['id']
            if 'airstamp' in tvmaze_data:
                aired_date_str = tvmaze_data['airstamp']
                aired_timestamp = util.date_str_to_timestamp(aired_date_str)
                if aired_timestamp:  # not 0
                    data['released'] = aired_timestamp
        DB_EP.insert(data)
        print(f'added new episode: {CSTR(episode, "green")}')

    if new:
        DB_EP.save()
        DB_EP.export_last_added()
    else:
        print('found no new episodes')


def _tv_diagnostics():
    print('tv diagnostics running')
    tv_dir = CFG.get('path_tv')
    shows = util_tv.list_all_shows()
    for show_dir in shows:
        show_path = Path(tv_dir) / show_dir
        season_dirs = os.listdir(show_path)
        missing = {}
        for season_dir in season_dirs:
            if '00' in season_dir:
                continue
            season_path = show_path / season_dir
            if season_path.is_dir():
                file_list = sorted(os.listdir(season_path))
                season_num = util_tv.parse_season(str(season_path))
                ep_num_last = -1
                for _file in file_list:
                    _, ep_num = util_tv.parse_season_episode(_file)
                    if not ep_num:
                        continue
                    if ep_num > ep_num_last:
                        ep_num_last = ep_num
                ep_list = util_tv.season_episode_str_list(
                    season_num, 1, ep_num_last)
                file_list_str = '|'.join(file_list)
                for ep in ep_list:
                    if ep.lower() not in file_list_str.lower():
                        missing[ep] = 'gap'
                if show_dir in DB_SHOW:
                    show_id = DB_SHOW.get(show_dir, 'tvmaze')
                    while show_id and True:
                        ep_num_last += 1
                        if tvmaze.episode_has_aired(show_dir, int(season_dir[1:]), ep_num_last, show_maze_id=show_id):
                            missing[season_dir.upper() +
                                    f'E{ep_num_last:02d}'] = 'aired'
                        else:
                            break
        if missing:
            print(f'missing eps for {show_dir}:')
            for missing_ep in missing:
                if missing[missing_ep] == 'gap':
                    print(f'    {missing_ep} {CSTR("(gap)", "orange")}')
                if missing[missing_ep] == 'aired':
                    print(f'    {missing_ep} {CSTR("(aired)", "yellow")}')


def _movie_diagnostics():
    print('movie diagnostics running')
    found_removed = False
    mov_disk_list = util_movie.list_all()
    for db_mov in DB_MOV:
        if DB_MOV.is_removed(db_mov):
            continue
        if db_mov not in mov_disk_list:
            found_removed = True
            print('missing on disk: ' + db_mov)
            DB_MOV.mark_removed(db_mov)
    if found_removed:
        DB_MOV.save()
        DB_MOV.export_last_removed()
    print('-----------------------------------')
    duplicate_imdb = DB_MOV.find_duplicates('imdb')
    if duplicate_imdb:
        print('found duplicate movies:')
        for imdb_id in duplicate_imdb:
            dup_mov = []
            for mov in duplicate_imdb[imdb_id]:
                if not DB_MOV.is_removed(mov) and not 'swedish' in mov.lower():
                    dup_mov.append(mov)  # Allow swedish dubs as duplicates...
            if len(dup_mov) > 1:
                print(imdb_id + ":")
                for mov in dup_mov:
                    print('   ' + mov)
        print('-----------------------------------')


if __name__ == '__main__':

    SCAN_ARGS_MOV = ['movies', 'm', 'film', 'f', 'mov', 'movie']
    SCAN_ARGS_TV = ['tv', 'eps', 't', 'shows', 'episodes']
    SCAN_ARGS_DIAG = ['diagnostics', 'diag', 'd']
    SCAN_ARGS_DIAG_TV = ['diagnostics-tv', 'diag-tv', 'dtv']
    SCAN_ARGS_DIAG_MOV = ['diagnostics-movies', 'diag-mov', 'dmov']

    SCAN_ARGS_ALL = SCAN_ARGS_MOV + SCAN_ARGS_TV + \
        SCAN_ARGS_DIAG + SCAN_ARGS_DIAG_TV + SCAN_ARGS_DIAG_MOV

    ARG_PARSER = argparse.ArgumentParser(description='Media Scanner')
    ARG_PARSER.add_argument('type', type=str, choices=SCAN_ARGS_ALL)
    ARGS = ARG_PARSER.parse_args()

    if ARGS.type in SCAN_ARGS_MOV:
        _scan_movies()
    elif ARGS.type in SCAN_ARGS_TV:
        _scan_new_shows()
        _scan_episodes()
    elif ARGS.type in SCAN_ARGS_DIAG:
        _tv_diagnostics()
        _movie_diagnostics()
    elif ARGS.type in SCAN_ARGS_DIAG_TV:
        _tv_diagnostics()
    elif ARGS.type in SCAN_ARGS_DIAG_MOV:
        _movie_diagnostics()
