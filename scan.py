#!/usr/bin/env python3

import argparse
from pathlib import Path
from enum import Enum
from datetime import datetime

import tvmaze
import util
import util_movie
import util_tv
from diskstation import is_ds_special_dir
from omdb import OMDb
from printout import pfcs

from db.db_mov import MovieDatabaseSingleton
from db.db_tv import ShowDatabaseSingleton, EpisodeDatabaseSingleton


class AllowedDuplicate(Enum):
    SwedishDub = "SWEDiSH"
    ExtendedVersion = "EXTENDED"
    UltraHDVersion = "2160p"
    DirectorsCut = "Directors.Cut"
    Uncut = "UNCUT"
    Theatrical = "THEATRICAL"
    Unrated = "UNRATED"
    JapAndSeDub = ".SE.JAP."
    EngAndSeAndJapDub = ".SE.ENG.JAP."
    EngAndSeDub = ".SE.ENG."
    EngAndFiAndSeDub = ".EN.FI.SE."
    NordicDubs = "NORDiC"
    SpecialEdition = "Special.Edition"
    RogueCut = ".THE.ROGUE.CUT."  # Special cut for one movie
    EncoreEdition = ".Encore.Edition."  # Special cut for one movie
    BlackAndChromeEdition = ".Black.and.Chrome.Edition."  # Special cut for one movie
    NoirEdition = ".NOIR.EDITION."  # Special cut for one movie
    JapDVD = ".DVD.JP"  # Special case for one movie
    BW = "BW.PROPER" # Special case for one movie


def process_new_movie(movie_folder: str) -> dict:
    pfcs(f"processing o[{movie_folder}]")
    data = {"folder": movie_folder, "scanned": util.now_timestamp(),
            "removed": False}
    guessed_title = util_movie.determine_title(movie_folder)
    guessed_year = util_movie.parse_year(movie_folder)
    imdb_id_from_nfo = util_movie.get_movie_nfo_imdb_id(movie_folder)
    omdb = OMDb()
    if imdb_id_from_nfo:
        pfcs(
            f"searching OMDb for i[{movie_folder}] using b[{imdb_id_from_nfo}]")
        result = omdb.movie_search(imdb_id=imdb_id_from_nfo)
    elif guessed_title:
        year_str = f" and b[{str(guessed_year)}]" if guessed_year else ""
        pfcs(
            f"searching OMDb for i[{movie_folder}] using b[{guessed_title}]{year_str}")
        result = omdb.movie_search(title=guessed_title, year=guessed_year)
    else:
        pfcs(
            f"failed to determine title or id from w[{movie_folder}] for OMDb query")
        return {}
    if result.title:
        data["title"] = result.title
        pfcs(f" - got title:   g[{data['title']}]")
    if result.year:
        year = result.year
        year_now = datetime.now().year
        if util.is_valid_year(year, min_value=1920, max_value=year_now + 1):
            data["year"] = int(year)
            pfcs(f" - got year:    g[{str(data['year'])}]")
    if result.id:
        imdb_id = util.parse_imdbid(result.id)
        if imdb_id:
            data["imdb"] = imdb_id
            pfcs(f" - got imdb-id: g[{imdb_id}]")
    return data


def process_new_show(show_folder: str, imdb_id=None) -> dict:
    pfcs(f"processing o[{show_folder}]")
    if imdb_id is None:
        nfo_imdb_id = util_tv.imdb_from_nfo(show_folder)
    else:
        nfo_imdb_id = imdb_id
    maze_data = {}
    if nfo_imdb_id:
        pfcs(f"searching TVMaze for i[{show_folder}] using b[{nfo_imdb_id}]")
        maze_data = tvmaze.show_search(nfo_imdb_id)
    if not maze_data:
        pfcs(f"searching TVMaze for i[{show_folder}] using b[{show_folder}]")
        maze_data = tvmaze.show_search(show_folder)
    data = {"folder": show_folder, "scanned": util.now_timestamp(),
            "removed": False}
    if maze_data:
        if "id" in maze_data:
            data["tvmaze"] = maze_data["id"]
            pfcs(f" - got tvmaze id:        g[{data['tvmaze']}]")
        if "name" in maze_data:
            data["title"] = maze_data["name"]
            pfcs(f" - got title:            g[{data['title']}]")
        if "premiered" in maze_data:
            year_str = maze_data["premiered"][0:4]
            if util.is_valid_year(year_str):
                data["year"] = int(year_str)
                pfcs(f" - got premiered year:   g[{data['year']}]")
        if "externals" in maze_data:
            ext = maze_data["externals"]
            if "imdb" in ext and ext["imdb"]:
                data["imdb"] = ext["imdb"]
                pfcs(f" - got imdb-id:          g[{data['imdb']}]")
                if util_tv.save_nfo(show_folder, data["imdb"]):
                    pfcs(f" - saved tvshow.nfo")
    return data


