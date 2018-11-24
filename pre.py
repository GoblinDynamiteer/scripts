#!/usr/bin/env python3.6

""" pre search """

import argparse
import json
import requests


def pre_search(query: str) -> list:
    """ runs a pre search, returns list matched names """
    json_response = requests.get(
        f"https://predb.ovh/api/v1/?q={query}&count=50")
    data = json.loads(json_response.text)
    rows = data['data']['rows']

    return [row['name'] for row in rows]


def pre_search_from_file(file_name: str) -> str:
    """ runs a pre search, return best match if possible """
    split_filename = file_name.split('.')
    result = []
    trim_right = -1
    query_list = split_filename
    while not result and query_list:
        query_list = split_filename[:trim_right]
        query = f'"{" ".join(query_list)}"'
        if not query:
            break
        result = pre_search(query)
        if result:
            break
        trim_right -= 1
    if result:
        return result[0]
    return ""


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Pre Search')
    PARSER.add_argument('query', type=str, help='Search query')
    PARSER.add_argument('--suffix', type=str, help='add suffix', default=None)
    ARGS = PARSER.parse_args()

    suffix = ARGS.suffix if ARGS.suffix else ""

    for name in pre_search(ARGS.query):
        print(name + suffix)
