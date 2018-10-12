#!/usr/bin/env python3

''' Personal navigation script '''

import os
import sys
import json


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


HOME = os.path.expanduser("~")
SCRIPT_DIR = os.path.realpath(__file__)
JSON_FILE_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "goto_locs.json")
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
                print(goto.get_path())