def handle_special_episode(show_id, filename):
    pfcs(f"determined as i[SPECIAL EP]")
    tv_maze_singleton = tvmaze.TvMazeData()
    specials = tv_maze_singleton.get_json_all_special_episodes(show_id)
    for spep in specials:
        name = spep.get("name", "").split(" ")
        # TODO: match season...
        if all(x.lower() in filename.lower() for x in name):
            return spep
    return {}


def process_new_episode(episode_filename: str, show_folder: str) -> dict:
    pfcs(f"processing o[{episode_filename}]")
    data = {
        "filename": episode_filename,
        "scanned": util.now_timestamp(),
        "removed": False,
    }
    if "mythbusters" in show_folder.lower():
        season_number, episode_number = util_tv.parse_season_episode(
        episode_filename, season_as_year=True)
    else:
        season_number, episode_number = util_tv.parse_season_episode(
            episode_filename)
    data["season_number"] = season_number
    data["episode_number"] = episode_number
    tvmaze_data = {}
    database = ShowDatabaseSingleton().db()
    if show_folder in database:
        data["tvshow"] = show_folder
        show_id = database.get(show_folder, "tvmaze")
        pfcs(
            f"searching TVMaze for i[{episode_filename}]\n -> using b[{show_folder}]"
            f" season: b[{season_number}] episode: b[{episode_number}] show-id: b[{show_id}]"
        )
        if episode_number == 0:  # specials
            tvmaze_data = handle_special_episode(show_id, episode_filename)
        else:
            tvmaze_data = tvmaze.episode_search(
                show_folder,
                season_number,
                episode_number,
                show_maze_id=show_id
            )
    if tvmaze_data:
        if "id" in tvmaze_data:
            data["tvmaze"] = tvmaze_data["id"]
            pfcs(f" - got tvmaze id:   g[{data['tvmaze']}]")
        if "airstamp" in tvmaze_data:
            aired_date_str = tvmaze_data["airstamp"]
            aired_timestamp = util.date_str_to_timestamp(aired_date_str)
            if aired_timestamp:  # not 0
                data["released"] = aired_timestamp
                pfcs(f" - got aired date:  g[{aired_date_str[0:10]}]")
    return data


def scan_movies():
    print("searching movie location for new movies...")
    database = MovieDatabaseSingleton().db()
    movies_not_in_db = [
        movie for movie in util_movie.list_all() if not database.exists(movie)
    ]
    new = False
    for new_movie in movies_not_in_db:
        if is_ds_special_dir(new_movie):
            continue
        data = process_new_movie(new_movie)
        if not data:
            continue
        database.insert(data)
        new = True
        pfcs(f"added g[{new_movie}] to database!")
        pfcs(f"d[{'-' * util.terminal_width()}]")
    if new:
        database.save()
        database.export_latest_added()
    else:
        print("found no new movies")


def scan_new_shows():
    print("searching tv location for new shows...")
    database = ShowDatabaseSingleton().db()
    shows_not_in_db = [
        show
        for show in util_tv.list_all_shows()
        if show not in database and not is_ds_special_dir(show)
    ]
    new = len(shows_not_in_db) > 0
    for new_show in shows_not_in_db:
        if is_ds_special_dir(new_show):
            continue
        data = process_new_show(new_show)
        database.insert(data)
        pfcs(f"added g[{new_show}] to database!")
        pfcs(f"d[{'-' * util.terminal_width()}]")
    if new:
        database.save()
    else:
        print("found no new shows")


def scan_episodes():
    print("searching tv location for new episodes...")
    new = False
    database = EpisodeDatabaseSingleton().db()
    for full_path_season_dir, episode_filename in util_tv.list_all_episodes(
        use_cache=False
    ):
        if episode_filename in database or is_ds_special_dir(episode_filename):
            continue
        new = True
        full_path_to_show = Path(full_path_season_dir).parents[0]
        data = process_new_episode(episode_filename, full_path_to_show.name)
        database.insert(data)
        pfcs(f"added g[{episode_filename}] to database!")
        pfcs(f"d[{'-' * util.terminal_width()}]")
    if new:
        database.save()
        database.export_latest_added()
    else:
        print("found no new episodes")


def tv_diagnostics_find_removed(filter_show=None):
    # TODO: use filter
    print("finding removed shows and episodes")
    database_ep = EpisodeDatabaseSingleton().db()
    database_show = ShowDatabaseSingleton().db()
    episode_files = [
        episode_filename
        for _, episode_filename in util_tv.list_all_episodes(use_cache=False)
    ]
    removed_episodes = [
        episode
        for episode in database_ep
        if episode not in episode_files and not database_ep.is_removed(episode)
    ]
    found_removed = False
    for episode in removed_episodes:
        pfcs(f"found removed episode: w[{episode}]")
        database_ep.mark_removed(episode)
        found_removed = True
    removed_shows = [
        show
        for show in database_show
        if show not in util_tv.list_all_shows() and not database_show.is_removed(show)
    ]
    for show_dir in removed_shows:
        pfcs(f"found removed show: w[{show_dir}]")
        database_show.mark_removed(show_dir)
        found_removed = True
    return found_removed


