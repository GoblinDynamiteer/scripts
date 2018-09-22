# -*- coding: utf-8 -*-
import paths, re, os, omdb, tvmaze
from config import configuration_manager as cfg
from printout import print_class as pr
import user_input as ui
import filetools as ftool
import db_tv
import user_input

pr = pr(os.path.basename(__file__))
_config = cfg()
db = db_tv.database()

assert db.load_success(), "TV database could not be loaded!"

# Determine tv root path
def root_path():
    path = _config.get_setting("path", "tvroot")
    return path

# Converts a show dictionary to show string name, if needed
def to_show_s(show_d_or_show_s):
    if isinstance(show_d_or_show_s, str):
        return show_d_or_show_s
    return show_d_or_show_s['folder'] # is show_d aka dict

# Converts a show string to show dictionary, if needed
def to_show_d(show_d_or_show_s):
    if isinstance(show_d_or_show_s, dict):
        return show_d_or_show_s
    if isinstance(show_d_or_show_s, str):
        if db.exists(show_d_or_show_s):
            show_d = db.data(show_d_or_show_s)
            return show_d # is show_d aka dict

def _show_path(show):
    show_s = to_show_s(show)
    return os.path.join(root_path(), show_s)

def _show_path_season(show, season_s): #season_s == "S01"..
    show_s = to_show_s(show)
    if isinstance(season_s, int) or not season_s.startswith("S"):
        season_s = "S{:02d}".format(season_s)
    return os.path.join(_show_path(show_s), season_s)

def has_nfo(show):
    show_s = to_show_s(show)
    full_path = _show_path(show_s)
    if not os.path.exists(full_path):
        pr.warning("path {} does not exists".format(full_path))
        return False
    for file in os.listdir(full_path):
        if file.endswith(".nfo"):
            return True
    return False

def add_nfo_manual(show, replace=False):
    show_s = to_show_s(show)
    path = _show_path(show_s)
    pr.info("add imdb-id for [{}]: ".format(show_s), end_line=False)
    imdb_input = input("")
    re_imdb = re.compile("tt\d{1,}")
    imdb_id = re_imdb.search(imdb_input)
    if imdb_id:
        id = imdb_id.group(0)
        ftool.create_nfo(path, id, "tv", replace)

# Extract IMDb-id from nfo
def nfo_to_imdb(show):
    show = to_show_s(show)
    if not has_nfo(show):
        return None
    f = open(ftool.get_file(_show_path(show), "nfo", full_path = True), "r")
    imdb_url = f.readline()
    f.close()
    re_imdb = re.compile("tt\d{1,}")
    imdb_id = re_imdb.search(imdb_url)
    return imdb_id.group(0) if imdb_id else None

def get_season_folder_list(show):
    list = []
    for item in os.listdir(_show_path(show)):
        if item.endswith(".nfo"):
            continue
        if os.path.isdir(_show_path_season(show, item)):
            list.append(str(item))
    return list

def get_episodes(show, season_s):
    show_s = to_show_s(show)
    ep_list = []
    full_path = os.listdir(os.path.join(_show_path(show_s), season_s))
    for item in full_path:
        if _is_vid_file(str(item)):
            ep_list.append(str(item))
    return ep_list

def _is_vid_file(file_string):
    if file_string.endswith(".mkv"):
        return True
    if file_string.endswith(".mp4"):
        return True
    if file_string.endswith(".avi"):
        return True
    return False

# Check if episode has srt file
def has_subtitle(show_d, ep_file_name, lang):
    if lang != "en" and lang != "sv":
        pr.error(f"got wrong lang for has_subtitle: {lang}")
        return None
    show_d = to_show_d(show_d)
    show_folder = show_d["folder"]
    season = guess_season(ep_file_name)
    path = _show_path_season(show_folder, season)
    srt_file_to_find = ep_file_name[:-3] + f"{lang}.srt"
    return ftool.get_file(path, srt_file_to_find)

# Determine full path to season folder from episode file name
def show_season_path_from_ep_s(ep_s, create_if_missing=True):
    show_s = guess_ds_folder(ep_s)
    if show_s.lower().startswith("marvels agents of"):
        show_s = "Marvels Agents of S.H.I.E.L.D"
    if db.exists(show_s): # Will compare lowercase strings...
        show_folder = db.data(show_s, "folder")
    else:
        pr.warning(f"could not determine show for episode, guessed [{show_s}]")
        show_folder = show_s
    season_n = guess_season(ep_s)
    path = _show_path_season(show_folder, season_n)
    if ftool.is_existing_folder(_show_path(show_folder)):
        pr.info(f"show path exists [{_show_path(show_folder)}]")
    if not ftool.is_existing_folder(path):
        pr.warning(f"path does not exist [{path}]")
        if create_if_missing:
            script_name = os.path.basename(__file__)
            if user_input.yes_no(f"create path {path}?", script_name=script_name):
                os.makedirs(path)
                return path
        else:
            return None
    else:
        pr.info(f"found existing path: [{path}]")
    return path

# Determine ds/tvpath from tv folder or filename
def guess_ds_folder(string):
    rgx = re.compile('\.[Ss]\d{2}')
    match = re.search(rgx, string.replace(" ", "."))
    if match:
        splits = string.split(match[0])
        return splits[0].replace(".", " ")

