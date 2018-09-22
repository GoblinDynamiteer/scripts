# -*- coding: utf-8 -*-
import json, sys, re, os, urllib.parse, urllib.request

site = "http://www.omdbapi.com"

class omdb_search:
    def __init__(self, query,
        type = None, year = None, api_key = None,
        season = None, episode = None):
        _apk = self._load_api_key()
        self.url_args = {}
        if not _apk and api_key:
            print("Using passed API-key")
            _apk = api_key
        elif not _apk:
            print("no valid API-key found or passed, quitting")
            quit();
        self.url_args['apikey'] = _apk
        self.json_data = ""
        if self._is_imdb(query):
            self.url_args['i'] = query
        else:
            self.url_args['t'] = query
            if self._valid_year(year):
                self.url_args['y'] = year
            if self._valid_type(type):
                self.url_args['type'] = type
        self.url_args['plot'] = "full"
        if season:
            self.url_args['Season'] = season
        if episode:
            self.url_args['Episode'] = episode
        self.search_string_url = site + "?" + urllib.parse.urlencode(self.url_args)
        self._search();

    def get_url(self):
        return self.search_string_url

    def get_api(self):
        return self.url_args['apikey']

    def _search(self):
        try:
            response = urllib.request.urlopen(self.search_string_url, timeout=4).read().decode("utf-8")
            self.json_data = json.loads(response)
        except:
            self.json_data = None

    # Load API-key from text-file in same directory as script file
    def _load_api_key(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        api_txt = os.path.join(script_path, "omdb_api.txt")
        try:
            f = open(api_txt, "r")
            key = f.readline().strip('\n')
            f.close()
            return key
        except:
            print("Could not load OMDb API-key from file")
            return None

    def data(self):
        return self.json_data

    def get_type(self):
        try:
            return self.json_data["Type"]
        except:
            return None

    # Check if string is an IMDB-id
    def _is_imdb(self, string):
        re_imdb = re.compile("^tt\d{1,}")
        return True if re_imdb.search(string) else False

    #Check that string is valid type
    def _valid_type(self, string):
        if string == None:
            return False
        re_type = re.compile("(^movie$|^series$|^episode$)")
        return True if re_type.search(string) else False

    #Check that string is valid year
    def _valid_year(self, string):
        if string == None:
            return False
        re_year = re.compile("^[1-2]\d{3}$")
        return True if (re_year.search(string) or string != None) else False
