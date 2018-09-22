# -*- coding: utf-8 -*-
import paths, json, os, argparse
import db_tv as tv_database
import filetools as ftool
import tvshow as tvtool
from printout import print_class as pr

pr = pr(os.path.basename(__file__))
db = tv_database.database()
if not db.load_success():
    pr.error("database read error, quitting...")
    quit()

tv_root = tvtool.root_path()
shows = os.listdir(tv_root)
shows.sort()

def __flatten_eps():
    flat_ep_list = []
    for show_s in db.list_shows():
        show_d = db.data(show_s)
        season_index = 0
        for season_d in show_d["seasons"]:
            episode_index = 0
            for episode_d in season_d["episodes"]:
                episode_d["show"] = show_s
                episode_d["season_index"] = season_index
                episode_d["episode_index"] = episode_index
                episode_d["full_path"] = os.path.join(tv_root, show_s, season_d["folder"], episode_d["file"])
                flat_ep_list.append(episode_d)
                episode_index += 1
            season_index += 1
    return flat_ep_list

def find_ep_data(key, data):
    pr.info(f"showing all eps where [{key} == {data}]")
    found = 0
    eps = __flatten_eps()
    for ep in eps:
        if ep[key] == data:
            pr.info(ep["file"])
            found += 1
    pr.info(f"scan done, found [{found}] eps")

def check_nfo():
    global shows
    skiplist = [ "Vad Blir Det For Mat" ]
    for show in shows:
        if show.startswith("@"): # Diskstation
            continue;
        if show in skiplist:
            pr.info(f"in skiplist: [{show}]")
            continue
        if tvtool.has_nfo(show):
            if tvtool.nfo_to_imdb(show):
                pr.info("{} has tvshow.nfo".format(show))
            else:
                pr.warning("{} has non-imdb tvshow.nfo".format(show))
                tvtool.add_nfo_manual(show, replace=True)
        else:
            tvtool.add_nfo_manual(show)

def se_upper():
    need_save = False
    for ep in __flatten_eps():
        if not ep["se"] or ep["status"] == "deleted":
            continue
        if ep["se"].startswith("s"):
            si = ep["season_index"]
            ei = ep["episode_index"]
            show_d = db.data(ep["show"])
            pr.info(f"found lowercase: {show_d['seasons'][si]['episodes'][ei]['se']}")
            show_d["seasons"][si]["episodes"][ei]["se"] = ep["se"].upper()
            db.update(ep["show"], show_d, key=None)
            pr.info(f"upper: {ep['se'].upper()}")
            need_save = True
    if need_save:
        db.save()
        ftool.copy_dbs_to_webserver("tv")

def check_status():
    pr.info("confirming episode status flags...")
    need_save = False
    for ep in __flatten_eps():
        if ep["status"] == "deleted":
            if ftool.is_existing_file(ep['full_path']):
                pr.warning(f"not deleted: [{ep['full_path']}]")
                si = ep["season_index"]
                ei = ep["episode_index"]
                show_d = db.data(ep["show"])
                show_d["seasons"][si]["episodes"][ei]['status'] = "ok"
                db.update(ep["show"], db.data(ep["show"], key=None))
                need_save = True
        else:
            if not ftool.is_existing_file(ep['full_path']):
                pr.info(f"found deleted: [{ep['full_path']}]")
                si = ep["season_index"]
                ei = ep["episode_index"]
                show_d = db.data(ep["show"])
                show_d["seasons"][si]["episodes"][ei]['status'] = "deleted"
                db.update(ep["show"], db.data(ep["show"], key=None))
                need_save = True
    if need_save:
        db.save()
        ftool.copy_dbs_to_webserver("tv")

