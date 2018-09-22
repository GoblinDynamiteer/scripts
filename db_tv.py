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
        self._db_file  = self._config.get_setting("path", "tvdb")
        self._loaded_db = None
        self._load_db()
        self._show_list = []
        self._key_list = []
        if self._loaded_db is not None and self._loaded_db:
            for show in self._loaded_db.keys():
                self._show_list.append(show)
            for key in self._loaded_db[self._show_list[0]].keys():
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
        pr.success("saved database to {}!".format(self._db_file))
        if self.backup_to_ds():
            pr.success("backed up database!")
        else:
            pr.warning("could not backup database!")

    # Add show to database
    def add(self, show):
        if self.load_success():
            key = show['folder']
            if key is not None:
                self._loaded_db[key] = show

    def add_season(self, show_s, season_d):
        if self.load_success():
            show_d = self._loaded_db[show_s]
            show_d['seasons'].append(season_d)
            pr.info(f"added {season_d['folder']} to {show_s}")

    def add_ep(self, show, season, episode_object):
        if self.load_success():
            show_obj = self._loaded_db[show]
            season_ix = 0
            for season_obj in show_obj['seasons']:
                if season_obj['folder'] == season:
                    show_obj['seasons'][season_ix]['episodes'].append(episode_object)
                    break
                season_ix += 1
            self._loaded_db[show] = show_obj

    # Check if database loaded correctly
    def load_success(self):
        return True if self._loaded_db is not None else False

    # Update data for show
    def update(self, show_folder, data, key = None):
        if not self.exists(show_folder):
            pr.warning("update: {} is not in database!".format(show_folder))
        else:
            try:
                if key:
                    self._loaded_db[show_folder][key] = data
                    if key is 'omdb':
                        data = "omdb-search"
                    pr.info("updated {} : {} = {}".format(show_folder, key, data))
                else:
                    self._loaded_db[show_folder] = data
                    pr.info("updated {} with new data!".format(show_folder, data))
            except:
                pr.warning("update: Could not update {}!".format(show_folder))

    # Get count of movies
    def count(self):
        return len(self._loaded_db)

    # Get a list of all show titles as strings
    def list_shows(self):
        return self._show_list

    # Get show data
    def data(self, show_s, key=None):
        if isinstance(show_s, dict) and "folder" in show_s:
            show_s = show_s["folder"]
        if self.exists(show_s):
            show_s = self._show_s_to_formatted_key(show_s)
            if key is None:
                return self._loaded_db[show_s]
            else:
                if key in self._loaded_db[show_s]:
                    return self._loaded_db[show_s][key]
        pr.warning(f"[data] could not retrieve data for show")
        return None

    # Determine if show has an episode
    def has_ep(self, show_s, episode_filename):
        if self.exists(show_s):
            show_s = self._show_s_to_formatted_key(show_s)
            for season in self._loaded_db[show_s]['seasons']:
                for episode in season['episodes']:
                    if episode['file'] == episode_filename:
                        return True
        else:
            pr.error(f"has_ep: not in db: [{show_s}]")
        return False

    # Determine if show has season
    def has_season(self, show_s, season_s):
        if self.exists(show_s):
            show_s = self._show_s_to_formatted_key(show_s)
            for season in self._loaded_db[show_s]['seasons']:
                se = str(season['folder'])
                if se.lower() == season_s.lower():
                    return True
        else:
            pr.error(f"has_season: not in db: [{show_s}]")
        return False

    # Check if tv show exists in loaded database
    def exists(self, show_name):
        for show_s in self._show_list:
            if show_name.lower() == show_s.lower():
                return True
        return False

    # For file name casing mismatch
    def _show_s_to_formatted_key(self, show_s):
        for key in self._show_list:
            if key.lower() == show_s.lower():
                return key
        return False

    # Backup database file
    def backup_to_ds(self):
        bpath = self._config.get_setting("path", "backup")
        dest = os.path.join(bpath, "Database", "TV")
        return filetools.backup_file(self._db_file, dest)

    # Get omdb data for show
    def omdb_data(self, show, key=None):
        omdb = self.movie_data(show, key="omdb")
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
