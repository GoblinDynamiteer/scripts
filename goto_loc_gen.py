#!/usr/bin/python3

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
MONSTER_OEB_HOME = os.path.join(os.sep, 'mnt', 'cs-builds', 'johan.kampe')

LOCS = {"dl":    {"destinations": [os.path.join(HOME, "downloads"),
                                   os.path.join(HOME, "Downloads"),
                                   os.path.join(os.sep, "volume2", "DATA", "Temp", "Downloads")]},
        "code":  {"destinations": [os.path.join(HOME, "code")]},
        "script":  {"destinations": [os.path.join(HOME, "script")]},
        "scripts":  {"destinations": [os.path.join(HOME, "scripts")]},
        "py":  {"destinations": [os.path.join(HOME, "script", "python")]},
        "cs":  {"destinations": [os.path.join(HOME, "cs")]},
        "svn":  {"destinations": [os.path.join(HOME, "cs", "svn")]},
        "cm":  {"destinations": [os.path.join(HOME, "cs", "chargemanager")]},
        "oeb":  {"destinations": [os.path.join(MONSTER_OEB_HOME, 'oe-build')]},
        "oeb35":  {"destinations": [os.path.join(MONSTER_OEB_HOME, 'oe-build-r3.5.x')]},
        "oeb36":  {"destinations": [os.path.join(MONSTER_OEB_HOME, 'oe-build-r3.6.x')]},
        "oeb37":  {"destinations": [os.path.join(MONSTER_OEB_HOME, 'oe-build-r3.7.x')]},
        "oeb38":  {"destinations": [os.path.join(MONSTER_OEB_HOME, 'oe-build-r3.8.x')]},
        "cm35":  {"destinations": [os.path.join(HOME, "cs", "chargemanager-r3.5.x")]},
        "cm36":  {"destinations": [os.path.join(HOME, "cs", "chargemanager-r3.6.x")]},
        "cm37":  {"destinations": [os.path.join(HOME, "cs", "chargemanager-r3.7.x")]},
        "cm38":  {"destinations": [os.path.join(HOME, "cs", "chargemanager-r3.8.x")]},
        "om":  {"destinations": [os.path.join(HOME, "cs", "outletmanager")]},
        "om35":  {"destinations": [os.path.join(HOME, "cs", "outletmanager-r3.5.x")]},
        "om36":  {"destinations": [os.path.join(HOME, "cs", "outletmanager-r3.6.x")]},
        "om37":  {"destinations": [os.path.join(HOME, "cs", "outletmanager-r3.7.x")]},
        "om38":  {"destinations": [os.path.join(HOME, "cs", "outletmanager-r3.8.x")]},
        "hcc":  {"destinations": [os.path.join(HOME, "cs", "hcc")]},
        "drive2": {"destinations": [os.path.join(HOME, "gdrive")]},
        "drive": {"destinations": [os.path.join(HOME, "hd2", "gdrive"),
                                   os.path.join(HOME, "gdrive-personal")]}
        }

save(LOCS, JSON_FILE_PATH)
