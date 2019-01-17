#!/usr/bin/env python3.6

'''Script to interact with torrent-server'''

import argparse
import os

import config
import util
from db_mov import MovieDatabase
from db_tv import EpisodeDatabase
from printing import to_color_str as CSTR
from run import local_command, remote_command_get_output
from util_tv import is_episode


def _parse_ls(line: str):
    splits = line.split()
    if len(splits) < 4:
        return {}
    data = {}
    data['type'] = 'dir' if line.startswith('d') else 'file'
    data['size'] = util.bytes_to_human_readable(splits[4])
    data['date'] = f'{splits[5]} {splits[6]}'
    data['name'] = line.split(data['date'])[1].strip()
    return data


def _get_items():
    file_list = remote_command_get_output(
        r'ls -trl --time-style="+%Y-%m-%d %H:%M" ~/files', "wb").split('\n')
    items = [_parse_ls(line) for line in file_list]
    index = 1

    db_mov = MovieDatabase()
    db_ep = EpisodeDatabase()

    for item in items:
        if item:
            item['index'] = index
            index += 1
            item['downloaded'] = False
            if item['name'] in db_mov or item['name'] in db_ep:
                item['downloaded'] = True
    return [item for item in items if item]


def wb_list_items(items):
    "Lists items on server"
    for item in items:
        item_type = 'D' if item['type'] == 'dir' else 'F'
        media_type = 'Ukwn'  # unknown, TODO: determine seasonpack, movie
        index = f'#{item["index"]:02d}'
        if is_episode(item["name"]):
            media_type = 'Epsd'
        item_str_color = 'orange'
        if item['downloaded']:
            item_str_color = 'lgreen'
        print(
            f'[{CSTR(index, "orange")}] {item["date"]} '
            f'{item["size"]:>10} ({item_type}/{media_type}) '
            f'[{CSTR(item["name"], item_str_color)}]')


def _parse_get_indexes(items: list, indexes: str) -> list:
    if indexes.startswith('-'):  # download last x items
        return items[int(indexes):]
    indexes_to_dl = []
    try:
        for ix_split in indexes.split(','):
            if '-' in ix_split:
                ranges = ix_split.split('-')
                ran = [r for r in range(int(ranges[0]), int(ranges[1]) + 1)]
                indexes_to_dl.extend(ran)
            else:
                indexes_to_dl.append(int(ix_split))
        return [item for item in items if item['index'] in indexes_to_dl]
    except:
        print(f'{CSTR("could not parse indexes, aborting!", "red")}')
        return []


def _download(item: dict, dest: str):
    file_name = item["name"].replace(' ', r'\ ')
    print(f'downloading: {CSTR(file_name, "orange")}')
    command = f'scp -r wb:"~/files/{file_name}" {dest}'
    local_command(command, hide_output=False)


def wb_download_items(items: list, indexes: str, dest_dir: str):
    "Downloads the items passed, based on indexes, to dest_dir"
    if not os.path.exists(dest_dir):
        print(f'{CSTR("destination does not exist, aborting!", "red")}')
        return
    items_to_dl = _parse_get_indexes(items, indexes)
    [_download(item, dest_dir) for item in items_to_dl]


if __name__ == "__main__":
    CFG = config.ConfigurationManager()
    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('command', type=str, help='list/download')
    PARSER.add_argument('--dest', type=str, default=CFG.get('path_download'))
    PARSER.add_argument('--get', type=str, default='-1',
                        help='items to download. indexes')
    ARGS = PARSER.parse_args()

    print('listing items...')
    DOWNLOAD_ITEMS = _get_items()

    if ARGS.command == 'list':
        wb_list_items(DOWNLOAD_ITEMS)
    elif ARGS.command == 'download':
        wb_download_items(DOWNLOAD_ITEMS, ARGS.get, ARGS.dest)
    else:
        print(CSTR('wrong command!', 'orange'))