# Determine season number from tv folder
def guess_season(string):
    rgx = re.compile('[Ss]\d{2,4}')
    match = re.search(rgx, string)
    if match:
        rgx = re.compile('\d{2,4}')
        match = re.search(rgx, match[0])
        if match:
            return int(match[0])
    return None

# Determine episode number from tv folder
def guess_episode(string):
    rgx = re.compile('\d{1}[Ee]\d{2}\.')
    match = re.search(rgx, string)
    if match:
        rgx = re.compile('\d{2}')
        match = re.search(rgx, match[0])
        if match:
            return int(match[0])
    return None

# Determine season from tv folder
def guess_season_episode(string):
    rgx = re.compile('[Ss]\d{2}[Ee]\d{2}')
    match = re.search(rgx, string)
    if match:
        return match[0].upper()
    return None

# Special cases for omdb/tvmaze where season is listed as year
def season_number_to_year(show_d, season_n):
    if show_d['folder'].lower() == "mythbusters":
        return season_n + 2002 # Mythbusters started in 2003
    return season_n

def __tvmaze_search(show_d, season_n = None, episode_n = None):
    folder = show_d['folder']
    query = { "tvmaze" : None, "imdb" : None, "folder" : show_d['folder'] }
    query_type = None
    if "tvmaze" in show_d:
        if show_d["tvmaze"] and "id" in show_d["tvmaze"]:
            query["tvmaze"] = str(show_d["tvmaze"]["id"])
    if show_d['imdb']:
            query["imdb"] = show_d['imdb']
    for type in [ "tvmaze", "imdb", "folder" ]:
        if not query[type]:
            continue
        pr.info(f"searching tvmaze for [{show_d['folder']}] ", end_line=False)
        pr.color_brackets(f"as [{query[type]}] ", "green", end_line=False)
        if season_n:
            season_n = season_number_to_year(show_d, season_n) # Converts to year if required
            pr.output(f"-season {season_n}", end_line=False)
        if episode_n:
            pr.output(f" -episode {episode_n}", end_line=False)
        search = tvmaze.tvmaze_search(query[type], season=season_n, episode=episode_n)
        data = search.data()
        try:
            if "status" in data:
                if data['status'] == "404":
                    pr.color_brackets(" [response false]!", "yellow")
            if "_links" in data: #tvmaze data success
                pr.color_brackets(" [got data]!", "green")
                return data
        except:
            pr.color_brackets(" [script error] !", "red")
    return None

def __omdb_search(show_d, season_n = None, episode_n = None):
    folder = show_d['folder']
    query = None
    if show_d['imdb']:
        query = show_d['imdb']
    else:
        query = show_d['folder']
    pr.info(f"searching omdb for [{show_d['folder']}] ", end_line=False)
    pr.color_brackets(f"as [{query}] ", "green", end_line=False)
    if season_n:
        pr.output(f"-season {season_n}", end_line=False)
    if episode_n:
        pr.output(f" -episode {episode_n}", end_line=False)
    search = omdb.omdb_search(query, season=season_n, episode=episode_n)
    data = search.data()
    try:
        if data['Response'] == "False":
            pr.color_brackets("> [response false]!", "yellow")
            return None
        pr.color_brackets("> [got data]!", "green")
        return data
    except:
        pr.color_brackets("> [script error] !", "red")
        return None

#TODO refactor search funcs
def omdb_search_show(show_d, season_n = None, episode_n = None):
    return __omdb_search(show_d, season_n=season_n, episode_n=episode_n)

def tvmaze_search_show(show_d, season_n = None, episode_n = None):
    return __tvmaze_search(show_d, season_n=season_n, episode_n=episode_n)

def omdb_search_season(show_d, season_s, episode_n=None):
    rgx = re.compile('\d{2,4}$')
    match_season_n = re.search(rgx, season_s)
    if match_season_n:
        return omdb_search_show(show_d, season_n=int(match_season_n[0]), episode_n=episode_n)

def tvmaze_search_season(show_d, season_s, episode_n=None):
    rgx = re.compile('\d{2,4}$')
    match_season_n = re.search(rgx, season_s)
    if match_season_n:
        return tvmaze_search_show(show_d, season_n=int(match_season_n[0]), episode_n=episode_n)

def omdb_search_episode(show_d, season_s, episode_s):
    rgx = re.compile('[Ss]\d{2,4}[Ee]\d{2}')
    match = re.search(rgx, episode_s)
    if match:
        rgx = re.compile('[Ee]\d{2}')
        match = re.search(rgx, match[0])
        if match:
            rgx = re.compile('\d{2}')
            match_episode_n = re.search(rgx, match[0])
            if match_episode_n:
                return omdb_search_season(show_d, season_s=season_s, episode_n=int(match_episode_n[0]))

def tvmaze_search_episode(show_d, season_s, episode_s):
    rgx = re.compile('[Ss]\d{2,4}[Ee]\d{2}')
    match = re.search(rgx, episode_s)
    if match:
        rgx = re.compile('[Ee]\d{2}')
        match = re.search(rgx, match[0])
        if match:
            rgx = re.compile('\d{2}')
            match_episode_n = re.search(rgx, match[0])
            if match_episode_n:
                return tvmaze_search_season(show_d, season_s=season_s, episode_n=int(match_episode_n[0]))
