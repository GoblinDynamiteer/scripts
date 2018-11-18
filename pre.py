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


PARSER = argparse.ArgumentParser(description='Pre Search')
PARSER.add_argument('query', type=str, help='Search query')
PARSER.add_argument('--suffix', type=str, help='add suffix', default=None)
ARGS = PARSER.parse_args()


suffix = ARGS.suffix if ARGS.suffix else ""

for name in pre_search(ARGS.query):
    print(name + suffix)
