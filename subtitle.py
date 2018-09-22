#!/usr/bin/env python3.6

''' Subtitle tools '''

import argparse
import os
import paths
import user_input
import shlex
import subprocess
import re
from printout import print_class as pr
import filetools as ftool
import tvshow as tvtool
import movie as mtool
import db_mov as movie_database
import subscene

DB_MOV = movie_database.database()
PRINT = pr(os.path.basename(__file__))

PARSER = argparse.ArgumentParser(description='subTools')
PARSER.add_argument('command', type=str, help='commands: ripall, renameall')
PARSER.add_argument('--movie', "-m", type=str,
                    dest="movie_folder", default=None, help='movie folder')
ARGS = PARSER.parse_args()
CWD = os.getcwd()


class MKVInfoCommand:
    def __init__(self, vid_file_path):
        self.file = vid_file_path
        self.o = self._run()

    def _run(self):
        PRINT.info(f"running command: [mkvinfo \"{self.file}\"]")
        args = ["mkvinfo", self.file]
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = process.communicate()
        return out

    def get_o(self):
        return self.o
    output = property(get_o)


def mkvextract(vid_file_path, track, lang):
    dest = vid_file_path.replace(".mkv", f".{lang}.srt")
    if not ftool.is_existing_file(dest):
        PRINT.info(f"mkvextract tracks {vid_file_path} {track}:{dest}")
        args = ["mkvextract", "tracks", vid_file_path, f"{track}:{dest}"]
        process = subprocess.Popen(args)
        out, err = process.communicate()
    else:
        PRINT.warning(f"[{dest}] already exists! skipping")


def _load_words(lang):
    ret_list = []
    script_loc = os.path.dirname(os.path.realpath(__file__))
    word_file = f"sub_words_{lang}.txt"
    word_file_path = os.path.join(script_loc, "txt", word_file)
    if not ftool.is_existing_file(word_file_path):
        PRINT.error(f"could not find file [{word_file_path}]")
        return None
    try:
        with open(word_file_path, 'r', encoding="ISO-8859-1") as words:
            for line in words:
                ret_list.append(line.replace("\n", ""))
    except:
        PRINT.error(f"could not load file [{word_file}]")
        return None
    return ret_list


def determine_lang(srt_file_path):
    words_en = _load_words("en")
    words_sv = _load_words("sv")
    points = {"en": 0, "sv": 0}
    with open(srt_file_path, 'r', encoding="ISO-8859-1") as srt_lines:
        for srt_line in srt_lines:
            for word in words_en:
                if word in srt_line:
                    points["en"] += 1
            for word in words_sv:
                if word in srt_line:
                    points["sv"] += 1
    if points["sv"] == points["en"]:
        return None
    if points["sv"] > points["en"]:
        return "sv"
    return "en"


def _vid_to_srt_filename(vid_file_name, lang):
    EXTENSIONS = [".mkv", ".avi", ".mp4"]
    for ext in EXTENSIONS:
        if vid_file_name.endswith(ext):
            return vid_file_name.replace(ext, f".{lang}.srt")
    return None


def rename_srt(srt_file_path, lang):
    sub_dir = os.path.dirname(os.path.realpath(srt_file_path))
    sub_file_name = os.path.basename(srt_file_path)
    file_list = os.listdir(sub_dir)
    vid_files = []  # vid files in same dir as passed subtitle
    for vid in file_list:
        if vid.endswith(".mkv") or vid.endswith(".avi") or vid.endswith(".mp4"):
            srt_file_name = _vid_to_srt_filename(vid, lang)
            vid_files.append({"file": vid, "srt_name": srt_file_name})
    sub_se = tvtool.guess_season_episode(sub_file_name)
    for vid in vid_files:
        if ftool.is_existing_file(vid['srt_name']):
            if vid['srt_name'] == sub_file_name:
                return
            continue  # already has subtitle
        if tvtool.guess_season_episode(vid["file"]) == sub_se:
            PRINT.info(
                f"srt:         [{sub_file_name}]", brackets_color="yellow")
            dst_path = os.path.join(sub_dir, vid['srt_name'])
            try:
                os.rename(srt_file_path, dst_path)
                PRINT.info(f"renamed ==> [{vid['srt_name']}]",
                           brackets_color="green")
                return
            except:
                PRINT.warning(f"could not rename [{sub_file_name}]")
            break
    PRINT.warning(f"could not rename/find match for [{sub_file_name}]")


