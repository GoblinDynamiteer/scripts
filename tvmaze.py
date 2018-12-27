#!/usr/bin/env python3.6

''' TVMaze '''

import json
import urllib.parse
import urllib.request

import util

URL = "http://api.tvmaze.com"


def _tvmaze_search(url):
    json_response = {}
    try:
        response = urllib.request.urlopen(
            url, timeout=4).read().decode("utf-8")
        json_response = json.loads(response)
    except:
        pass
    return json_response


def show_search(query_string):
    ''' Search a TV Show, query can be show name or IMDb-id'''
    url_args = {}
    url = ""
    if util.is_imdbid(query_string):
        url_args['imdb'] = util.parse_imdbid(query_string)
        url = f'{URL}/lookup/shows?'
    else:
        url_args['q'] = query_string
        url = f'{URL}/singlesearch/shows?'
    url = f'{url}{urllib.parse.urlencode(url_args)}'
    return _tvmaze_search(url)
