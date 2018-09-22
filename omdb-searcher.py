#!/usr/bin/env python3.6

''' Search OMDb '''

import json
import sys
import argparse
import omdb

PARSER = argparse.ArgumentParser(description='OMDb search')
PARSER.add_argument('query', type=str, help='Search query')
PARSER.add_argument('-api', dest='api_key', type=str,
                    help='API key, if ombd_api.txt does not exists.')
PARSER.add_argument('-year', dest='search_year', help='Year')
PARSER.add_argument('-episode', '-ep', dest='episode', help='Episode',
                    default=None)
PARSER.add_argument('-season', '-se', dest='season', help='Season',
                    default=None)
PARSER.add_argument('-type', dest='search_type',
                    help='get_type: movie, series, episode')
ARGS = PARSER.parse_args()

SEARCH_RESULT = omdb.omdb_search(ARGS.query,
                                 type=ARGS.search_type, api_key=ARGS.api_key,
                                 year=ARGS.search_year, episode=ARGS.episode,
                                 season=ARGS.season)

if not SEARCH_RESULT.data():
    print(f"Error searching for {ARGS.query}")
    print(f"String Generated: {SEARCH_RESULT.get_url()}")
    sys.exit()
else:
    print(json.dumps(SEARCH_RESULT.data(), indent=4))
