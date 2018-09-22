# -*- coding: utf-8 -*-
import paths, json, io, os, filetools
import diskstation as ds
from config import configuration_manager as cfg
from printout import print_class as pr

pr = pr(os.path.basename(__file__))

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

class database:
    def __init__(self):
        self._config = cfg()
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self._db_file  = self._config.get_setting("path", "movdb")
        self._loaded_db = None
        self._load_db()
        self._mov_list = []
        self._key_list = []
        if self._loaded_db is not None and self._loaded_db:
            for mov in self._loaded_db.keys():
                self._mov_list.append(mov)
            for key in self._loaded_db[self._mov_list[0]].keys():
                self._key_list.append(key)

    # Load JSON database to variable
    def _load_db(self):
        if filetools.is_file_empty(self._db_file):
            self._loaded_db = {}
            pr.warning("creating empty database")
        else:
            try:
                with open(self._db_file, 'r') as db:
                    self._loaded_db = json.load(db)
                    pr.info("loaded database file: [ {} ]".format(self._db_file))
            except:
                pr.error("Could not open file: {0}".format(self._db_file))
                self._loaded_db = None

    # Save to database JSON file
    def save(self):
        with open(self._db_file, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(self._loaded_db,
                indent=4, sort_keys=True,
                separators=(',', ': '), ensure_ascii=False)
            outfile.write(to_unicode(str_))
        pr.info("saved database to {}!".format(self._db_file))
        if self.backup_to_ds():
            pr.info("backed up database!")
        else:
            pr.warning("could not backup database!")

    # Add movie to database
    def add(self, movie):
        if self.load_success():
            key = movie['folder']
            if key is not None:
                self._loaded_db[key] = movie

    # Check if database loaded correctly
    def load_success(self):
        return True if self._loaded_db is not None else False

    # Update data for movie
    def update(self, movie_folder, key, data):
        if not self.exists(movie_folder):
            pr.warning("update: {} is not in database!".format(movie_folder))
        else:
            try:
                self._loaded_db[movie_folder][key] = data
                if key is 'omdb':
                    data = "omdb-search"
                pr.info("Updated {} : {} = {}".format(movie_folder, key, data))
            except:
                pr.warning("update: Could not update {}!".format(movie_folder))

    # Get count of movies
    def count(self):
        return len(self._loaded_db)

    # Get a list of all movie titles as strings
    def list_movies(self):
        return self._mov_list

    # Get movie data
    def movie_data(self, movie, key=None):
        if isinstance(movie, list):
            movie = movie[0]
        try:
            if key is None:
                return self._loaded_db[movie]
            else:
                return self._loaded_db[movie][key]
        except:
            return None

    # Check if movie exists in loaded database
    def exists(self, movie_name):
        return True if movie_name in self._loaded_db else False

    # Backup database file
    def backup_to_ds(self):
        bpath = self._config.get_setting("path", "backup")
        dest = os.path.join(bpath, "Database", "Movie")
        return filetools.backup_file(self._db_file, dest)

    # Get omdb data for movie
    def omdb_data(self, movie, key=None):
        omdb = self.movie_data(movie, key="omdb")
        try:
            if key is None:
                return omdb
            else:
                return omdb[key]
        except:
            return None

    # Get a list of all key values as strings
    def list_keys(self):
        return self._key_list

    # Search for movie titles, get hits as a list of strings
    def search(self, search_string, first_hit=False):
        res = []
        for movie_name in self._mov_list:
            if movie_name.lower().find(search_string.lower()) is not -1:
                res.append(movie_name)
                if first_hit is True:
                    break
        return res
