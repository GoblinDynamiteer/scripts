#!/usr/bin/env python3

import configparser
from pathlib import Path
from enum import Enum

from base_log import BaseLog
from singleton import Singleton


class SettingKeys(Enum):
    PATH_HOME = "home"
    PATH_MOVIE_DATABASE = "path_movdb"
    PATH_EPISODE_DATABASE = "path_epdb"
    PATH_MOVIE_CACHE_DATABASE = "path_mov_cachedb"
    PATH_TV_CACHE_DATABASE = "path_tv_cachedb"
    PATH_TVSHOW_DATABASE = "path_showdb"
    PATH_DOWNLOADS = "path_download"
    PATH_MISC = "path_misc"
    PATH_MOVIES = "path_film"
    PATH_TV = "path_tv"
    PATH_BACKUP = "path_backup"
    PATH_RESTORE = "path_rest"
    PATH_SCRIPTS = "path_scripts"
    PATH_COOKIES_TXT = "path_cookies_txt"
    PATH_ECONOMY_CSV = "path_economy_csv"
    NAS_SHARE_MOUNT_PATH = "ds_mount_path"
    SMB_CREDENTIALS_REGULAR = "smb_credentials_reg"
    SMB_CREDENTIALS_DRB = "smb_credentials_drb"
    API_KEY_OMDB = "omdb_api_key"
    API_KEY_HUE = "hue_api_key"
    IP_NAS = "ds_ip"
    IP_HUE = "hue_ip"
    WB_SERVER_1 = "server1"
    WB_SERVER_2 = "server2"
    WB_USERNAME = "username"
    WB_PASSWORD = "password"


class SettingSection(Enum):
    WB = "wb"


class ConfigurationManager(BaseLog, metaclass=Singleton):
    SETTINGS = None
    FILE_NAME = "settings.ini"
    BASE_DIR = Path(__file__).resolve().parent
    REPLACEMENTS = [("$HOME", str(Path.home()))]

    def __init__(self, file_path=None, verbose=False):
        self.custom_settings_file_path = file_path
        super().__init__(verbose)
        self.set_log_prefix("CONFIG")
        self.log("init")

    def valid(self):
        if self.SETTINGS is None:
            return self._load()
        return True

    def get(self, key, convert=None, section=None, default=None):
        if self.SETTINGS is None:
            if not self._load():
                return default
        if isinstance(key, SettingKeys):
            key = key.value
        if isinstance(section, SettingSection):
            section = section.value
        value = None
        if section:
            if section in self.SETTINGS:
                if key in self.SETTINGS[section]:
                    value = self.SETTINGS[section][key]
        else:
            for _section in self.SETTINGS:
                if key in self.SETTINGS[_section]:
                    value = self.SETTINGS[_section][key]
                    break
        if value is None:
            self.log_warn(f"could not find key: {key},"
                          f" returning default: {default}")
            return default
        for match, repl in self.REPLACEMENTS:
            value = value.replace(match, repl)
        if convert is not None:
            return convert(value)
        return value

    def _load(self):
        settings_path = self.settings_file_path()
        self.log(f"loading settings: {settings_path}")
        if not settings_path.is_file():
            return False
        self.SETTINGS = configparser.ConfigParser()
        try:
            self.SETTINGS.read(settings_path)
        except Exception as error:
            print(error)
            return False
        return True

    def set_config_file(self, path: Path):
        self.log(f"setting custom settings file: {path}")
        self.custom_settings_file_path = path
        self._load()

    def set_default_config_file(self):
        self.custom_settings_file_path = None
        self.log(f"setting default settings file: {self.settings_file_path()}")
        self._load()

    def path(self, key):
        return self.get(f'path_{key}')

    def settings_file_path(self):
        if self.custom_settings_file_path is not None:
            return self.custom_settings_file_path
        return self.BASE_DIR / self.FILE_NAME


def list_all_values():
    cfg = ConfigurationManager(verbose=True)
    for key in SettingKeys:
        print(f"{key.name} ({key.value}) = "
              f"{cfg.get(key)}")


def main():
    list_all_values()


if __name__ == "__main__":
    main()
