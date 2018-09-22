#!/usr/bin/env python3.6

'''String output'''

import configparser
import os
import str_o

PRINT = str_o.PrintClass(os.path.basename(__file__))


class ConfigurationManager:
    def __init__(self, settings_file=None):
        if not settings_file:
            path_of_config_script = os.path.dirname(os.path.abspath(__file__))
            self.filename = os.path.join(path_of_config_script, "settings.ini")
        else:
            self.filename = settings_file
        self.config = None
        self.load_success = False
        self._load_settings()

    def _load_settings(self):
        if os.path.isfile(self.filename):
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.filename)
                self.load_success = True
            except:
                PRINT.error("could not load {}".format(self.filename))
        else:
            PRINT.error("file missing: {}".format(self.filename))

    def get_setting(self, section, key):
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        PRINT.error("{}:{} does not exist in {}"
                    .format(section, key, self.filename))
        return None
