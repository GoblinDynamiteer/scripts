#!/usr/bin/env python3.6

'''String output'''

import configparser
import os
import printing

DEFAULT_SETTINGS_FILE = 'settings.ini'

class ConfigurationManager:
    def __init__(self, settings_file=None):
        settings = DEFAULT_SETTINGS_FILE
        if settings_file:
            settings = settings_file
        self.config = configparser.ConfigParser()
        self.config.read(settings)

    def get(self, key):
        return self.config['default'][key]