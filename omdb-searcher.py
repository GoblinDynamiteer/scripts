# -*- coding: utf-8 -*-
import json, sys, argparse
import omdb

parser = argparse.ArgumentParser(description='OMDb search')
parser.add_argument('query', type=str, help='Search query')
parser.add_argument('-api', dest='api_key', type=str,
    help='API key, if ombd_api.txt does not exists.')
parser.add_argument('-year', dest='search_year', help='Year')
parser.add_argument('-episode', '-ep', dest='episode', help='Episode',
    default=None)
parser.add_argument('-season', '-se', dest='season', help='Season',
    default=None)
parser.add_argument('-type', dest='search_type',
    help='get_type: movie, series, episode')
args = parser.parse_args()

search = omdb.omdb_search(args.query,
    type=args.search_type, api_key=args.api_key,
    year=args.search_year, episode=args.episode,
    season=args.season)

if search.data() == None:
    print("Error searching for {}".format(args.query))
    print("String Generated: {}".format(search.get_url()))
    sys.exit()
else:
    print(json.dumps(search.data(), indent=4))
