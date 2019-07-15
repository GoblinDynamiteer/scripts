#!/usr/bin/env python3.6

'''Settings file value getter'''

import configparser
import os

import util

DIR_OF_CONFIG_SCRIPT = util.dirname_of_file(__file__)
DEFAULT_SETTINGS_FILE = os.path.join(DIR_OF_CONFIG_SCRIPT, 'settings.ini')

SETTING_VARS = [('$HOME', util.home_dir())]


class ConfigurationManager:
    ''' Reads settings.ini (or other passed ini) '''

    def __init__(self, settings_file=None):
        settings = DEFAULT_SETTINGS_FILE
        if settings_file:
            settings = settings_file
        self.config = configparser.ConfigParser()
        self.config.read(settings)

    def get(self, key):
        '''Get a config setting'''
        try:
            setting = self.config['default'][key]
            for var, rep in SETTING_VARS:
                if var in setting:
                    return setting.replace(var, rep)
            return setting
        except KeyError:
            print(f"{key} is not a valid settings key")
            return ""

    def path(self, key):
        '''Get a path config seting'''
        return self.get(f'path_{key}')
