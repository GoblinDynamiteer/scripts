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


HOME = os.path.expanduser("~")
SCRIPT_DIR = os.path.realpath(__file__)
JSON_FILE_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "goto_locs.json")

LOCS = {"dl":    {"destinations": [os.path.join(HOME, "downloads"),
                                   os.path.join(HOME, "Downloads"),
                                   os.path.join(os.sep, "volume2", "DATA", "Temp", "Downloads")]},
        "code":  {"destinations": [os.path.join(HOME, "code")]},
        "script":  {"destinations": [os.path.join(HOME, "scripts")]},
        "film":  {"destinations": [os.path.join(HOME, "smb", "film"),
                                   os.path.join(os.sep, "volume2", "FILM")],
                  "alternatives": ["movies", "mov"]},
        "tv":    {"destinations": [os.path.join(HOME, "smb", "tv"),
                                   os.path.join(os.sep, "volume2", "TV")]},
        "dsdl":  {"destinations": [os.path.join(HOME, "smb", "data", "Temp", "Downloads")],
                  "alternatives": ["dlds", "datadl"]},
        "data":  {"destinations": [os.path.join(HOME, "smb", "data")]},
        "nzb":   {"destinations": [os.path.join(HOME, "nzbget")]},
        "dotfiles":   {"destinations": [os.path.join(HOME, "dotfiles")], 'alternatives' : ['df']},
        "smb":   {"destinations": [os.path.join(HOME, "smb")]},
        "misc":  {"destinations": [os.path.join(HOME, "smb", "misc")]},
        "audio": {"destinations": [os.path.join(HOME, "smb", "audio")]},
        "drive": {"destinations": [os.path.join(HOME, "hd2", "gdrive"),
                                   os.path.join(HOME, "gdrive")]}
        }

save(LOCS, JSON_FILE_PATH)