def omdb_update():
    pr.info("trying to omdb-search for missing data")
    save_db = False
    success_count = 0
    for show_s in db.list_shows():
        if in_skip_list(show_s):
            pr.info(f"skipping {show_s}, in skip list...")
            continue
        need_update = False
        show_d = db.data(show_s)
        nfo_imdb = tvtool.nfo_to_imdb(show_d)
        if nfo_imdb:
            if show_d["imdb"] != nfo_imdb:
                show_d["imdb"] = nfo_imdb
                need_update = True
                pr.info(f"found new (hopefully) imdb-id [{nfo_imdb}] in nfo for {show_s}")
        if not show_d["omdb"]:
            omdb_result = tvtool.omdb_search_show(show_d)
            if omdb_result:
                show_d["omdb"] = omdb_result
                need_update = True
                success_count += 1
        season_index = 0
        for season_d in show_d["seasons"]:
            if not season_d["omdb"]:
                omdb_result = tvtool.omdb_search_season(show_d, season_d["folder"])
                if omdb_result:
                    show_d["seasons"][season_index]["omdb"] = omdb_result
                    need_update = True
                    success_count += 1
            episode_index = 0
            for episode_d in season_d["episodes"]:
                if episode_d["status"] == "deleted":
                    continue
                if not episode_d["omdb"]:
                    omdb_result = tvtool.omdb_search_episode(
                        show_d, season_d["folder"], episode_d["file"])
                    if omdb_result:
                        need_update = True
                        success_count += 1
                        show_d["seasons"][season_index]["episodes"][episode_index]["omdb"] = omdb_result
                episode_index += 1
            season_index +=1
        if need_update:
            save_db = True
            db.update(show_d["folder"], show_d, key=None)
    pr.info("done!")
    if success_count > 0:
        pr.info("successfully updated omdb-data for {} items".format(success_count))
    if save_db:
        db.save()
        ftool.copy_dbs_to_webserver("tv")

def in_skip_list(tv_show_folder):
    if tv_show_folder in [  'Breaking News med Filip & Fredrik', 'En Stark Resa',
                            'GWs Mord', 'Hela Sverige Bakar', 'Lyxfallan',
                            'Outsiders', 'Tunnelbanan', 'Vad Blir Det For Mat',
                            'American Dad', 'Mythbusters', 'Sommar Med Ernst']:
        return True
    return False

def tvmaze_update():
    pr.info("trying to tvmaze-search for missing data")
    save_db = False
    success_count = 0
    for show_s in db.list_shows():
        if in_skip_list(show_s):
            pr.info(f"skipping {show_s}, in skip list...")
            continue
        need_update = False
        show_d = db.data(show_s)
        nfo_imdb = tvtool.nfo_to_imdb(show_d)
        if nfo_imdb:
            if show_d["imdb"] != nfo_imdb:
                show_d["imdb"] = nfo_imdb
                need_update = True
                pr.info(f"found new (hopefully) imdb-id [{nfo_imdb}] in nfo for {show_s}")
        if not "tvmaze" in show_d:
            show_d["tvmaze"] = None
        if not show_d["tvmaze"]:
            tvmaze_result = tvtool.tvmaze_search_show(show_d)
            if tvmaze_result:
                show_d["tvmaze"] = tvmaze_result
                need_update = True
                success_count += 1
        season_index = 0
        for season_d in show_d["seasons"]:
            if not "tvmaze" in season_d:
                season_d["tvmaze"] = None
            if not season_d["tvmaze"]:
                tvmaze_result = tvtool.tvmaze_search_season(show_d, season_d["folder"])
                if tvmaze_result:
                    show_d["seasons"][season_index]["tvmaze"] = tvmaze_result
                    need_update = True
                    success_count += 1
            episode_index = 0
            for episode_d in season_d["episodes"]:
                if episode_d["status"] == "deleted":
                    continue
                if not "tvmaze" in episode_d:
                    episode_d["tvmaze"] = None
                if not episode_d["tvmaze"]:
                    tvmaze_result = tvtool.tvmaze_search_episode(
                        show_d, season_d["folder"], episode_d["file"])
                    if tvmaze_result:
                        need_update = True
                        success_count += 1
                        show_d["seasons"][season_index]["episodes"][episode_index]["tvmaze"] = tvmaze_result
                episode_index += 1
            season_index +=1
        if need_update:
            save_db = True
            db.update(show_d["folder"], show_d, key=None)
    pr.info("done!")
    if success_count > 0:
        pr.info("successfully updated tvmaze-data for {} items".format(success_count))
    if save_db:
        db.save()
        ftool.copy_dbs_to_webserver("tv")

