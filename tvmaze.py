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


def id_from_show_name(show_name: str):
    'Try to determine tvmaze id from show name'
    result = show_search(show_name)
    return result.get('id', None)


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


def episode_search(show_name: str, season: int, episode: int, show_maze_id: int = None) -> dict:
    ''' Retrieve episode data '''
    url_args = {'season': season, 'number': episode}
    if not show_maze_id:
        show_maze_id = 1
        # TODO: determine maze id from show_name
        pass
    url = f'{URL}/shows/{show_maze_id}/episodebynumber?{urllib.parse.urlencode(url_args)}'
    return _tvmaze_search(url)
