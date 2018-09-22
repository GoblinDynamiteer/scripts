# -*- coding: utf-8 -*-
import paths, os, platform, re, omdb
from config import configuration_manager as cfg
from printout import print_class as pr
import filetools as ftool

pr = pr(os.path.basename(__file__))
_mov_letters = { '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', \
    'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'VW', 'X', 'Y', 'Z' }

_config = cfg()

# Check if path is a valid movie root dir
def valid_movie_path(path):
    for let in _mov_letters:
        p = os.path.join(path, let)
        if not os.path.exists(p):
            return False
    return True

# Determine movie root path
def root_path():
    path = _config.get_setting("path", "movieroot")
    if not valid_movie_path(path):
        print_log("Could not find movies root location!", category="warning")
        quit()
    return path

# Check if movie has srt file
def has_subtitle(path, lang):
    return ftool.get_file(path, lang + ".srt")

# Check if movie has srt file
def has_nfo(path):
    return True if ftool.get_file(path, "nfo") is not None else False

# Extract IMDb-id from nfo
def nfo_to_imdb(path):
    if not has_nfo(path):
        return None
    f = open(ftool.get_file(path, "nfo", full_path = True), "r")
    imdb_url = f.readline()
    f.close()
    re_imdb = re.compile("tt\d{1,}")
    imdb_id = re_imdb.search(imdb_url)
    return imdb_id.group(0) if imdb_id else None

# Determine video file for movie
def get_vid_file(path):
    for ext in [ "mkv", "avi", "mp4" ]:
        vid = ftool.get_file(path, ext)
        if vid:
            return vid
    return None

# Determine letter from movie folder
def determine_letter(folder):
    folder = folder.replace(" ", ".")
    let = folder[0:1]
    for prefix in ['The.', 'An.', 'A.']:
        if folder.startswith(prefix):
            let = folder[len(prefix):len(prefix) + 1]
    if let is "V" or let is "W":
        return "VW"
    pr.info("guessed letter: {}".format(let))
    return let

# Try to determine movie title from folder name
def determine_title(folder, replace_dots_with=' '):
    re_title = re.compile(".+?(?=\.(\d{4}|REPACK|720p|1080p|DVD|BluRay))")
    title = re_title.search(folder)
    if title is not None:
        title = re.sub('(REPACK|LiMiTED|EXTENDED|Unrated)', '.', title.group(0))
        title = re.sub('\.', replace_dots_with, title)
        return title
    else:
        pr.warning("could not guess title for {}".format(folder))
        return None

# Try to determine movie year from folder name
def determine_year(folder):
    re_year = re.compile("(19|20)\d{2}")
    year = re_year.search(folder)
    if year is not None:
        return year.group(0)
    else:
        pr.warning("could not guess year for {}".format(folder))
        return None

def remove_extras_from_folder(folder):
    extras = [  "repack", "limited", "extended", "unrated", "swedish",
                "remastered", "festival", "docu", "rerip", "internal",
                "finnish", "danish", "dc.remastered", "proper", "bluray",
                "jpn", "hybrid", "uncut"]
    rep_string = "\\.({})".format("|".join(extras))
    return re.sub(rep_string, '', folder, flags=re.IGNORECASE)

# Search OMDb for movie
def omdb_search(movie):
    folder = movie['folder']
    pr.info(f"searching OMDb for [{folder}] ", end_line=False)
    if movie['imdb'] is not None:
        pr.color_brackets(f"as [{movie['imdb']}] >", "green", end_line=False)
        omdb_search = omdb.omdb_search(str(movie['imdb']))
    else:
        title = determine_title(folder , replace_dots_with='+')
        year =  determine_year(folder)
        pr.color_brackets(f"as [{title}] >", "green", end_line=False)
        omdb_search = omdb.omdb_search(title, type="movie", year=year)
    data = omdb_search.data()
    try:
        if data['Response'] == "False":
            pr.color_brackets(" [response false]!", "yellow")
            return None
        pr.color_brackets(" [got data]!", "green")
        return data
    except:
        pr.color_brackets(" [script error] !", "red")
        return None