def scan_all_subtitles():
    pr.info("scanning for subs")
    save_db = False
    new_count = 0
    for ep in __flatten_eps():
        if ep["status"] == "deleted":
            continue
        si = ep["season_index"]
        ei = ep["episode_index"]
        if not "subs" in ep:
            show_d = db.data(ep["show"])
            show_d["seasons"][si]["episodes"][ei]['subs'] = {'sv' : None, 'en' : None }
            ep["subs"] = {'sv' : None, 'en' : None }
            db.update(ep["show"], show_d, key=None)
            save_db = True
        if not ep['subs']['sv']:
            sv_srt_file = tvtool.has_subtitle(ep["show"], ep["file"], "sv")
            if sv_srt_file:
                show_d = db.data(ep["show"])
                show_d["seasons"][si]["episodes"][ei]['subs']['sv'] = sv_srt_file
                db.update(ep["show"], show_d, key=None)
                pr.info(f"found [{sv_srt_file}]")
                save_db = True
        if not ep['subs']['en']:
            en_srt_file = tvtool.has_subtitle(ep["show"], ep["file"], "en")
            if en_srt_file:
                show_d = db.data(ep["show"])
                show_d["seasons"][si]["episodes"][ei]['subs']['en'] = en_srt_file
                db.update(ep["show"], show_d, key=None)
                pr.info(f"found [{en_srt_file}]")
                save_db = True
    pr.info("done!")
    if save_db:
        db.save()
        ftool.copy_dbs_to_webserver("tv")

def omdb_force_update(show_s):
    success_count = 0
    pr.info("force-updating omdb-data for {}".format(show_s))
    show_d = db.data(show_s)
    nfo_imdb = tvtool.nfo_to_imdb(show_d)
    if nfo_imdb:
        if show_d["imdb"] != nfo_imdb:
            show_d["imdb"] = nfo_imdb
            need_update = True
            pr.info(f"found new (hopefully) imdb-id [{nfo_imdb}] in nfo for {show_s}")
    omdb_result = tvtool.omdb_search_show(show_d)
    show_d["omdb"] = omdb_result
    season_index = 0
    for season_d in show_d["seasons"]:
        omdb_result = tvtool.omdb_search_season(show_d, season_d["folder"])
        show_d["seasons"][season_index]["omdb"] = omdb_result
        episode_index = 0
        for episode_d in season_d["episodes"]:
            if episode_d["status"] == "deleted":
                continue
            omdb_result = tvtool.omdb_search_episode(show_d, season_d["folder"], episode_d["file"])
            show_d["seasons"][season_index]["episodes"][episode_index]["omdb"] = omdb_result
            episode_index += 1
        season_index +=1
    db.update(show_d["folder"], show_d, key=None)
    db.save()
    ftool.copy_dbs_to_webserver("tv")

parser = argparse.ArgumentParser(description='TVDb tools')
parser.add_argument('func', type=str,
    help='TVDb command: maintain, checknfo, omdbsearch, tvmazesearch, omdbforce, subscan, epdata')
parser.add_argument('--show', "-s", type=str, dest="show_s", default=None, help='show to process')
parser.add_argument('--key', "-k", type=str, dest="key", default=None, help='key')
parser.add_argument('--data', "-d", type=str, dest="data", default=None, help='daa')
args = parser.parse_args()

if args.func == "checknfo":
    check_nfo()
elif args.func == "subscan":
    scan_all_subtitles()
elif args.func == "maintain":
    se_upper()
    check_status()
elif args.func == "epdata":
    if args.key and args.data:
        find_ep_data(args.key, args.data)
    else:
        pr.error("need to supply key and data for epdata")
elif args.func == "omdbsearch":
    omdb_update()
elif args.func == "tvmazesearch":
    tvmaze_update()
elif args.func == "omdbforce":
    if not args.show_s:
        pr.error("please supply show name with --s / -s")
    elif not db.exists(args.show_s):
        pr.error("invalid show: {}".format(args.show_s))
    else:
        omdb_force_update(args.show_s)
else:
    pr.error("wrong command: {}".format(args.func))
