# -*- coding: utf-8 -*-
import json, sys, re, os, urllib.parse, urllib.request

class tvmaze_search:
    def __init__(self, query, season=None, episode=None):
        self.site = "http://api.tvmaze.com"
        self.url_args = {}
        self.json_data = ""
        if self._is_imdb(query):
            self.url_args['imdb'] = query
            self.site +=  "/lookup/shows"
        elif self._is_possible_maze_id(query):
            self.site += f"/shows/{query}"
        else:
            self.url_args['q'] = query
            self.site += "/singlesearch/shows"
        self.search_string_url = self.site + "?" + urllib.parse.urlencode(self.url_args)
        self._search();
        if self.json_data:
            self.tvmaze_url = self.json_data["_links"]["self"]["href"]
            if season and not episode:
                self.search_string_url = self.tvmaze_url + f"/seasons"
                self._search();
                for json_season in self.json_data:
                    if int(json_season['number']) == int(season):
                        self.json_data = json_season
                        break
            if episode and season:
                self.url_args = {}
                self.url_args['season'] = season
                self.url_args['number'] = episode
                self.search_string_url = self.tvmaze_url + "/episodebynumber?" + urllib.parse.urlencode(self.url_args)
                self._search();

    def _search(self):
        try:
            response = urllib.request.urlopen(self.search_string_url, timeout=4).read().decode("utf-8")
            self.json_data = json.loads(response)
        except:
            self.json_data = None

    def get_url(self):
        return self.search_string_url

    # Check if string is an IMDB-id
    def _is_imdb(self, string):
        re_imdb = re.compile("^tt\d{1,}")
        return True if re_imdb.search(string) else False

    def _is_possible_maze_id(self, string):
        re_imdb = re.compile("^\d{1,}")
        return True if re_imdb.search(string) else False

    def data(self):
        return self.json_data