def tv_diagnostics(filter_show=None):
    print("tv diagnostics running")
    database_ep = EpisodeDatabaseSingleton().db()
    database_show = ShowDatabaseSingleton().db()
    if filter_show:
        print(f"only processing shows matching: {filter_show}")
        # TODO: find episode gaps
    if tv_diagnostics_find_removed(filter_show):
        database_ep.save()
        database_show.save()
        database_ep.export_last_removed()


def movie_diagnostics_find_removed(filter_mov=None):
    found_removed = False
    mov_disk_list = util_movie.list_all()
    database = MovieDatabaseSingleton().db()
    print("scanning for removed movies")
    for db_mov in database:
        if database.is_removed(db_mov):
            continue
        if filter_mov and filter_mov.lower() not in db_mov.lower():
            continue
        if db_mov not in mov_disk_list:
            found_removed = True
            print("missing on disk: " + db_mov)
            database.mark_removed(db_mov)
    if found_removed:
        database.save()
        database.export_last_removed()
    else:
        print("found no removed movies")


def movie_diagnostics_list_duplicates(filter_mov=None):
    database = MovieDatabaseSingleton().db()
    duplicate_imdb = database.find_duplicates("imdb")
    print("scanning for duplicate movies")
    if not duplicate_imdb:
        print("found no duplicate movies")
        return
    print("found duplicate movies:")
    omdb = OMDb()
    for imdb_id in duplicate_imdb:
        dup_mov = []
        for mov in duplicate_imdb[imdb_id]:
            if filter_mov and filter_mov.lower() not in mov.lower():
                continue
            if database.is_removed(mov):
                continue
            if any([x.value.lower() in mov.lower() for x in AllowedDuplicate]):
                continue
            dup_mov.append(mov)
        if len(dup_mov) > 1:
            resp = omdb.movie_search(imdb_id=imdb_id)
            if resp.title and resp.year:
                pfcs(f"g[{imdb_id}] (OMDb: b[{resp.title} - {resp.year}] )")
            else:
                print(imdb_id + ":")
            for mov in dup_mov:
                print("   " + mov)


def movie_diagnostics(filter_mov=None):
    print("movie diagnostics running")
    if filter_mov:
        print(f"only processing movies matching: {filter_mov}")
    movie_diagnostics_find_removed(filter_mov=filter_mov)
    print("-" * 30)
    movie_diagnostics_list_duplicates(filter_mov=filter_mov)
    print("-" * 30)


if __name__ == "__main__":
    SCAN_ARGS_MOV = ["movies", "m", "film", "f", "mov", "movie"]
    SCAN_ARGS_TV = ["tv", "eps", "t", "shows", "episodes"]
    SCAN_ARGS_DIAG = ["diagnostics", "diag", "d"]
    SCAN_ARGS_DIAG_TV = ["diagnostics-tv", "diag-tv", "dtv"]
    SCAN_ARGS_DIAG_MOV = ["diagnostics-movies", "diag-mov", "dmov"]

    SCAN_ARGS_ALL = (
        SCAN_ARGS_MOV
        + SCAN_ARGS_TV
        + SCAN_ARGS_DIAG
        + SCAN_ARGS_DIAG_TV
        + SCAN_ARGS_DIAG_MOV
    )

    ARG_PARSER = argparse.ArgumentParser(description="Media Scanner")
    ARG_PARSER.add_argument("type", type=str, choices=SCAN_ARGS_ALL)
    ARG_PARSER.add_argument(
        "--filter",
        "-f",
        type=str,
        default=None,
        help="only process items matching string",
    )
    ARGS = ARG_PARSER.parse_args()

    if ARGS.type in SCAN_ARGS_MOV:
        if ARGS.filter:
            print("filter is only used with diagnostics")
        scan_movies()
    elif ARGS.type in SCAN_ARGS_TV:
        if ARGS.filter:
            print("filter is only used with diagnostics")
        scan_new_shows()
        scan_episodes()
    elif ARGS.type in SCAN_ARGS_DIAG:
        tv_diagnostics(filter_show=ARGS.filter)
        movie_diagnostics(filter_mov=ARGS.filter)
    elif ARGS.type in SCAN_ARGS_DIAG_TV:
        tv_diagnostics(filter_show=ARGS.filter)
    elif ARGS.type in SCAN_ARGS_DIAG_MOV:
        movie_diagnostics(filter_mov=ARGS.filter)
