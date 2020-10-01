#!/usr/bin/env python3.6

''' TVMaze '''

import json
import urllib.parse
import urllib.request

import util

URL = "http://api.tvmaze.com"

# TODO: refactor / move all methods into TvMazeData class


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


def show_search(query_string: str):
    ''' Search a TV Show, query can be show name or IMDb-id'''
    if not isinstance(query_string, str):
        raise TypeError('query has to be a string!')
    if not query_string:
        raise ValueError('query cannot be empty!')
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


def episode_has_aired(show_name: str, season: int, episode: int, show_maze_id: int = None) -> bool:
    result = episode_search(show_name, season, episode, show_maze_id)
    if 'airdate' in result:
        timestamp = util.date_str_to_timestamp(result['airdate'], r'%Y-%m-%d')
        return timestamp < util.now_timestamp()
    return False


def episode_search(show_name: str, season: int, episode: int, show_maze_id: int = None) -> dict:
    ''' Retrieve episode data '''
    url_args = {'season': season, 'number': episode}
    if not show_maze_id:
        show_maze_id = id_from_show_name(show_name)
        if not show_maze_id:
            return None
    url = f'{URL}/shows/{show_maze_id}/episodebynumber?{urllib.parse.urlencode(url_args)}'
    return _tvmaze_search(url)


class TvMazeData(metaclass=util.Singleton):
    "TVMaze data holder, only executes a new search if needed"
    DATA = {}

    def get_json_all_episodes(self, show_id: int) -> dict:
        url = self.url(show_id)
        if url not in self.DATA:
            self.DATA[url] = _tvmaze_search(url)
        return self.DATA[url]

    def get_json_all_special_episodes(self, show_id: int) -> dict:
        url = self.url(show_id) + "?specials=1"
        if url not in self.DATA:
            special_list = [ep for ep in _tvmaze_search(
                url) if ep["number"] is None]
            self.DATA[url] = special_list
        return self.DATA[url]

    def url(self, show_id: int):
        return f"http://api.tvmaze.com/shows/{show_id}/episodes"


def main():
    # pylint: disable=import-outside-toplevel
    import argparse
    # pylint: enable=import-outside-toplevel
    parser = argparse.ArgumentParser("tvmaze searcher")
    parser.add_argument("id", type=int)
    parser.add_argument("--specials", action="store_true")
    args = parser.parse_args()
    tvmaze_data = TvMazeData()
    if args.specials:
        data = tvmaze_data.get_json_all_special_episodes(args.id)
    else:
        data = tvmaze_data.get_json_all_episodes(args.id)
    print("data for", tvmaze_data.url(args.id))
    print(json.dumps(data, indent=4))


if __name__ == "__main__":
    main()
