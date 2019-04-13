#!/usr/bin/env python3

'''
Personal navigation script
Use with external script, example for fish:

    function goto
        set dir (~/scripts/goto.py $argv)
        cd $dir
    end
'''

import os
import sys
import json
import util


def load(json_file):
    """ Loads json file with goto location data """
    with open(json_file, 'r') as jf:
        data = json.load(jf)
    return data


class Goto(object):
    """ Stores 'goto-locations' """

    def __init__(self, shortcut):
        self.shortcuts = [shortcut]
        self.destinations = []

    def add_destination(self, destination):
        """ Adds an alternative goto destination,
        that can be used if primary is missing """
        self.destinations.append(destination)

    def get_shortcuts(self):
        """ Returns the shortcut of the Goto """
        return self.shortcuts

    def add_shortcut(self, shortcut):
        """ Adds another shortcut that can be used
        for the location """
        self.shortcuts.append(shortcut)

    def get_path(self):
        """ Returns the first valid destination,
        stored in Location. None is returned if
        no existing path is found """
        for dest in self.destinations:
            if os.path.exists(dest):
                return dest
        return None


def _match_subdir(orig_path, sub_str: str):
    if not util.is_dir(orig_path):
        return ""
    for item in os.listdir(orig_path):
        if util.is_file(os.path.join(orig_path, item)):
            continue
        if sub_str.lower() in item.lower():
            return item  # TODO: handle several matches
    return ""


if __name__ == '__main__':
    HOME = os.path.expanduser("~")
    SCRIPT_DIR = os.path.realpath(__file__)
    JSON_FILE_PATH = os.path.join(
        os.path.dirname(SCRIPT_DIR), "goto_locs.json")
    LOCS = load(JSON_FILE_PATH)

    GOTOS = []
    ARGUMENT = None

    for sc in LOCS:
        g = Goto(sc)
        for d in LOCS[sc]["destinations"]:
            g.add_destination(d)
        try:
            for a in LOCS[sc]["alternatives"]:
                g.add_shortcut(a)
        except KeyError:
            pass
        GOTOS.append(g)

    if len(sys.argv) > 1:
        ARGUMENT = sys.argv[1]
        for goto in GOTOS:
            for sc in goto.get_shortcuts():
                if ARGUMENT == sc:
                    path = goto.get_path()
                    if len(sys.argv) > 2:
                        for index, arg in enumerate(sys.argv):
                            if index < 2:
                                continue
                            subdir = _match_subdir(path, sys.argv[index])
                            path = os.path.join(path, subdir)
                    print(path)
