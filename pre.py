#!/usr/bin/env python3.6

""" pre search """

import argparse
import glob
import json
import sys
from pathlib import Path

import requests

import config


CFG = config.ConfigurationManager()


def run_replace_list_on_query(query_string):
    replace_file_path = Path(CFG.path("scripts")) / 'pre_replace.json'
    with open(replace_file_path) as replace_fp:
        for string, replacement in json.load(replace_fp).items():
            query_string = query_string.replace(string, replacement)
    return query_string


def pre_search(query: str) -> list:
    """ runs a pre search, returns list matched names """
    json_response = requests.get(
        f"https://predb.ovh/api/v1/?q={query}&count=50")
    try:
        data = json.loads(json_response.text)
        rows = data['data']['rows']
    except json.decoder.JSONDecodeError:
        print(f"got json decoder error! on query: {query}")
        print(json_response)
        return False
    return [row['name'] for row in rows]


def pre_search_from_file(file_name: str, use_replacement_list=True) -> str:
    """ runs a pre search, return best match if possible """
    file_name = run_replace_list_on_query(
        file_name) if use_replacement_list else file_name
    split_filename = file_name.split('.')
    query = f'{" ".join(split_filename)}'
    results = pre_search(query)
    if results:
        for result in results:
            if '1080p' in result:  # prefer 1080p results
                return result
        return results[0]
    return ""


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Pre Search')
    PARSER.add_argument('query', type=str, help='Search query')
    PARSER.add_argument('--suffix', type=str, help='add suffix', default=None)
    PARSER.add_argument(
        '-f', '--file', help='use file search mode', action='store_true')
    PARSER.add_argument(
        '-r', '--rename', help='rename file', action='store_true')
    ARGS = PARSER.parse_args()

    suffix = ARGS.suffix if ARGS.suffix else ""

    if ARGS.file:
        if '*' in ARGS.query:
            ITEMS = glob.glob(ARGS.query)
        else:
            ITEMS = [ARGS.query]
        for item in ITEMS:
            RET = pre_search_from_file(item)
            if not RET:
                if ARGS.rename:
                    print(
                        f"could not find release, not renaming file {item}")
                    sys.exit(1)
                else:
                    print("could not find release")
                    sys.exit(1)
            print(RET + suffix)
            if ARGS.rename:
                FILE_NAME = Path(item)
                if not FILE_NAME.exists():
                    print(
                        f'found release but {FILE_NAME} does not exist, will not rename...')
                    sys.exit(1)
                NEW_FILE_NAME = RET
                if not RET.endswith(FILE_NAME.suffix):
                    NEW_FILE_NAME = RET + FILE_NAME.suffix
                print("renaming: " + str(FILE_NAME) + " -> " + NEW_FILE_NAME)
                FILE_NAME.rename(NEW_FILE_NAME)
    else:
        RET = pre_search(ARGS.query)
        if not RET:
            print("could not find release")
        else:
            for name in RET:
                print(name + suffix)
