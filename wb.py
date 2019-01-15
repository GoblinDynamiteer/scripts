#!/usr/bin/env python3.6

'''Script to interact with torrent-server'''

import argparse

import util
from util_tv import is_episode
from printing import to_color_str as CSTR
from run import remote_command_get_output


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
    for item in items:
        if item:
            item['index'] = index
            index += 1
    return [item for item in items if item]


def wb_list_items(items):
    for item in items:
        item_type = 'D' if item['type'] == 'dir' else 'F'
        media_type = 'Ukwn'  # unknown, TODO: determine seasonpack, movie
        index = f'#{item["index"]:02d}'
        if is_episode(item["name"]):
            media_type = 'Epsd'
        print(
            f'[{CSTR(index, "orange")}] {item["date"]} '
            f'{item["size"]:>10} ({item_type}/{media_type}) '
            f'[{CSTR(item["name"], "lgreen")}]')


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='ripper')
    PARSER.add_argument('command', type=str, help='list/download')
    ARGS = PARSER.parse_args()

    DOWNLOAD_ITEMS = _get_items()

    if ARGS.command == 'list':
        wb_list_items(DOWNLOAD_ITEMS)
    elif ARGS.command == 'download':
        print(CSTR('Not yet implemented', 'red'))
    else:
        print(CSTR('wrong command!', 'orange'))
