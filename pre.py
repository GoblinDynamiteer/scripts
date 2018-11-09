#!/usr/bin/env python3.6

""" pre search """

import argparse
import json
import requests

PARSER = argparse.ArgumentParser(description='Pre Search')
PARSER.add_argument('query', type=str, help='Search query')
PARSER.add_argument('--suffix', type=str, help='add suffix', default=None)
ARGS = PARSER.parse_args()

JSON_RESPONSE = requests.get(
    f"https://predb.ovh/api/v1/?q={ARGS.query}&count=50")
DATA = json.loads(JSON_RESPONSE.text)

ROWS = DATA['data']['rows']

suffix = ARGS.suffix if ARGS.suffix else ""

for row in ROWS:
    print(row['name'] + suffix)
