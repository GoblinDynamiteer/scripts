#!/usr/bin/env python3.6

''' Search TVMaze '''

import json
import argparse
import sys
import tvmaze


PARSER = argparse.ArgumentParser(description='TVMaze search')
PARSER.add_argument('query', type=str, help='Search query, Show title'
                    ' or IMDb-id')
PARSER.add_argument('-episode', '-e', dest='episode', help='Episode',
                    default=None)
PARSER.add_argument('-season', '-s', dest='season', help='Season',
                    default=None)

ARGS = PARSER.parse_args()
MAZE = tvmaze.tvmaze_search(ARGS.query)
SEARCH_RESULT = tvmaze.tvmaze_search(
    ARGS.query, episode=ARGS.episode, season=ARGS.season)

if not SEARCH_RESULT.data():
    print(f"Error searching for: {ARGS.query}")
    print(f"String Generated: {SEARCH_RESULT.get_url()}")
    sys.exit()
else:
    print(json.dumps(SEARCH_RESULT.data(), indent=4))
