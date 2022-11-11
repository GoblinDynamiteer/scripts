#!/usr/bin/env python3

from typing import List

from config import ConfigurationManager, SettingSection, SettingKeys
from base_log import BaseLogGlobalSettings

from wb.helper_methods import parse_download_arg
from wb.server import ServerHandler
from wb.settings import WBSettings
from wb.enums import Command


def get_server_addresses_from_settings() -> List[str]:
    _ret = []
    _num = ConfigurationManager().get(key=SettingKeys.WB_NUM_SERVERS, section=SettingSection.WB, assert_exists=True,
                                      convert=int)
    for _n in range(1, _num + 1):
        _key = SettingKeys.WB_SERVER_PREFIX.value + str(_n)
        _ret.append(ConfigurationManager().get(key=_key, section=SettingSection.WB, assert_exists=True))
    return _ret


def main():
    setting = WBSettings()
    BaseLogGlobalSettings().verbose = setting.verbose
    BaseLogGlobalSettings().use_timestamps = True
    handler = ServerHandler(setting)
    for _addr in get_server_addresses_from_settings():
        handler.add(_addr)
    if not len(handler):
        print(f"no servers found in settings!")
    if not handler.valid():
        print("could not connect to server(s)")
        return
    for cmd in setting.commands:
        if cmd == Command.Download:
            _keys = parse_download_arg(setting.download_items, number_of_items=handler.number_of_items())
            for _key in _keys:
                handler.download(_key)
        elif cmd == Command.List:
            handler.print_file_list()


if __name__ == "__main__":
    main()
