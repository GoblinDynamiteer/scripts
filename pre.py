#!/usr/bin/env python3.6

""" pre search """

import argparse
import json
import requests

PARSER = argparse.ArgumentParser(description='Pre Search')
PARSER.add_argument('query', type=str, help='Search query')
ARGS = PARSER.parse_args()

JSON_RESPONSE = requests.get(
    f"https://predb.ovh/api/v1/?q={ARGS.query}&count=50")
DATA = json.loads(JSON_RESPONSE.text)

ROWS = DATA['data']['rows']

for row in ROWS:
    print(row['name'])
