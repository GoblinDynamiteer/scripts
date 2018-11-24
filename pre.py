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


def _query_list_trim(queries: list, left: int = 0, right: int = 0):
    list_len = len(queries)
    if not right:
        right = list_len
    if left > list_len or abs(right) > list_len:
        return []
    if left > abs(right):
        return []
    return queries[left:right]


def pre_search_from_file(file_name: str) -> str:
    """ runs a pre search, return best match if possible """
    split_filename = file_name.split('.')
    result = []
    trim_right = 0
    trim_left = 0
    query_lists = {"left": split_filename,
                   "right": split_filename, "both": split_filename}
    while True:
        query_lists["left"] = _query_list_trim(split_filename, left=trim_left)
        query_lists["right"] = _query_list_trim(
            split_filename, right=trim_right)
        query_lists["both"] = _query_list_trim(
            split_filename, left=trim_left, right=trim_right)

        if not query_lists["right"] and not query_lists["left"]:
            break

        for _, query_list in query_lists.items():
            if not query_list:
                continue
            query = f'"{" ".join(query_list)}"'
            if not query:
                continue
            result = pre_search(query)
            if result:
                return result[0]
            trim_right -= 1
            trim_left += 1
    return ""


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Pre Search')
    PARSER.add_argument('query', type=str, help='Search query')
    PARSER.add_argument('--suffix', type=str, help='add suffix', default=None)
    PARSER.add_argument(
        '-f', '--file', help='use file search mode', action='store_true')
    ARGS = PARSER.parse_args()

    suffix = ARGS.suffix if ARGS.suffix else ""

    if ARGS.file:
        RET = pre_search_from_file(ARGS.query)
        if not RET:
            print("could not find release")
        print(RET + suffix)
    else:
        RET = pre_search(ARGS.query)
        if not RET:
            print("could not find release")
        else:
            for name in RET:
                print(name + suffix)
