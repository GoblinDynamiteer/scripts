# -*- coding: utf-8 -*-
import json, argparse, tvmaze, sys

parser = argparse.ArgumentParser(description='TVMaze search')
parser.add_argument('query', type = str, help='Search query, Show title'\
    ' or IMDb-id')
parser.add_argument('-episode', '-e', dest='episode', help='Episode',
    default=None)
parser.add_argument('-season', '-s', dest='season', help='Season',
    default=None)

args = parser.parse_args()
maze = tvmaze.tvmaze_search(args.query)
search = tvmaze.tvmaze_search(args.query, episode=args.episode, season=args.season)

if search.data() == None:
    print("Error searching for {}".format(args.query))
    print("String Generated: {}".format(search.get_url()))
    sys.exit()
else:
    print(json.dumps(search.data(), indent=4))
