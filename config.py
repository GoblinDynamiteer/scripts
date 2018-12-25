#!/usr/bin/env python3.6

'''String output'''

import configparser

import util

DEFAULT_SETTINGS_FILE = 'settings.ini'

SETTING_VARS = [('$HOME', util.home_dir())]


class ConfigurationManager:
    def __init__(self, settings_file=None):
        settings = DEFAULT_SETTINGS_FILE
        if settings_file:
            settings = settings_file
        self.config = configparser.ConfigParser()
        self.config.read(settings)

    def get(self, key):
        '''Get a config setting'''
        setting = self.config['default'][key]
        for var, rep in SETTING_VARS:
            if var in setting:
                return setting.replace(var, rep)
        return setting