def find_srt_tracks(vid_file_path):
    re_track_number = re.compile("track\\snumber:\\s\\d{1,2}", re.IGNORECASE)
    mkvinfo = MKVInfoCommand(vid_file_path)
    lines = mkvinfo.output.decode('utf-8').split("|")
    tracks = {}
    track_number = -1
    for line in lines:
        match = re_track_number.search(line)
        if match:
            track_number = match[0].split(":")[1].replace(" ", "")
            tracks[int(track_number)] = {
                "type": None, "lang": None, "name": None}
        if "Track type: subtitles" in line:
            tracks[int(track_number)]["type"] = "sub"
        if "Language: " in line:
            tracks[int(track_number)]["lang"] = line.split(": ")[1]
        if "Name: " in line:
            tracks[int(track_number)]["name"] = line.split(": ")[1]
    srt_tracks = []
    for track_no in tracks:
        lang = "unkown"
        if tracks[track_no]["type"]:
            if tracks[track_no]["name"]:
                if "nglish" in tracks[track_no]["name"]:
                    lang = "en"
                elif "wedish" in tracks[track_no]["name"]:
                    lang = "sv"
            if tracks[track_no]["lang"]:
                # TODO: Check that eng/swe is correct string for matching
                if "eng" in tracks[track_no]["lang"]:
                    lang = "en"
                elif "swe" in tracks[track_no]["lang"]:
                    lang = "sv"
        srt_tracks.append({"track": track_no, "lang": lang})
    return srt_tracks


def subscene_search(movie_title, movie_folder):
    PRINT.info(f"searching subscene for {movie_title}")
    folder_words = movie_folder.split(".")
    film = subscene.search(movie_title)
    sub_candidates = {"en": [], "sv": []}
    sv_winner = None
    en_winner = None  # TODO: can hearing impaired be identified?
    for sub in film.subtitles:
        if sub.language.lower() == "swedish":
            sub_candidates["sv"].append(
                {"name": str(sub), "url": sub.zipped_url, "points": 0})
        elif sub.language.lower() == "english":
            sub_candidates["en"].append(
                {"name": str(sub), "url": sub.zipped_url, "points": 0})
    for sv_sub in sub_candidates["sv"]:
        for word in folder_words:
            if word in sv_sub["name"]:
                sv_sub["points"] += 1
    for en_sub in sub_candidates["en"]:
        for word in folder_words:
            if word in en_sub["name"]:
                en_sub["points"] += 1
    old_points = -1
    for sv_sub in sub_candidates["sv"]:
        if sv_sub["points"] > old_points:
            sv_winner = sv_sub
            old_points = sv_sub["points"]
    old_points = -1
    for en_sub in sub_candidates["en"]:
        if en_sub["points"] > old_points:
            en_winner = en_sub
            old_points = en_sub["points"]
    return {"sv": sv_winner, "en": en_winner}


if ARGS.command == "ripall":
    PRINT.info(f"extracting all srts from mkv-files in dir [{CWD}]")
    FILES = os.listdir(CWD)
    FILES.sort()
    for f in FILES:
        if f.endswith(".mkv"):
            vid = os.path.join(CWD, f)
            srts = find_srt_tracks(vid)
            for srt in srts:
                if srt["lang"] == "sv" or srt["lang"] == "en":
                    mkvextract(vid, srt["track"] - 1, srt["lang"])
elif ARGS.command == "renameall":
    FILES = os.listdir(CWD)
    FILES.sort()
    for f in FILES:
        if f.endswith(".srt"):
            lang = determine_lang(os.path.join(CWD, f))
            if not lang:
                PRINT.warning(f"could not determine lang of [{f}]")
                continue
            rename_srt(os.path.join(CWD, f), lang)
elif ARGS.command == "search":
    if not ARGS.movie_folder:
        PRINT.error("pass movie folder with --movie / -m")
    elif DB_MOV.exists(ARGS.movie_folder.replace(r"/", "")):
        TITLE = DB_MOV.omdb_data(ARGS.movie_folder, "Title")
        if TITLE:
            SUBS = subscene_search(TITLE, ARGS.movie_folder.replace(r"/", ""))
        else:
            SUBS = subscene_search(mtool.determine_title(
                ARGS.movie_folder), ARGS.movie_folder.replace(r"/", ""))
        print(SUBS["en"]["url"])
        print(SUBS["sv"]["url"])
    else:
        PRINT.warning(f"{ARGS.movie_folder} not in db")
