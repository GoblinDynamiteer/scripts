#!/usr/bin/python3.6

''' Generates a goto_locs.json file to be used by navigational script goto.py '''

import os
import json


def save(data, json_file):
    ''' Saves generated goto-locations to a json-file, file is used in goto.py script '''
    with open(json_file, 'w', encoding='utf8') as jf:
        json_string = json.dumps(data,
                                 indent=4, sort_keys=True,
                                 separators=(',', ': '), ensure_ascii=False)
        jf.write(json_string)


OPJ = os.path.join
HOME = os.path.expanduser("~")
SCRIPT_DIR = os.path.realpath(__file__)
JSON_FILE_PATH = OPJ(os.path.dirname(SCRIPT_DIR), "goto_locs.json")

LOCS = {"dl":    {"destinations": [OPJ(HOME, "downloads"),
                                   OPJ(HOME, "Downloads"),
                                   OPJ(os.sep, "mnt", "c", "Downloads"),
                                   OPJ(os.sep, "volume2", "DATA", "Temp", "Downloads")]},
        "code":  {"destinations": [OPJ(HOME, "code")]},
        "script":  {"destinations": [OPJ(HOME, "scripts")]},
        "film":  {"destinations": [OPJ(HOME, "smb", "film"),
                                   OPJ(os.sep, "volume2", "FILM")],
        "edu":  {"destinations": [OPJ(HOME, "smb", "docedu"),
                                  OPJ(os.sep, "volume2", "DOCEDU")]},
                  "alternatives": ["movies", "mov"]},
        "tv":    {"destinations": [OPJ(HOME, "smb", "tv"),
                                   OPJ(os.sep, "volume2", "TV")]},
        "dsdl":  {"destinations": [OPJ(HOME, "smb", "data", "Temp", "Downloads")],
                  "alternatives": ["dlds", "datadl"]},
        "data":  {"destinations": [OPJ(HOME, "smb", "data")]},
        "nzb":   {"destinations": [OPJ(HOME, "nzbget")]},
        "dotfiles":   {"destinations": [OPJ(HOME, "dotfiles")], 'alternatives': ['df']},
        "smb":   {"destinations": [OPJ(HOME, "smb")]},
        "misc":  {"destinations": [OPJ(HOME, "smb", "misc")]},
        "audio": {"destinations": [OPJ(HOME, "smb", "audio")]},
        "drive": {"destinations": [OPJ(HOME, "hd2", "gdrive"),
                                   OPJ(HOME, "gdrive")]}
        }

save(LOCS, JSON_FILE_PATH)
