#!/usr/bin/env python3.6

''' Searches the OMDb database '''

import json
import urllib.parse
import urllib.request

import util
from config import ConfigurationManager

CFG = ConfigurationManager()

URL = "http://www.omdbapi.com"
API_KEY = CFG.get('omdb_api_key')


def _omdb_search(url):
    json_response = {}
    try:
        response = urllib.request.urlopen(
            url, timeout=4).read().decode("utf-8")
        json_response = json.loads(response)
    except:
        pass
    return json_response


def movie_search(query_string, year=None):
    ''' Searches the OMDb database for a movie, returns
        the json response as a dict'''
    url_args = {'apikey': API_KEY, 'type': 'movie'}
    if util.is_imdbid(query_string):
        url_args['i'] = util.parse_imdbid(query_string)
    else:
        url_args['t'] = query_string
    if util.is_valid_year(year):
        url_args['y'] = year
    url = f'{URL}?{urllib.parse.urlencode(url_args)}'
    print(url)
    return _omdb_search(url)
