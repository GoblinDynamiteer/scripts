#!/usr/bin/env python3.6

import os
import sys
import socket
from collections import namedtuple


def get_home():
    return os.path.expanduser("~")


def find_drive_location():
    home = get_home()
    possbile_locs = []
    possbile_locs.append(os.path.join(home, 'hd2', 'gdrive'))
    for loc in possbile_locs:
        if os.path.isdir(loc):
            return loc
    return None


def find_backup_sources():
    home = get_home()
    src_list = []
    possible_src = []
    possible_src.append(os.path.join(home, '.config', 'i3'))


def get_gdrive_home():
    homes = {'corsair': 'corsair'}
    host_name = socket.gethostname()
    if host_name in homes:
        print('could not determine backup home dest from hostname')
        return homes[host_name]
    return None


def get_backup_home_loc():
    gdrive_loc = find_drive_location()
    if not gdrive_loc:
        return None
    grdive_home_loc = get_gdrive_home()
    return os.path.join(gdrive_loc, 'backup', 'homes', grdive_home_loc)


DESTINATION = get_backup_home_loc()
if not DESTINATION:
    print('could not determine backup destination!\nquitting...')
    sys.exit()

if not os.path.exists(DESTINATION):
    print(
        f'backup destination found, but does not exist ({DESTINATION})!\nquitting...')
    sys.exit()

SOURCE = namedtuple('source', 'source dest')
SOURCES = [SOURCE(os.path.join(get_home(), '.config', 'i3*'), '.config/'),
           SOURCE(os.path.join(get_home(), '.bash*'), ''),
           SOURCE(os.path.join(get_home(), '.vimrc'), ''),
           SOURCE(os.path.join(get_home(), '.inputrc'), ''),
           SOURCE(os.path.join(get_home(), '.screenlayout'), ''),
           SOURCE(os.path.join(get_home(), '.ssh'), '')]

RSYNC_COMMAND_PREFIX = r'rsync -urv --exclude=.git --exclude=__pycache__'
DRIVE_COMMMAND = f'drive push -hidden -ignore-checksum=false -no-prompt {DESTINATION}'

# TODO run rsyn command
for s, d in SOURCES:
    print(f"{RSYNC_COMMAND_PREFIX} {s} {os.path.join(DESTINATION, d)}")
