#!/usr/bin/env python3

from argparse import ArgumentParser

from config import ConfigurationManager, SettingSection, SettingKeys
from base_log import BaseLogGlobalSettings

from wb.helper_methods import parse_download_arg
from wb.server import ServerHandler


def get_args():
    _parser = ArgumentParser("WB Handler")
    _parser.add_argument("--download",
                         "-d",
                         default="",
                         dest="download_items",
                         help="item(s) to download, can be index(es) or name.")
    _parser.add_argument("--list",
                         "-l",
                         action="store_true",
                         dest="list_items",
                         help="list items on WB server(s)")
    _parser.add_argument("--verbose",
                         "-v",
                         action="store_true")
    return _parser.parse_args()


def main():
    args = get_args()
    BaseLogGlobalSettings().verbose = args.verbose
    BaseLogGlobalSettings().use_timestamps = True
    handler = ServerHandler()
    for _key in [SettingKeys.WB_SERVER_1, SettingKeys.WB_SERVER_2]:
        _hostname = ConfigurationManager().get(key=_key, section=SettingSection.WB)
        if _hostname:
            handler.add(_hostname)
        else:
            print(f"could not get hostname (key {_key.value}) from settings")
    if not handler.valid():
        print("could not connect to server(s)")
        return
    if not args.download_items or args.list_items:
        handler.print_file_list()
    elif args.download_items:
        _dl_dir = ConfigurationManager().path("download", convert_to_path=True, assert_path_exists=True)
        _keys = parse_download_arg(args.download_items)
        for _key in _keys:
            handler.download(_key, _dl_dir)


if __name__ == "__main__":
    main()
